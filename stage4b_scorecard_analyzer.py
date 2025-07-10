#!/usr/bin/env python3

"""
Stage 4B: Scorecard-Driven Theme Analyzer

This module implements scorecard-driven theme development using criteria prioritization
and sentiment alignment as a complementary approach to similarity-based theming.
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
import yaml
import re
from supabase_database import SupabaseDatabase
import openai
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criterion keywords for validation
CRITERION_KEYWORDS = {
    'security_compliance': ['security', 'compliance', 'encryption', 'privacy', 'gdpr', 'hipaa', 'secure', 'confidential'],
    'commercial_terms': ['price', 'cost', 'pricing', 'billing', 'rate', 'fee', 'expensive', 'cheap', 'affordable'],
    'implementation_onboarding': ['onboarding', 'setup', 'implementation', 'installation', 'deployment', 'training'],
    'product_capability': ['feature', 'capability', 'functionality', 'tool', 'platform', 'software', 'system'],
    'sales_experience_partnership': ['sales', 'partnership', 'relationship', 'account', 'rep', 'representative'],
    'support_service_quality': ['support', 'service', 'help', 'assistance', 'customer service', 'response'],
    'speed_responsiveness': ['speed', 'fast', 'quick', 'turnaround', 'response time', 'efficiency', 'timely'],
    'market_position_reputation': ['reputation', 'brand', 'market', 'position', 'known', 'recognized'],
    'integration_technical_fit': ['integration', 'api', 'connect', 'technical', 'compatibility', 'workflow'],
    'vendor_stability': ['vendor', 'company', 'stability', 'reliable', 'trustworthy', 'established']
}

def validate_quote_quality(quote_text: str) -> bool:
    """Validate quote quality and filter out corrupted text"""
    if not quote_text or not isinstance(quote_text, str):
        return False
    
    # Check minimum length
    if len(quote_text.strip()) < 10:
        return False
    
    # Check for minimum word count
    if len(quote_text.split()) < 3:
        return False
    
    # Check for broken formatting (repeated single characters)
    if re.search(r'[A-Z]\s+[A-Z]\s+[A-Z]', quote_text):
        return False
    
    # Check for excessive repetition
    words = quote_text.split()
    if len(words) > 10:
        word_counts = Counter(words)
        most_common = word_counts.most_common(1)[0]
        if most_common[1] > len(words) * 0.3:  # More than 30% repetition
            return False
    
    return True

def validate_criterion_alignment(quotes: List[Dict], criterion: str) -> bool:
    """Validate that quotes actually relate to the criterion"""
    if not quotes:
        return False
    
    keywords = CRITERION_KEYWORDS.get(criterion, [])
    if not keywords:
        return True  # If no keywords defined, assume valid
    
    relevant_quotes = 0
    for q in quotes:
        if isinstance(q, dict):
            text = q.get('text', '').lower()
        else:
            text = str(q).lower()
        
        if any(keyword in text for keyword in keywords):
            relevant_quotes += 1
    
    # At least 70% of quotes must be relevant
    return relevant_quotes >= len(quotes) * 0.7

def deduplicate_quotes_robust(quotes: List[Dict]) -> List[Dict]:
    """Robust deduplication of quotes with text normalization"""
    seen = set()
    deduped = []
    
    for q in quotes:
        if isinstance(q, dict):
            text = q.get('text', '').strip()
        else:
            text = str(q).strip()
        
        if not text:
            continue
        
        # Normalize text (remove extra spaces, punctuation, convert to lowercase)
        normalized = re.sub(r'\s+', ' ', text.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        if normalized and normalized not in seen:
            deduped.append(q)
            seen.add(normalized)
    
    return deduped

class Stage4BScorecardAnalyzer:
    """Scorecard-driven theme analyzer for Stage 4B"""
    
    def __init__(self, config_path: str = "config/analysis_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db = SupabaseDatabase()
        
        # Processing metrics
        self.processing_metrics = {
            "total_criteria_analyzed": 0,
            "prioritized_criteria_found": 0,
            "scorecard_themes_generated": 0,
            "high_quality_themes": 0,
            "sentiment_aligned_themes": 0,
            "processing_errors": 0,
            "themes_before_merging": 0,
            "themes_after_merging": 0,
            "merged_groups": 0
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
        """Get default configuration"""
        return {
            'stage4b': {
                'relevance_threshold': 4.0,
                'min_quotes_per_theme': 3,
                'min_companies_per_theme': 2,
                'sentiment_consistency_threshold': 0.7,
                'quote_diversity_threshold': 0.5,
                'quality_thresholds': {
                    'evidence_strength': 0.6,
                    'stakeholder_weight': 0.5,
                    'overall_quality': 0.6
                },
                'criteria_prioritization': {
                    'min_high_relevance_quotes': 3,
                    'min_companies_affected': 2,
                    'relevance_ratio_threshold': 0.3
                }
            }
        }
    
    def analyze_criteria_prioritization(self, client_id: str = 'default') -> Dict:
        """Analyze criteria prioritization from quote analysis data"""
        logger.info("🔍 Analyzing criteria prioritization...")
        
        try:
            # Get quote analysis data
            response = self.db.supabase.table('quote_analysis').select('*').eq('client_id', client_id).execute()
            quote_data = response.data
            
            if not quote_data:
                logger.warning("No quote analysis data found")
                return {}
            
            # Convert to DataFrame
            df = pd.DataFrame(quote_data)
            
            # Group by criterion
            criteria_analysis = {}
            
            for criterion in df['criterion'].unique():
                criterion_data = df[df['criterion'] == criterion]
                
                # Calculate prioritization metrics
                total_quotes = len(criterion_data)
                high_relevance_quotes = len(criterion_data[criterion_data['relevance_score'] >= 4.0])
                companies_affected = criterion_data['quote_id'].nunique()  # Use quote_id as proxy for companies
                
                # Calculate sentiment distribution
                sentiment_counts = Counter(criterion_data['sentiment'].fillna('neutral'))
                
                # Calculate deal impact distribution (use is_deal_impacting if available)
                if 'is_deal_impacting' in criterion_data.columns:
                    deal_counts = Counter(criterion_data['is_deal_impacting'].fillna(False))
                else:
                    deal_counts = {'unknown': len(criterion_data)}
                
                # Calculate priority score
                relevance_ratio = high_relevance_quotes / total_quotes if total_quotes > 0 else 0
                priority_score = (relevance_ratio * 0.4 + 
                                (companies_affected / 10) * 0.3 + 
                                (high_relevance_quotes / 10) * 0.3)
                
                # Check if meets prioritization thresholds
                config = self.config.get('stage4b', {}).get('criteria_prioritization', {})
                min_quotes = config.get('min_high_relevance_quotes', 3)
                min_companies = config.get('min_companies_affected', 2)
                min_ratio = config.get('relevance_ratio_threshold', 0.3)
                
                meets_thresholds = (
                    high_relevance_quotes >= min_quotes and
                    companies_affected >= min_companies and
                    relevance_ratio >= min_ratio
                )
                
                criteria_analysis[criterion] = {
                    'priority_score': round(priority_score, 3),
                    'high_relevance_quotes': high_relevance_quotes,
                    'total_quotes': total_quotes,
                    'relevance_ratio': round(relevance_ratio, 3),
                    'companies_affected': companies_affected,
                    'sentiment_distribution': dict(sentiment_counts),
                    'deal_impact_distribution': dict(deal_counts),
                    'meets_prioritization_thresholds': meets_thresholds,
                    'prioritization_evidence': {
                        'high_relevance_quote_ids': criterion_data[criterion_data['relevance_score'] >= 4.0]['quote_id'].tolist(),
                        'quote_list': criterion_data['quote_id'].unique().tolist(),
                        'deal_impact_list': criterion_data.get('is_deal_impacting', pd.Series([False] * len(criterion_data))).unique().tolist()
                    }
                }
                
                self.processing_metrics["total_criteria_analyzed"] += 1
                if meets_thresholds:
                    self.processing_metrics["prioritized_criteria_found"] += 1
            
            logger.info(f"✅ Analyzed {len(criteria_analysis)} criteria, {self.processing_metrics['prioritized_criteria_found']} prioritized")
            return criteria_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing criteria prioritization: {e}")
            self.processing_metrics["processing_errors"] += 1
            return {}
    
    def generate_scorecard_themes(self, criteria_prioritization: Dict, client_id: str = 'default') -> List[Dict]:
        """Generate scorecard themes from prioritized criteria"""
        logger.info("🎯 Generating scorecard themes...")
        
        themes = []
        
        try:
            # Get quote analysis data for theme generation
            response = self.db.supabase.table('quote_analysis').select('*').eq('client_id', client_id).execute()
            quote_data = response.data
            
            if not quote_data:
                logger.warning("No quote analysis data found for theme generation")
                return themes
            
            df = pd.DataFrame(quote_data)
            
            # Process each prioritized criterion
            for criterion, analysis in criteria_prioritization.items():
                if not analysis.get('meets_prioritization_thresholds', False):
                    continue
                
                criterion_quotes = df[df['criterion'] == criterion]
                
                # Group by sentiment direction
                sentiment_groups = criterion_quotes.groupby('sentiment')
                
                for sentiment, sentiment_quotes in sentiment_groups:
                    if len(sentiment_quotes) < 3:  # Minimum quotes per theme
                        continue
                    
                    # Generate theme for this sentiment group
                    theme = self._generate_single_theme(
                        criterion, sentiment, sentiment_quotes, analysis, client_id
                    )
                    
                    if theme:
                        themes.append(theme)
                        self.processing_metrics["scorecard_themes_generated"] += 1
                        
                        # Check quality
                        if theme.get('overall_quality_score', 0) >= 0.7:
                            self.processing_metrics["high_quality_themes"] += 1
                        
                        if theme.get('sentiment_consistency_score', 0) >= 0.7:
                            self.processing_metrics["sentiment_aligned_themes"] += 1
            
            logger.info(f"✅ Generated {len(themes)} scorecard themes")
            return themes
            
        except Exception as e:
            logger.error(f"Error generating scorecard themes: {e}")
            self.processing_metrics["processing_errors"] += 1
            return themes
    
    def _generate_single_theme(self, criterion: str, sentiment: str, quotes_df: pd.DataFrame, 
                              analysis: Dict, client_id: str) -> Optional[Dict]:
        """Generate a single scorecard theme"""
        try:
            # Get core responses to get the actual quote text
            quote_ids = quotes_df['quote_id'].unique().tolist()
            if not quote_ids:
                logger.warning(f"No quote IDs found for {criterion}-{sentiment}")
                return None
            
            # Get core responses for these quote IDs
            response = self.db.supabase.table('core_responses').select('*').in_('response_id', quote_ids).eq('client_id', client_id).execute()
            core_responses = {resp['response_id']: resp for resp in response.data}
            
            # Prepare supporting quotes with quality validation
            supporting_quotes = []
            companies_represented = set()
            
            for _, quote in quotes_df.iterrows():
                quote_id = quote['quote_id']
                core_response = core_responses.get(quote_id)
                
                if not core_response:
                    logger.warning(f"No core response found for quote_id: {quote_id}")
                    continue
                
                quote_text = core_response['verbatim_response']
                
                # Validate quote quality
                if not validate_quote_quality(quote_text):
                    logger.debug(f"Skipping low-quality quote: {quote_id}")
                    continue
                
                quote_obj = {
                    'text': quote_text,
                    'relevance_score': quote['relevance_score'],
                    'sentiment': quote['sentiment'],
                    'company': core_response.get('company', 'Unknown'),
                    'interviewee': core_response.get('interviewee_name', 'Unknown'),
                    'deal_status': core_response.get('deal_status', 'unknown')
                }
                supporting_quotes.append(quote_obj)
                companies_represented.add(core_response.get('company', 'Unknown'))
            
            # Validate criterion alignment
            if not validate_criterion_alignment(supporting_quotes, criterion):
                logger.warning(f"Quotes don't align with criterion {criterion}, skipping theme")
                return None
            
            # Deduplicate quotes
            supporting_quotes = deduplicate_quotes_robust(supporting_quotes)
            
            # Check minimum requirements after filtering
            if len(supporting_quotes) < 3:
                logger.warning(f"Insufficient quotes after filtering for {criterion}-{sentiment}")
                return None
            
            if len(companies_represented) < 2:
                logger.warning(f"Insufficient company diversity for {criterion}-{sentiment}")
                return None
            
            # Generate theme title
            theme_title = self._generate_theme_title(criterion, sentiment, len(companies_represented))
            
            # Generate performance summary
            performance_summary = self._generate_performance_summary(
                criterion, sentiment, quotes_df, companies_represented
            )
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(
                supporting_quotes, companies_represented, analysis
            )
            
            # Create theme object
            theme = {
                'client_id': client_id,
                'theme_title': theme_title,
                'scorecard_criterion': criterion,
                'sentiment_direction': sentiment,
                'client_performance_summary': performance_summary,
                'supporting_quotes': supporting_quotes,
                'quote_count': len(supporting_quotes),
                'companies_represented': len(companies_represented),
                'company_list': list(companies_represented),
                'evidence_strength': quality_metrics['evidence_strength'],
                'sentiment_consistency_score': quality_metrics['sentiment_consistency'],
                'quote_diversity_score': quality_metrics['quote_diversity'],
                'stakeholder_weight_score': quality_metrics['stakeholder_weight'],
                'overall_quality_score': quality_metrics['overall_quality'],
                'strategic_note': self._generate_strategic_note(criterion, sentiment, analysis),
                'competitive_positioning': self._generate_competitive_positioning(criterion, sentiment),
                'created_at': pd.Timestamp.now().isoformat()
            }
            
            return theme
            
        except Exception as e:
            logger.error(f"Error generating theme for {criterion}-{sentiment}: {e}")
            return None
    
    def _generate_theme_title(self, criterion: str, sentiment: str, company_count: int) -> str:
        """Generate theme title"""
        criterion_map = {
            'commercial': 'Pricing and Commercial Terms',
            'implementation': 'Implementation and Onboarding',
            'product': 'Product Capabilities',
            'sales': 'Sales Experience and Partnership',
            'support': 'Support and Service Quality',
            'speed': 'Speed and Responsiveness',
            'security': 'Security and Compliance',
            'market': 'Market Position and Reputation',
            'integration': 'Integration and Technical Fit',
            'vendor': 'Vendor Stability'
        }
        
        sentiment_map = {
            'positive': 'Positive',
            'negative': 'Challenges with',
            'neutral': 'Mixed Performance in',
            'terms_positive': 'Positive Pricing Structure',
            'terms_neutral': 'Pricing Transparency',
            'onboarding_positive': 'Streamlined Onboarding',
            'onboarding_neutral': 'Implementation Complexity',
            'capability_positive': 'Superior Capabilities',
            'capability_neutral': 'Capability Enhancement Needs',
            'experience_partnership_positive': 'Strong Partnership Experience',
            'experience_partnership_neutral': 'Partnership Opportunities',
            'service_quality_positive': 'High Service Quality',
            'service_quality_neutral': 'Service Quality Enhancement',
            'responsiveness_positive': 'Excellent Responsiveness',
            'responsiveness_neutral': 'Responsiveness Opportunities',
            'compliance_positive': 'Strong Compliance',
            'compliance_neutral': 'Compliance Enhancement',
            'position_reputation_positive': 'Strong Market Position',
            'position_reputation_neutral': 'Market Position Development',
            'technical_fit_positive': 'Excellent Technical Fit',
            'technical_fit_neutral': 'Technical Integration Needs',
            'stability_positive': 'Vendor Stability',
            'stability_neutral': 'Vendor Stability Considerations'
        }
        
        criterion_name = criterion_map.get(criterion, criterion.title())
        sentiment_desc = sentiment_map.get(sentiment, sentiment.replace('_', ' ').title())
        
        return f"{sentiment_desc} in {criterion_name} ({company_count} companies)"
    
    def _generate_performance_summary(self, criterion: str, sentiment: str, 
                                    quotes_df: pd.DataFrame, companies: set) -> str:
        """Generate performance summary based on actual quote content"""
        # Get sample quotes for context - we'll use the first few quote IDs to get actual text
        sample_quote_ids = quotes_df.head(3)['quote_id'].tolist()
        
        # Get the actual quote text from core_responses
        if sample_quote_ids:
            response = self.db.supabase.table('core_responses').select('verbatim_response').in_('response_id', sample_quote_ids).execute()
            sample_quotes = [resp['verbatim_response'] for resp in response.data]
        else:
            sample_quotes = []
        
        # Extract actual keywords from quotes
        keywords = []
        for quote_text in sample_quotes:
            text = quote_text.lower()
            if 'turnaround' in text or 'speed' in text or 'fast' in text or 'quick' in text:
                keywords.append('rapid turnaround')
            if 'price' in text or 'cost' in text or 'billing' in text or 'expensive' in text or 'cheap' in text:
                keywords.append('cost-effective')
            if 'accuracy' in text or 'precise' in text or 'correct' in text:
                keywords.append('high accuracy')
            if 'security' in text or 'compliance' in text or 'encryption' in text:
                keywords.append('secure & compliant')
            if 'support' in text or 'help' in text or 'assistance' in text:
                keywords.append('excellent support')
            if 'integration' in text or 'api' in text or 'connect' in text:
                keywords.append('seamless integration')
            if 'ease' in text or 'easy' in text or 'simple' in text:
                keywords.append('user-friendly')
        
        # Remove duplicates and limit to top 3
        keywords = list(set(keywords))[:3]
        
        summary = f"Analysis of {criterion.replace('_', ' ')} performance across {len(companies)} companies "
        summary += f"shows {sentiment.replace('_', ' ')} sentiment. "
        
        if keywords:
            summary += f"Key highlights include: {', '.join(keywords)}."
        else:
            summary += "Client feedback indicates consistent performance in this area."
        
        return summary
    
    def _calculate_quality_metrics(self, supporting_quotes: List[Dict], 
                                 companies: set, analysis: Dict) -> Dict:
        """Calculate quality metrics for the theme"""
        # Evidence strength (based on relevance scores)
        relevance_scores = [q.get('relevance_score', 0) for q in supporting_quotes]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        evidence_strength = min(avg_relevance / 5.0, 1.0)  # Normalize to 0-1
        
        # Sentiment consistency (all quotes have same sentiment)
        sentiments = [q.get('sentiment', 'neutral') for q in supporting_quotes]
        sentiment_consistency = 1.0 if len(set(sentiments)) == 1 else 0.5
        
        # Quote diversity (company representation)
        quote_diversity = len(companies) / len(supporting_quotes) if supporting_quotes else 0
        
        # Stakeholder weight (decision-maker perspectives)
        stakeholder_weight = min(len(companies) / 10.0, 1.0)  # Normalize to 0-1
        
        # Overall quality (weighted average)
        overall_quality = (
            evidence_strength * 0.4 +
            sentiment_consistency * 0.3 +
            quote_diversity * 0.2 +
            stakeholder_weight * 0.1
        )
        
        return {
            'evidence_strength': round(evidence_strength, 3),
            'sentiment_consistency': round(sentiment_consistency, 3),
            'quote_diversity': round(quote_diversity, 3),
            'stakeholder_weight': round(stakeholder_weight, 3),
            'overall_quality': round(overall_quality, 3)
        }
    
    def _generate_strategic_note(self, criterion: str, sentiment: str, analysis: Dict) -> str:
        """Generate strategic note"""
        priority_score = analysis.get('priority_score', 0)
        
        if priority_score >= 0.7:
            return f"High-priority criterion ({priority_score:.2f}) requiring immediate attention"
        elif priority_score >= 0.5:
            return f"Medium-priority criterion ({priority_score:.2f}) with strategic importance"
        else:
            return f"Standard priority criterion ({priority_score:.2f}) for monitoring"
    
    def _generate_competitive_positioning(self, criterion: str, sentiment: str) -> str:
        """Generate competitive positioning note"""
        if 'positive' in sentiment:
            return "Competitive strength that differentiates from alternatives"
        elif 'neutral' in sentiment:
            return "Competitive parity with opportunities for differentiation"
        else:
            return "Competitive gap requiring strategic investment"
    
    def save_scorecard_themes(self, themes: List[Dict], client_id: str = 'default') -> bool:
        """Save scorecard themes to database"""
        logger.info(f"💾 Saving {len(themes)} scorecard themes to database...")
        
        try:
            if not themes:
                logger.info("No themes to save")
                return True
            
            # Define the fields that exist in the scorecard_themes table
            valid_fields = [
                'client_id', 'theme_title', 'scorecard_criterion', 'sentiment_direction',
                'client_performance_summary', 'supporting_quotes', 'quote_count',
                'companies_represented', 'company_list', 'evidence_strength',
                'sentiment_consistency_score', 'quote_diversity_score', 'stakeholder_weight_score',
                'overall_quality_score', 'strategic_note', 'competitive_positioning', 'created_at'
            ]
            
            # Required fields that must have values
            required_fields = [
                'client_id', 'theme_title', 'scorecard_criterion', 'sentiment_direction',
                'client_performance_summary'
            ]
            
            # Insert themes in batches
            batch_size = 10
            for i in range(0, len(themes), batch_size):
                batch = themes[i:i + batch_size]
                
                # Filter and prepare themes for database
                db_themes = []
                for theme in batch:
                    # Filter to only include valid fields
                    db_theme = {k: v for k, v in theme.items() if k in valid_fields}
                    
                    # Add client_id if not present
                    if 'client_id' not in db_theme:
                        db_theme['client_id'] = client_id
                    
                    # Ensure required fields have values
                    for field in required_fields:
                        if field not in db_theme or db_theme[field] is None:
                            if field == 'client_performance_summary':
                                # Generate a default performance summary
                                db_theme[field] = f"Analysis of {db_theme.get('scorecard_criterion', 'criterion')} performance across {db_theme.get('companies_represented', 0)} companies shows {db_theme.get('sentiment_direction', 'mixed')} sentiment."
                            elif field == 'theme_title':
                                db_theme[field] = f"{db_theme.get('scorecard_criterion', 'Criterion').title()} Analysis"
                            elif field == 'scorecard_criterion':
                                db_theme[field] = 'general'
                            elif field == 'sentiment_direction':
                                db_theme[field] = 'neutral'
                    
                    # Convert supporting_quotes to JSON string if it's a list
                    if 'supporting_quotes' in db_theme and isinstance(db_theme['supporting_quotes'], list):
                        db_theme['supporting_quotes'] = json.dumps(db_theme['supporting_quotes'])
                    
                    # Convert company_list to JSON string if it's a list
                    if 'company_list' in db_theme and isinstance(db_theme['company_list'], list):
                        db_theme['company_list'] = json.dumps(db_theme['company_list'])
                    
                    db_themes.append(db_theme)
                
                response = self.db.supabase.table('scorecard_themes').insert(db_themes).execute()
                
                if not response.data:
                    logger.error(f"Failed to save batch {i//batch_size + 1}")
                    return False
            
            logger.info("✅ Scorecard themes saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scorecard themes: {e}")
            self.processing_metrics["processing_errors"] += 1
            return False
    
    def process_scorecard_themes(self, client_id: str = 'default') -> Dict:
        """Main processing function for Stage 4B"""
        logger.info("🚀 STAGE 4B: SCORECARD-DRIVEN THEME DEVELOPMENT")
        logger.info("=" * 60)
        
        # Analyze criteria prioritization
        criteria_prioritization = self.analyze_criteria_prioritization(client_id)
        
        if not criteria_prioritization:
            logger.info("✅ No criteria data available for analysis")
            return {"status": "no_criteria_data", "message": "No criteria data available"}
        
        # Generate scorecard themes
        themes = self.generate_scorecard_themes(criteria_prioritization, client_id)
        
        if not themes:
            logger.info("✅ No scorecard themes generated")
            return {"status": "no_themes", "message": "No themes generated"}
        
        # Apply semantic merging and enrichment
        enriched_themes = self.apply_semantic_merging(themes, similarity_threshold=0.3)
        
        # Save themes to database
        save_success = self.save_scorecard_themes(enriched_themes, client_id)
        
        if not save_success:
            logger.error("❌ Failed to save themes to database")
            return {"status": "save_error", "message": "Failed to save themes"}
        
        # Generate summary statistics
        summary = self.generate_summary_statistics(criteria_prioritization, enriched_themes)
        
        logger.info(f"\n✅ Stage 4B complete! Generated {len(enriched_themes)} enriched scorecard themes")
        self.print_summary_report(summary)
        
        # After saving themes, update embeddings
        self.update_scorecard_theme_embeddings(client_id)
        return {
            "status": "success",
            "criteria_analyzed": len(criteria_prioritization),
            "prioritized_criteria": self.processing_metrics["prioritized_criteria_found"],
            "scorecard_themes_generated": len(themes),
            "enriched_themes_final": len(enriched_themes),
            "high_quality_themes": self.processing_metrics["high_quality_themes"],
            "themes_before_merging": self.processing_metrics["themes_before_merging"],
            "themes_after_merging": self.processing_metrics["themes_after_merging"],
            "merged_groups": self.processing_metrics["merged_groups"],
            "criteria_prioritization": criteria_prioritization,
            "scorecard_themes": enriched_themes,
            "summary": summary,
            "processing_metrics": self.processing_metrics
        }
    
    def generate_summary_statistics(self, criteria_prioritization: Dict, themes: List[Dict]) -> Dict:
        """Generate summary statistics"""
        
        # Criteria prioritization stats
        total_criteria = len(criteria_prioritization)
        prioritized_criteria = sum(1 for c in criteria_prioritization.values() 
                                 if c.get('meets_prioritization_thresholds', False))
        prioritization_ratio = prioritized_criteria / total_criteria if total_criteria > 0 else 0
        
        # Theme generation stats
        total_themes = len(themes)
        high_quality_themes = sum(1 for t in themes if t.get('overall_quality_score', 0) >= 0.7)
        quality_ratio = high_quality_themes / total_themes if total_themes > 0 else 0
        
        # Sentiment distribution
        sentiment_counts = Counter(t['sentiment_direction'] for t in themes)
        
        # Criteria coverage
        criteria_counts = Counter(t['scorecard_criterion'] for t in themes)
        
        return {
            'criteria_prioritization': {
                'total_criteria_analyzed': total_criteria,
                'prioritized_criteria': prioritized_criteria,
                'prioritization_ratio': round(prioritization_ratio, 3)
            },
            'theme_generation': {
                'total_themes_generated': total_themes,
                'high_quality_themes': high_quality_themes,
                'quality_ratio': round(quality_ratio, 3)
            },
            'sentiment_distribution': dict(sentiment_counts),
            'criteria_coverage': dict(criteria_counts),
            'processing_metrics': self.processing_metrics
        }
    
    def print_summary_report(self, summary: Dict):
        """Print summary report"""
        logger.info("\n📊 STAGE 4B SUMMARY REPORT")
        logger.info("=" * 40)
        
        # Criteria prioritization
        criteria_stats = summary.get('criteria_prioritization', {})
        logger.info(f"Criteria Analyzed: {criteria_stats.get('total_criteria_analyzed', 0)}")
        logger.info(f"Prioritized Criteria: {criteria_stats.get('prioritized_criteria', 0)}")
        logger.info(f"Prioritization Ratio: {criteria_stats.get('prioritization_ratio', 0):.1%}")
        
        # Theme generation
        theme_stats = summary.get('theme_generation', {})
        logger.info(f"Themes Generated: {theme_stats.get('total_themes_generated', 0)}")
        logger.info(f"Enriched Themes (Final): {self.processing_metrics.get('themes_after_merging', 0)}")
        logger.info(f"High Quality Themes: {theme_stats.get('high_quality_themes', 0)}")
        logger.info(f"Quality Ratio: {theme_stats.get('quality_ratio', 0):.1%}")
        
        # Semantic merging stats
        if self.processing_metrics.get('merged_groups', 0) > 0:
            logger.info(f"\nSemantic Merging:")
            logger.info(f"  Themes Before Merging: {self.processing_metrics.get('themes_before_merging', 0)}")
            logger.info(f"  Themes After Merging: {self.processing_metrics.get('themes_after_merging', 0)}")
            logger.info(f"  Merged Groups: {self.processing_metrics.get('merged_groups', 0)}")
            reduction = ((self.processing_metrics.get('themes_before_merging', 0) - self.processing_metrics.get('themes_after_merging', 0)) / self.processing_metrics.get('themes_before_merging', 1)) * 100
            logger.info(f"  Reduction: {reduction:.1f}%")
        
        # Sentiment distribution
        sentiment_dist = summary.get('sentiment_distribution', {})
        if sentiment_dist:
            logger.info("\nSentiment Distribution:")
            for sentiment, count in sentiment_dist.items():
                logger.info(f"  {sentiment}: {count}")
        
        # Criteria coverage
        criteria_coverage = summary.get('criteria_coverage', {})
        if criteria_coverage:
            logger.info("\nCriteria Coverage:")
            for criterion, count in criteria_coverage.items():
                logger.info(f"  {criterion}: {count} themes")
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison by removing common words and punctuation"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = text.split()
        words = [word for word in words if word not in common_words and len(word) > 2]
        
        return ' '.join(words)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using word overlap"""
        norm1 = set(self.normalize_text(text1).split())
        norm2 = set(self.normalize_text(text2).split())
        
        if not norm1 or not norm2:
            return 0.0
        
        intersection = norm1.intersection(norm2)
        union = norm1.union(norm2)
        
        return len(intersection) / len(union)
    
    def find_similar_theme_groups(self, themes: List[Dict], similarity_threshold: float = 0.3) -> List[List[int]]:
        """Find groups of similar themes based on title similarity"""
        similar_groups = []
        processed = set()
        
        for i, theme1 in enumerate(themes):
            if i in processed:
                continue
                
            group = [i]
            processed.add(i)
            
            for j, theme2 in enumerate(themes):
                if j in processed:
                    continue
                    
                similarity = self.calculate_similarity(theme1['theme_title'], theme2['theme_title'])
                
                if similarity >= similarity_threshold:
                    group.append(j)
                    processed.add(j)
            
            if len(group) > 1:  # Only add groups with multiple themes
                similar_groups.append(group)
        
        return similar_groups
    
    def find_similar_theme_groups_vector(self, themes: List[Dict], embeddings: List[List[float]], 
                                       similarity_threshold: float = 0.3) -> List[List[int]]:
        """Find groups of similar themes using vector embeddings"""
        import numpy as np
        
        groups = []
        used_indices = set()
        
        for i in range(len(themes)):
            if i in used_indices or embeddings[i] is None:
                continue
                
            # Start a new group
            current_group = [i]
            used_indices.add(i)
            
            # Find similar themes using vector similarity
            for j in range(i + 1, len(themes)):
                if j in used_indices or embeddings[j] is None:
                    continue
                    
                # Calculate cosine similarity
                vec1 = np.array(embeddings[i])
                vec2 = np.array(embeddings[j])
                
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    continue
                    
                similarity = dot_product / (norm1 * norm2)
                
                if similarity >= similarity_threshold:
                    current_group.append(j)
                    used_indices.add(j)
            
            # Only add groups with multiple themes
            if len(current_group) > 1:
                groups.append(current_group)
        
        return groups
    
    def merge_theme_group(self, themes: List[Dict], group_indices: List[int]) -> Dict:
        """Merge a group of similar themes into one enriched theme"""
        group_themes = [themes[i] for i in group_indices]
        
        # Get the theme with highest quality score as the base
        base_theme = max(group_themes, key=lambda x: x.get('overall_quality_score', 0))
        
        # Create enriched title
        titles = [theme['theme_title'] for theme in group_themes]
        enriched_title = self._create_enriched_title(titles, base_theme['scorecard_criterion'])
        
        # Aggregate data
        all_companies = set()
        total_quotes = 0
        quality_scores = []
        sentiments = set()
        all_supporting_quotes = []
        
        for theme in group_themes:
            # Companies (union from company_list)
            if theme.get('company_list'):
                if isinstance(theme['company_list'], str):
                    try:
                        companies = json.loads(theme['company_list'])
                        all_companies.update(companies)
                    except:
                        pass
                else:
                    all_companies.update(theme['company_list'])
            
            # Quotes (sum)
            if pd.notna(theme.get('quote_count')):
                total_quotes += theme['quote_count']
            
            # Quality scores (for averaging)
            if pd.notna(theme.get('overall_quality_score')):
                quality_scores.append(theme['overall_quality_score'])
            
            # Sentiments (for tracking)
            if pd.notna(theme.get('sentiment_direction')):
                sentiments.add(theme['sentiment_direction'])
            
            # Supporting quotes (combine)
            if theme.get('supporting_quotes'):
                if isinstance(theme['supporting_quotes'], str):
                    try:
                        quotes = json.loads(theme['supporting_quotes'])
                        all_supporting_quotes.extend(quotes)
                    except:
                        pass
                else:
                    all_supporting_quotes.extend(theme['supporting_quotes'])
        
        # Calculate aggregated values
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else base_theme.get('overall_quality_score', 0)
        
        # Determine sentiment
        if len(sentiments) > 1:
            final_sentiment = 'mixed'
        else:
            final_sentiment = list(sentiments)[0] if sentiments else base_theme.get('sentiment_direction', 'neutral')
        
        # Create description
        description = self._create_enriched_description(titles, sentiments, base_theme['scorecard_criterion'])
        
        # Create merged theme
        merged_theme = {
            'theme_title': enriched_title,
            'scorecard_criterion': base_theme['scorecard_criterion'],
            'sentiment_direction': final_sentiment,
            'companies_represented': len(all_companies),
            'quote_count': total_quotes,
            'overall_quality_score': avg_quality,
            'description': description,
            'supporting_quotes': all_supporting_quotes,
            'merged_from': titles,  # Track original themes
            'original_theme_ids': group_indices  # Track original IDs
        }
        
        return merged_theme
    
    def _create_enriched_title(self, titles: List[str], criterion: str) -> str:
        """Create an enriched title from multiple similar themes"""
        # Extract key concepts from titles
        concepts = set()
        for title in titles:
            # Extract key words (capitalized words, important terms)
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', title)
            concepts.update(words)
        
        # Remove common words
        common_concepts = {'Rev', 'Legal', 'Services', 'The', 'A', 'An', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'As', 'Is', 'Are', 'Was', 'Were', 'Be', 'Been', 'Being', 'Have', 'Has', 'Had', 'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should', 'May', 'Might', 'Can', 'This', 'That', 'These', 'Those', 'I', 'You', 'He', 'She', 'It', 'We', 'They', 'Me', 'Him', 'Her', 'Us', 'Them'}
        concepts = concepts - common_concepts
        
        # Create enriched title
        if concepts:
            key_concepts = list(concepts)[:3]  # Take top 3 concepts
            enriched_title = f"{' '.join(key_concepts)}: {criterion.title()} Excellence"
        else:
            enriched_title = f"{criterion.title()} Excellence and Performance"
        
        return enriched_title
    
    def _create_enriched_description(self, titles: List[str], sentiments: set, criterion: str) -> str:
        """Create an enriched description from multiple similar themes"""
        if len(sentiments) > 1:
            sentiment_desc = f"Mixed sentiment across {criterion} themes"
        else:
            sentiment_desc = f"Consistent {list(sentiments)[0]} sentiment"
        
        description = f"Combined insights from {len(titles)} related themes. {sentiment_desc}. "
        description += f"Key areas include: {', '.join(titles[:3])}"
        
        if len(titles) > 3:
            description += f" and {len(titles) - 3} additional related themes."
        
        return description
    
    def apply_semantic_merging(self, themes: List[Dict], similarity_threshold: float = 0.3) -> List[Dict]:
        """Apply semantic merging using vector embeddings to reduce duplicate themes"""
        logger.info("🔗 Applying vector-based semantic theme merging and enrichment...")
        
        initial_count = len(themes)
        self.processing_metrics["themes_before_merging"] = initial_count
        
        if initial_count <= 1:
            return themes
        
        # Get embeddings for all themes
        theme_embeddings = []
        for theme in themes:
            # Combine title and summary for embedding
            text = f"{theme.get('theme_title', '')} {theme.get('client_performance_summary', '')}"
            if text.strip():
                embedding = self.get_openai_embedding(text)
                theme_embeddings.append(embedding)
            else:
                theme_embeddings.append(None)
        
        # Find similar theme groups using vector similarity
        similar_groups = self.find_similar_theme_groups_vector(themes, theme_embeddings, similarity_threshold)
        
        if not similar_groups:
            logger.info("No similar theme groups found. All themes are unique.")
            self.processing_metrics["themes_after_merging"] = initial_count
            return themes
        
        logger.info(f"Found {len(similar_groups)} groups of similar themes using vector similarity")
        self.processing_metrics["merged_groups"] = len(similar_groups)
        
        # Merge each group
        merged_themes = []
        processed_indices = set()
        
        for group in similar_groups:
            merged_theme = self.merge_theme_group(themes, group)
            merged_themes.append(merged_theme)
            processed_indices.update(group)
            logger.info(f"Merged group: {merged_theme['theme_title']}")
        
        # Add themes that weren't in any group (unique themes)
        for i, theme in enumerate(themes):
            if i not in processed_indices:
                # Add description to standalone themes
                theme['description'] = f"Standalone theme: {theme['theme_title']}"
                theme['merged_from'] = [theme['theme_title']]
                theme['original_theme_ids'] = [i]
                merged_themes.append(theme)
                logger.info(f"Kept unique theme: {theme['theme_title']}")
        
        final_count = len(merged_themes)
        self.processing_metrics["themes_after_merging"] = final_count
        
        logger.info(f"Themes before semantic merging: {initial_count}")
        logger.info(f"Themes after semantic merging: {final_count}")
        logger.info(f"Reduction: {((initial_count - final_count) / initial_count * 100):.1f}%")
        
        return merged_themes

    def get_openai_embedding(self, text: str) -> list:
        """Get OpenAI embedding for a given text"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    def update_core_response_embeddings(self, client_id: str = 'default'):
        """Generate and store embeddings for all core_responses for this client"""
        response = self.db.supabase.table('core_responses').select('response_id,verbatim_response,embedding').eq('client_id', client_id).execute()
        for row in response.data:
            if row.get('embedding') is not None:
                continue  # Skip if already embedded
            text = row['verbatim_response']
            if not text:
                continue
            embedding = self.get_openai_embedding(text)
            self.db.supabase.table('core_responses').update({'embedding': embedding}).eq('response_id', row['response_id']).execute()

    def update_scorecard_theme_embeddings(self, client_id: str = 'default'):
        """Generate and store embeddings for all scorecard themes for this client"""
        response = self.db.supabase.table('scorecard_themes').select('id,client_performance_summary,embedding').eq('client_id', client_id).execute()
        for row in response.data:
            if row.get('embedding') is not None:
                continue  # Skip if already embedded
            text = row['client_performance_summary']
            if not text:
                continue
            embedding = self.get_openai_embedding(text)
            self.db.supabase.table('scorecard_themes').update({'embedding': embedding}).eq('id', row['id']).execute()


def run_stage4b_analysis(client_id: str = 'default'):
    """Run Stage 4B scorecard theme analysis"""
    analyzer = Stage4BScorecardAnalyzer()
    return analyzer.process_scorecard_themes(client_id=client_id)


if __name__ == "__main__":
    # Test the analyzer
    result = run_stage4b_analysis('Rev')
    print(json.dumps(result, indent=2)) 