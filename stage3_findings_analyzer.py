#!/usr/bin/env python3

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import logging
from typing import Dict, List, Optional, Tuple, Set
import yaml
from collections import defaultdict, Counter
import re

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage3FindingsAnalyzer:
    """
    Stage 3: Enhanced Findings Identification with Buried Wins Criteria v4.0
    Automated confidence scoring and executive-ready insights
    """
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4000,
            temperature=0.2
        )
        
        # Initialize Supabase database
        self.db = SupabaseDatabase()
        
        # Load criteria from config
        self.criteria = self.config.get('criteria', {})
        
        # Enhanced evaluation criteria from Buried Wins v4.0
        self.evaluation_criteria = {
            'novelty': {
                'description': 'The observation is new/unexpected for the client, challenging assumptions or established beliefs',
                'trigger_question': 'Is this something the client has not previously recognized?'
            },
            'actionability': {
                'description': 'The observation suggests a clear step, fix, or action the client could take to improve outcomes',
                'trigger_question': 'Could this directly inform a roadmap item or go-to-market plan?'
            },
            'specificity': {
                'description': 'The finding is precise, detailed, and not generic. References a particular feature, workflow, market condition, or user group',
                'trigger_question': 'Is this about a concrete product aspect, metric, or process?'
            },
            'materiality': {
                'description': 'The finding has meaningful business impact—affecting revenue, customer satisfaction, retention, or competitive positioning',
                'trigger_question': 'Does this affect a key business KPI or customer segment?'
            },
            'recurrence': {
                'description': 'The same observation appears across multiple interviews or sources, suggesting a theme',
                'trigger_question': 'Is this echoed by two or more stakeholders/roles?'
            },
            'stakeholder_weight': {
                'description': 'The observation comes from a high-influence decision maker or critical user persona',
                'trigger_question': 'Does the source matter to the client\'s business priorities?'
            },
            'tension_contrast': {
                'description': 'The finding exposes a tension, tradeoff, or significant contrast, revealing friction or opportunity',
                'trigger_question': 'Does this highlight a dilemma, blocker, or gap vs. competitors?'
            },
            'metric_quantification': {
                'description': 'The finding is supported by a tangible metric, timeframe, or quantifiable outcome',
                'trigger_question': 'Is there a number or business measure that makes this impactful?'
            }
        }
        
        # Processing metrics
        self.processing_metrics = {
            "total_quotes_processed": 0,
            "patterns_identified": 0,
            "findings_generated": 0,
            "priority_findings": 0,
            "standard_findings": 0,
            "processing_errors": 0
        }
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Default configuration for Stage 3 with enhanced scoring"""
        return {
            'stage3': {
                'confidence_thresholds': {
                    'priority_finding': 3.0,
                    'standard_finding': 2.0,
                    'minimum_confidence': 1.0
                },
                'pattern_thresholds': {
                    'minimum_quotes': 2,
                    'minimum_companies': 1,
                    'minimum_criteria_met': 1
                },
                'stakeholder_multipliers': {
                    'executive_perspective': 1.5,
                    'budget_holder_perspective': 1.5,
                    'champion_perspective': 1.3,
                    'end_user_perspective': 1.0,
                    'it_technical_perspective': 1.0
                },
                'decision_impact_multipliers': {
                    'deal_tipping_point': 2.0,
                    'differentiator_factor': 1.5,
                    'blocker_factor': 1.5,
                    'high_salience': 1.4,
                    'medium_salience': 1.2,
                    'low_salience': 1.0
                },
                'evidence_strength_multipliers': {
                    'strong_positive': 1.3,
                    'strong_negative': 1.3,
                    'perspective_shifting': 1.3,
                    'organizational_conflict': 1.2,
                    'standard_evidence': 1.0
                },
                'batch_size': 100,
                'max_patterns_per_criterion': 5,
                'max_quotes_per_finding': 3
            },
            'criteria': {
                'product_capability': {'description': 'Functionality, features, performance, and core solution fit'},
                'implementation_onboarding': {'description': 'Deployment ease, time-to-value, setup complexity'},
                'integration_technical_fit': {'description': 'APIs, data compatibility, technical architecture alignment'},
                'support_service_quality': {'description': 'Post-sale support, responsiveness, expertise, SLAs'},
                'security_compliance': {'description': 'Data protection, certifications, governance, risk management'},
                'market_position_reputation': {'description': 'Brand trust, references, analyst recognition, market presence'},
                'vendor_stability': {'description': 'Financial health, roadmap clarity, long-term viability'},
                'sales_experience_partnership': {'description': 'Buying process quality, relationship building, trust'},
                'commercial_terms': {'description': 'Price, contract flexibility, ROI, total cost of ownership'},
                'speed_responsiveness': {'description': 'Implementation timeline, decision-making speed, agility'}
            }
        }
    
    def get_scored_quotes(self, client_id: str = 'default') -> pd.DataFrame:
        """Get all quotes with scores from Supabase"""
        df = self.db.get_scored_quotes(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} scored quotes from Supabase for client {client_id}")
        return df
    
    def evaluate_finding_criteria(self, quotes_data: List[Dict]) -> Dict:
        """Evaluate quotes against the 8 Buried Wins evaluation criteria"""
        criteria_scores = {criterion: 0 for criterion in self.evaluation_criteria.keys()}
        
        # Analyze quotes for each criterion
        for quote in quotes_data:
            text = f"{quote.get('original_quote', '')} {quote.get('relevance_explanation', '')}"
            text_lower = text.lower()
            
            # Novelty check
            if any(word in text_lower for word in ['new', 'unexpected', 'surprising', 'didn\'t realize', 'first time']):
                criteria_scores['novelty'] += 1
            
            # Actionability check
            if any(word in text_lower for word in ['should', 'could', 'need to', 'must', 'recommend', 'suggest']):
                criteria_scores['actionability'] += 1
            
            # Specificity check
            if any(word in text_lower for word in ['specific', 'particular', 'exactly', 'specifically', 'concrete']):
                criteria_scores['specificity'] += 1
            
            # Materiality check
            if any(word in text_lower for word in ['revenue', 'cost', 'money', 'business', 'impact', 'critical', 'important']):
                criteria_scores['materiality'] += 1
            
            # Recurrence check (handled separately in pattern analysis)
            if len(quotes_data) >= 2:
                criteria_scores['recurrence'] = 1
            
            # Stakeholder weight check
            if any(word in text_lower for word in ['executive', 'ceo', 'director', 'manager', 'decision']):
                criteria_scores['stakeholder_weight'] += 1
            
            # Tension/contrast check
            if any(word in text_lower for word in ['but', 'however', 'although', 'despite', 'while', 'tension', 'conflict']):
                criteria_scores['tension_contrast'] += 1
            
            # Metric/quantification check
            if re.search(r'\d+%|\d+ percent|\$\d+|\d+ dollars|\d+ hours|\d+ days', text_lower):
                criteria_scores['metric_quantification'] += 1
        
        # Normalize scores
        for criterion in criteria_scores:
            criteria_scores[criterion] = min(criteria_scores[criterion], 1)  # Cap at 1
        
        return criteria_scores
    
    def calculate_enhanced_confidence_score(self, quotes_data: List[Dict], criteria_scores: Dict) -> float:
        """Calculate enhanced confidence score using Buried Wins v4.0 framework"""
        config = self.config['stage3']
        
        # Base score: Number of criteria met (2-8 points)
        base_score = sum(criteria_scores.values())
        
        if base_score < 2:  # Minimum requirement not met
            return 0.0
        
        # Stakeholder weight multiplier
        stakeholder_multiplier = 1.0
        for quote in quotes_data:
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['executive', 'ceo', 'director', 'manager']):
                stakeholder_multiplier = max(stakeholder_multiplier, config['stakeholder_multipliers']['executive_perspective'])
            elif any(word in text for word in ['budget', 'finance', 'cost']):
                stakeholder_multiplier = max(stakeholder_multiplier, config['stakeholder_multipliers']['budget_holder_perspective'])
            elif any(word in text for word in ['champion', 'advocate', 'supporter']):
                stakeholder_multiplier = max(stakeholder_multiplier, config['stakeholder_multipliers']['champion_perspective'])
        
        # Decision impact multiplier
        decision_impact_multiplier = 1.0
        for quote in quotes_data:
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['deal breaker', 'critical', 'essential']):
                decision_impact_multiplier = max(decision_impact_multiplier, config['decision_impact_multipliers']['deal_tipping_point'])
            elif any(word in text for word in ['differentiator', 'unique', 'competitive']):
                decision_impact_multiplier = max(decision_impact_multiplier, config['decision_impact_multipliers']['differentiator_factor'])
            elif any(word in text for word in ['blocker', 'obstacle', 'problem']):
                decision_impact_multiplier = max(decision_impact_multiplier, config['decision_impact_multipliers']['blocker_factor'])
        
        # Evidence strength multiplier
        evidence_strength_multiplier = 1.0
        for quote in quotes_data:
            score = quote.get('score', 0)
            if score >= 4:
                evidence_strength_multiplier = max(evidence_strength_multiplier, config['evidence_strength_multipliers']['strong_positive'])
            elif score <= 1:
                evidence_strength_multiplier = max(evidence_strength_multiplier, config['evidence_strength_multipliers']['strong_negative'])
        
        # Calculate final confidence score
        final_confidence = base_score * stakeholder_multiplier * decision_impact_multiplier * evidence_strength_multiplier
        
        return min(final_confidence, 10.0)  # Cap at 10.0
    
    def select_optimal_quotes(self, quotes_data: List[Dict], max_quotes: int = 3) -> List[Dict]:
        """Select optimal quotes for finding presentation using automated logic"""
        if not quotes_data:
            return []
        
        # Score each quote for selection priority
        scored_quotes = []
        for quote in quotes_data:
            priority_score = 0
            
            # Primary priority factors
            if quote.get('score', 0) >= 4:  # High scores
                priority_score += 10
            elif quote.get('score', 0) <= 1:  # Critical issues
                priority_score += 8
            
            # Deal tipping point priority
            text = quote.get('original_quote', '').lower()
            if any(word in text for word in ['deal breaker', 'critical', 'essential', 'must have']):
                priority_score += 15
            
            # Stakeholder perspective priority
            if any(word in text for word in ['executive', 'ceo', 'director', 'manager']):
                priority_score += 12
            elif any(word in text for word in ['budget', 'finance', 'cost']):
                priority_score += 10
            
            # Sentiment priority
            if quote.get('score', 0) >= 4 or quote.get('score', 0) <= 1:
                priority_score += 5
            
            # Specificity bonus
            if len(quote.get('original_quote', '')) > 100:  # Substantial discussion
                priority_score += 3
            
            scored_quotes.append((priority_score, quote))
        
        # Sort by priority score and select top quotes
        scored_quotes.sort(key=lambda x: x[0], reverse=True)
        selected_quotes = [quote for _, quote in scored_quotes[:max_quotes]]
        
        return selected_quotes
    
    def identify_enhanced_patterns(self, df: pd.DataFrame) -> Dict:
        """Identify patterns with enhanced evaluation criteria"""
        logger.info("🔍 Identifying enhanced patterns across companies...")
        
        patterns = {}
        thresholds = self.config['stage3']['pattern_thresholds']
        
        for criterion in self.criteria.keys():
            criterion_data = df[df['criterion'] == criterion].copy()
            
            if len(criterion_data) < thresholds['minimum_quotes']:
                continue
            
            # Group by company and analyze patterns
            company_patterns = self._analyze_enhanced_company_patterns(criterion_data, criterion)
            
            # Filter patterns by enhanced thresholds
            valid_patterns = []
            for pattern in company_patterns:
                if (pattern['quote_count'] >= thresholds['minimum_quotes'] and
                    pattern['company_count'] >= thresholds['minimum_companies']):
                    
                    # CRITICAL FIX: Ensure pattern has quotes_data
                    if not pattern.get('quotes_data'):
                        logger.warning(f"⚠️ Skipping pattern for {criterion} - no quotes_data found")
                        continue
                    
                    # Evaluate against Buried Wins criteria
                    criteria_scores = self.evaluate_finding_criteria(pattern['quotes_data'])
                    criteria_met = sum(criteria_scores.values())
                    
                    if criteria_met >= thresholds['minimum_criteria_met']:
                        # Calculate enhanced confidence score
                        enhanced_confidence = self.calculate_enhanced_confidence_score(
                            pattern['quotes_data'], criteria_scores
                        )
                        
                        if enhanced_confidence >= self.config['stage3']['confidence_thresholds']['minimum_confidence']:
                            # CRITICAL FIX: Ensure selected_quotes is not empty
                            selected_quotes = self.select_optimal_quotes(pattern['quotes_data'])
                            if not selected_quotes:
                                logger.warning(f"⚠️ Skipping pattern for {criterion} - select_optimal_quotes returned empty list")
                                continue
                            
                            pattern['enhanced_confidence'] = enhanced_confidence
                            pattern['criteria_scores'] = criteria_scores
                            pattern['criteria_met'] = criteria_met
                            pattern['selected_quotes'] = selected_quotes
                            valid_patterns.append(pattern)
            
            if valid_patterns:
                # Sort by enhanced confidence score
                valid_patterns.sort(key=lambda x: x['enhanced_confidence'], reverse=True)
                patterns[criterion] = valid_patterns[:self.config['stage3']['max_patterns_per_criterion']]
        
        logger.info(f"✅ Identified enhanced patterns for {len(patterns)} criteria")
        return patterns
    
    def _analyze_enhanced_company_patterns(self, criterion_data: pd.DataFrame, criterion: str) -> List[Dict]:
        """Analyze patterns for a specific criterion with loosened constraints - REDESIGNED FOR EVIDENCE-BACKED INSIGHTS"""
        patterns = []
        
        # Group by company
        company_groups = criterion_data.groupby('company')
        
        for company, company_quotes in company_groups:
            # LOOSENED CONSTRAINT: Allow single quotes for strong evidence
            if len(company_quotes) < 1:  # Changed from 2 to 1
                continue
            
            # NEW: Group quotes by score ranges to allow multiple patterns per company
            # 0-1.9 = Low relevance (skip)
            # 2.0-2.9 = Moderate relevance 
            # 3.0-3.9 = High relevance
            # 4.0-5.0 = Critical relevance
            
            low_relevance = company_quotes[company_quotes['score'] < 2.0]
            moderate_relevance = company_quotes[(company_quotes['score'] >= 2.0) & (company_quotes['score'] < 3.0)]
            high_relevance = company_quotes[(company_quotes['score'] >= 3.0) & (company_quotes['score'] < 4.0)]
            critical_relevance = company_quotes[company_quotes['score'] >= 4.0]
            
            # Create patterns for each relevance level that has quotes
            relevance_groups = [
                ('moderate', moderate_relevance, 2.0, 2.9),
                ('high', high_relevance, 3.0, 3.9),
                ('critical', critical_relevance, 4.0, 5.0)
            ]
            
            for relevance_level, quotes_subset, min_score, max_score in relevance_groups:
                if len(quotes_subset) == 0:
                    continue
                
                # Prepare quotes data for evaluation
                quotes_data = []
                for _, quote in quotes_subset.iterrows():
                    quotes_data.append({
                        'original_quote': quote.get('original_quote', ''),
                        'relevance_explanation': quote.get('relevance_explanation', ''),
                        'score': quote.get('score', 0),
                        'confidence': quote.get('confidence', 'medium'),
                        'context_keywords': quote.get('context_keywords', 'neutral'),
                        'question_relevance': quote.get('question_relevance', 'unrelated'),
                        'response_id': quote.get('response_id', None),
                        'company': quote.get('company', company)
                    })
                
                # Analyze sentiment patterns within this relevance level
                avg_score = quotes_subset['score'].mean()
                score_std = quotes_subset['score'].std()
                
                # Extract common themes from relevance explanations
                themes = self._extract_themes(quotes_subset['relevance_explanation'].tolist())
                
                # Identify deal impact patterns
                deal_impacts = quotes_subset['context_keywords'].value_counts().to_dict()
                
                # Evaluate finding criteria for this pattern
                criteria_scores = self.evaluate_finding_criteria(quotes_data)
                criteria_met = sum(1 for score in criteria_scores.values() if score > 0)
                
                # Calculate enhanced confidence score
                enhanced_confidence = self.calculate_enhanced_confidence_score(quotes_data, criteria_scores)
                
                # Select optimal quotes for this pattern
                selected_quotes = self.select_optimal_quotes(quotes_data, self.config['stage3']['max_quotes_per_finding'])
                
                pattern = {
                    'criterion': criterion,
                    'company': company,
                    'relevance_level': relevance_level,
                    'score_range': (min_score, max_score),
                    'quote_count': len(quotes_subset),
                    'company_count': 1,  # Will be updated in cross-company analysis
                    'avg_score': avg_score,
                    'score_std': score_std,
                    'themes': themes,
                    'deal_impacts': deal_impacts,
                    'quotes_data': quotes_data,
                    'selected_quotes': selected_quotes,
                    'sample_quotes': quotes_subset['original_quote'].head(3).tolist(),
                    'criteria_scores': criteria_scores,
                    'criteria_met': criteria_met,
                    'enhanced_confidence': enhanced_confidence
                }
                
                patterns.append(pattern)
        
        # NEW: Simplified cross-company analysis - focus on individual patterns first
        # Only group if there are truly similar patterns across companies
        cross_company_patterns = self._analyze_cross_company_patterns(patterns, criterion)
        
        return cross_company_patterns
    
    def _analyze_cross_company_patterns(self, company_patterns: List[Dict], criterion: str) -> List[Dict]:
        """Analyze patterns across multiple companies - REDESIGNED TO PRIORITIZE INDIVIDUAL PATTERNS"""
        if len(company_patterns) < 2:
            return company_patterns
        
        # NEW APPROACH: Prioritize individual patterns, only group when truly similar
        # Use fuzzy matching for theme similarity instead of exact matches
        
        # Group by similar themes using fuzzy matching
        theme_groups = defaultdict(list)
        for pattern in company_patterns:
            # Create a fuzzy theme key based on relevance level and score range
            theme_key = f"{pattern['relevance_level']}_{pattern['score_range'][0]}-{pattern['score_range'][1]}"
            
            # Add company-specific themes if they exist
            if pattern['themes']:
                theme_key += f"_{'_'.join(pattern['themes'][:2])}"  # Top 2 themes
            
            theme_groups[theme_key].append(pattern)
        
        cross_company_patterns = []
        used_companies = set()
        
        # First, try to create cross-company patterns for similar themes
        # BUT: Only if there are multiple companies with similar patterns
        for theme_key, patterns in theme_groups.items():
            if len(patterns) >= 2:  # Multiple companies with similar themes
                # Check if these are from different companies
                companies = set(p['company'] for p in patterns)
                if len(companies) >= 2:  # Actually different companies
                    # Combine patterns
                    combined_pattern = {
                        'criterion': criterion,
                        'companies': [p['company'] for p in patterns],
                        'company_count': len(patterns),
                        'quote_count': sum(p['quote_count'] for p in patterns),
                        'avg_score': sum(p['avg_score'] for p in patterns) / len(patterns),
                        'score_std': pd.Series([p['avg_score'] for p in patterns]).std(),
                        'themes': list(set(theme for p in patterns for theme in p['themes'])),
                        'deal_impacts': self._combine_deal_impacts([p['deal_impacts'] for p in patterns]),
                        'quotes_data': [q for p in patterns for q in p['quotes_data']],
                        'selected_quotes': [q for p in patterns for q in p['selected_quotes']],
                        'sample_quotes': [q for p in patterns for q in p['sample_quotes'][:2]],
                        'criteria_scores': self._combine_criteria_scores([p['criteria_scores'] for p in patterns]),
                        'criteria_met': max(p['criteria_met'] for p in patterns),
                        'enhanced_confidence': max(p['enhanced_confidence'] for p in patterns),
                        'relevance_level': patterns[0]['relevance_level'],
                        'score_range': patterns[0]['score_range'],
                        'is_cross_company': True
                    }
                    cross_company_patterns.append(combined_pattern)
                    
                    # Mark companies as used
                    for pattern in patterns:
                        used_companies.add(pattern['company'])
        
        # Then, add individual company patterns that weren't used in cross-company patterns
        # THIS IS THE KEY CHANGE: Individual patterns are valuable and should be included
        for pattern in company_patterns:
            if pattern['company'] not in used_companies:
                # Mark as individual pattern
                pattern['is_cross_company'] = False
                cross_company_patterns.append(pattern)
        
        return cross_company_patterns
    
    def _combine_criteria_scores(self, criteria_scores_list: List[Dict]) -> Dict:
        """Combine criteria scores from multiple patterns"""
        combined = defaultdict(int)
        for scores in criteria_scores_list:
            for criterion, score in scores.items():
                combined[criterion] += score
        return dict(combined)
    
    def _combine_deal_impacts(self, deal_impacts_list: List[Dict]) -> Dict:
        """Combine deal impacts from multiple patterns"""
        combined = defaultdict(int)
        for impacts in deal_impacts_list:
            for impact, count in impacts.items():
                combined[impact] += count
        return dict(combined)
    
    def _extract_themes(self, explanations: List[str]) -> List[str]:
        """Extract common themes from relevance explanations"""
        if not explanations:
            return []
        
        # Enhanced keyword extraction
        keywords = []
        for explanation in explanations:
            # Extract key phrases
            words = explanation.lower().split()
            for i, word in enumerate(words):
                if len(word) > 4 and word not in ['about', 'their', 'this', 'that', 'with', 'from']:
                    keywords.append(word)
        
        # Count and return top themes
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(5)]
    
    def generate_enhanced_findings(self, patterns: Dict) -> List[Dict]:
        """Generate findings with enhanced confidence scoring and credibility enforcement"""
        logger.info("🎯 Generating enhanced findings...")
        
        findings = []
        used_primary_quote_ids: Set[str] = set()  # Track used primary quotes for recycling prevention
        
        for criterion, criterion_patterns in patterns.items():
            if not criterion_patterns:
                continue
            criterion_findings = self._generate_criterion_enhanced_findings(criterion, criterion_patterns)
            for finding in criterion_findings:
                # --- CREDIBILITY/EVIDENCE ENFORCEMENT ---
                # Count unique companies and unique quotes
                companies = set()
                unique_quote_ids = set()
                for q in finding['selected_quotes']:
                    # Try to get response_id if present in quote dict
                    rid = q.get('response_id') or q.get('id') or q.get('quote_id')
                    if rid:
                        unique_quote_ids.add(rid)
                    # Try to get company if present
                    company = q.get('company')
                    if company:
                        companies.add(company)
                # Fallback: use companies_affected and quote_count if not present
                if not companies and finding.get('companies_affected'):
                    companies = set([finding['companies_affected']])
                if not unique_quote_ids and finding.get('quote_count'):
                    unique_quote_ids = set([str(finding['quote_count'])])
                num_companies = len(companies)
                num_quotes = len(unique_quote_ids)
                # --- Quote recycling prevention ---
                primary_quote = finding['selected_quotes'][0] if finding['selected_quotes'] else None
                primary_quote_id = primary_quote.get('response_id') if primary_quote else None
                if primary_quote_id and primary_quote_id in used_primary_quote_ids:
                    logger.warning(f"⚠️ Skipping finding for {criterion} - primary quote {primary_quote_id} already used in another finding")
                    continue  # Block duplicate primary quote
                if primary_quote_id:
                    used_primary_quote_ids.add(primary_quote_id)
                # --- Credibility tier assignment ---
                if num_companies >= 3 and num_quotes >= 6:
                    credibility_tier = 'Tier 1: Multi-company, strong evidence'
                elif num_companies == 2 and num_quotes >= 3:
                    credibility_tier = 'Tier 2: Two companies, moderate evidence'
                elif num_companies == 1 and num_quotes >= 1:
                    credibility_tier = 'Tier 3: Single company, anecdotal'
                else:
                    credibility_tier = 'Tier 4: Insufficient evidence (not saved)'
                finding['credibility_tier'] = credibility_tier
                # --- Block or downgrade based on evidence ---
                if credibility_tier == 'Tier 4: Insufficient evidence (not saved)':
                    logger.warning(f"⚠️ Skipping finding for {criterion} - insufficient evidence: {num_companies} companies, {num_quotes} quotes")
                    continue
                findings.append(finding)
        # Sort findings by confidence score
        findings.sort(key=lambda x: x['enhanced_confidence'], reverse=True)
        # Classify findings by priority
        for finding in findings:
            if finding['enhanced_confidence'] >= self.config['stage3']['confidence_thresholds']['priority_finding']:
                finding['priority_level'] = 'priority'
                self.processing_metrics["priority_findings"] += 1
            elif finding['enhanced_confidence'] >= self.config['stage3']['confidence_thresholds']['standard_finding']:
                finding['priority_level'] = 'standard'
                self.processing_metrics["standard_findings"] += 1
            else:
                finding['priority_level'] = 'low'
        logger.info(f"✅ Generated {len(findings)} enhanced findings (with credibility enforcement)")
        return findings
    
    def _generate_criterion_enhanced_findings(self, criterion: str, patterns: List[Dict]) -> List[Dict]:
        """Generate findings for a specific criterion - REDESIGNED FOR MULTIPLE EVIDENCE-BACKED INSIGHTS"""
        findings = []
        
        if not patterns:
            return findings
        
        # NEW APPROACH: Generate findings for each pattern based on evidence strength
        # Each pattern represents a distinct insight that can stand alone
        
        # Sort patterns by enhanced confidence score
        sorted_patterns = sorted(patterns, key=lambda x: x['enhanced_confidence'], reverse=True)
        
        for pattern in sorted_patterns:
            # Generate finding for each pattern that meets minimum evidence threshold
            if pattern['quote_count'] >= 1 and pattern['enhanced_confidence'] >= 1.0:  # Loosened threshold
                finding = self._create_pattern_based_finding(criterion, pattern)
                if finding:
                    findings.append(finding)
        
        # Generate additional trend findings if we have multiple patterns
        # Note: Removed trend finding generation to focus on individual pattern-based findings
        # Each pattern now generates its own finding for better granularity
        
        return findings
    
    def _create_pattern_based_finding(self, criterion: str, pattern: Dict) -> Optional[Dict]:
        """Create a finding based on a single pattern - NEW METHOD FOR EVIDENCE-BACKED INSIGHTS"""
        if not pattern:
            return None
        
        # Ensure we have selected quotes
        selected_quotes = pattern.get('selected_quotes', [])
        if not selected_quotes:
            logger.warning(f"⚠️ Skipping finding for {criterion} - no selected_quotes found in pattern")
            return None
        
        criterion_desc = self.criteria.get(criterion, {}).get('description', criterion)
        
        # Determine finding type based on relevance level and sentiment
        finding_type = self._determine_finding_type(pattern)
        
        # Generate finding text
        finding_text = self._generate_pattern_based_finding_text(criterion, pattern, finding_type, criterion_desc)
        
        # Format selected quotes with attribution
        formatted_quotes = []
        for quote in selected_quotes[:self.config['stage3']['max_quotes_per_finding']]:
            formatted_quotes.append({
                'text': quote.get('original_quote', ''),
                'score': quote.get('score', 0),
                'attribution': f"Score: {quote.get('score', 0)} - {quote.get('context_keywords', 'neutral')}"
            })
        
        # Determine credibility tier based on evidence strength
        credibility_tier = self._determine_credibility_tier(pattern)
        
        return {
            'criterion': criterion,
            'finding_type': finding_type,
            'priority_level': 'standard',  # Will be updated in main function
            'title': f"{criterion.replace('_', ' ').title()} - {finding_type.title()} ({pattern['relevance_level']} relevance)",
            'description': finding_text,
            'enhanced_confidence': pattern['enhanced_confidence'],
            'criteria_scores': pattern.get('criteria_scores', {}),
            'criteria_met': pattern.get('criteria_met', 0),
            'impact_score': pattern['avg_score'],
            'companies_affected': pattern.get('company_count', 1),
            'quote_count': pattern['quote_count'],
            'selected_quotes': formatted_quotes,
            'themes': pattern['themes'],
            'deal_impacts': pattern['deal_impacts'],
            'relevance_level': pattern['relevance_level'],
            'score_range': pattern['score_range'],
            'is_cross_company': pattern.get('is_cross_company', False),
            'credibility_tier': credibility_tier,
            'generated_at': datetime.now().isoformat()
        }
    
    def _determine_finding_type(self, pattern: Dict) -> str:
        """Determine finding type based on pattern characteristics"""
        relevance_level = pattern.get('relevance_level', 'moderate')
        avg_score = pattern.get('avg_score', 0)
        
        if relevance_level == 'critical':
            if avg_score >= 4.5:
                return 'exceptional_strength'
            else:
                return 'critical_issue'
        elif relevance_level == 'high':
            if avg_score >= 3.5:
                return 'strong_positive'
            else:
                return 'important_feedback'
        else:  # moderate
            if avg_score >= 2.5:
                return 'moderate_positive'
            else:
                return 'moderate_concern'
    
    def _determine_credibility_tier(self, pattern: Dict) -> str:
        """Determine credibility tier based on evidence strength"""
        quote_count = pattern.get('quote_count', 0)
        company_count = pattern.get('company_count', 1)
        enhanced_confidence = pattern.get('enhanced_confidence', 0)
        
        if company_count >= 3 and quote_count >= 6 and enhanced_confidence >= 3.0:
            return 'Tier 1: Multi-company, strong evidence'
        elif company_count >= 2 and quote_count >= 3 and enhanced_confidence >= 2.5:
            return 'Tier 2: Two companies, moderate evidence'
        elif company_count == 1 and quote_count >= 2 and enhanced_confidence >= 2.0:
            return 'Tier 3: Single company, good evidence'
        elif company_count == 1 and quote_count >= 1 and enhanced_confidence >= 1.5:
            return 'Tier 4: Single company, anecdotal evidence'
        else:
            return 'Tier 5: Insufficient evidence'
    
    def _generate_pattern_based_finding_text(self, criterion: str, pattern: Dict, finding_type: str, criterion_desc: str) -> str:
        """Generate finding text based on pattern characteristics"""
        
        relevance_level = pattern.get('relevance_level', 'moderate')
        avg_score = pattern.get('avg_score', 0)
        quote_count = pattern.get('quote_count', 0)
        company_count = pattern.get('company_count', 1)
        themes = pattern.get('themes', [])
        
        # Base description
        if relevance_level == 'critical':
            if finding_type == 'exceptional_strength':
                base_text = f"Exceptional feedback on {criterion_desc} with {avg_score:.1f} average score from {quote_count} quotes"
            else:
                base_text = f"Critical feedback on {criterion_desc} with {avg_score:.1f} average score from {quote_count} quotes"
        elif relevance_level == 'high':
            base_text = f"Strong feedback on {criterion_desc} with {avg_score:.1f} average score from {quote_count} quotes"
        else:  # moderate
            base_text = f"Moderate feedback on {criterion_desc} with {avg_score:.1f} average score from {quote_count} quotes"
        
        # Add company context
        if company_count > 1:
            base_text += f" across {company_count} companies"
        else:
            base_text += f" from {pattern.get('company', 'one company')}"
        
        # Add themes if available
        if themes:
            theme_text = ', '.join(themes[:3])  # Top 3 themes
            base_text += f". Key themes: {theme_text}"
        
        # Add deal impact context
        deal_impacts = pattern.get('deal_impacts', {})
        if deal_impacts:
            impact_items = [f"{impact} ({count})" for impact, count in deal_impacts.items() if count > 0]
            if impact_items:
                impact_text = ', '.join(impact_items[:2])  # Top 2 impacts
                base_text += f". Deal impacts: {impact_text}"
        
        return base_text
    
    def save_enhanced_findings_to_supabase(self, findings: List[Dict], client_id: str = 'default'):
        """Save enhanced findings to Supabase, including credibility tier"""
        logger.info("💾 Saving enhanced findings to Supabase...")
        for finding in findings:
            db_finding = {
                'criterion': finding['criterion'],
                'finding_type': finding['finding_type'],
                'priority_level': finding['priority_level'],
                'credibility_tier': finding.get('credibility_tier', 'Unclassified'),
                'title': finding['title'],
                'description': finding['description'],
                'enhanced_confidence': finding['enhanced_confidence'],
                'criteria_scores': json.dumps(finding['criteria_scores']),
                'criteria_met': finding['criteria_met'],
                'impact_score': finding['impact_score'],
                'companies_affected': finding['companies_affected'],
                'quote_count': finding['quote_count'],
                'selected_quotes': json.dumps(finding['selected_quotes']),
                'themes': json.dumps(finding['themes']),
                'deal_impacts': json.dumps(finding['deal_impacts']),
                'generated_at': finding['generated_at'],
                'client_id': client_id
            }
            self.db.save_enhanced_finding(db_finding, client_id=client_id)
        logger.info(f"✅ Saved {len(findings)} enhanced findings to Supabase for client {client_id}")
    
    def process_enhanced_findings(self, client_id: str = 'default') -> Dict:
        """Main processing function for enhanced Stage 3"""
        
        logger.info("🚀 STAGE 3: ENHANCED FINDINGS IDENTIFICATION (Buried Wins v4.0)")
        logger.info("=" * 70)
        
        # Get scored quotes
        df = self.get_scored_quotes(client_id=client_id)
        
        if df.empty:
            logger.info("✅ No scored quotes found for analysis")
            return {"status": "no_data", "message": "No scored quotes available"}
        
        self.processing_metrics["total_quotes_processed"] = len(df)
        
        # Identify enhanced patterns
        patterns = self.identify_enhanced_patterns(df)
        self.processing_metrics["patterns_identified"] = sum(len(p) for p in patterns.values())
        
        # Generate enhanced findings
        findings = self.generate_enhanced_findings(patterns)
        self.processing_metrics["findings_generated"] = len(findings)
        
        # Save to Supabase
        self.save_enhanced_findings_to_supabase(findings, client_id=client_id)
        
        # Generate summary
        summary = self.generate_enhanced_summary_statistics(findings, patterns)
        
        logger.info(f"\n✅ Enhanced Stage 3 complete! Generated {len(findings)} findings")
        self.print_enhanced_summary_report(summary)
        
        return {
            "status": "success",
            "quotes_processed": len(df),
            "patterns_identified": self.processing_metrics["patterns_identified"],
            "findings_generated": len(findings),
            "priority_findings": self.processing_metrics["priority_findings"],
            "standard_findings": self.processing_metrics["standard_findings"],
            "summary": summary,
            "processing_metrics": self.processing_metrics
        }
    
    def generate_enhanced_summary_statistics(self, findings: List[Dict], patterns: Dict) -> Dict:
        """Generate enhanced summary statistics"""
        
        # Criterion coverage
        criteria_covered = set(finding['criterion'] for finding in findings)
        
        # Finding type and priority distribution
        finding_types = Counter(finding['finding_type'] for finding in findings)
        priority_levels = Counter(finding['priority_level'] for finding in findings)
        
        # Enhanced confidence analysis
        confidence_scores = [finding['enhanced_confidence'] for finding in findings]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Criteria met analysis
        criteria_met_counts = [finding['criteria_met'] for finding in findings]
        avg_criteria_met = sum(criteria_met_counts) / len(criteria_met_counts) if criteria_met_counts else 0
        
        # Company coverage
        companies_affected = set()
        for finding in findings:
            companies_affected.add(finding['companies_affected'])
        
        return {
            'total_findings': len(findings),
            'priority_findings': self.processing_metrics["priority_findings"],
            'standard_findings': self.processing_metrics["standard_findings"],
            'criteria_covered': len(criteria_covered),
            'criteria_list': list(criteria_covered),
            'finding_type_distribution': dict(finding_types),
            'priority_level_distribution': dict(priority_levels),
            'average_confidence_score': avg_confidence,
            'average_criteria_met': avg_criteria_met,
            'total_companies_affected': len(companies_affected),
            'patterns_by_criterion': {k: len(v) for k, v in patterns.items()}
        }
    
    def print_enhanced_summary_report(self, summary: Dict):
        """Print enhanced summary report"""
        
        logger.info(f"\n📊 ENHANCED STAGE 3 SUMMARY REPORT (Buried Wins v4.0)")
        logger.info("=" * 70)
        logger.info(f"Total findings generated: {summary['total_findings']}")
        logger.info(f"Priority findings (≥4.0): {summary['priority_findings']}")
        logger.info(f"Standard findings (≥3.0): {summary['standard_findings']}")
        logger.info(f"Criteria covered: {summary['criteria_covered']}/10")
        logger.info(f"Average confidence score: {summary['average_confidence_score']:.2f}/10.0")
        logger.info(f"Average criteria met: {summary['average_criteria_met']:.1f}/8")
        logger.info(f"Companies affected: {summary['total_companies_affected']}")
        
        logger.info(f"\n📈 FINDING TYPE DISTRIBUTION:")
        for finding_type, count in summary['finding_type_distribution'].items():
            logger.info(f"  {finding_type}: {count}")
        
        logger.info(f"\n🎯 PRIORITY LEVEL DISTRIBUTION:")
        for priority, count in summary['priority_level_distribution'].items():
            logger.info(f"  {priority}: {count}")
        
        logger.info(f"\n📈 PATTERNS BY CRITERION:")
        for criterion, pattern_count in summary['patterns_by_criterion'].items():
            logger.info(f"  {criterion}: {pattern_count} patterns")

def run_stage3_analysis(client_id: str = 'default'):
    """Run enhanced Stage 3 findings analysis"""
    analyzer = Stage3FindingsAnalyzer()
    return analyzer.process_enhanced_findings(client_id=client_id)

# Run the analysis
if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    client_id = 'default'
    if '--client_id' in sys.argv:
        try:
            client_id_index = sys.argv.index('--client_id')
            if client_id_index + 1 < len(sys.argv):
                client_id = sys.argv[client_id_index + 1]
        except (ValueError, IndexError):
            pass
    
    print(f"🔍 Running Enhanced Stage 3: Findings Identification (Buried Wins v4.0) for client '{client_id}'...")
    result = run_stage3_analysis(client_id=client_id)
    print(f"✅ Enhanced Stage 3 complete: {result}") 