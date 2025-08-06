#!/usr/bin/env python3
"""
LLM Harmonization Integration Script
Integrates LLM-based semantic harmonization with existing Stage 1 data
Processes both existing data and integrates with ongoing pipeline
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
from fixed_llm_harmonizer import FixedLLMHarmonizer
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMHarmonizationIntegrator:
    """Integrates LLM harmonization with existing VOC Pipeline"""
    
    def __init__(self, batch_size: int = 20, max_workers: int = 3):
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Initialize components
        try:
            self.harmonizer = FixedLLMHarmonizer()
            self.db = SupabaseDatabase()
            logger.info("✅ Fixed LLM Harmonization Integrator initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize integrator: {e}")
            raise
        
        # Progress tracking
        self.progress_lock = threading.Lock()
        self.progress_data = {
            'total_responses': 0,
            'processed_responses': 0,
            'successful_harmonizations': 0,
            'failed_harmonizations': 0,
            'new_categories_suggested': set(),
            'confidence_scores': []
        }
    
    def harmonize_existing_data(self, client_id: str = "default", 
                               force_reharmonize: bool = False) -> Dict:
        """
        Harmonize all existing Stage 1 data for a client
        
        Args:
            client_id: Target client ID
            force_reharmonize: Re-harmonize already processed data
            
        Returns:
            Summary of harmonization results
        """
        logger.info(f"🚀 Starting harmonization of existing data for client: {client_id}")
        
        try:
            # Get data to harmonize
            data_to_process = self._get_data_for_harmonization(client_id, force_reharmonize)
            
            if not data_to_process:
                logger.info("📋 No data found that needs harmonization")
                return self._create_summary_result()
            
            logger.info(f"📊 Found {len(data_to_process)} responses to harmonize")
            self.progress_data['total_responses'] = len(data_to_process)
            
            # Process in batches
            results = self._process_batches(data_to_process, client_id)
            
            # Generate summary
            summary = self._create_summary_result()
            logger.info(f"✅ Harmonization complete: {summary['successful_harmonizations']}/{summary['total_responses']} successful")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Harmonization failed: {e}")
            raise
    
    def _get_data_for_harmonization(self, client_id: str, force_reharmonize: bool) -> List[Dict]:
        """Get Stage 1 data that needs harmonization"""
        try:
            # Build query condition
            query = self.db.supabase.table('stage1_data_responses').select('*')
            
            if client_id != "all":
                query = query.eq('client_id', client_id)
            
            # Only get unharmonized data unless forcing reharmonization
            if not force_reharmonize:
                query = query.is_('harmonized_subject', 'null')
            
            result = query.execute()
            
            if not result.data:
                return []
            
            # Convert to list of dicts
            data_list = []
            for row in result.data:
                # Only process if subject exists
                if row.get('subject'):
                    data_list.append({
                        'response_id': row.get('response_id'),
                        'subject': row.get('subject'),
                        'verbatim_response': row.get('verbatim_response', ''),
                        'company_name': row.get('company_name', ''),
                        'deal_status': row.get('deal_status', ''),
                        'interview_date': row.get('interview_date', ''),
                        'client_id': row.get('client_id', client_id)
                    })
            
            logger.info(f"📋 Prepared {len(data_list)} responses for harmonization")
            return data_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get data for harmonization: {e}")
            return []
    
    def _process_batches(self, data_list: List[Dict], client_id: str) -> List[Dict]:
        """Process harmonization in parallel batches"""
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
                    with self.progress_lock:
                        self.progress_data['processed_responses'] += len(batch_results)
                        successful = sum(1 for r in batch_results if r.get('harmonized_subject'))
                        self.progress_data['successful_harmonizations'] += successful
                        self.progress_data['failed_harmonizations'] += (len(batch_results) - successful)
                    
                    logger.info(f"✅ Batch {batch_num}/{len(batches)} complete ({len(batch_results)} responses)")
                    
                except Exception as e:
                    logger.error(f"❌ Batch {batch_num} failed: {e}")
        
        return all_results
    
    def _process_batch(self, batch_num: int, batch_data: List[Dict], client_id: str) -> List[Dict]:
        """Process a single batch of responses"""
        batch_results = []
        
        for item in batch_data:
            try:
                # Build interview context
                interview_context = f"Company: {item.get('company_name', 'Unknown')}, " \
                                  f"Deal Status: {item.get('deal_status', 'Unknown')}, " \
                                  f"Date: {item.get('interview_date', 'Unknown')}"
                
                # Harmonize the subject
                harmonization_result = self.harmonizer.harmonize_subject(
                    natural_subject=item['subject'],
                    verbatim_response=item['verbatim_response'],
                    interview_context=interview_context
                )
                
                # Prepare database update
                update_data = {
                    'harmonized_subject': harmonization_result.get('harmonized_subject'),
                    'harmonization_confidence': harmonization_result.get('confidence'),
                    'harmonization_method': harmonization_result.get('mapping_method'),
                    'harmonization_reasoning': harmonization_result.get('reasoning'),
                    'suggested_new_category': harmonization_result.get('new_category_suggestion'),
                    'harmonized_at': datetime.now().isoformat()
                }
                
                # Save to database
                success = self._update_harmonization_in_db(item['response_id'], update_data)
                
                if success:
                    # Track confidence scores and new categories
                    with self.progress_lock:
                        self.progress_data['confidence_scores'].append(harmonization_result.get('confidence', 0.0))
                        if harmonization_result.get('new_category_suggestion'):
                            self.progress_data['new_categories_suggested'].add(
                                harmonization_result.get('new_category_suggestion')
                            )
                    
                    logger.debug(f"✅ Harmonized '{item['subject']}' → "
                               f"'{harmonization_result.get('harmonized_subject')}' "
                               f"(confidence: {harmonization_result.get('confidence', 0.0):.3f})")
                
                # Add to results
                result_item = item.copy()
                result_item.update(harmonization_result)
                result_item['db_update_success'] = success
                batch_results.append(result_item)
                
            except Exception as e:
                logger.error(f"❌ Failed to process item {item.get('response_id', 'unknown')}: {e}")
                # Add failed result
                result_item = item.copy()
                result_item.update({
                    'harmonized_subject': None,
                    'confidence': 0.0,
                    'reasoning': f"Processing failed: {str(e)}",
                    'db_update_success': False
                })
                batch_results.append(result_item)
        
        return batch_results
    
    def _update_harmonization_in_db(self, response_id: str, update_data: Dict) -> bool:
        """Update harmonization results in database"""
        try:
            # Remove None values for cleaner database
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
    
    def _create_summary_result(self) -> Dict:
        """Create harmonization summary"""
        with self.progress_lock:
            avg_confidence = (sum(self.progress_data['confidence_scores']) / 
                            len(self.progress_data['confidence_scores'])) \
                            if self.progress_data['confidence_scores'] else 0.0
            
            # Confidence distribution
            high_conf = sum(1 for c in self.progress_data['confidence_scores'] if c >= 0.7)
            med_conf = sum(1 for c in self.progress_data['confidence_scores'] if 0.4 <= c < 0.7)
            low_conf = sum(1 for c in self.progress_data['confidence_scores'] if c < 0.4)
            
            return {
                'total_responses': self.progress_data['total_responses'],
                'processed_responses': self.progress_data['processed_responses'],
                'successful_harmonizations': self.progress_data['successful_harmonizations'],
                'failed_harmonizations': self.progress_data['failed_harmonizations'],
                'success_rate': (self.progress_data['successful_harmonizations'] / 
                               max(1, self.progress_data['processed_responses']) * 100),
                'average_confidence': round(avg_confidence, 3),
                'confidence_distribution': {
                    'high (≥0.7)': high_conf,
                    'medium (0.4-0.7)': med_conf,
                    'low (<0.4)': low_conf
                },
                'new_categories_suggested': list(self.progress_data['new_categories_suggested']),
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def harmonize_new_response(self, response_data: Dict) -> Dict:
        """
        Harmonize a single new response (for integration with Stage 1 processing)
        
        Args:
            response_data: Stage 1 response data with 'subject' field
            
        Returns:
            Enhanced response data with harmonization fields
        """
        try:
            # Build interview context
            interview_context = f"Company: {response_data.get('company', 'Unknown')}, " \
                              f"Deal Status: {response_data.get('deal_status', 'Unknown')}"
            
            # Harmonize the subject
            harmonization_result = self.harmonizer.harmonize_subject(
                natural_subject=response_data.get('subject', ''),
                verbatim_response=response_data.get('verbatim_response', ''),
                interview_context=interview_context
            )
            
            # Add harmonization fields to response data
            enhanced_data = response_data.copy()
            enhanced_data.update({
                'harmonized_subject': harmonization_result.get('harmonized_subject'),
                'harmonization_confidence': harmonization_result.get('confidence'),
                'harmonization_method': harmonization_result.get('mapping_method'),
                'harmonization_reasoning': harmonization_result.get('reasoning'),
                'suggested_new_category': harmonization_result.get('new_category_suggestion'),
                'harmonized_at': datetime.now().isoformat()
            })
            
            logger.debug(f"🎯 Real-time harmonized: '{response_data.get('subject')}' → "
                        f"'{harmonization_result.get('harmonized_subject')}' "
                        f"(confidence: {harmonization_result.get('confidence', 0.0):.3f})")
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Real-time harmonization failed: {e}")
            # Return original data with error information
            enhanced_data = response_data.copy()
            enhanced_data.update({
                'harmonized_subject': None,
                'harmonization_confidence': 0.0,
                'harmonization_method': 'error',
                'harmonization_reasoning': f"Harmonization failed: {str(e)}",
                'suggested_new_category': None,
                'harmonized_at': datetime.now().isoformat()
            })
            return enhanced_data
    
    def get_harmonization_analytics(self, client_id: str = "default") -> Dict:
        """Get analytics on harmonization quality for a client"""
        try:
            # Query harmonized data
            query = self.db.supabase.table('stage1_data_responses') \
                .select('harmonized_subject, harmonization_confidence, harmonization_method, suggested_new_category') \
                .not_.is_('harmonized_subject', 'null')
            
            if client_id != "all":
                query = query.eq('client_id', client_id)
            
            result = query.execute()
            
            if not result.data:
                return {'message': 'No harmonized data found'}
            
            # Analyze results
            data = result.data
            total_harmonized = len(data)
            
            # Category distribution
            category_counts = {}
            confidence_scores = []
            new_categories = set()
            
            for row in data:
                # Count categories
                category = row.get('harmonized_subject')
                if category:
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                # Track confidence
                conf = row.get('harmonization_confidence')
                if conf is not None:
                    confidence_scores.append(float(conf))
                
                # Track new categories
                new_cat = row.get('suggested_new_category')
                if new_cat:
                    new_categories.add(new_cat)
            
            # Calculate metrics
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            high_conf = sum(1 for c in confidence_scores if c >= 0.7)
            med_conf = sum(1 for c in confidence_scores if 0.4 <= c < 0.7)
            low_conf = sum(1 for c in confidence_scores if c < 0.4)
            
            return {
                'total_harmonized_responses': total_harmonized,
                'average_confidence': round(avg_confidence, 3),
                'confidence_distribution': {
                    'high (≥0.7)': high_conf,
                    'medium (0.4-0.7)': med_conf,
                    'low (<0.4)': low_conf
                },
                'category_distribution': dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)),
                'new_categories_suggested': list(new_categories),
                'unique_categories_used': len(category_counts),
                'client_id': client_id
            }
            
        except Exception as e:
            logger.error(f"❌ Analytics generation failed: {e}")
            return {'error': str(e)}

def main():
    """Command line interface for LLM harmonization integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM Harmonization Integration')
    parser.add_argument('--harmonize', action='store_true', help='Harmonize existing data')
    parser.add_argument('--client-id', default='default', help='Client ID to process')
    parser.add_argument('--force', action='store_true', help='Force re-harmonization of already processed data')
    parser.add_argument('--analytics', action='store_true', help='Show harmonization analytics')
    parser.add_argument('--batch-size', type=int, default=20, help='Batch size for processing')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Initialize integrator
    integrator = LLMHarmonizationIntegrator(
        batch_size=args.batch_size,
        max_workers=args.workers
    )
    
    if args.harmonize:
        print(f"\n🚀 Starting harmonization for client: {args.client_id}")
        print("=" * 60)
        
        result = integrator.harmonize_existing_data(
            client_id=args.client_id,
            force_reharmonize=args.force
        )
        
        print(f"\n📊 Harmonization Results:")
        print(f"  Total processed: {result['processed_responses']}")
        print(f"  Successful: {result['successful_harmonizations']}")
        print(f"  Success rate: {result['success_rate']:.1f}%")
        print(f"  Average confidence: {result['average_confidence']}")
        
        if result['new_categories_suggested']:
            print(f"  💡 New categories suggested: {', '.join(result['new_categories_suggested'])}")
    
    elif args.analytics:
        print(f"\n📈 Harmonization Analytics for client: {args.client_id}")
        print("=" * 60)
        
        analytics = integrator.get_harmonization_analytics(args.client_id)
        
        if 'error' in analytics:
            print(f"❌ Error: {analytics['error']}")
        elif 'message' in analytics:
            print(f"📋 {analytics['message']}")
        else:
            print(f"Total harmonized responses: {analytics['total_harmonized_responses']}")
            print(f"Average confidence: {analytics['average_confidence']}")
            print(f"Unique categories: {analytics['unique_categories_used']}")
            
            print(f"\nTop categories:")
            for cat, count in list(analytics['category_distribution'].items())[:5]:
                print(f"  • {cat}: {count} responses")
            
            if analytics['new_categories_suggested']:
                print(f"\nNew categories suggested: {', '.join(analytics['new_categories_suggested'])}")
    
    else:
        print("🤖 LLM Harmonization Integration Ready!")
        print("Use --harmonize to process existing data")
        print("Use --analytics to view harmonization statistics")

if __name__ == "__main__":
    main() 