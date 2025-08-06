#!/usr/bin/env python3
"""
Enhanced Subject-Driven Stage 2 Analyzer
Uses Stage 1 subjects to route responses to appropriate business criteria with quality weighting.
"""

import yaml
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import os
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from supabase_database import SupabaseDatabase

logger = logging.getLogger(__name__)

class SubjectDrivenStage2Analyzer:
    """Enhanced Stage 2 analyzer with subject-driven criteria routing and quality weighting"""
    
    def __init__(self, config_path: str = "config/subject_criteria_mapping.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.db = SupabaseDatabase()
        
        # Extract mapping configurations
        self.subject_to_criteria = self.config.get('subject_to_criteria_mapping', {})
        self.quality_weights = self.config.get('subject_quality_weights', {})
        self.analysis_config = self.config.get('analysis_config', {})
        
        logger.info(f"🎯 Loaded subject-driven analyzer with {len(self.subject_to_criteria)} subject mappings")
    
    def _load_config(self) -> Dict:
        """Load subject-criteria mapping configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"❌ Config file not found: {self.config_path}")
                return {}
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}
    
    def get_criterion_from_subject(self, subject: str) -> str:
        """Map Stage 1 subject to business criterion"""
        criterion = self.subject_to_criteria.get(subject)
        
        if criterion:
            logger.info(f"🎯 Mapped '{subject}' → '{criterion}'")
            return criterion
        else:
            default = self.analysis_config.get('default_criterion', 'product_capability')
            logger.warning(f"⚠️ No mapping for '{subject}', using default: '{default}'")
            return default
    
    def get_quality_weight(self, subject: str) -> float:
        """Get quality weight for subject"""
        weight = self.quality_weights.get(subject, 0.8)  # Default to 0.8
        logger.debug(f"📊 Quality weight for '{subject}': {weight}")
        return weight
    
    def should_flag_multi_criteria(self, verbatim_response: str) -> bool:
        """Check if response should be flagged for potential multi-criteria analysis"""
        if not self.analysis_config.get('flag_multi_criteria_candidates', False):
            return False
        
        indicators = self.analysis_config.get('multi_criteria_indicators', [])
        response_lower = verbatim_response.lower()
        
        for indicator in indicators:
            if indicator in response_lower:
                logger.info(f"🔍 Multi-criteria candidate detected: '{indicator}' in response")
                return True
        
        return False
    
    def analyze_response(self, response_data: Dict) -> Dict:
        """Analyze a single response with subject-driven routing"""
        try:
            # Extract response details
            response_id = response_data.get('response_id', '')
            subject = response_data.get('subject', '')
            verbatim_response = response_data.get('verbatim_response', '')
            company = response_data.get('company', '')
            deal_status = response_data.get('deal_status', '')
            
            # Map subject to criterion
            criterion = self.get_criterion_from_subject(subject)
            
            # Get quality weight
            quality_weight = self.get_quality_weight(subject)
            
            # Check for multi-criteria potential
            multi_criteria_flag = self.should_flag_multi_criteria(verbatim_response)
            
            # Create enhanced analysis result
            analysis_result = {
                'quote_id': response_id,
                'original_subject': subject,
                'mapped_criterion': criterion,
                'quality_weight': quality_weight,
                'multi_criteria_candidate': multi_criteria_flag,
                'routing_confidence': self._calculate_routing_confidence(subject, verbatim_response),
                'analysis_metadata': {
                    'subject_mapping_used': True,
                    'quality_weighting_applied': self.analysis_config.get('apply_quality_weighting', True),
                    'mapping_timestamp': datetime.now().isoformat()
                }
            }
            
            # Perform criterion-specific analysis
            criterion_analysis = self._analyze_for_criterion(
                verbatim_response, criterion, company, deal_status, quality_weight
            )
            
            # Merge results
            analysis_result.update(criterion_analysis)
            
            logger.info(f"✅ Analyzed response {response_id}: {subject} → {criterion}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze response {response_data.get('response_id', 'unknown')}: {e}")
            return {}
    
    def _calculate_routing_confidence(self, subject: str, verbatim_response: str) -> float:
        """Calculate confidence in subject-to-criterion routing"""
        # Base confidence from subject quality
        base_confidence = self.get_quality_weight(subject)
        
        # Adjust based on response length and specificity
        word_count = len(verbatim_response.split())
        length_factor = min(1.0, word_count / 50)  # Normalize to 50 words
        
        # Specific keywords boost confidence
        criterion = self.get_criterion_from_subject(subject)
        keyword_boost = self._check_criterion_keywords(verbatim_response, criterion)
        
        confidence = base_confidence * (0.7 + 0.2 * length_factor + 0.1 * keyword_boost)
        return min(1.0, confidence)
    
    def _check_criterion_keywords(self, text: str, criterion: str) -> float:
        """Check for criterion-specific keywords to boost routing confidence"""
        text_lower = text.lower()
        
        keyword_maps = {
            'product_capability': ['feature', 'capability', 'functionality', 'product'],
            'integration_technical_fit': ['integration', 'api', 'connect', 'technical', 'system'],
            'implementation_onboarding': ['setup', 'onboarding', 'implementation', 'training'],
            'commercial_terms': ['price', 'cost', 'budget', 'expensive', 'affordable'],
            'support_service_quality': ['support', 'service', 'help', 'assistance'],
            'security_compliance': ['security', 'compliance', 'privacy', 'gdpr'],
            'vendor_stability': ['reliable', 'stable', 'trust', 'confidence'],
            'sales_experience_partnership': ['sales', 'partnership', 'relationship'],
            'speed_responsiveness': ['fast', 'quick', 'speed', 'performance'],
            'market_position_reputation': ['competitor', 'market', 'reputation', 'leader']
        }
        
        keywords = keyword_maps.get(criterion, [])
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        return min(1.0, matches / len(keywords) if keywords else 0.0)
    
    def _analyze_for_criterion(self, verbatim_response: str, criterion: str, 
                              company: str, deal_status: str, quality_weight: float) -> Dict:
        """Perform criterion-specific analysis"""
        
        # This is a simplified analysis - in production, you'd call your existing
        # Stage 2 analysis logic here with criterion-specific prompts
        
        # Basic sentiment and relevance analysis
        sentiment = self._analyze_sentiment(verbatim_response, criterion)
        relevance_score = self._calculate_relevance_score(verbatim_response, criterion)
        
        # Apply quality weighting if enabled
        if self.analysis_config.get('apply_quality_weighting', True):
            weighted_score = relevance_score * quality_weight
        else:
            weighted_score = relevance_score
        
        # Deal outcome weighting
        deal_weighted_score = self._apply_deal_weighting(
            weighted_score, deal_status, sentiment
        )
        
        return {
            'criterion': criterion,
            'relevance_score': relevance_score,
            'sentiment': sentiment,
            'quality_weighted_score': weighted_score,
            'deal_weighted_score': deal_weighted_score,
            'confidence': 'high' if quality_weight >= 0.9 else 'medium' if quality_weight >= 0.8 else 'low',
            'priority': self._determine_priority(relevance_score, sentiment, deal_status),
            'relevance_explanation': f"Subject-driven analysis for {criterion}",
            'context_keywords': self._extract_keywords(verbatim_response, criterion)
        }
    
    def _analyze_sentiment(self, text: str, criterion: str) -> str:
        """Basic sentiment analysis (simplified)"""
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'love', 'easy', 'helpful', 'satisfied']
        negative_words = ['bad', 'terrible', 'difficult', 'problem', 'issue', 'expensive', 'slow']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_relevance_score(self, text: str, criterion: str) -> int:
        """Calculate relevance score (0-5) for criterion"""
        # Simplified scoring based on keyword presence and length
        keyword_score = self._check_criterion_keywords(text, criterion) * 3
        length_score = min(2, len(text.split()) / 25)
        
        total_score = keyword_score + length_score
        return min(5, max(1, round(total_score)))
    
    def _apply_deal_weighting(self, base_score: float, deal_status: str, sentiment: str) -> float:
        """Apply deal outcome weighting to scores"""
        if deal_status.lower() in ['closed lost', 'lost']:
            if sentiment == 'negative':
                return base_score * 1.2  # Amplify negative feedback from lost deals
            else:
                return base_score * 1.1  # Slightly amplify all lost deal feedback
        
        return base_score
    
    def _determine_priority(self, relevance_score: int, sentiment: str, deal_status: str) -> str:
        """Determine priority level for response"""
        if relevance_score >= 4 and sentiment == 'negative' and 'lost' in deal_status.lower():
            return 'high'
        elif relevance_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _extract_keywords(self, text: str, criterion: str) -> str:
        """Extract relevant keywords for the criterion"""
        # Simplified keyword extraction
        words = text.lower().split()
        criterion_keywords = {
            'product_capability': ['feature', 'capability', 'functionality'],
            'integration_technical_fit': ['integration', 'api', 'connect'],
            'commercial_terms': ['price', 'cost', 'budget'],
            # Add more as needed
        }.get(criterion, [])
        
        found_keywords = [word for word in words if word in criterion_keywords]
        return ', '.join(found_keywords[:5])  # Limit to 5 keywords
    
    def process_responses(self, client_id: str, max_responses: Optional[int] = None) -> Dict:
        """Process responses for a client using subject-driven routing"""
        try:
            logger.info(f"🚀 Starting subject-driven Stage 2 analysis for client: {client_id}")
            
            # Get unanalyzed responses
            responses_df = self.db.get_unanalyzed_quotes(client_id)
            
            if responses_df.empty:
                logger.info("📭 No unanalyzed responses found")
                return {"success": True, "processed": 0, "message": "No responses to analyze"}
            
            if max_responses:
                responses_df = responses_df.head(max_responses)
            
            logger.info(f"📊 Processing {len(responses_df)} responses with subject-driven routing")
            
            # Process each response
            processed_count = 0
            results = []
            
            for idx, row in responses_df.iterrows():
                try:
                    # Convert row to dict
                    response_data = row.to_dict()
                    
                    # Analyze with subject-driven routing
                    analysis_result = self.analyze_response(response_data)
                    
                    if analysis_result:
                        # Save to database
                        success = self._save_analysis_result(analysis_result, client_id)
                        
                        if success:
                            processed_count += 1
                            results.append(analysis_result)
                        
                except Exception as e:
                    logger.error(f"❌ Failed to process response {row.get('response_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Completed subject-driven analysis: {processed_count} responses processed")
            
            return {
                "success": True,
                "processed": processed_count,
                "total_found": len(responses_df),
                "results": results,
                "mapping_stats": self._get_mapping_stats(results)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process responses: {e}")
            return {"success": False, "error": str(e)}
    
    def _save_analysis_result(self, analysis_result: Dict, client_id: str) -> bool:
        """Save analysis result to database"""
        try:
            # Prepare data for stage2_response_labeling table
            labeling_data = {
                'quote_id': analysis_result.get('quote_id'),
                'criterion': analysis_result.get('criterion'),
                'score': analysis_result.get('relevance_score'),  # Map to expected field name
                'sentiment': analysis_result.get('sentiment'),
                'priority': analysis_result.get('priority'),
                'confidence': analysis_result.get('confidence'),
                'relevance_explanation': analysis_result.get('relevance_explanation'),
                'deal_weighted_score': analysis_result.get('deal_weighted_score'),
                'context_keywords': analysis_result.get('context_keywords'),
                'client_id': client_id
            }
            
            # Save to database using existing method
            success = self.db.save_stage2_response_labeling(labeling_data)
            
            if success:
                logger.debug(f"💾 Saved analysis for {analysis_result.get('quote_id')}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to save analysis result: {e}")
            return False
    
    def _get_mapping_stats(self, results: List[Dict]) -> Dict:
        """Get statistics on subject-to-criteria mapping"""
        if not results:
            return {}
        
        criterion_counts = {}
        quality_weights = []
        confidence_scores = []
        
        for result in results:
            criterion = result.get('criterion', 'unknown')
            criterion_counts[criterion] = criterion_counts.get(criterion, 0) + 1
            
            quality_weights.append(result.get('quality_weight', 0))
            confidence_scores.append(result.get('routing_confidence', 0))
        
        return {
            'criterion_distribution': criterion_counts,
            'avg_quality_weight': sum(quality_weights) / len(quality_weights),
            'avg_routing_confidence': sum(confidence_scores) / len(confidence_scores),
            'high_confidence_responses': sum(1 for conf in confidence_scores if conf >= 0.9)
        }

def main():
    """Command line interface for subject-driven Stage 2 analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run subject-driven Stage 2 analysis')
    parser.add_argument('client_id', help='Client ID to process')
    parser.add_argument('--max-responses', type=int, help='Maximum responses to process')
    parser.add_argument('--config', default='config/subject_criteria_mapping.yaml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Initialize analyzer
    analyzer = SubjectDrivenStage2Analyzer(config_path=args.config)
    
    # Process responses
    result = analyzer.process_responses(args.client_id, args.max_responses)
    
    # Print results
    if result.get('success'):
        print(f"\n✅ Subject-driven analysis completed!")
        print(f"📊 Processed: {result['processed']}")
        print(f"📊 Total found: {result['total_found']}")
        
        mapping_stats = result.get('mapping_stats', {})
        if mapping_stats:
            print(f"\n📈 Mapping Statistics:")
            print(f"  Average quality weight: {mapping_stats.get('avg_quality_weight', 0):.2f}")
            print(f"  Average routing confidence: {mapping_stats.get('avg_routing_confidence', 0):.2f}")
            print(f"  High confidence responses: {mapping_stats.get('high_confidence_responses', 0)}")
            
            print(f"\n🎯 Criterion Distribution:")
            for criterion, count in mapping_stats.get('criterion_distribution', {}).items():
                print(f"  {criterion}: {count}")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 