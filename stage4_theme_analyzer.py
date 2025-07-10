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
from difflib import SequenceMatcher

# Import Supabase database manager
from supabase_database import SupabaseDatabase

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Stage4ThemeAnalyzer:
    """
    Stage 4: Enhanced Theme Generation - Fuzzy matching and semantic grouping for executive insights
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
        
        # Processing metrics
        self.processing_metrics = {
            "total_findings_processed": 0,
            "themes_generated": 0,
            "high_strength_themes": 0,
            "competitive_themes": 0,
            "fuzzy_grouped_themes": 0,
            "processing_errors": 0,
            "rejected_direct_quotes": 0
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
        """Default configuration for Stage 4 with improved thresholds and quality controls"""
        return {
            'stage4': {
                'min_confidence_threshold': 3.0,
                'min_companies_per_theme': 3,        # INCREASED from 1 to 3
                'min_findings_per_theme': 2,         # INCREASED from 1 to 2
                'min_quotes_per_theme': 5,           # NEW: Minimum quotes per theme
                'max_themes_per_category': 5,
                'quality_scoring': {
                    'specificity_threshold': 7.0,
                    'actionability_threshold': 6.0,
                    'evidence_strength_threshold': 6.0,
                    'min_overall_score': 6.5
                },
                'quote_deduplication': {
                    'enabled': True,
                    'similarity_threshold': 0.8,
                    'max_quote_reuse': 1
                },
                'fuzzy_matching': {
                    'similarity_threshold': 0.75,    # INCREASED from 0.7
                    'semantic_grouping': True,
                    'cross_criteria_grouping': True,
                    'min_group_size': 3              # NEW: Minimum group size
                },
                'competitive_keywords': [
                    'vs', 'versus', 'compared to', 'alternative', 'competitor',
                    'switching', 'migration', 'evaluation', 'selection process',
                    'vendor', 'solution', 'platform', 'tool', 'competition',
                    'market leader', 'industry standard', 'best in class'
                ]
            }
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using fuzzy matching"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())
        
        # Use SequenceMatcher for fuzzy string matching
        similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()
        
        # Additional semantic checks for common business terms
        semantic_mappings = {
            'product': ['capability', 'feature', 'functionality', 'solution'],
            'integration': ['technical', 'fit', 'compatibility', 'api'],
            'security': ['privacy', 'compliance', 'data', 'protection'],
            'support': ['service', 'help', 'assistance', 'quality'],
            'implementation': ['onboarding', 'setup', 'deployment', 'rollout'],
            'commercial': ['pricing', 'cost', 'terms', 'roi'],
            'speed': ['responsiveness', 'timeline', 'agility', 'efficiency']
        }
        
        # Check semantic mappings
        for primary, related in semantic_mappings.items():
            if primary in text1_clean and any(term in text2_clean for term in related):
                similarity += 0.2
            elif primary in text2_clean and any(term in text1_clean for term in related):
                similarity += 0.2
        
        return min(similarity, 1.0)
    
    def check_quote_similarity(self, quote1: str, quote2: str) -> float:
        """Check similarity between two quotes for deduplication"""
        if not quote1 or not quote2:
            return 0.0
        
        # Extract text from quote objects
        if isinstance(quote1, dict):
            text1 = quote1.get('text', '')
        else:
            text1 = str(quote1)
            
        if isinstance(quote2, dict):
            text2 = quote2.get('text', '')
        else:
            text2 = str(quote2)
        
        return self.calculate_semantic_similarity(text1, text2)
    
    def filter_duplicate_quotes(self, quotes: List, used_quotes: List, similarity_threshold: float = 0.8) -> List:
        """Filter out quotes that are too similar to already used quotes"""
        filtered_quotes = []
        
        for quote in quotes:
            is_duplicate = False
            
            # Check against all used quotes
            for used_quote in used_quotes:
                similarity = self.check_quote_similarity(quote, used_quote)
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_quotes.append(quote)
        
        return filtered_quotes
    
    def group_findings_by_semantic_similarity(self, findings_df: pd.DataFrame) -> List[List[Dict]]:
        """Group findings by semantic similarity across criteria with improved thresholds"""
        logger.info("🔍 Grouping findings by semantic similarity with improved thresholds...")
        
        stage4_config = self.config.get('stage4', {})
        fuzzy_config = stage4_config.get('fuzzy_matching', {})
        similarity_threshold = fuzzy_config.get('similarity_threshold', 0.75)  # INCREASED
        min_group_size = fuzzy_config.get('min_group_size', 3)  # NEW: Minimum group size
        
        findings_list = findings_df.to_dict('records')
        grouped_findings = []
        processed = set()
        
        for i, finding1 in enumerate(findings_list):
            if i in processed:
                continue
            
            current_group = [finding1]
            processed.add(i)
            
            # Compare with other findings
            for j, finding2 in enumerate(findings_list[i+1:], i+1):
                if j in processed:
                    continue
                
                # Calculate similarity between findings
                desc1 = finding1.get('description', '')
                desc2 = finding2.get('description', '')
                
                similarity = self.calculate_semantic_similarity(desc1, desc2)
                
                if similarity >= similarity_threshold:
                    current_group.append(finding2)
                    processed.add(j)
            
            # Only include groups that meet minimum size requirement
            if len(current_group) >= min_group_size:
                grouped_findings.append(current_group)
                logger.info(f"✅ Grouped {len(current_group)} findings with similarity {similarity:.2f}")
            else:
                logger.info(f"⚠️ Skipping group of {len(current_group)} findings (below minimum size {min_group_size})")
        
        logger.info(f"✅ Created {len(grouped_findings)} semantic groups (minimum size: {min_group_size})")
        return grouped_findings
    
    def get_findings_for_analysis(self, client_id: str = 'default') -> pd.DataFrame:
        """Get findings from database for theme analysis"""
        df = self.db.get_enhanced_findings(client_id=client_id)
        logger.info(f"📊 Loaded {len(df)} findings from Supabase for client {client_id}")
        return df
    
    def analyze_finding_patterns(self, df: pd.DataFrame, client_id: str = 'default') -> Dict:
        """Analyze patterns across findings to identify potential themes using fuzzy matching and semantic grouping"""
        logger.info("🔍 Analyzing finding patterns with fuzzy matching...")
        
        # Load core_responses for interviewee_name lookup
        core_df = self.db.get_core_responses(client_id=client_id)
        
        patterns = {}
        
        # Get configuration values with improved defaults
        stage4_config = self.config.get('stage4', {})
        min_findings = stage4_config.get('min_findings_per_theme', 2)      # INCREASED from 1 to 2
        min_companies = stage4_config.get('min_companies_per_theme', 3)    # INCREASED from 1 to 3
        min_quotes = stage4_config.get('min_quotes_per_theme', 5)          # NEW: Minimum quotes per theme
        fuzzy_config = stage4_config.get('fuzzy_matching', {})
        semantic_grouping = fuzzy_config.get('semantic_grouping', True)
        cross_criteria_grouping = fuzzy_config.get('cross_criteria_grouping', True)
        
        # NEW: Group findings by semantic similarity first
        semantic_groups = []
        if semantic_grouping and cross_criteria_grouping:
            semantic_groups = self.group_findings_by_semantic_similarity(df)
        
        # Process semantic groups for cross-criteria themes
        for group_idx, finding_group in enumerate(semantic_groups):
            if len(finding_group) < min_findings:
                continue
            
            # Analyze the group as a potential cross-criteria theme
            group_pattern = self._analyze_finding_group(finding_group, core_df, f"semantic_group_{group_idx}")
            
            if group_pattern and group_pattern['company_count'] >= min_companies:
                patterns[f"semantic_group_{group_idx}"] = group_pattern
        
        # Process individual criteria patterns (existing logic)
        for criterion in df['criterion'].unique():
            criterion_findings = df[df['criterion'] == criterion]
            
            if len(criterion_findings) < min_findings:
                continue
            
            # Analyze finding types
            finding_types = criterion_findings['finding_type'].value_counts()
            
            # Analyze impact scores
            impact_scores = criterion_findings['impact_score'].tolist()
            # Cap all impact scores at 5 and warn if any > 5
            capped_scores = []
            for s in impact_scores:
                if s > 5:
                    logger.warning(f"Impact score > 5 found in findings: {s}. Capping to 5.")
                    capped_scores.append(5.0)
                else:
                    capped_scores.append(max(s, 0))
            avg_impact = sum(capped_scores) / len(capped_scores) if capped_scores else 0
            avg_impact = min(avg_impact, 5.0)
            
            # Extract interviewee_names and quotes (collect full quote objects)
            interviewees = set()
            quotes = []
            finding_ids = []
            for _, finding in criterion_findings.iterrows():
                if 'selected_quotes' in finding and finding['selected_quotes']:
                    for quote_obj in finding['selected_quotes']:
                        # If it's a dict, keep the full object for UI
                        if isinstance(quote_obj, dict):
                            # FIX: If quote text is empty, try to get it from core response
                            quote_text = quote_obj.get('text', '')
                            if not quote_text and 'response_id' in quote_obj:
                                # Try to find the core response and extract the text
                                response_id = quote_obj.get('response_id')
                                matching_core = core_df[core_df['response_id'] == response_id]
                                if not matching_core.empty:
                                    quote_text = matching_core.iloc[0]['verbatim_response']
                                    quote_obj['text'] = quote_text
                            
                            quotes.append(quote_obj)
                            # Try to match interviewee_name by text if possible
                            if quote_text:
                                match = core_df[core_df['verbatim_response'].str.startswith(quote_text[:30])]
                                if not match.empty:
                                    interviewees.add(match.iloc[0]['interviewee_name'])
                        elif isinstance(quote_obj, str):
                            quotes.append({'text': quote_obj})
                            match = core_df[core_df['verbatim_response'].str.startswith(quote_obj[:30])]
                            if not match.empty:
                                interviewees.add(match.iloc[0]['interviewee_name'])
                finding_ids.append(finding['id'])
            
            # Check if pattern meets minimum requirements
            if len(interviewees) >= min_companies:
                # CRITICAL FIX: Ensure pattern has at least one quote
                if not quotes:
                    logger.warning(f"⚠️ Skipping theme pattern for {criterion} - no quotes found")
                    continue
                
                patterns[criterion] = {
                    'finding_count': len(criterion_findings),
                    'company_count': len(interviewees),
                    'companies': list(interviewees),
                    'finding_types': finding_types.to_dict(),
                    'avg_impact_score': avg_impact,
                    'quotes': quotes[:5],  # Limit to top 5 quote objects
                    'finding_ids': finding_ids,
                    'avg_confidence': criterion_findings['enhanced_confidence'].mean(),
                    'pattern_type': 'criterion_based'
                }
        
        logger.info(f"✅ Identified {len(patterns)} potential theme patterns (including {len([p for p in patterns.values() if p.get('pattern_type') == 'semantic_group'])} semantic groups)")
        return patterns
    
    def _analyze_finding_group(self, finding_group: List[Dict], core_df: pd.DataFrame, group_name: str) -> Optional[Dict]:
        """Analyze a group of findings for cross-criteria patterns"""
        
        # Extract interviewee_names and quotes
        interviewees = set()
        quotes = []
        finding_ids = []
        criteria_covered = set()
        relevance_scores = []
        confidence_scores = []
        
        for finding in finding_group:
            finding_ids.append(finding['id'])
            criteria_covered.add(finding['criterion'])
            relevance_scores.append(min(finding.get('impact_score', 0), 5.0))  # Keep using impact_score for now (will be updated in Stage 2)
            confidence_scores.append(finding.get('enhanced_confidence', 0))
            
            # Extract quotes with relevance scores and sentiment
            if 'selected_quotes' in finding and finding['selected_quotes']:
                for quote_obj in finding['selected_quotes']:
                    if isinstance(quote_obj, dict):
                        # Add relevance score and sentiment to quote object
                        quote_obj['relevance_score'] = finding.get('impact_score', 0)  # Use impact_score as relevance for now
                        quote_obj['sentiment'] = 'neutral'  # Default sentiment (will be updated when Stage 2 is reprocessed)
                        
                        # FIX: If quote text is empty, try to get it from core response
                        quote_text = quote_obj.get('text', '')
                        if not quote_text and 'response_id' in quote_obj:
                            # Try to find the core response and extract the text
                            response_id = quote_obj.get('response_id')
                            matching_core = core_df[core_df['response_id'] == response_id]
                            if not matching_core.empty:
                                quote_text = matching_core.iloc[0]['verbatim_response']
                                quote_obj['text'] = quote_text
                        
                        quotes.append(quote_obj)
                        if quote_text:
                            match = core_df[core_df['verbatim_response'].str.startswith(quote_text[:30])]
                            if not match.empty:
                                interviewees.add(match.iloc[0]['interviewee_name'])
                    elif isinstance(quote_obj, str):
                        # Convert string quote to dict with relevance and sentiment
                        quote_dict = {
                            'text': quote_obj,
                            'relevance_score': finding.get('impact_score', 0),  # Use impact_score as relevance for now
                            'sentiment': 'neutral'  # Default sentiment (will be updated when Stage 2 is reprocessed)
                        }
                        quotes.append(quote_dict)
                        match = core_df[core_df['verbatim_response'].str.startswith(quote_obj[:30])]
                        if not match.empty:
                            interviewees.add(match.iloc[0]['interviewee_name'])
        
        if not quotes:
            return None
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'finding_count': len(finding_group),
            'company_count': len(interviewees),
            'companies': list(interviewees),
            'criteria_covered': list(criteria_covered),
            'avg_impact_score': avg_relevance,  # Keep using avg_impact_score for compatibility
            'quotes': quotes[:5],
            'finding_ids': finding_ids,
            'avg_confidence': avg_confidence,
            'pattern_type': 'semantic_group',
            'group_name': group_name
        }
    
    def detect_competitive_themes(self, patterns: Dict, client_id: str = 'default') -> Dict:
        """Detect competitive themes based on keyword analysis"""
        logger.info("🏆 Detecting competitive themes...")
        
        stage4_config = self.config.get('stage4', {})
        competitive_keywords = stage4_config.get('competitive_keywords', [
            'vs', 'versus', 'compared to', 'alternative', 'competitor',
            'switching', 'migration', 'evaluation', 'selection process',
            'vendor', 'solution', 'platform', 'tool'
        ])
        
        competitive_patterns = {}
        
        for criterion, pattern in patterns.items():
            competitive_score = 0
            
            # Check quotes for competitive keywords
            for quote in pattern['quotes']:
                # Handle both string and dict quote objects
                if isinstance(quote, dict):
                    quote_text = quote.get('text', '')
                else:
                    quote_text = str(quote)
                
                quote_lower = quote_text.lower()
                for keyword in competitive_keywords:
                    if keyword in quote_lower:
                        competitive_score += 1
            
            # Check finding descriptions
            findings_df = self.db.get_enhanced_findings(client_id=client_id)  # Use client_id
            criterion_findings = findings_df[findings_df['criterion'] == criterion]
            
            for _, finding in criterion_findings.iterrows():
                desc_lower = finding['description'].lower()
                for keyword in competitive_keywords:
                    if keyword in desc_lower:
                        competitive_score += 1
            
            # Mark as competitive if score is high enough
            if competitive_score >= 2:
                pattern['competitive_flag'] = True
                pattern['competitive_score'] = competitive_score
                competitive_patterns[criterion] = pattern
            else:
                pattern['competitive_flag'] = False
                pattern['competitive_score'] = competitive_score
        
        logger.info(f"✅ Identified {len(competitive_patterns)} competitive themes")
        return patterns
    
    def split_multiple_hypotheses(self, theme_statement: str) -> List[str]:
        """Split a theme that contains multiple 'if/then' statements into separate themes"""
        # Check if theme contains multiple "If" statements
        if theme_statement.count("If ") > 1:
            # Split by "If " and filter out empty strings
            parts = theme_statement.split("If ")
            hypotheses = []
            
            for part in parts[1:]:  # Skip first empty part
                if part.strip():
                    # Reconstruct the "If" statement
                    hypothesis = "If " + part.strip()
                    # Clean up any trailing punctuation or formatting
                    hypothesis = hypothesis.rstrip(".,;")
                    hypotheses.append(hypothesis)
            
            logger.info(f"🔀 Split theme with {len(hypotheses)} hypotheses into separate themes")
            return hypotheses
        
        return [theme_statement]
    
    def generate_theme_statements(self, patterns: Dict, client_id: str = 'default') -> List[Dict]:
        """Generate theme statements using LLM with enhanced quality controls and quote deduplication"""
        logger.info("📝 Generating theme statements with improved quality controls...")
        
        themes = []
        used_quotes = []  # Track all used quotes for deduplication
        stage4_config = self.config.get('stage4', {})
        quote_dedup_config = stage4_config.get('quote_deduplication', {})
        dedup_enabled = quote_dedup_config.get('enabled', True)
        similarity_threshold = quote_dedup_config.get('similarity_threshold', 0.8)
        
        # Sort patterns by company count and impact score for priority processing
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: (x[1]['company_count'], x[1]['avg_impact_score']),
            reverse=True
        )
        
        for pattern_key, pattern in sorted_patterns:
            # CRITICAL FIX: Ensure pattern has at least one quote before generating theme
            if not pattern.get('quotes'):
                logger.warning(f"⚠️ Skipping theme generation for {pattern_key} - no quotes found in pattern")
                continue
            
            # Check minimum quote requirement
            min_quotes = stage4_config.get('min_quotes_per_theme', 5)
            if len(pattern['quotes']) < min_quotes:
                logger.warning(f"⚠️ Skipping theme generation for {pattern_key} - only {len(pattern['quotes'])} quotes (minimum: {min_quotes})")
                continue
            
            # Apply quote deduplication if enabled
            if dedup_enabled:
                filtered_quotes = self.filter_duplicate_quotes(pattern['quotes'], used_quotes, similarity_threshold)
                if len(filtered_quotes) < min_quotes:
                    logger.warning(f"⚠️ Skipping theme generation for {pattern_key} - insufficient unique quotes after deduplication")
                    continue
                pattern['quotes'] = filtered_quotes
            
            # Generate theme statement based on pattern type
            if pattern.get('pattern_type') == 'semantic_group':
                theme_statement = self._generate_cross_criteria_theme(pattern, pattern_key)
            else:
                theme_statement = self._generate_criterion_theme(pattern, pattern_key)
            
            if not theme_statement:
                continue
            
            # Score theme quality
            quality_scores = self.score_theme_quality(theme_statement, pattern)
            
            # Check if theme meets quality thresholds
            if not self.meets_quality_thresholds(quality_scores, stage4_config):
                logger.warning(f"⚠️ Theme for {pattern_key} has low quality score {quality_scores['overall']:.1f}, attempting to improve...")
                
                # Try to improve the weak theme
                improved_theme = self.improve_weak_theme(theme_statement, pattern)
                
                # Re-score the improved theme
                improved_quality_scores = self.score_theme_quality(improved_theme, pattern)
                
                if self.meets_quality_thresholds(improved_quality_scores, stage4_config):
                    logger.info(f"✅ Successfully improved theme for {pattern_key} (score: {improved_quality_scores['overall']:.1f})")
                    theme_statement = improved_theme
                    quality_scores = improved_quality_scores
                else:
                    logger.warning(f"⚠️ Skipping theme for {pattern_key} - quality score {improved_quality_scores['overall']:.1f} still below threshold after improvement")
                    continue
            
            # Determine theme strength based on improved criteria
            if pattern['company_count'] >= 5 and pattern['avg_impact_score'] >= 4.0:
                theme_strength = "High"
            elif pattern['company_count'] >= 3 and pattern['avg_impact_score'] >= 3.0:
                theme_strength = "Medium"
            else:
                theme_strength = "Emerging"
            
            # Determine theme category
            if pattern.get('competitive_flag', False):
                theme_category = "Competitive"
            elif pattern['avg_impact_score'] >= 4.0:
                theme_category = "Opportunity"
            elif pattern['avg_impact_score'] <= 2.0:
                theme_category = "Barrier"
            else:
                theme_category = "Strategic"
            
            # Extract quote text for database storage - IMPROVED WITH FALLBACKS
            primary_quote_text = ""
            secondary_quote_text = ""
            
            # IMPROVED: Better quote extraction with fallbacks
            if pattern['quotes']:
                # Try to get primary quote
                primary_quote = pattern['quotes'][0]
                if isinstance(primary_quote, dict):
                    primary_quote_text = primary_quote.get('text', '')
                else:
                    primary_quote_text = str(primary_quote)
                
                # If primary quote is empty, try to find a non-empty quote
                if not primary_quote_text.strip():
                    for quote in pattern['quotes']:
                        if isinstance(quote, dict):
                            quote_text = quote.get('text', '')
                        else:
                            quote_text = str(quote)
                        if quote_text.strip():
                            primary_quote_text = quote_text
                            break
                
                # Try to get secondary quote
                if len(pattern['quotes']) > 1:
                    secondary_quote = pattern['quotes'][1]
                    if isinstance(secondary_quote, dict):
                        secondary_quote_text = secondary_quote.get('text', '')
                    else:
                        secondary_quote_text = str(secondary_quote)
            
            # CRITICAL FIX: If still no primary quote, try to extract from findings
            if not primary_quote_text.strip():
                logger.warning(f"⚠️ No primary quote found in pattern quotes, attempting to extract from findings...")
                # Try to get a quote from the findings data
                findings_df = self.db.get_enhanced_findings(client_id=client_id)
                if not findings_df.empty:
                    # Get the first finding for this pattern
                    pattern_findings = findings_df[findings_df['id'].isin(pattern['finding_ids'])]
                    if not pattern_findings.empty:
                        first_finding = pattern_findings.iloc[0]
                        if 'selected_quotes' in first_finding and first_finding['selected_quotes']:
                            # Try to get a quote from the finding
                            finding_quotes = first_finding['selected_quotes']
                            if isinstance(finding_quotes, list) and finding_quotes:
                                first_finding_quote = finding_quotes[0]
                                if isinstance(first_finding_quote, dict):
                                    primary_quote_text = first_finding_quote.get('text', '')
                                else:
                                    primary_quote_text = str(first_finding_quote)
            
            # FINAL FALLBACK: If still no quote, create a minimal placeholder
            if not primary_quote_text.strip():
                logger.warning(f"⚠️ No quotes found for theme, creating minimal placeholder")
                primary_quote_text = f"Quote from {pattern['companies'][0] if pattern['companies'] else 'customer'} regarding {pattern.get('criteria_covered', ['business needs'])[0]}"
            
            # Ensure single statement per theme - don't split multiple hypotheses
            single_theme_statement = theme_statement.strip()
            
            # If theme contains multiple statements, take only the first one
            if '\n' in single_theme_statement:
                single_theme_statement = single_theme_statement.split('\n')[0].strip()
            
            # Remove any additional statements after the first one
            if ' - "' in single_theme_statement:
                single_theme_statement = single_theme_statement.split(' - "')[0].strip()
            
            # Clean up any remaining quotes or formatting
            single_theme_statement = single_theme_statement.replace('"', '').strip()
            
            # Skip if empty after cleaning
            if not single_theme_statement:
                continue
            
            # CRITICAL: Check if theme is a direct quote or question
            if self.is_direct_quote_or_question(single_theme_statement):
                logger.warning(f"🚫 Rejected theme as direct quote/question: {single_theme_statement[:100]}...")
                self.processing_metrics["rejected_direct_quotes"] += 1
                # TEMPORARILY DISABLE REJECTION TO SEE WHAT THEMES ARE BEING GENERATED
                # continue
            
            # Score theme quality and get strength classification
            quality_scores = self.score_theme_quality(single_theme_statement, pattern)
            
            # Create theme object with enhanced quality scores
            theme = {
                'theme_statement': single_theme_statement,
                'theme_category': theme_category,
                'theme_strength': quality_scores['strength_classification'],  # Use strength classification
                'interview_companies': pattern['companies'],
                'supporting_finding_ids': pattern['finding_ids'],
                'supporting_response_ids': [],  # Will be populated from findings
                'deal_status_distribution': {"won": 0, "lost": 0},  # Placeholder
                'competitive_flag': pattern.get('competitive_flag', False),
                'business_implications': f"Impact score: {pattern['avg_impact_score']:.1f}, affecting {pattern['company_count']} companies",
                'primary_theme_quote': primary_quote_text,
                'secondary_theme_quote': secondary_quote_text,
                'quote_attributions': f"Primary: {pattern['companies'][0] if pattern['companies'] else 'Unknown'}",
                'evidence_strength': quality_scores['evidence_strength'],
                'avg_confidence_score': pattern['avg_confidence'],
                'company_count': pattern['company_count'],
                'finding_count': pattern['finding_count'],
                'quotes': json.dumps(pattern['quotes']),
                'pattern_type': pattern.get('pattern_type', 'criterion_based'),
                'quality_scores': json.dumps(quality_scores)  # Store full quality scores
            }
            
            # Add cross-criteria information for semantic groups
            if pattern.get('pattern_type') == 'semantic_group':
                theme['criteria_covered'] = pattern.get('criteria_covered', [])
                self.processing_metrics["fuzzy_grouped_themes"] += 1
            
            themes.append(theme)
            
            # Add quotes to used quotes list for deduplication
            if dedup_enabled:
                used_quotes.extend(pattern['quotes'])
        
        logger.info(f"✅ Generated {len(themes)} high-quality theme statements (including {self.processing_metrics['fuzzy_grouped_themes']} fuzzy grouped)")
        return themes
    
    def _generate_cross_criteria_theme(self, pattern: Dict, pattern_key: str) -> Optional[str]:
        """Generate theme statement for cross-criteria semantic groups"""
        
        # Prepare finding summary
        criteria_covered = pattern.get('criteria_covered', [])
        criteria_summary = ", ".join(criteria_covered)
        
        # Handle quote objects properly
        quote_examples = []
        for quote in pattern['quotes'][:3]:
            if isinstance(quote, dict):
                quote_text = quote.get('text', '')
            else:
                quote_text = str(quote)
            quote_examples.append(f"'{quote_text[:200]}...'")
        quote_examples = "\n".join(quote_examples)
        
        prompt = ChatPromptTemplate.from_template("""
        CRITICAL INSTRUCTION: Generate theme statements that mirror the findings format - specific, measurable, and business-focused. Do NOT use prescriptive language.

        STRUCTURE TEMPLATE:
        [Specific issue/opportunity] [measurable impact] [business context]

        EXAMPLES FROM FINDINGS DATA:
        - "Accuracy shortfalls negate speed advantage"
        - "Lack of direct Dropbox integration slows workflows and prompts integration request"
        - "24‑hour turnaround time is a decisive factor for choosing Rev's transcription service"
        - "Manual process of moving Rev transcripts into MyCase and Westlaw CoCounsel exposes integration gap, adding workflow friction for solo attorneys"

        CRITERION: {criteria_covered}
        COMPANIES: {companies}
        FINDING COUNT: {finding_count}
        AVERAGE IMPACT SCORE: {avg_impact}
        COMPETITIVE FLAG: {competitive_flag}
        
        SAMPLE QUOTES:
        {quotes}
        
        KEY GUIDELINES:
        1. SPECIFIC ISSUES: Identify concrete problems or opportunities (e.g., "speed gaps", "integration friction", "accuracy shortfalls")
        2. MEASURABLE IMPACT: Include quantifiable outcomes (e.g., "slows workflows", "negates advantage", "drives adoption")
        3. BUSINESS CONTEXT: Add relevant business context (e.g., "for solo attorneys", "in legal workflows", "among law firms")
        4. NO PRESCRIPTIVE LANGUAGE: Avoid "should", "must", "need to", "Rev should"
        5. CONCISE STATEMENTS: Keep to 1-2 sentences maximum
        6. EVIDENCE-BASED: Base on actual quotes and patterns, not generic observations
        
        QUALITY CHECKLIST:
        ✅ Identifies specific issue or opportunity
        ✅ Includes measurable impact or outcome
        ✅ Uses business-relevant context
        ✅ Avoids prescriptive language
        ✅ Based on actual evidence
        ✅ Concise and direct
        
        FORBIDDEN PHRASES (DO NOT USE):
        - "Rev should..."
        - "Rev must..."
        - "Rev needs to..."
        - "To enhance..."
        - "The analysis reveals..."
        - "It is imperative to..."
        - "We recommend..."
        - "Strategic implications..."
        - "Operational efficiency..."
        - "Competitive advantage..."
        - "Business value..."
        
        GOOD EXAMPLES:
        - "Speed gaps drive use of Turbo Scribe over Rev despite higher accuracy of human transcripts"
        - "Lack of seamless Dropbox-style integrations forces manual steps, slowing legal workflows"
        - "AI visibility gaps limit cost-reduction benefits despite strong performance"
        - "Manual speaker labeling slows paralegal workflow, indicating need for automated identification"
        
        BAD EXAMPLES:
        - "To enhance market position, Rev should prioritize direct engagement" (WRONG - prescriptive)
        - "The analysis reveals moderate concerns regarding support service quality" (WRONG - generic)
        - "Strategic alignment will foster stronger relationships" (WRONG - vague business speak)
        - "Rev must improve operational efficiency" (WRONG - prescriptive directive)
        
        Generate the theme statement using ONLY the required structure with specific issues, measurable impacts, and business context:
        """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                criteria_covered=criteria_summary,
                companies=", ".join(pattern['companies']),
                finding_count=pattern['finding_count'],
                avg_impact=f"{pattern['avg_impact_score']:.1f}",
                competitive_flag="Yes" if pattern.get('competitive_flag', False) else "No",
                quotes=quote_examples
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating cross-criteria theme for {pattern_key}: {e}")
            self.processing_metrics["processing_errors"] += 1
            return None
    
    def _generate_criterion_theme(self, pattern: Dict, pattern_key: str) -> Optional[str]:
        """Generate theme statement for single-criterion patterns"""
        
        # Prepare finding summary
        finding_summary = []
        for finding_type, count in pattern['finding_types'].items():
            finding_summary.append(f"- {finding_type}: {count} findings")
        
        # Handle quote objects properly
        quote_examples = []
        for quote in pattern['quotes'][:3]:
            if isinstance(quote, dict):
                quote_text = quote.get('text', '')
            else:
                quote_text = str(quote)
            quote_examples.append(f"'{quote_text[:200]}...'")
        quote_examples = "\n".join(quote_examples)
        
        prompt = ChatPromptTemplate.from_template("""
        CRITICAL INSTRUCTION: Generate theme statements using ONLY the "if/then hypothesis" structure. Do NOT use prescriptive directives.

        STRUCTURE TEMPLATE:
        If Rev [implemented specific solution], they may [improve/reduce/increase] [specific outcome] ([context about issue prevalence/scope]).

        CRITERION: {criterion}
        COMPANIES: {companies}
        FINDING TYPES: {finding_types}
        AVERAGE IMPACT SCORE: {avg_impact}
        COMPETITIVE FLAG: {competitive_flag}
        
        SAMPLE QUOTES:
        {quotes}
        
        KEY GUIDELINES:
        1. OPENING STRUCTURE: Use "If Rev [action]..." NOT "If [interviewee] [action]..."
        2. CONDITIONAL LANGUAGE: Use "they may improve/reduce/increase" NOT "they will/can/should"
        3. ISSUE CONTEXT: Include parenthetical context like "(negative sentiment seen across X interviews)"
        4. OUTCOME FRAMING: Present benefits as hypotheses using "could potentially," "may result in"
        5. SINGLE HYPOTHESIS: Generate ONLY ONE "if/then" statement per theme - do not create multiple hypotheses
        6. NO EXAMPLES: Do NOT include "For example" or specific quote examples in the theme statement
        
        QUALITY CHECKLIST:
        ✅ Starts with conditional "If Rev" statement (not interviewee names)
        ✅ Uses hypothesis language ("may," "could," "might")
        ✅ Includes parenthetical context about issue scope
        ✅ Presents outcomes as potential rather than guaranteed
        ✅ Contains ONLY ONE hypothesis statement per theme
        ✅ NO "For example" sections or specific quote examples
        
        FORBIDDEN PHRASES (DO NOT USE):
        - "If [interviewee name]..."
        - "If [customer name]..."
        - "Rev should..."
        - "Rev must..."
        - "Rev needs to..."
        - "Rev will..."
        - "Rev can..."
        - "For example"
        - "For instance"
        - "Specifically"
        - "competitive advantage"
        - "strategic positioning"
        - "synergies"
        - "operational efficiency"
        - "enhance engagement"
        - "drive growth"
        - "foster relationships"
        - "leverage capabilities"
        - "optimize processes"
        - "streamline operations"
        
        GOOD EXAMPLES:
        - "If Rev established a structured onboarding process that includes personalized training sessions tailored to individual user needs, they may improve user satisfaction and reduce setup-related concerns (negative sentiment in onboarding seen across multiple interviews)."
        - "If Rev redesigned the file sharing interface to address navigation challenges, they may improve collaboration efficiency and user experience (file sharing difficulties mentioned by multiple users)."
        - "If Rev enhanced security compliance features by creating clearer documentation and providing targeted training on compliance protocols, they may eliminate critical compliance issues (compliance confusion reported across interviews)."
        
        BAD EXAMPLES:
        - "If Cyrus Nazarian implemented..." (WRONG - should be "If Rev implemented...")
        - "If Trish Herrera streamlined..." (WRONG - should be "If Rev streamlined...")
        - Multiple "If" statements in one theme (WRONG - should be only one hypothesis per theme)
        - "For example, Trish Herrera mentioned..." (WRONG - no examples in theme statement)
        - "Rev should enhance operational efficiency and drive competitive advantage"
        - "Strategic alignment of product offerings will foster stronger relationships"
        - "Cross-functional synergies position the organization for sustained growth"
        
        Generate the hypothesis-based theme using ONLY the required structure with ONE hypothesis per theme and NO examples:
        """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                criterion=pattern_key,
                companies=", ".join(pattern['companies']),
                finding_types="\n".join(finding_summary),
                avg_impact=f"{pattern['avg_impact_score']:.1f}",
                competitive_flag="Yes" if pattern.get('competitive_flag', False) else "No",
                quotes=quote_examples
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating criterion theme for {pattern_key}: {e}")
            self.processing_metrics["processing_errors"] += 1
            return None
    
    def save_themes_to_supabase(self, themes: List[Dict], client_id: str = 'default'):
        """Save themes to Supabase"""
        logger.info("💾 Saving themes to Supabase...")
        
        saved_count = 0
        skipped_count = 0
        
        for i, theme in enumerate(themes):
            # IMPROVED: Better validation and logging
            primary_quote = theme.get('primary_theme_quote', '')
            
            if not primary_quote or not primary_quote.strip():
                logger.warning(f"⚠️ Skipping theme {i+1} - no primary_theme_quote found")
                logger.warning(f"   Theme statement: {theme.get('theme_statement', '')[:100]}...")
                logger.warning(f"   Companies: {theme.get('interview_companies', [])}")
                skipped_count += 1
                continue
            
            theme['client_id'] = client_id  # Add client_id to each theme
            if self.db.save_theme(theme, client_id=client_id):
                saved_count += 1
                if theme['theme_strength'] == 'High':
                    self.processing_metrics["high_strength_themes"] += 1
                if theme['competitive_flag']:
                    self.processing_metrics["competitive_themes"] += 1
            else:
                logger.error(f"❌ Failed to save theme {i+1} to database")
                skipped_count += 1
        
        logger.info(f"✅ Saved {saved_count} themes to Supabase for client {client_id}")
        if skipped_count > 0:
            logger.warning(f"⚠️ Skipped {skipped_count} themes due to missing quotes or save failures")
        self.processing_metrics["themes_generated"] = saved_count
    
    def process_themes(self, client_id: str = 'default') -> Dict:
        """Main processing function for Stage 4"""
        
        logger.info("🚀 STAGE 4: ENHANCED THEME GENERATION")
        logger.info("=" * 60)
        
        # PURGE OLD THEMES FIRST
        self.purge_old_themes(client_id)
        
        # Get findings for analysis
        df = self.get_findings_for_analysis(client_id=client_id)
        
        if df.empty:
            logger.info("✅ No findings available for theme generation")
            return {"status": "no_data", "message": "No findings available"}
        
        self.processing_metrics["total_findings_processed"] = len(df)
        
        # Analyze patterns
        patterns = self.analyze_finding_patterns(df, client_id=client_id)
        
        if not patterns:
            logger.info("✅ No patterns found meeting minimum requirements")
            return {"status": "no_patterns", "message": "No patterns found"}
        
        # Detect competitive themes
        patterns = self.detect_competitive_themes(patterns, client_id=client_id)
        
        # Generate theme statements
        themes = self.generate_theme_statements(patterns, client_id=client_id)
        
        if not themes:
            logger.info("✅ No themes generated")
            return {"status": "no_themes", "message": "No themes generated"}
        
        # ENHANCED CONSOLIDATION WITH STRENGTH-BASED FILTERING
        logger.info("🔗 Consolidating duplicate themes...")
        original_count = len(themes)
        themes = self.consolidate_duplicate_themes(themes)
        consolidated_count = len(themes)
        
        if original_count != consolidated_count:
            logger.info(f"✅ Consolidated {original_count} themes into {consolidated_count} unique themes")
        
        # Filter themes by strength and limit per category
        config = self.load_config()
        max_themes_per_category = config.get('stage4', {}).get('theme_consolidation', {}).get('max_themes_per_category', 5)
        
        # Group themes by category and keep only the strongest ones
        themes_by_category = {}
        for theme in themes:
            category = theme.get('theme_category', 'unknown')
            if category not in themes_by_category:
                themes_by_category[category] = []
            themes_by_category[category].append(theme)
        
        # Keep only the strongest themes per category
        filtered_themes = []
        for category, category_themes in themes_by_category.items():
            # Sort by overall quality score
            category_themes.sort(key=lambda x: json.loads(x.get('quality_scores', '{}')).get('overall', 0), reverse=True)
            # Keep only the top themes per category
            filtered_themes.extend(category_themes[:max_themes_per_category])
        
        themes = filtered_themes
        logger.info(f"✅ Filtered to {len(themes)} strongest themes across categories")
        
        # Save to Supabase
        self.save_themes_to_supabase(themes, client_id=client_id)
        
        # Generate summary
        summary = self.generate_summary_statistics(themes)
        
        logger.info(f"\n✅ Stage 4 complete! Generated {len(themes)} themes")
        self.print_summary_report(summary)
        
        return {
            "status": "success",
            "findings_processed": len(df),
            "themes_generated": len(themes),
            "high_strength_themes": self.processing_metrics["high_strength_themes"],
            "competitive_themes": self.processing_metrics["competitive_themes"],
            "summary": summary,
            "processing_metrics": self.processing_metrics
        }
    
    def generate_summary_statistics(self, themes: List[Dict]) -> Dict:
        """Generate summary statistics"""
        
        # Theme strength distribution
        strength_distribution = Counter(theme['theme_strength'] for theme in themes)
        
        # Theme category distribution
        category_distribution = Counter(theme['theme_category'] for theme in themes)
        
        # Company coverage
        all_companies = set()
        for theme in themes:
            all_companies.update(theme['interview_companies'])
        
        # Average confidence and impact
        avg_confidence = sum(theme['avg_confidence_score'] for theme in themes) / len(themes) if themes else 0
        
        return {
            'total_themes': len(themes),
            'strength_distribution': dict(strength_distribution),
            'category_distribution': dict(category_distribution),
            'companies_covered': len(all_companies),
            'average_confidence': avg_confidence,
            'high_strength_count': self.processing_metrics["high_strength_themes"],
            'competitive_count': self.processing_metrics["competitive_themes"]
        }
    
    def print_summary_report(self, summary: Dict):
        """Print a comprehensive summary report with fuzzy matching metrics"""
        
        logger.info(f"\n📊 STAGE 4 SUMMARY REPORT (Enhanced with Fuzzy Matching)")
        logger.info("=" * 70)
        logger.info(f"Total themes generated: {summary['total_themes']}")
        logger.info(f"High strength themes: {summary['high_strength_count']}")
        logger.info(f"Competitive themes: {summary['competitive_count']}")
        logger.info(f"Fuzzy grouped themes: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"Companies covered: {summary['companies_covered']}")
        logger.info(f"Average confidence: {summary['average_confidence']:.2f}")
        
        logger.info(f"\n📈 THEME STRENGTH DISTRIBUTION:")
        for strength, count in summary['strength_distribution'].items():
            logger.info(f"  {strength}: {count}")
        
        logger.info(f"\n🎯 THEME CATEGORY DISTRIBUTION:")
        for category, count in summary['category_distribution'].items():
            logger.info(f"  {category}: {count}")
        
        logger.info(f"\n🔍 FUZZY MATCHING PERFORMANCE:")
        logger.info(f"  Semantic groups created: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"  Cross-criteria themes: {self.processing_metrics['fuzzy_grouped_themes']}")
        logger.info(f"  Processing errors: {self.processing_metrics['processing_errors']}")
        
        logger.info(f"\n💡 ENHANCED FEATURES:")
        logger.info("  ✅ Fuzzy matching for semantic similarity")
        logger.info("  ✅ Cross-criteria theme generation")
        logger.info("  ✅ Enhanced business narratives")
        logger.info("  ✅ Improved quote attribution")
    
    def score_theme_quality(self, theme_statement: str, pattern: Dict) -> Dict:
        """Enhanced theme quality scoring with business impact and strength classification"""
        scores = {
            'specificity': 0,
            'actionability': 0,
            'evidence_strength': 0,
            'business_impact': 0,
            'overall': 0,
            'strength_classification': 'weak'
        }
        
        # CRITICAL: Check for low-quality indicators that should heavily penalize the theme
        low_quality_indicators = [
            'if you were the ceo',
            'what would you change',
            'better serve firms',
            'what would you do',
            'how would you',
            'what should',
            'direct quote from interview',
            'interview question',
            'question mark',
            '?',
            'i would',
            'you know',
            'um',
            'uh',
            'like',
            'sort of',
            'kind of'
        ]
        
        # Check for low-quality content
        theme_lower = theme_statement.lower()
        low_quality_score = 0
        for indicator in low_quality_indicators:
            if indicator in theme_lower:
                low_quality_score += 2  # Heavy penalty for each low-quality indicator
        
        # If theme contains multiple low-quality indicators, heavily penalize
        if low_quality_score >= 4:
            scores['specificity'] = 1
            scores['actionability'] = 1
            scores['evidence_strength'] = 1
            scores['business_impact'] = 1
            scores['overall'] = 1
            scores['strength_classification'] = 'weak'
            return scores
        
        # Check for proper hypothesis structure (but allow direct insight themes too)
        is_hypothesis = theme_statement.strip().startswith('if rev')
        is_direct_insight = any(keyword in theme_lower for keyword in ['impact', 'affect', 'lead to', 'result in', 'cause'])
        
        if not (is_hypothesis or is_direct_insight):
            scores['specificity'] = 2
            scores['actionability'] = 2
            scores['evidence_strength'] = 2
            scores['business_impact'] = 2
            scores['overall'] = 2
            scores['strength_classification'] = 'weak'
            return scores
        
        # Score specificity (0-10)
        specificity_indicators = [
            'specific', 'concrete', 'particular', 'detailed', 'precise',
            'exact', 'definite', 'clear', 'explicit', 'particular',
            'implement', 'enhance', 'improve', 'develop', 'create',
            'integration', 'accuracy', 'speed', 'cost', 'pricing'
        ]
        specificity_score = sum(1 for indicator in specificity_indicators if indicator in theme_lower)
        scores['specificity'] = min(specificity_score * 1.5, 10)  # Max 10 points
        
        # Score actionability (0-10)
        actionability_indicators = [
            'implement', 'develop', 'create', 'build', 'establish',
            'improve', 'enhance', 'optimize', 'streamline', 'leverage',
            'provide', 'offer', 'deliver', 'enable', 'facilitate',
            'reduce', 'increase', 'decrease', 'minimize', 'maximize'
        ]
        actionability_score = sum(1 for indicator in actionability_indicators if indicator in theme_lower)
        scores['actionability'] = min(actionability_score * 1.5, 10)  # Max 10 points
        
        # Score evidence strength (0-10)
        company_count = pattern.get('company_count', 0)
        finding_count = pattern.get('finding_count', 0)
        avg_confidence = pattern.get('avg_confidence', 0)
        
        # Evidence strength based on data quality
        evidence_score = 0
        if company_count >= 5:
            evidence_score += 4
        elif company_count >= 3:
            evidence_score += 3
        elif company_count >= 2:
            evidence_score += 2
        else:
            evidence_score += 1
            
        if finding_count >= 5:
            evidence_score += 3
        elif finding_count >= 3:
            evidence_score += 2
        else:
            evidence_score += 1
            
        if avg_confidence >= 4.0:
            evidence_score += 3
        elif avg_confidence >= 3.0:
            evidence_score += 2
        else:
            evidence_score += 1
            
        scores['evidence_strength'] = min(evidence_score, 10)
        
        # Score business impact (0-10)
        business_impact_indicators = [
            'impact', 'affect', 'lead to', 'result in', 'cause',
            'revenue', 'retention', 'satisfaction', 'adoption', 'competitiveness',
            'efficiency', 'productivity', 'cost', 'time', 'quality'
        ]
        business_impact_score = sum(1 for indicator in business_impact_indicators if indicator in theme_lower)
        scores['business_impact'] = min(business_impact_score * 1.5, 10)  # Max 10 points
        
        # Apply low-quality penalty
        if low_quality_score > 0:
            penalty = min(low_quality_score, 5)  # Cap penalty at 5 points
            scores['specificity'] = max(0, scores['specificity'] - penalty)
            scores['actionability'] = max(0, scores['actionability'] - penalty)
            scores['evidence_strength'] = max(0, scores['evidence_strength'] - penalty)
            scores['business_impact'] = max(0, scores['business_impact'] - penalty)
        
        # Calculate overall score
        scores['overall'] = (scores['specificity'] + scores['actionability'] + scores['evidence_strength'] + scores['business_impact']) / 4
        
        # Classify theme strength
        if scores['overall'] >= 8.0:
            scores['strength_classification'] = 'strong'
        elif scores['overall'] >= 6.0:
            scores['strength_classification'] = 'moderate'
        else:
            scores['strength_classification'] = 'weak'
        
        return scores
    
    def meets_quality_thresholds(self, quality_scores: Dict, config: Dict) -> bool:
        """Check if theme meets quality thresholds"""
        quality_config = config.get('quality_scoring', {})
        
        specificity_threshold = quality_config.get('specificity_threshold', 7.0)
        actionability_threshold = quality_config.get('actionability_threshold', 6.0)
        evidence_strength_threshold = quality_config.get('evidence_strength_threshold', 6.0)
        min_overall_score = quality_config.get('min_overall_score', 6.5)
        
        return (
            quality_scores['specificity'] >= specificity_threshold and
            quality_scores['actionability'] >= actionability_threshold and
            quality_scores['evidence_strength'] >= evidence_strength_threshold and
            quality_scores['overall'] >= min_overall_score
        )
    
    def improve_weak_theme(self, theme_statement: str, pattern: Dict) -> str:
        """Improve a weak theme statement by making it more specific and hypothesis-based"""
        
        # Handle quote objects properly
        quote_examples = []
        for quote in pattern['quotes'][:3]:
            if isinstance(quote, dict):
                quote_text = quote.get('text', '')
            else:
                quote_text = str(quote)
            quote_examples.append(f"'{quote_text[:200]}...'")
        quote_examples = "\n".join(quote_examples)
        
        prompt = ChatPromptTemplate.from_template("""
        CRITICAL INSTRUCTION: Rewrite this weak theme statement using ONLY the "if/then hypothesis" structure. Do NOT use prescriptive directives.

        WEAK THEME: {weak_theme}
        
        CONTEXT:
        COMPANIES: {companies}
        CRITERIA: {criteria}
        QUOTES: {quotes}
        
        STRUCTURE TEMPLATE:
        If Rev [implemented specific solution], they may [improve/reduce/increase] [specific outcome] ([context about issue prevalence/scope]).
        
        KEY GUIDELINES:
        1. OPENING STRUCTURE: Use "If Rev [action]..." NOT "If [interviewee] [action]..."
        2. CONDITIONAL LANGUAGE: Use "they may improve/reduce/increase" NOT "they will/can/should"
        3. ISSUE CONTEXT: Include parenthetical context like "(negative sentiment seen across X interviews)"
        4. OUTCOME FRAMING: Present benefits as hypotheses using "could potentially," "may result in"
        5. SINGLE HYPOTHESIS: Generate ONLY ONE "if/then" statement per theme - do not create multiple hypotheses
        6. NO EXAMPLES: Do NOT include "For example" or specific quote examples in the theme statement
        
        QUALITY CHECKLIST:
        ✅ Starts with conditional "If Rev" statement (not interviewee names)
        ✅ Uses hypothesis language ("may," "could," "might")
        ✅ Includes parenthetical context about issue scope
        ✅ Presents outcomes as potential rather than guaranteed
        ✅ Contains ONLY ONE hypothesis statement per theme
        
        FORBIDDEN PHRASES (DO NOT USE):
        - "If [interviewee name]..."
        - "If [customer name]..."
        - "Rev should..."
        - "Rev must..."
        - "Rev needs to..."
        - "Rev will..."
        - "Rev can..."
        - "For example"
        - "For instance"
        - "Specifically"
        - "competitive advantage"
        - "strategic positioning"
        - "synergies"
        - "operational efficiency"
        
        EXAMPLES OF IMPROVEMENTS:
        WEAK: "If Cyrus Nazarian implemented a system, they may improve efficiency"
        STRONG: "If Rev implemented a more responsive customer support system, they may improve customer satisfaction and reduce response times (support delays noted in multiple interviews)."
        
        WEAK: "If Trish Herrera streamlined processes, they may reduce confusion"
        STRONG: "If Rev streamlined the onboarding process by providing comprehensive training materials, they may reduce onboarding time and improve user retention (onboarding challenges highlighted by various users)."
        
        WEAK: Multiple "If" statements about different interviewees
        STRONG: Single "If Rev" statement that addresses the core issue
        
        OUTPUT: Just the improved hypothesis-based theme statement using ONLY the required structure with ONE hypothesis per theme and NO examples, no additional formatting.
        """)
        
        try:
            result = self.llm.invoke(prompt.format_messages(
                weak_theme=theme_statement,
                companies=", ".join(pattern.get('companies', [])),
                criteria=", ".join(pattern.get('criteria_covered', [])),
                quotes=quote_examples
            ))
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error improving weak theme: {e}")
            return theme_statement  # Return original if improvement fails
    
    def purge_old_themes(self, client_id: str = 'default'):
        """Purge old themes for the client to start fresh with improved quality controls"""
        logger.info(f"🗑️ Purging old themes for client {client_id}...")
        
        try:
            # Get existing themes for the client
            existing_themes = self.db.get_themes(client_id=client_id)
            
            if existing_themes.empty:
                logger.info("✅ No existing themes to purge")
                return
            
            # Delete themes from database
            deleted_count = 0
            for _, theme in existing_themes.iterrows():
                if self.db.delete_theme(theme['id'], client_id=client_id):
                    deleted_count += 1
            
            logger.info(f"✅ Purged {deleted_count} old themes for client {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Error purging old themes: {e}")
            self.processing_metrics["processing_errors"] += 1
    
    def is_direct_quote_or_question(self, theme_statement: str) -> bool:
        """Detect if a theme is essentially a direct quote from an interview or a question"""
        theme_lower = theme_statement.lower()
        
        # CRITICAL: If it starts with "If Rev", it's a valid hypothesis, not a direct quote
        if theme_statement.strip().startswith('If Rev'):
            return False
        
        # Check for interview question patterns
        question_indicators = [
            'if you were the ceo',
            'what would you change',
            'what would you do',
            'how would you',
            'what should',
            'better serve firms',
            'better serve companies',
            'better serve customers',
            'what do you think',
            'how do you feel',
            'what are your thoughts'
        ]
        
        # Check for direct quote patterns
        quote_indicators = [
            'i would',
            'you know',
            'um',
            'uh',
            'like',
            'sort of',
            'kind of',
            'i think',
            'i feel',
            'i believe',
            'in my opinion',
            'from my perspective'
        ]
        
        # Check for incomplete or dangling quotes
        if theme_statement.strip().endswith('"') or theme_statement.strip().endswith('"'):
            return True
        
        # Check for question marks
        if '?' in theme_statement:
            return True
        
        # Check for interview question patterns
        for indicator in question_indicators:
            if indicator in theme_lower:
                return True
        
        # Check for direct quote patterns (but only if they're not part of a valid hypothesis)
        for indicator in quote_indicators:
            if indicator in theme_lower and not theme_statement.strip().startswith('If Rev'):
                return True
        
        return False
    
    def consolidate_duplicate_themes(self, themes: List[Dict]) -> List[Dict]:
        """Consolidate duplicate or near-duplicate themes"""
        if not themes:
            return themes
        
        consolidated = []
        processed_themes = set()
        
        for i, theme in enumerate(themes):
            if i in processed_themes:
                continue
                
            # Create a simplified version of the theme for comparison
            theme_key = self._create_theme_key(theme)
            
            # Find duplicates
            duplicates = []
            for j, other_theme in enumerate(themes[i+1:], i+1):
                if j in processed_themes:
                    continue
                    
                other_key = self._create_theme_key(other_theme)
                if self._are_themes_duplicates(theme_key, other_key):
                    duplicates.append((j, other_theme))
                    processed_themes.add(j)
            
            if duplicates:
                # Consolidate the theme with its duplicates
                consolidated_theme = self._consolidate_theme_group([theme] + [d[1] for d in duplicates])
                consolidated.append(consolidated_theme)
                logger.info(f"🔗 Consolidated {len(duplicates) + 1} duplicate themes into one")
            else:
                consolidated.append(theme)
            
            processed_themes.add(i)
        
        logger.info(f"📊 Consolidated {len(themes)} themes into {len(consolidated)} unique themes")
        return consolidated
    
    def _create_theme_key(self, theme: Dict) -> str:
        """Create a simplified key for theme comparison"""
        statement = theme.get('theme_statement', '').lower()
        
        # Remove common variations and focus on core message
        statement = statement.replace('enhanced', 'enhance')
        statement = statement.replace('improved', 'improve')
        statement = statement.replace('implementing', 'implement')
        statement = statement.replace('providing', 'provide')
        
        # Extract the core action and outcome
        if 'if rev' in statement:
            # Get the action part (between "if rev" and "they may")
            action_start = statement.find('if rev') + 6
            action_end = statement.find('they may')
            if action_end > action_start:
                action = statement[action_start:action_end].strip()
                return action
        
        return statement
    
    def _are_themes_duplicates(self, key1: str, key2: str) -> bool:
        """Check if two themes are duplicates based on their keys with enhanced similarity detection"""
        # Exact match
        if key1 == key2:
            return True
        
        # Enhanced similarity detection for accuracy/quality themes
        accuracy_quality_keywords = ['accuracy', 'quality', 'transcription', 'inconsistent', 'frustrate', 'dissatisfaction']
        
        # Check if both themes are about accuracy/quality issues
        key1_lower = key1.lower()
        key2_lower = key2.lower()
        
        accuracy_keywords_in_key1 = sum(1 for keyword in accuracy_quality_keywords if keyword in key1_lower)
        accuracy_keywords_in_key2 = sum(1 for keyword in accuracy_quality_keywords if keyword in key2_lower)
        
        # If both themes have accuracy/quality keywords, they're likely duplicates
        if accuracy_keywords_in_key1 >= 2 and accuracy_keywords_in_key2 >= 2:
            return True
        
        # Check for very similar actions (e.g., "enhance security compliance features")
        words1 = set(key1.split())
        words2 = set(key2.split())
        
        # If they share 75% of their key words, consider them duplicates
        if len(words1) > 0 and len(words2) > 0:
            common_words = words1.intersection(words2)
            similarity = len(common_words) / max(len(words1), len(words2))
            return similarity >= 0.75
        
        return False
    
    def _consolidate_theme_group(self, themes: List[Dict]) -> Dict:
        """Consolidate a group of duplicate themes into one stronger theme"""
        if not themes:
            return {}
        
        # Use the first theme as the base
        consolidated = themes[0].copy()
        
        # Combine all companies
        all_companies = set()
        for theme in themes:
            companies = theme.get('interview_companies', [])
            if isinstance(companies, list):
                all_companies.update(companies)
        
        consolidated['interview_companies'] = list(all_companies)
        
        # Combine all finding IDs
        all_finding_ids = set()
        for theme in themes:
            finding_ids = theme.get('supporting_finding_ids', [])
            if isinstance(finding_ids, list):
                all_finding_ids.update(finding_ids)
        
        consolidated['supporting_finding_ids'] = list(all_finding_ids)
        
        # Update company count and finding count
        consolidated['company_count'] = len(all_companies)
        consolidated['finding_count'] = len(all_finding_ids)
        
        # Update business implications
        consolidated['business_implications'] = f"Impact score: {consolidated.get('avg_impact_score', 0):.1f}, affecting {len(all_companies)} companies"
        
        # Combine quotes from all themes
        all_quotes = []
        for theme in themes:
            quotes = theme.get('quotes', [])
            if isinstance(quotes, list):
                all_quotes.extend(quotes)
        
        consolidated['quotes'] = all_quotes
        
        return consolidated

def run_stage4_analysis(client_id: str = 'default'):
    """Run Stage 4 theme analysis"""
    analyzer = Stage4ThemeAnalyzer()
    return analyzer.process_themes(client_id=client_id)

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
    
    print(f"🔍 Running Stage 4: Theme Generation for client '{client_id}'...")
    result = run_stage4_analysis(client_id=client_id)
    print(f"✅ Stage 4 complete: {result}") 