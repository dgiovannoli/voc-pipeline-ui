#!/usr/bin/env python3
"""
Enhanced Stage 2 Processor - Single Table Approach
Adds sentiment and impact analysis directly to stage1_data_responses table
Focus: Harmonized subject + sentiment + impact (simplified from multi-criteria)
"""

import sys
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Progress tracking for UI
stage2_progress_data = {"completed_responses": 0, "total_responses": 0, "results": [], "errors": []}
stage2_progress_lock = threading.Lock()

class EnhancedSingleTableStage2:
    """Enhanced Stage 2 processor for single table approach"""
    
    def __init__(self, batch_size: int = 30, max_workers: int = 3):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Initialize database
        try:
            self.db = SupabaseDatabase()
            logger.info("✅ Enhanced Single Table Stage 2 initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Stage 2 processor: {e}")
            raise
        
        # Track processing stats
        self.processing_stats = {
            'total_processed': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0},
            'impact_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'harmonized_subjects_analyzed': set()
        }
    
    def process_incremental(self, client_id: str = "default") -> Dict:
        """Process unanalyzed responses for Stage 2 with progress tracking"""
        
        logger.info(f"🎯 Starting enhanced Stage 2 analysis for client: {client_id}")
        
        try:
            # Get unanalyzed responses (those with harmonized subjects but no Stage 2 analysis)
            unanalyzed_data = self._get_unanalyzed_responses(client_id)
            
            if not unanalyzed_data:
                logger.info("📋 No unanalyzed responses found")
                return self._create_summary_result()
            
            logger.info(f"📊 Found {len(unanalyzed_data)} responses ready for Stage 2 analysis")
            
            # Update progress tracking
            with stage2_progress_lock:
                stage2_progress_data['total_responses'] = len(unanalyzed_data)
                stage2_progress_data['completed_responses'] = 0
                stage2_progress_data['results'] = []
                stage2_progress_data['errors'] = []
            
            # Process in batches
            results = self._process_batches(unanalyzed_data, client_id)
            
            # Generate summary
            summary = self._create_summary_result()
            logger.info(f"✅ Enhanced Stage 2 analysis complete: {summary['successful_analyses']}/{summary['total_processed']} successful")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Enhanced Stage 2 analysis failed: {e}")
            raise
    
    def _get_unanalyzed_responses(self, client_id: str) -> List[Dict]:
        """Get responses that have harmonized subjects but no Stage 2 analysis"""
        try:
            # Query for responses with harmonized subjects but no Stage 2 analysis
            query = self.db.supabase.table('stage1_data_responses').select('*')
            
            if client_id != "all":
                query = query.eq('client_id', client_id)
            
            # Must have harmonized subject and not yet analyzed in Stage 2
            query = query.not_.is_('harmonized_subject', 'null').eq('stage2_completed', False)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            # Convert to list of dicts
            data_list = []
            for row in result.data:
                data_list.append({
                    'response_id': row.get('response_id'),
                    'verbatim_response': row.get('verbatim_response', ''),
                    'harmonized_subject': row.get('harmonized_subject'),
                    'subject': row.get('subject', ''),
                    'question': row.get('question', ''),
                    'company': row.get('company', ''),
                    'deal_status': row.get('deal_status', ''),
                    'client_id': row.get('client_id', client_id)
                })
            
            logger.info(f"📋 Prepared {len(data_list)} responses for Stage 2 analysis")
            return data_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get unanalyzed responses: {e}")
            return []
    
    def _process_batches(self, data_list: List[Dict], client_id: str) -> List[Dict]:
        """Process Stage 2 analysis in parallel batches"""
        all_results = []
        batches = [data_list[i:i + self.batch_size] for i in range(0, len(data_list), self.batch_size)]
        
        logger.info(f"🔄 Processing {len(batches)} batches with {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch jobs
            future_to_batch = {
                executor.submit(self._process_batch, batch_num, batch, client_id): batch_num 
                for batch_num, batch in enumerate(batches, 1)
            }
            
            # Collect results
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    # Update progress
                    with stage2_progress_lock:
                        stage2_progress_data['completed_responses'] += len(batch_results)
                        successful = sum(1 for r in batch_results if r.get('stage2_success', False))
                        stage2_progress_data['results'].extend(batch_results)
                    
                    logger.info(f"✅ Batch {batch_num}/{len(batches)} complete ({len(batch_results)} responses)")
                    
                except Exception as e:
                    logger.error(f"❌ Batch {batch_num} failed: {e}")
                    with stage2_progress_lock:
                        stage2_progress_data['errors'].append(f"Batch {batch_num}: {str(e)}")
        
        return all_results
    
    def _process_batch(self, batch_num: int, batch_data: List[Dict], client_id: str) -> List[Dict]:
        """Process a single batch of responses for Stage 2 analysis"""
        batch_results = []
        
        for item in batch_data:
            try:
                # Analyze sentiment and impact for this harmonized subject
                analysis_result = self._analyze_sentiment_and_impact(item)
                
                # Update database with Stage 2 analysis
                success = self._update_stage2_analysis(item['response_id'], analysis_result)
                
                # Track results
                result_item = item.copy()
                result_item.update(analysis_result)
                result_item['stage2_success'] = success
                batch_results.append(result_item)
                
                # Update processing stats
                self._update_processing_stats(analysis_result, success)
                
                if success:
                    logger.debug(f"✅ Analyzed '{item['response_id']}': {analysis_result.get('sentiment')} sentiment, impact {analysis_result.get('impact_score')}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process item {item.get('response_id', 'unknown')}: {e}")
                # Add failed result
                result_item = item.copy()
                result_item.update({
                    'sentiment': None,
                    'impact_score': None,
                    'stage2_explanation': f"Analysis failed: {str(e)}",
                    'stage2_confidence': 0.0,
                    'stage2_success': False
                })
                batch_results.append(result_item)
        
        return batch_results
    
    def _analyze_sentiment_and_impact(self, response_data: Dict) -> Dict:
        """Analyze sentiment and impact using LLM for a harmonized subject"""
        
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.0,
                max_tokens=200
            )
            
            # Build analysis prompt
            harmonized_subject = response_data.get('harmonized_subject', 'Unknown')
            verbatim_response = response_data.get('verbatim_response', '')
            deal_status = response_data.get('deal_status', 'Unknown')
            
            prompt_text = f"""Analyze this customer feedback for sentiment and decision impact.

CATEGORY: "{harmonized_subject}"
CUSTOMER SAID: "{verbatim_response[:400]}"
DEAL STATUS: "{deal_status}"

Provide:
1. SENTIMENT: positive, negative, neutral, or mixed
2. IMPACT SCORE (1-5): How much this influenced their buying decision
   - 5: Critical factor, deal maker/breaker
   - 4: High influence on decision
   - 3: Notable factor in decision  
   - 2: Minor consideration
   - 1: Passing comment, minimal impact

Respond with only this JSON:
{{"sentiment": "positive", "impact_score": 4, "reasoning": "brief explanation"}}"""

            response = llm.invoke(prompt_text)
            result_text = response.content.strip()
            
            # Parse JSON response
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_text = result_text[start:end]
                try:
                    llm_result = json.loads(json_text)
                except:
                    llm_result = self._parse_fallback_stage2(result_text, response_data)
            else:
                llm_result = self._parse_fallback_stage2(result_text, response_data)
            
            # Validate and standardize result
            return self._standardize_stage2_result(response_data, llm_result)
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed for '{response_data.get('response_id')}': {e}")
            return self._fallback_stage2_analysis(response_data)
    
    def _parse_fallback_stage2(self, text: str, response_data: Dict) -> Dict:
        """Fallback parsing when JSON fails"""
        sentiment = "neutral"
        impact_score = 3
        
        # Extract sentiment from text
        text_lower = text.lower()
        if any(word in text_lower for word in ["positive", "good", "great", "excellent"]):
            sentiment = "positive"
        elif any(word in text_lower for word in ["negative", "bad", "poor", "terrible"]):
            sentiment = "negative"
        elif "mixed" in text_lower:
            sentiment = "mixed"
        
        # Extract impact score from text
        for i in range(1, 6):
            if str(i) in text:
                impact_score = i
                break
        
        return {
            "sentiment": sentiment,
            "impact_score": impact_score,
            "reasoning": f"Fallback parsing from: {text[:50]}..."
        }
    
    def _fallback_stage2_analysis(self, response_data: Dict) -> Dict:
        """Rule-based fallback when LLM fails"""
        verbatim = response_data.get('verbatim_response', '').lower()
        deal_status = response_data.get('deal_status', '').lower()
        
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'perfect', 'satisfied']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'problems', 'issues', 'disappointed', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in verbatim)
        negative_count = sum(1 for word in negative_words if word in verbatim)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Simple impact scoring
        impact_score = 3  # Default medium
        
        # High impact indicators
        if any(phrase in verbatim for phrase in ['deal breaker', 'critical', 'essential', 'must have']):
            impact_score = 5
        elif any(phrase in verbatim for phrase in ['important', 'significant', 'major']):
            impact_score = 4
        elif any(phrase in verbatim for phrase in ['minor', 'small', 'slight']):
            impact_score = 2
        
        # Adjust based on deal status
        if 'won' in deal_status and sentiment == 'positive':
            impact_score = min(5, impact_score + 1)
        elif 'lost' in deal_status and sentiment == 'negative':
            impact_score = min(5, impact_score + 1)
        
        return {
            'sentiment': sentiment,
            'impact_score': impact_score,
            'stage2_explanation': f'Fallback analysis: {sentiment} sentiment, impact {impact_score}',
            'stage2_confidence': 0.6
        }
    
    def _standardize_stage2_result(self, response_data: Dict, llm_result: Dict) -> Dict:
        """Convert LLM result to standard Stage 2 format"""
        sentiment = llm_result.get('sentiment', 'neutral')
        impact_score = int(llm_result.get('impact_score', 3))
        reasoning = llm_result.get('reasoning', 'LLM analysis')
        
        # Validate sentiment
        valid_sentiments = ['positive', 'negative', 'neutral', 'mixed']
        if sentiment not in valid_sentiments:
            sentiment = 'neutral'
        
        # Validate impact score
        if impact_score < 1 or impact_score > 5:
            impact_score = 3
        
        return {
            'sentiment': sentiment,
            'impact_score': impact_score,
            'stage2_explanation': reasoning,
            'stage2_confidence': 0.8,  # High confidence for successful LLM analysis
            'stage2_analyzed_at': datetime.now().isoformat()
        }
    
    def _update_stage2_analysis(self, response_id: str, analysis_result: Dict) -> bool:
        """Update Stage 2 analysis in the stage1_data_responses table"""
        try:
            # Prepare update data
            update_data = {
                'sentiment': analysis_result.get('sentiment'),
                'impact_score': analysis_result.get('impact_score'),
                'stage2_explanation': analysis_result.get('stage2_explanation'),
                'stage2_confidence': analysis_result.get('stage2_confidence'),
                'stage2_analyzed_at': analysis_result.get('stage2_analyzed_at'),
                'stage2_completed': True
            }
            
            # Remove None values
            clean_data = {k: v for k, v in update_data.items() if v is not None}
            
            # Update in Supabase
            result = self.db.supabase.table('stage1_data_responses') \
                .update(clean_data) \
                .eq('response_id', response_id) \
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Database update failed for {response_id}: {e}")
            return False
    
    def _update_processing_stats(self, analysis_result: Dict, success: bool):
        """Update processing statistics"""
        self.processing_stats['total_processed'] += 1
        
        if success:
            self.processing_stats['successful_analyses'] += 1
            
            # Track sentiment distribution
            sentiment = analysis_result.get('sentiment')
            if sentiment in self.processing_stats['sentiment_distribution']:
                self.processing_stats['sentiment_distribution'][sentiment] += 1
            
            # Track impact distribution
            impact = analysis_result.get('impact_score')
            if impact in self.processing_stats['impact_distribution']:
                self.processing_stats['impact_distribution'][impact] += 1
        else:
            self.processing_stats['failed_analyses'] += 1
    
    def _create_summary_result(self) -> Dict:
        """Create Stage 2 processing summary"""
        return {
            'total_processed': self.processing_stats['total_processed'],
            'successful_analyses': self.processing_stats['successful_analyses'],
            'failed_analyses': self.processing_stats['failed_analyses'],
            'success_rate': (self.processing_stats['successful_analyses'] / 
                           max(1, self.processing_stats['total_processed']) * 100),
            'sentiment_distribution': dict(self.processing_stats['sentiment_distribution']),
            'impact_distribution': dict(self.processing_stats['impact_distribution']),
            'harmonized_subjects_analyzed': list(self.processing_stats['harmonized_subjects_analyzed']),
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def get_stage2_analytics(self, client_id: str = "default") -> Dict:
        """Get analytics on Stage 2 analysis quality for a client"""
        try:
            # Query Stage 2 analyzed data
            query = self.db.supabase.table('stage1_data_responses') \
                .select('harmonized_subject, sentiment, impact_score, stage2_confidence, deal_status') \
                .eq('stage2_completed', True)
            
            if client_id != "all":
                query = query.eq('client_id', client_id)
            
            result = query.execute()
            
            if not result.data:
                return {'message': 'No Stage 2 analyzed data found'}
            
            # Analyze results
            data = result.data
            total_analyzed = len(data)
            
            # Distributions
            sentiment_dist = {}
            impact_dist = {}
            subject_sentiment = {}
            
            for row in data:
                # Sentiment distribution
                sentiment = row.get('sentiment', 'unknown')
                sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
                
                # Impact distribution
                impact = row.get('impact_score', 0)
                impact_dist[impact] = impact_dist.get(impact, 0) + 1
                
                # Subject-sentiment analysis
                subject = row.get('harmonized_subject', 'unknown')
                if subject not in subject_sentiment:
                    subject_sentiment[subject] = {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0}
                if sentiment in subject_sentiment[subject]:
                    subject_sentiment[subject][sentiment] += 1
            
            return {
                'total_analyzed_responses': total_analyzed,
                'sentiment_distribution': sentiment_dist,
                'impact_distribution': impact_dist,
                'subject_sentiment_breakdown': subject_sentiment,
                'client_id': client_id
            }
            
        except Exception as e:
            logger.error(f"❌ Analytics generation failed: {e}")
            return {'error': str(e)}

def main():
    """Command line interface for enhanced Stage 2 processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Single Table Stage 2 Processing')
    parser.add_argument('--process', action='store_true', help='Process unanalyzed responses')
    parser.add_argument('--client-id', default='default', help='Client ID to process')
    parser.add_argument('--analytics', action='store_true', help='Show Stage 2 analytics')
    parser.add_argument('--batch-size', type=int, default=30, help='Batch size for processing')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = EnhancedSingleTableStage2(
        batch_size=args.batch_size,
        max_workers=args.workers
    )
    
    if args.process:
        print(f"\n🎯 Starting Enhanced Stage 2 processing for client: {args.client_id}")
        print("=" * 60)
        
        result = processor.process_incremental(client_id=args.client_id)
        
        print(f"\n📊 Stage 2 Processing Results:")
        print(f"  Total processed: {result['total_processed']}")
        print(f"  Successful: {result['successful_analyses']}")
        print(f"  Success rate: {result['success_rate']:.1f}%")
        
        if result['sentiment_distribution']:
            print(f"  Sentiment: {result['sentiment_distribution']}")
        if result['impact_distribution']:
            print(f"  Impact: {result['impact_distribution']}")
    
    elif args.analytics:
        print(f"\n📈 Stage 2 Analytics for client: {args.client_id}")
        print("=" * 60)
        
        analytics = processor.get_stage2_analytics(args.client_id)
        
        if 'error' in analytics:
            print(f"❌ Error: {analytics['error']}")
        elif 'message' in analytics:
            print(f"📋 {analytics['message']}")
        else:
            print(f"Total analyzed: {analytics['total_analyzed_responses']}")
            print(f"Sentiment distribution: {analytics['sentiment_distribution']}")
            print(f"Impact distribution: {analytics['impact_distribution']}")
    
    else:
        print("🎯 Enhanced Single Table Stage 2 Processor Ready!")
        print("Use --process to analyze unprocessed responses")
        print("Use --analytics to view Stage 2 statistics")

if __name__ == "__main__":
    main() 