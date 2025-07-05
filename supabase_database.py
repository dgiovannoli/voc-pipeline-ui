#!/usr/bin/env python3
"""
Supabase-only Database Manager for VOC Pipeline
Replaces all SQLite functionality with direct Supabase operations
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dotenv import load_dotenv
import json

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available. Install with: pip install supabase")

load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    """
    Supabase-only database manager for VOC Pipeline
    Handles all data operations directly with Supabase
    """
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        # Initialize Supabase connection
        self.supabase = None
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                self.verify_connection()
                logger.info("✅ Supabase connection established")
            except Exception as e:
                logger.error(f"❌ Supabase connection failed: {e}")
                raise Exception(f"Failed to connect to Supabase: {e}")
        else:
            raise Exception("Supabase not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env file")
    
    def verify_connection(self):
        """Verify Supabase connection and table structure"""
        try:
            # Test connection by querying core_responses table
            result = self.supabase.table('core_responses').select('count').limit(1).execute()
            logger.info("✅ Supabase connection verified")
        except Exception as e:
            logger.error(f"❌ Supabase table verification failed: {e}")
            raise Exception(f"Supabase tables not found or connection failed: {e}")
    
    def test_connection(self) -> bool:
        """Test Supabase connection and return boolean result"""
        try:
            # Test connection by querying core_responses table
            result = self.supabase.table('core_responses').select('count').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
    
    def save_core_response(self, response_data: Dict[str, Any]) -> bool:
        """Save a core response to Supabase"""
        try:
            # Prepare data for Supabase
            data = {
                'response_id': response_data.get('response_id'),
                'verbatim_response': response_data.get('verbatim_response'),
                'subject': response_data.get('subject'),
                'question': response_data.get('question'),
                'deal_status': response_data.get('deal_status'),
                'company': response_data.get('company'),
                'interviewee_name': response_data.get('interviewee_name'),
                'interview_date': response_data.get('interview_date'),
                'file_source': response_data.get('file_source', ''),
                'created_at': datetime.now().isoformat()
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('core_responses').upsert(data).execute()
            
            logger.info(f"✅ Saved core response: {response_data.get('response_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save core response: {e}")
            return False
    
    def save_quote_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Save quote analysis to Supabase"""
        try:
            # Prepare data for Supabase
            data = {
                'quote_id': analysis_data.get('quote_id'),
                'criterion': analysis_data.get('criterion'),
                'score': analysis_data.get('score'),
                'priority': analysis_data.get('priority', 'medium'),
                'confidence': analysis_data.get('confidence', 'medium'),
                'relevance_explanation': analysis_data.get('relevance_explanation', ''),
                'deal_weighted_score': analysis_data.get('deal_weighted_score'),
                'context_keywords': analysis_data.get('context_keywords', ''),
                'question_relevance': analysis_data.get('question_relevance', 'unrelated'),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('quote_analysis').upsert(data).execute()
            
            logger.info(f"✅ Saved quote analysis: {analysis_data.get('quote_id')} - {analysis_data.get('criterion')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save quote analysis: {e}")
            return False
    
    def get_core_responses(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Get core responses from Supabase"""
        try:
            query = self.supabase.table('core_responses').select('*')
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key in ['company', 'deal_status', 'interviewee_name']:
                        query = query.eq(key, value)
                    elif key == 'date_from':
                        query = query.gte('interview_date', value)
                    elif key == 'date_to':
                        query = query.lte('interview_date', value)
            
            # Order by created_at desc
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            logger.info(f"📊 Retrieved {len(df)} core responses from Supabase")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get core responses: {e}")
            return pd.DataFrame()
    
    def get_quote_analysis(self, quote_id: Optional[str] = None) -> pd.DataFrame:
        """Get quote analysis from Supabase"""
        try:
            query = self.supabase.table('quote_analysis').select('*')
            
            if quote_id:
                query = query.eq('quote_id', quote_id)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            logger.info(f"📊 Retrieved {len(df)} quote analyses from Supabase")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get quote analysis: {e}")
            return pd.DataFrame()
    
    def get_unanalyzed_quotes(self) -> pd.DataFrame:
        """Get quotes that haven't been analyzed yet"""
        try:
            # Get all core responses
            core_df = self.get_core_responses()
            
            if core_df.empty:
                return pd.DataFrame()
            
            # Get all analyzed quote IDs
            analysis_df = self.get_quote_analysis()
            analyzed_ids = set(analysis_df['quote_id'].unique()) if not analysis_df.empty else set()
            
            # Filter out already analyzed quotes
            unanalyzed_df = core_df[~core_df['response_id'].isin(analyzed_ids)]
            
            logger.info(f"🔍 Found {len(unanalyzed_df)} unanalyzed quotes")
            return unanalyzed_df
            
        except Exception as e:
            logger.error(f"❌ Failed to get unanalyzed quotes: {e}")
            return pd.DataFrame()
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics from Supabase"""
        try:
            # Get core responses
            core_df = self.get_core_responses()
            
            if core_df.empty:
                return {
                    "total_quotes": 0,
                    "quotes_with_scores": 0,
                    "coverage_percentage": 0,
                    "criteria_performance": {},
                    "deal_outcome_distribution": {},
                    "company_distribution": {}
                }
            
            # Get quote analysis
            analysis_df = self.get_quote_analysis()
            
            # Calculate statistics
            total_quotes = len(core_df)
            quotes_with_scores = len(analysis_df['quote_id'].unique()) if not analysis_df.empty else 0
            coverage_percentage = round((quotes_with_scores / total_quotes) * 100, 1) if total_quotes > 0 else 0
            
            # Criteria performance
            criteria_performance = {}
            if not analysis_df.empty:
                for criterion in analysis_df['criterion'].unique():
                    criterion_data = analysis_df[analysis_df['criterion'] == criterion]
                    mentions = len(criterion_data)
                    avg_score = criterion_data['deal_weighted_score'].mean()
                    min_score = criterion_data['deal_weighted_score'].min()
                    max_score = criterion_data['deal_weighted_score'].max()
                    
                    criteria_performance[criterion] = {
                        "mention_count": mentions,
                        "average_score": round(avg_score, 2),
                        "score_range": [min_score, max_score],
                        "coverage_percentage": round((mentions / total_quotes) * 100, 1)
                    }
            
            # Deal outcome distribution
            deal_outcome_distribution = core_df['deal_status'].value_counts().to_dict()
            
            # Company distribution
            company_distribution = core_df['company'].value_counts().to_dict()
            
            return {
                "total_quotes": total_quotes,
                "quotes_with_scores": quotes_with_scores,
                "coverage_percentage": coverage_percentage,
                "criteria_performance": criteria_performance,
                "deal_outcome_distribution": deal_outcome_distribution,
                "company_distribution": company_distribution
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get summary statistics: {e}")
            return {"error": str(e)}
    
    def save_processing_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Save processing metadata to Supabase"""
        try:
            data = {
                'processing_date': datetime.now().isoformat(),
                'quotes_processed': metadata.get('quotes_processed', 0),
                'quotes_with_scores': metadata.get('quotes_with_scores', 0),
                'processing_errors': metadata.get('processing_errors', 0),
                'config_version': metadata.get('config_version', '1.0'),
                'processing_duration_seconds': metadata.get('processing_duration_seconds', 0)
            }
            
            result = self.supabase.table('processing_metadata').insert(data).execute()
            
            logger.info("✅ Saved processing metadata")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save processing metadata: {e}")
            return False
    
    def delete_core_response(self, response_id: str) -> bool:
        """Delete a core response and its associated analyses"""
        try:
            # Delete associated quote analyses first
            self.supabase.table('quote_analysis').delete().eq('quote_id', response_id).execute()
            
            # Delete core response
            self.supabase.table('core_responses').delete().eq('response_id', response_id).execute()
            
            logger.info(f"✅ Deleted core response: {response_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete core response: {e}")
            return False
    
    def export_data(self, format: str = 'csv') -> str:
        """Export data from Supabase"""
        try:
            # Get all data
            core_df = self.get_core_responses()
            analysis_df = self.get_quote_analysis()
            
            if format.lower() == 'csv':
                # Create export filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                core_filename = f"core_responses_{timestamp}.csv"
                analysis_filename = f"quote_analysis_{timestamp}.csv"
                
                # Save to CSV
                core_df.to_csv(core_filename, index=False)
                analysis_df.to_csv(analysis_filename, index=False)
                
                logger.info(f"✅ Exported data to {core_filename} and {analysis_filename}")
                return f"Exported {len(core_df)} core responses and {len(analysis_df)} analyses"
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export data: {e}")
            return f"Export failed: {e}"

def create_supabase_database() -> SupabaseDatabase:
    """Factory function to create Supabase database instance"""
    return SupabaseDatabase() 