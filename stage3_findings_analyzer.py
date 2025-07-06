#!/usr/bin/env python3

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import logging
from typing import Dict, List, Optional, Tuple
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
                    'priority_finding': 4.0,
                    'standard_finding': 3.0,
                    'minimum_confidence': 2.0
                },
                'pattern_thresholds': {
                    'minimum_quotes': 3,
                    'minimum_companies': 2,
                    'minimum_criteria_met': 2
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
    
    def get_scored_quotes(self) -> pd.DataFrame:
        """Get all quotes with scores from Supabase"""
        df = self.db.get_scored_quotes()
        logger.info(f"📊 Loaded {len(df)} scored quotes from Supabase")
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
                    
                    # Evaluate against Buried Wins criteria
                    criteria_scores = self.evaluate_finding_criteria(pattern['quotes_data'])
                    criteria_met = sum(criteria_scores.values())
                    
                    if criteria_met >= thresholds['minimum_criteria_met']:
                        # Calculate enhanced confidence score
                        enhanced_confidence = self.calculate_enhanced_confidence_score(
                            pattern['quotes_data'], criteria_scores
                        )
                        
                        if enhanced_confidence >= self.config['stage3']['confidence_thresholds']['minimum_confidence']:
                            pattern['enhanced_confidence'] = enhanced_confidence
                            pattern['criteria_scores'] = criteria_scores
                            pattern['criteria_met'] = criteria_met
                            pattern['selected_quotes'] = self.select_optimal_quotes(pattern['quotes_data'])
                            valid_patterns.append(pattern)
            
            if valid_patterns:
                # Sort by enhanced confidence score
                valid_patterns.sort(key=lambda x: x['enhanced_confidence'], reverse=True)
                patterns[criterion] = valid_patterns[:self.config['stage3']['max_patterns_per_criterion']]
        
        logger.info(f"✅ Identified enhanced patterns for {len(patterns)} criteria")
        return patterns
    
    def _analyze_enhanced_company_patterns(self, criterion_data: pd.DataFrame, criterion: str) -> List[Dict]:
        """Analyze patterns for a specific criterion across companies with enhanced data"""
        patterns = []
        
        # Group by company
        company_groups = criterion_data.groupby('company')
        
        for company, company_quotes in company_groups:
            if len(company_quotes) < 2:  # Need at least 2 quotes for pattern
                continue
            
            # Prepare quotes data for evaluation
            quotes_data = []
            for _, quote in company_quotes.iterrows():
                quotes_data.append({
                    'original_quote': quote.get('original_quote', ''),
                    'relevance_explanation': quote.get('relevance_explanation', ''),
                    'score': quote.get('score', 0),
                    'confidence': quote.get('confidence', 'medium'),
                    'context_assessment': quote.get('context_assessment', 'neutral'),
                    'question_relevance': quote.get('question_relevance', 'unrelated')
                })
            
            # Analyze sentiment patterns
            avg_score = company_quotes['score'].mean()
            score_std = company_quotes['score'].std()
            
            # Extract common themes from relevance explanations
            themes = self._extract_themes(company_quotes['relevance_explanation'].tolist())
            
            # Identify deal impact patterns
            deal_impacts = company_quotes['context_assessment'].value_counts().to_dict()
            
            pattern = {
                'criterion': criterion,
                'company': company,
                'quote_count': len(company_quotes),
                'company_count': 1,  # Will be updated in cross-company analysis
                'avg_score': avg_score,
                'score_std': score_std,
                'themes': themes,
                'deal_impacts': deal_impacts,
                'quotes_data': quotes_data,
                'sample_quotes': company_quotes['original_quote'].head(3).tolist()
            }
            
            patterns.append(pattern)
        
        # Cross-company pattern analysis
        cross_company_patterns = self._analyze_cross_company_patterns(patterns, criterion)
        
        return cross_company_patterns
    
    def _analyze_cross_company_patterns(self, company_patterns: List[Dict], criterion: str) -> List[Dict]:
        """Analyze patterns across multiple companies"""
        if len(company_patterns) < 2:
            return company_patterns
        
        # Group by similar themes and scores
        theme_groups = defaultdict(list)
        for pattern in company_patterns:
            theme_key = '|'.join(sorted(pattern['themes'][:3]))  # Top 3 themes
            theme_groups[theme_key].append(pattern)
        
        cross_company_patterns = []
        for theme_key, patterns in theme_groups.items():
            if len(patterns) >= 2:  # Multiple companies with similar themes
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
                    'sample_quotes': [q for p in patterns for q in p['sample_quotes'][:2]]
                }
                cross_company_patterns.append(combined_pattern)
        
        return cross_company_patterns
    
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
        """Generate findings with enhanced confidence scoring"""
        logger.info("🎯 Generating enhanced findings...")
        
        findings = []
        
        for criterion, criterion_patterns in patterns.items():
            if not criterion_patterns:
                continue
            
            criterion_findings = self._generate_criterion_enhanced_findings(criterion, criterion_patterns)
            findings.extend(criterion_findings)
        
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
        
        logger.info(f"✅ Generated {len(findings)} enhanced findings")
        return findings
    
    def _generate_criterion_enhanced_findings(self, criterion: str, patterns: List[Dict]) -> List[Dict]:
        """Generate findings for a specific criterion with enhanced analysis"""
        findings = []
        
        if not patterns:
            return findings
        
        # Calculate overall criterion score
        avg_score = sum(p['avg_score'] for p in patterns) / len(patterns)
        
        # Generate strength findings for high scores
        high_score_patterns = [p for p in patterns if p['avg_score'] >= 3.5]
        if high_score_patterns:
            strength_finding = self._create_enhanced_finding(criterion, high_score_patterns, 'strength', avg_score)
            if strength_finding:
                findings.append(strength_finding)
        
        # Generate improvement findings for low scores
        low_score_patterns = [p for p in patterns if p['avg_score'] <= 2.0]
        if low_score_patterns:
            improvement_finding = self._create_enhanced_finding(criterion, low_score_patterns, 'improvement', avg_score)
            if improvement_finding:
                findings.append(improvement_finding)
        
        # Generate trend findings for mixed patterns
        if len(patterns) >= 3 and (len(high_score_patterns) > 0 and len(low_score_patterns) > 0):
            trend_finding = self._create_trend_enhanced_finding(criterion, patterns, avg_score)
            if trend_finding:
                findings.append(trend_finding)
        
        return findings
    
    def _create_enhanced_finding(self, criterion: str, patterns: List[Dict], finding_type: str, avg_score: float) -> Optional[Dict]:
        """Create an enhanced finding with confidence scoring"""
        if not patterns:
            return None
        
        # Use the highest confidence pattern for the finding
        best_pattern = max(patterns, key=lambda x: x['enhanced_confidence'])
        
        criterion_desc = self.criteria.get(criterion, {}).get('description', criterion)
        
        # Generate finding text using enhanced LLM prompt
        finding_text = self._generate_enhanced_finding_text(criterion, patterns, finding_type, criterion_desc, best_pattern)
        
        # Format selected quotes with attribution
        formatted_quotes = []
        for quote in best_pattern.get('selected_quotes', [])[:self.config['stage3']['max_quotes_per_finding']]:
            formatted_quotes.append({
                'text': quote.get('original_quote', ''),
                'score': quote.get('score', 0),
                'attribution': f"Score: {quote.get('score', 0)} - {quote.get('context_assessment', 'neutral')}"
            })
        
        return {
            'criterion': criterion,
            'finding_type': finding_type,
            'priority_level': 'standard',  # Will be updated in main function
            'title': f"{criterion.replace('_', ' ').title()} {finding_type.title()}",
            'description': finding_text,
            'enhanced_confidence': best_pattern['enhanced_confidence'],
            'criteria_scores': best_pattern.get('criteria_scores', {}),
            'criteria_met': best_pattern.get('criteria_met', 0),
            'impact_score': avg_score,
            'companies_affected': best_pattern.get('company_count', len(patterns)),
            'quote_count': best_pattern['quote_count'],
            'selected_quotes': formatted_quotes,
            'themes': best_pattern['themes'],
            'deal_impacts': best_pattern['deal_impacts'],
            'generated_at': datetime.now().isoformat()
        }
    
    def _create_trend_enhanced_finding(self, criterion: str, patterns: List[Dict], avg_score: float) -> Optional[Dict]:
        """Create a trend finding with enhanced analysis"""
        if len(patterns) < 3:
            return None
        
        # Analyze score distribution
        scores = [p['avg_score'] for p in patterns]
        score_std = pd.Series(scores).std()
        
        # Only create trend finding if there's significant variation
        if score_std < 0.5:
            return None
        
        # Identify trend direction
        high_scores = [s for s in scores if s >= 3.0]
        low_scores = [s for s in scores if s <= 2.0]
        
        if len(high_scores) > len(low_scores):
            trend_type = 'positive_trend'
        else:
            trend_type = 'negative_trend'
        
        return self._create_enhanced_finding(criterion, patterns, trend_type, avg_score)
    
    def _generate_enhanced_finding_text(self, criterion: str, patterns: List[Dict], finding_type: str, criterion_desc: str, best_pattern: Dict) -> str:
        """Generate enhanced finding text using Buried Wins v4.0 framework"""
        
        prompt = ChatPromptTemplate.from_template("""
            Generate an executive-ready finding using the Buried Wins Findings Criteria v4.0 framework.
            
            CRITERION: {criterion} - {criterion_desc}
            FINDING TYPE: {finding_type}
            ENHANCED CONFIDENCE: {confidence_score:.1f}/10.0
            CRITERIA MET: {criteria_met}/8 (Novelty, Actionability, Specificity, Materiality, Recurrence, Stakeholder Weight, Tension/Contrast, Metric/Quantification)
            
            PATTERN SUMMARY:
            {pattern_summary}
            
            SELECTED EVIDENCE:
            {selected_evidence}
            
            REQUIREMENTS (Buried Wins v4.0):
            - Write 2-3 sentences maximum
            - Focus on actionable insights that could influence executive decision-making
            - Use business language with specific impact
            - Include material business implications
            - Be clear, direct, and executive-ready
            - Reference specific criteria met if relevant
            
            OUTPUT: Just the finding text, no additional formatting.
            """)
        
        # Create enhanced pattern summary
        pattern_summary = []
        for pattern in patterns[:3]:
            summary = f"Company: {pattern.get('company', 'Multiple')}, Score: {pattern['avg_score']:.1f}, Quotes: {pattern['quote_count']}"
            if pattern['themes']:
                summary += f", Themes: {', '.join(pattern['themes'][:3])}"
            pattern_summary.append(summary)
        
        # Create selected evidence summary
        selected_evidence = []
        for quote in best_pattern.get('selected_quotes', [])[:2]:
            evidence = f"Score {quote.get('score', 0)}: {quote.get('original_quote', '')[:150]}..."
            selected_evidence.append(evidence)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                criterion=criterion,
                criterion_desc=criterion_desc,
                finding_type=finding_type,
                confidence_score=best_pattern['enhanced_confidence'],
                criteria_met=best_pattern.get('criteria_met', 0),
                pattern_summary='\n'.join(pattern_summary),
                selected_evidence='\n'.join(selected_evidence)
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced finding text: {e}")
            # Fallback text
            return f"Significant {finding_type} identified in {criterion} with confidence {best_pattern['enhanced_confidence']:.1f}/10.0 across {best_pattern.get('company_count', 1)} companies."
    
    def save_enhanced_findings_to_supabase(self, findings: List[Dict]):
        """Save enhanced findings to Supabase"""
        logger.info("💾 Saving enhanced findings to Supabase...")
        
        for finding in findings:
            # Convert to database format
            db_finding = {
                'criterion': finding['criterion'],
                'finding_type': finding['finding_type'],
                'priority_level': finding['priority_level'],
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
                'generated_at': finding['generated_at']
            }
            
            self.db.save_enhanced_finding(db_finding)
        
        logger.info(f"✅ Saved {len(findings)} enhanced findings to Supabase")
    
    def process_enhanced_findings(self) -> Dict:
        """Main processing function for enhanced Stage 3"""
        
        logger.info("🚀 STAGE 3: ENHANCED FINDINGS IDENTIFICATION (Buried Wins v4.0)")
        logger.info("=" * 70)
        
        # Get scored quotes
        df = self.get_scored_quotes()
        
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
        self.save_enhanced_findings_to_supabase(findings)
        
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
        
        logger.info(f"\n🔍 PATTERNS BY CRITERION:")
        for criterion, pattern_count in summary['patterns_by_criterion'].items():
            logger.info(f"  {criterion}: {pattern_count} patterns")

def run_stage3_analysis():
    """Run enhanced Stage 3 findings analysis"""
    analyzer = Stage3FindingsAnalyzer()
    return analyzer.process_enhanced_findings()

# Run the analysis
if __name__ == "__main__":
    print("🔍 Running Enhanced Stage 3: Findings Identification (Buried Wins v4.0)...")
    result = run_stage3_analysis()
    print(f"✅ Enhanced Stage 3 complete: {result}") 