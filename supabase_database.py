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
import traceback
import math

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
            # Test connection by querying stage1_data_responses table
            result = self.supabase.table('stage1_data_responses').select('count').limit(1).execute()
            logger.info("✅ Supabase connection verified")
        except Exception as e:
            logger.error(f"❌ Supabase table verification failed: {e}")
            raise Exception(f"Supabase tables not found or connection failed: {e}")
    
    def test_connection(self) -> bool:
        """Test Supabase connection and return boolean result"""
        try:
            # Test connection by querying stage1_data_responses table
            result = self.supabase.table('stage1_data_responses').select('count').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
    
    def save_core_response(self, response_data: Dict[str, Any]) -> bool:
        """Save a core response to Supabase with optional harmonized subject fields"""
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
                'industry': response_data.get('industry'),
                'audio_video_link': response_data.get('audio_video_link'),
                'contact_website': response_data.get('contact_website'),
                'file_source': response_data.get('file_source', ''),
                'client_id': response_data.get('client_id', 'default'),
                'created_at': datetime.now().isoformat(),
                'start_timestamp': response_data.get('start_timestamp'),
                'end_timestamp': response_data.get('end_timestamp')
            }
            
            # Add harmonized subject fields if present
            if response_data.get('harmonized_subject') is not None:
                data.update({
                    'harmonized_subject': response_data.get('harmonized_subject'),
                    'harmonization_confidence': response_data.get('harmonization_confidence'),
                    'harmonization_method': response_data.get('harmonization_method'),
                    'harmonization_reasoning': response_data.get('harmonization_reasoning'),
                    'suggested_new_category': response_data.get('suggested_new_category'),
                    'harmonized_at': response_data.get('harmonized_at', datetime.now().isoformat())
                })
            
            # Sanitize NaN/inf to None
            try:
                for k, v in list(data.items()):
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        data[k] = None
            except Exception:
                pass
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('stage1_data_responses').upsert(data).execute()
            
            logger.info(f"✅ Saved core response: {response_data.get('response_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save core response: {e}")
            return False
    
    def save_stage2_response_labeling(self, analysis_data: Dict[str, Any]) -> bool:
        """Save quote analysis to Supabase"""
        try:
            # Prepare data for Supabase
            data = {
                'quote_id': analysis_data.get('quote_id'),
                'criterion': analysis_data.get('criterion'),
                'relevance_score': analysis_data.get('score'),  # Map 'score' to 'relevance_score'
                'sentiment': analysis_data.get('sentiment', 'neutral'),
                'priority': analysis_data.get('priority', 'medium'),
                'confidence': analysis_data.get('confidence', 'medium'),
                'relevance_explanation': analysis_data.get('relevance_explanation', ''),
                'deal_weighted_score': analysis_data.get('deal_weighted_score'),
                'context_keywords': analysis_data.get('context_keywords', ''),
                'question_relevance': analysis_data.get('question_relevance', 'unrelated'),
                'client_id': analysis_data.get('client_id', 'default'),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('stage2_response_labeling').upsert(data).execute()
            
            logger.info(f"✅ Saved quote analysis: {analysis_data.get('quote_id')} - {analysis_data.get('criterion')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save quote analysis: {e}")
            return False
    
    def update_stage2_analysis(self, response_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Update Stage 2 analysis in the stage1_data_responses table"""
        try:
            # Prepare update data
            update_data = {
                'sentiment': analysis_data.get('sentiment'),
                'impact_score': analysis_data.get('impact_score'),
                'reasoning': analysis_data.get('reasoning', ''),
                'research_question_alignment': analysis_data.get('research_question_alignment', ''),
                'total_questions_addressed': analysis_data.get('total_questions_addressed', 0),
                'coverage_summary': analysis_data.get('coverage_summary', ''),
                'stage2_analysis_timestamp': analysis_data.get('stage2_analysis_timestamp', datetime.now().isoformat())
            }
            
            # Update the response in stage1_data_responses table
            result = self.supabase.table('stage1_data_responses').update(update_data).eq('response_id', response_id).execute()
            
            if result.data:
                logger.info(f"✅ Updated Stage 2 analysis for response: {response_id}")
                return True
            else:
                logger.error(f"❌ Failed to update Stage 2 analysis for response: {response_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update Stage 2 analysis: {e}")
            return False
    
    def get_stage1_data_responses(self, filters: Optional[Dict] = None, client_id: Optional[str] = None) -> pd.DataFrame:
        """Get core responses from Supabase, filtered by client_id for data siloing"""
        try:
            query = self.supabase.table('stage1_data_responses').select('*')
            
            # Require explicit client_id in production
            if not client_id or client_id == '' or client_id == 'default':
                logger.error(f"❌ get_stage1_data_responses called with invalid client_id='{client_id}'. You must provide a valid client_id. Returning empty DataFrame. Call stack:\n" + ''.join(traceback.format_stack()))
                return pd.DataFrame()
            
            # Always filter by client_id for data siloing
            query = query.eq('client_id', client_id)
            
            # Apply additional filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.order('created_at', desc=True).execute()
            df = pd.DataFrame(result.data)
            logger.info(f"📊 Retrieved {len(df)} core responses from Supabase for client {client_id}")
            return df
        except Exception as e:
            logger.error(f"❌ Failed to get Stage 1 data responses: {e}")
            return pd.DataFrame()
    
    def get_stage2_response_labeling(self, client_id: str, quote_id: Optional[str] = None) -> pd.DataFrame:
        """Get quote analysis from Supabase, filtered by client_id for data siloing"""
        try:
            query = self.supabase.table('stage2_response_labeling').select('*')
            
            # Always filter by client_id for data siloing
            query = query.eq('client_id', client_id)
            
            if quote_id:
                query = query.eq('quote_id', quote_id)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            logger.info(f"📊 Retrieved {len(df)} quote analyses from Supabase for client {client_id}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get quote analysis: {e}")
            return pd.DataFrame()
    
    def get_unanalyzed_quotes(self, client_id: str) -> pd.DataFrame:
        """Get quotes that haven't been analyzed yet, filtered by client_id"""
        try:
            # Get all core responses for this client
            core_df = self.get_stage1_data_responses(client_id=client_id)
            
            if core_df.empty:
                return pd.DataFrame()
            
            # Get all analyzed quote IDs for this client
            analysis_df = self.get_stage2_response_labeling(client_id=client_id)
            analyzed_ids = set(analysis_df['quote_id'].unique()) if not analysis_df.empty else set()
            
            # Filter out already analyzed quotes
            unanalyzed_df = core_df[~core_df['response_id'].isin(analyzed_ids)]
            
            logger.info(f"🔍 Found {len(unanalyzed_df)} unanalyzed quotes for client {client_id}")
            return unanalyzed_df
            
        except Exception as e:
            logger.error(f"❌ Failed to get unanalyzed quotes: {e}")
            return pd.DataFrame()
    
    def get_summary_statistics(self, client_id: str) -> Dict[str, Any]:
        """Get summary statistics from Supabase, filtered by client_id for data siloing"""
        try:
            # Get core responses
            core_df = self.get_stage1_data_responses(client_id=client_id)
            
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
            analysis_df = self.get_stage2_response_labeling(client_id=client_id)
            
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
                    avg_score = criterion_data['relevance_score'].mean()
                    min_score = criterion_data['relevance_score'].min()
                    max_score = criterion_data['relevance_score'].max()
                    
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
            return {}
    
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
            self.supabase.table('stage2_response_labeling').delete().eq('quote_id', response_id).execute()
            
            # Delete core response
            self.supabase.table('stage1_data_responses').delete().eq('response_id', response_id).execute()
            
            logger.info(f"✅ Deleted core response: {response_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete core response: {e}")
            return False
    
    def export_data(self, client_id: str, format: str = 'csv') -> str:
        """Export data from Supabase, filtered by client_id"""
        try:
            # Get all data
            core_df = self.get_stage1_data_responses(client_id=client_id)
            analysis_df = self.get_stage2_response_labeling(client_id=client_id)
            
            if format.lower() == 'csv':
                # Create export filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                core_filename = f"stage1_data_responses_{client_id}_{timestamp}.csv"
                analysis_filename = f"stage2_response_labeling_{client_id}_{timestamp}.csv"
                
                # Save to CSV
                core_df.to_csv(core_filename, index=False)
                analysis_df.to_csv(analysis_filename, index=False)
                
                logger.info(f"✅ Exported data to {core_filename} and {analysis_filename} for client {client_id}")
                return f"Exported {len(core_df)} core responses and {len(analysis_df)} analyses for client {client_id}"
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export data: {e}")
            return f"Export failed: {e}"
    
    def get_scored_quotes(self, client_id: str) -> pd.DataFrame:
        """Get all quotes with scores from Supabase for Stage 3 analysis, filtered by client_id"""
        try:
            # Get core responses
            core_df = self.get_stage1_data_responses(client_id=client_id)
            
            # Get quote analysis
            analysis_df = self.get_stage2_response_labeling(client_id=client_id)
            
            if core_df.empty or analysis_df.empty:
                return pd.DataFrame()
            
            # Filter analysis to only scored quotes
            scored_analysis = analysis_df[analysis_df['relevance_score'] > 0].copy()
            
            # Join the dataframes
            merged_df = scored_analysis.merge(
                core_df, 
                left_on='quote_id', 
                right_on='response_id', 
                how='inner'
            )
            
            # Add original_quote column
            merged_df['original_quote'] = merged_df['verbatim_response'].str[:200]
            
            logger.info(f"📊 Retrieved {len(merged_df)} scored quotes for Stage 3 analysis for client {client_id}")
            return merged_df
            
        except Exception as e:
            logger.error(f"❌ Failed to get scored quotes: {e}")
            return pd.DataFrame()
    
    def save_finding(self, finding_data: Dict[str, Any]) -> bool:
        """Save a finding to Supabase (legacy method for backward compatibility)"""
        try:
            # Prepare data for Supabase
            data = {
                'criterion': finding_data.get('criterion'),
                'finding_type': finding_data.get('finding_type'),
                'title': finding_data.get('title'),
                'description': finding_data.get('description'),
                'impact_score': finding_data.get('impact_score'),
                'confidence_score': finding_data.get('confidence_score'),
                'companies_affected': finding_data.get('companies_affected'),
                'quote_count': finding_data.get('quote_count'),
                'sample_quotes': json.dumps(finding_data.get('sample_quotes', [])),
                'themes': json.dumps(finding_data.get('themes', [])),
                'generated_at': finding_data.get('generated_at', datetime.now().isoformat())
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('findings').upsert(data).execute()
            
            logger.info(f"✅ Saved finding: {finding_data.get('title')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save finding: {e}")
            return False
    
    def save_enhanced_finding(self, finding_data: Dict[str, Any], client_id: str) -> bool:
        """Save an enhanced finding to Supabase with Buried Wins v4.0 framework"""
        try:
            # Generate unique finding ID if not provided
            finding_id = finding_data.get('finding_id')
            if not finding_id:
                # Get the next available finding ID for this specific client
                result = self.supabase.table('stage3_findings').select('finding_id').eq('client_id', client_id).order('finding_id', desc=True).limit(1).execute()
                if result.data:
                    last_id = result.data[0].get('finding_id', 'F0')
                    last_num = int(last_id.replace('F', '')) if last_id.startswith('F') else 0
                    finding_id = f"F{last_num + 1}"
                else:
                    finding_id = "F1"
            
            # Check if this finding_id already exists for this client
            existing = self.supabase.table('stage3_findings').select('finding_id').eq('client_id', client_id).eq('finding_id', finding_id).execute()
            if existing.data:
                # If finding already exists, skip it to avoid duplicates
                logger.info(f"⚠️ Finding {finding_id} already exists for client {client_id}, skipping...")
                return True
            
            # Prepare data for Supabase matching CSV structure exactly
            data = {
                'client_id': client_id,
                'finding_id': finding_id,
                'finding_statement': finding_data.get('finding_statement', finding_data.get('description', '')),
                'interview_company': finding_data.get('interview_company', finding_data.get('company', '')),
                'date': finding_data.get('date', datetime.now().strftime('%m/%d/%Y')),
                'deal_status': finding_data.get('deal_status', 'closed won'),
                'interviewee_name': finding_data.get('interviewee_name', ''),
                'supporting_response_ids': finding_data.get('supporting_response_ids', ''),
                'evidence_strength': finding_data.get('evidence_strength', finding_data.get('evidence_strength_score', 1)),
                'finding_category': finding_data.get('finding_category', finding_data.get('finding_type', '')),
                'criteria_met': finding_data.get('criteria_met', ''),
                'priority_level': finding_data.get('priority_level', 'Standard Finding'),
                'primary_quote': finding_data.get('primary_quote', ''),
                'secondary_quote': finding_data.get('secondary_quote', ''),
                'quote_attributions': finding_data.get('quote_attributions', ''),
                'column_1': None,
                'column_2': None,
                'column_3': None,
                'column_4': None,
                'column_5': None,
                'column_6': None,
                'column_7': None,
                'column_8': None,
                'column_9': None,
                'column_10': None,
                'column_11': None,
                'column_12': None,
                
                # Additional metadata fields for internal use
                'enhanced_confidence': finding_data.get('enhanced_confidence', 0.0),
                'criteria_scores': finding_data.get('criteria_scores', {}),
                'credibility_tier': finding_data.get('credibility_tier', 'standard'),
                'companies_affected': finding_data.get('companies_affected', []),
                'processing_metadata': finding_data.get('processing_metadata', {})
            }
            
            # Remove None values and handle JSON serialization
            clean_data = {}
            for k, v in data.items():
                if v is not None:
                    if isinstance(v, (dict, list)):
                        clean_data[k] = json.dumps(v) if v else '{}' if isinstance(v, dict) else '[]'
                    elif hasattr(v, 'isoformat') and callable(getattr(v, 'isoformat')):
                        # Convert date objects to ISO format string
                        clean_data[k] = v.isoformat()
                    else:
                        clean_data[k] = v
            
            # Insert to Supabase (not upsert to avoid conflicts)
            try:
                result = self.supabase.table('stage3_findings').insert(clean_data).execute()
                logger.info(f"✅ Saved enhanced finding: {finding_id} - {finding_data.get('title', '')[:50]}... (Confidence: {finding_data.get('enhanced_confidence', 0):.1f})")
                return True
            except Exception as insert_error:
                # If insert fails due to duplicate, try to update instead
                if "duplicate key" in str(insert_error).lower():
                    logger.warning(f"⚠️ Finding {finding_id} already exists, updating instead...")
                    try:
                        # Update existing finding
                        result = self.supabase.table('stage3_findings').update(clean_data).eq('client_id', client_id).eq('finding_id', finding_id).execute()
                        logger.info(f"✅ Updated enhanced finding: {finding_id}")
                        return True
                    except Exception as update_error:
                        logger.error(f"❌ Failed to update finding {finding_id}: {update_error}")
                        return False
                else:
                    logger.error(f"❌ Failed to insert finding {finding_id}: {insert_error}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Failed to save enhanced finding: {e}")
            return False
    
    def get_findings(self, criterion: Optional[str] = None, finding_type: Optional[str] = None) -> pd.DataFrame:
        """Get findings from Supabase"""
        try:
            query = self.supabase.table('findings').select('*')
            
            if criterion:
                query = query.eq('criterion', criterion)
            
            if finding_type:
                query = query.eq('finding_type', finding_type)
            
            # Order by impact_score desc, then by created_at desc
            query = query.order('impact_score', desc=True).order('created_at', desc=True)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            # Parse JSON columns
            if not df.empty:
                if 'sample_quotes' in df.columns:
                    df['sample_quotes'] = df['sample_quotes'].apply(lambda x: json.loads(x) if x else [])
                if 'themes' in df.columns:
                    df['themes'] = df['themes'].apply(lambda x: json.loads(x) if x else [])
            
            logger.info(f"📊 Retrieved {len(df)} findings from Supabase")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get findings: {e}")
            return pd.DataFrame()
    
    def get_stage3_findings(self, client_id: str, criterion: Optional[str] = None, finding_type: Optional[str] = None, priority_level: Optional[str] = None) -> pd.DataFrame:
        """Get Stage 3 findings from Supabase, filtered by client_id for data siloing"""
        try:
            query = self.supabase.table('stage3_findings').select('*')
            
            # Always filter by client_id for data siloing
            query = query.eq('client_id', client_id)
            
            # Apply additional filters
            if criterion:
                query = query.eq('criteria_met', criterion)
            if finding_type:
                query = query.eq('finding_category', finding_type)
            if priority_level:
                query = query.eq('priority_level', priority_level)
            
            # Order by enhanced_confidence desc
            query = query.order('enhanced_confidence', desc=True)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            logger.info(f"📊 Retrieved {len(df)} enhanced findings from Supabase for client {client_id}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get Stage 3 findings: {e}")
            return pd.DataFrame()

    def get_stage3_findings_list(self, client_id: str) -> List[Dict[str, Any]]:
        """Get Stage 3 findings as a list of dictionaries for LLM processing"""
        try:
            df = self.get_stage3_findings(client_id=client_id)
            if df.empty:
                return []
            
            # Convert DataFrame to list of dictionaries
            findings_list = df.to_dict('records')
            logger.info(f"📊 Retrieved {len(findings_list)} findings as list for client {client_id}")
            return findings_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get Stage 3 findings as list: {e}")
            return []

    def delete_stage4_themes(self, client_id: str) -> bool:
        """Delete all Stage 4 themes for a specific client"""
        try:
            response = self.supabase.table('stage4_themes').delete().eq('client_id', client_id).execute()
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"🗑️ Deleted {deleted_count} existing themes for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete Stage 4 themes: {e}")
            return False

    def delete_stage3_findings(self, client_id: str) -> bool:
        """Delete all Stage 3 findings for a specific client"""
        try:
            response = self.supabase.table('stage3_findings').delete().eq('client_id', client_id).execute()
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"🗑️ Deleted {deleted_count} existing findings for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete Stage 3 findings: {e}")
            return False

    def save_stage4_theme(self, theme_data: Dict[str, Any]) -> bool:
        """Save a Stage 4 theme or strategic alert to the database with comprehensive protocol schema"""
        try:
            # Convert competitive_flag to proper boolean
            competitive_flag = theme_data.get('competitive_flag', False)
            if isinstance(competitive_flag, str):
                competitive_flag = competitive_flag.lower() in ['true', '1', 'yes', 'y', 't']
            elif isinstance(competitive_flag, int):
                competitive_flag = bool(competitive_flag)
            else:
                competitive_flag = bool(competitive_flag)
            
            # Determine if this is a theme or strategic alert
            theme_type = theme_data.get('theme_type', 'theme')
            
            # Prepare data for the comprehensive schema
            record = {
                'client_id': theme_data.get('client_id', 'default'),
                'theme_id': theme_data.get('theme_id', 'T1'),
                'theme_type': theme_type,
                'competitive_flag': competitive_flag
            }
            
            # Add theme-specific fields
            if theme_type == 'theme':
                record.update({
                    'theme_title': theme_data.get('theme_title', ''),
                    'theme_statement': theme_data.get('theme_statement', ''),
                    'classification': theme_data.get('classification', ''),
                    'deal_context': theme_data.get('deal_context', ''),
                    'metadata_insights': theme_data.get('metadata_insights', ''),
                    'primary_quote': theme_data.get('primary_quote', ''),
                    'secondary_quote': theme_data.get('secondary_quote', ''),
                    'supporting_finding_ids': theme_data.get('supporting_finding_ids', ''),
                    'company_ids': theme_data.get('company_ids', '')
                })
            else:  # strategic_alert
                record.update({
                    'alert_title': theme_data.get('alert_title', ''),
                    'alert_statement': theme_data.get('alert_statement', ''),
                    'alert_classification': theme_data.get('alert_classification', ''),
                    'strategic_implications': theme_data.get('strategic_implications', ''),
                    'primary_alert_quote': theme_data.get('primary_alert_quote', ''),
                    'secondary_alert_quote': theme_data.get('secondary_alert_quote', ''),
                    'supporting_alert_finding_ids': theme_data.get('supporting_alert_finding_ids', ''),
                    'alert_company_ids': theme_data.get('alert_company_ids', '')
                })
            
            # Insert record
            response = self.supabase.table('stage4_themes').insert(record).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Saved Stage 4 {theme_type}: {theme_data.get('theme_id', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Failed to save Stage 4 {theme_type}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to save Stage 4 {theme_data.get('theme_type', 'item')}: {e}")
            return False
    
    def update_stage3_finding_classification(self, finding_id: str, classification: str, classification_reasoning: str, client_id: str) -> bool:
        """Update the classification and classification_reasoning for a Stage 3 finding"""
        try:
            # Prepare update data
            update_data = {
                'classification': classification,
                'classification_reasoning': classification_reasoning,
                'updated_at': datetime.now().isoformat()
            }
            
            # Update the finding in the database
            result = self.supabase.table('stage3_findings').update(update_data).eq('finding_id', finding_id).eq('client_id', client_id).execute()
            
            if result.data:
                logger.info(f"✅ Updated classification for finding {finding_id}: {classification}")
                return True
            else:
                logger.warning(f"⚠️ No finding found with ID {finding_id} for client {client_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update classification for finding {finding_id}: {e}")
            return False

    def get_stage3_findings_summary(self, client_id: str) -> Dict:
        """Get enhanced findings summary statistics, filtered by client_id"""
        try:
            df = self.get_stage3_findings(client_id=client_id)
            if df.empty:
                return {
                    'total_findings': 0,
                    'priority_findings': 0,
                    'standard_findings': 0,
                    'low_findings': 0,
                    'criteria_covered': 0,
                    'average_confidence': 0.0,
                    'average_criteria_met': 0.0
                }
            
            # Handle data type conversions safely
            total_findings = len(df)
            
            # Safely convert priority levels to numeric for counting
            priority_findings = 0
            standard_findings = 0
            low_findings = 0
            
            for _, row in df.iterrows():
                priority_level = str(row.get('priority_level', '')).lower()
                if 'priority' in priority_level:
                    priority_findings += 1
                elif 'standard' in priority_level:
                    standard_findings += 1
                else:
                    low_findings += 1
            
            criteria_covered = df['criterion'].nunique() if 'criterion' in df.columns else 0
            
            # Safely handle numeric conversions
            try:
                average_confidence = df['enhanced_confidence'].astype(float).mean()
            except (ValueError, TypeError):
                average_confidence = 0.0
                
            try:
                average_criteria_met = df['criteria_met'].astype(float).mean()
            except (ValueError, TypeError):
                average_criteria_met = 0.0
            
            finding_type_distribution = df['finding_type'].value_counts().to_dict() if 'finding_type' in df.columns else {}
            priority_level_distribution = df['priority_level'].value_counts().to_dict() if 'priority_level' in df.columns else {}
            
            criteria_performance = {}
            if 'criterion' in df.columns:
                for criterion in df['criterion'].unique():
                    if pd.notna(criterion):
                        criterion_df = df[df['criterion'] == criterion]
                        criteria_performance[str(criterion)] = {
                            'findings_count': len(criterion_df),
                            'average_confidence': criterion_df['enhanced_confidence'].astype(float).mean() if 'enhanced_confidence' in criterion_df.columns else 0.0,
                            'priority_findings': len(criterion_df[criterion_df['priority_level'].astype(str).str.contains('priority', case=False, na=False)])
                        }
            
            return {
                'total_findings': total_findings,
                'priority_findings': priority_findings,
                'standard_findings': standard_findings,
                'low_findings': low_findings,
                'criteria_covered': criteria_covered,
                'average_confidence': average_confidence,
                'average_criteria_met': average_criteria_met,
                'finding_type_distribution': finding_type_distribution,
                'priority_level_distribution': priority_level_distribution,
                'criteria_performance': criteria_performance
            }
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced findings summary: {e}")
            return {
                'error': str(e),
                'total_findings': 0,
                'priority_findings': 0,
                'standard_findings': 0,
                'low_findings': 0,
                'criteria_covered': 0,
                'average_confidence': 0.0,
                'average_criteria_met': 0.0
            }
    
    def get_priority_findings(self, min_confidence: float = 4.0) -> pd.DataFrame:
        """Get priority findings with high confidence scores"""
        try:
            df = self.get_stage3_findings()
            
            if df.empty:
                return pd.DataFrame()
            
            # Filter by confidence threshold and priority level
            priority_df = df[
                (df['enhanced_confidence'] >= min_confidence) | 
                (df['priority_level'] == 'priority')
            ].copy()
            
            # Sort by confidence score
            priority_df = priority_df.sort_values('enhanced_confidence', ascending=False)
            
            logger.info(f"📊 Retrieved {len(priority_df)} priority findings")
            return priority_df
            
        except Exception as e:
            logger.error(f"❌ Failed to get priority findings: {e}")
            return pd.DataFrame()

    # Stage 4: Theme Generation Methods
    def get_high_confidence_findings(self, min_confidence: float = 3.0) -> pd.DataFrame:
        """Get findings with high confidence scores for theme generation"""
        try:
            response = self.supabase.table('findings').select('*').gte('confidence_score', min_confidence).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting high confidence findings: {e}")
            return pd.DataFrame()

    def save_theme(self, theme_data: Dict, client_id: str) -> bool:
        """Save a theme to the stage4_themes table with client_id for data siloing"""
        try:
            # Use client_id from theme_data if provided, otherwise use parameter
            if 'client_id' not in theme_data or not theme_data['client_id']:
                theme_data['client_id'] = client_id
            response = self.supabase.table('stage4_themes').insert(theme_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error saving theme: {e}")
            return False

    def get_themes(self, client_id: str) -> pd.DataFrame:
        """Get all themes from the stage4_themes table, filtered by client_id"""
        try:
            query = self.supabase.table('stage4_themes').select('*')
            if client_id is not None:
                query = query.eq('client_id', client_id)
            response = query.order('created_at', desc=True).execute()
            df = pd.DataFrame(response.data)
            
            # Parse JSON columns safely
            if not df.empty:
                if 'quotes' in df.columns:
                    df['quotes'] = df['quotes'].apply(lambda x: self._safe_json_parse(x))
                if 'supporting_finding_ids' in df.columns:
                    df['supporting_finding_ids'] = df['supporting_finding_ids'].apply(lambda x: self._safe_json_parse(x))
                if 'interview_companies' in df.columns:
                    df['interview_companies'] = df['interview_companies'].apply(lambda x: self._safe_json_parse(x))
                if 'deal_status_distribution' in df.columns:
                    df['deal_status_distribution'] = df['deal_status_distribution'].apply(lambda x: self._safe_json_parse(x))
            
            return df
        except Exception as e:
            logger.error(f"Error getting themes: {e}")
            return pd.DataFrame()
    
    def _safe_json_parse(self, value):
        """Safely parse JSON values, returning the original value if parsing fails"""
        if value is None or value == '':
            return value
        
        if isinstance(value, (dict, list)):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return value
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # If it's not valid JSON, return as is
                return value
        
        return value

    def delete_theme(self, theme_id: str, client_id: str) -> bool:
        """Delete a theme from the stage4_themes table"""
        try:
            response = self.supabase.table('stage4_themes').delete().eq('id', theme_id).eq('client_id', client_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting theme: {e}")
            return False

    def get_themes_summary(self, client_id: str) -> Dict:
        """Get summary statistics for stage4_themes, filtered by client_id"""
        try:
            # Get total themes count filtered by client_id
            total_themes = self.supabase.table('stage4_themes').select('id', count='exact').eq('client_id', client_id).execute()
            total_count = total_themes.count if total_themes.count is not None else 0
            
            if total_count == 0:
                return {
                    'total_themes': 0,
                    'high_strength': 0,
                    'competitive_themes': 0,
                    'companies_covered': 0,
                    'theme_categories': {}
                }
            
            # Get themes data filtered by client_id
            themes_data = self.supabase.table('stage4_themes').select('*').eq('client_id', client_id).execute()
            df = pd.DataFrame(themes_data.data)
            
            # Calculate statistics
            high_strength = len(df[df['theme_strength'] == 'High'])
            competitive_themes = len(df[df['competitive_flag'] == True])
            theme_categories = df['theme_category'].value_counts().to_dict()
            
            # Count unique companies across all themes
            all_companies = []
            for companies in df['interview_companies']:
                if companies and isinstance(companies, (list, str)):
                    if isinstance(companies, str):
                        try:
                            companies = self._safe_json_parse(companies)
                        except:
                            companies = [companies]
                    if isinstance(companies, list):
                        all_companies.extend(companies)
                    elif isinstance(companies, str) and companies.strip():
                        # If it's a comma-separated string, split it
                        all_companies.extend([c.strip() for c in companies.split(',') if c.strip()])
            companies_covered = len(set(all_companies))
            
            return {
                'total_themes': total_count,
                'high_strength': high_strength,
                'competitive_themes': competitive_themes,
                'companies_covered': companies_covered,
                'theme_categories': theme_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting themes summary: {e}")
            return {
                'total_themes': 0,
                'high_strength': 0,
                'competitive_themes': 0,
                'companies_covered': 0,
                'theme_categories': {}
            }

    def get_findings_for_theme_analysis(self) -> pd.DataFrame:
        """Get findings with related quote data for theme analysis"""
        try:
            # Get findings with confidence >= 3.0
            findings_response = self.supabase.table('findings').select('*').gte('confidence_score', 3.0).execute()
            findings_df = pd.DataFrame(findings_response.data)
            
            if findings_df.empty:
                return pd.DataFrame()
            
            # Get related quote analysis data for context
            stage2_response_labeling_response = self.supabase.table('stage2_response_labeling').select('*').execute()
            quote_df = pd.DataFrame(stage2_response_labeling_response.data)
            
            # Get core responses for additional context
            stage1_data_responses_response = self.supabase.table('stage1_data_responses').select('*').execute()
            core_df = pd.DataFrame(stage1_data_responses_response.data)
            
            return findings_df
            
        except Exception as e:
            logger.error(f"Error getting findings for theme analysis: {e}")
            return pd.DataFrame()

    # Stage 5: Executive Synthesis Methods
    def get_themes_for_executive_synthesis(self) -> pd.DataFrame:
        """Get themes ready for executive synthesis from stage4_themes"""
        try:
            # Get themes with high/medium strength
            response = self.supabase.table('stage4_themes').select('*').in_('theme_strength', ['High', 'Medium']).execute()
            df = pd.DataFrame(response.data)
            
            if df.empty:
                return pd.DataFrame()
            
            # Get related findings data for context
            findings_response = self.supabase.table('findings').select('*').execute()
            findings_df = pd.DataFrame(findings_response.data)
            
            # Get quote analysis data for additional context
            stage2_response_labeling_response = self.supabase.table('stage2_response_labeling').select('*').execute()
            quote_df = pd.DataFrame(stage2_response_labeling_response.data)
            
            logger.info(f"📊 Loaded {len(df)} stage4_themes for executive synthesis")
            return df
            
        except Exception as e:
            logger.error(f"Error getting themes for executive synthesis: {e}")
            return pd.DataFrame()

    def generate_criteria_scorecard(self, client_id: str) -> Dict:
        """Generate executive criteria scorecard from Stage 2 data, filtered by client_id"""
        try:
            # Get quote analysis data filtered by client_id
            stage2_response_labeling_response = self.supabase.table('stage2_response_labeling').select('*').eq('client_id', client_id).execute()
            quote_df = pd.DataFrame(stage2_response_labeling_response.data)
            
            if quote_df.empty:
                return {}
            
            # Get core responses for company information filtered by client_id
            stage1_data_responses_response = self.supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).execute()
            core_df = pd.DataFrame(stage1_data_responses_response.data)
            
            # Merge data for analysis
            merged_df = quote_df.merge(core_df, left_on='quote_id', right_on='response_id', how='left')
            
            # Group by criterion and calculate metrics
            scorecard_data = []
            
            for criterion in merged_df['criterion'].unique():
                criterion_data = merged_df[merged_df['criterion'] == criterion]
                
                if len(criterion_data) == 0:
                    continue
                
                # Calculate metrics
                avg_score = criterion_data['relevance_score'].mean()
                total_mentions = len(criterion_data)
                companies_affected = criterion_data['company'].nunique()
                critical_mentions = len(criterion_data[criterion_data['relevance_score'] >= 4])
                
                # Calculate performance rating
                performance_rating = self._calculate_performance_rating(avg_score, total_mentions, critical_mentions)
                
                # Calculate executive priority
                executive_priority = self._determine_executive_priority(avg_score, companies_affected, critical_mentions)
                
                # Calculate action urgency
                action_urgency = self._calculate_action_urgency(avg_score, critical_mentions, companies_affected)
                
                # Get sample quotes
                sample_quotes = criterion_data['relevance_explanation'].head(3).tolist()
                
                # Analyze deal impact
                deal_impact = criterion_data['deal_status'].value_counts().to_dict()
                
                scorecard_entry = {
                    'criterion': criterion,
                    'performance_rating': performance_rating,
                    'avg_score': round(avg_score, 2),
                    'total_mentions': total_mentions,
                    'companies_affected': companies_affected,
                    'critical_mentions': critical_mentions,
                    'executive_priority': executive_priority,
                    'action_urgency': action_urgency,
                    'trend_direction': 'STABLE',  # Placeholder - could be enhanced with historical data
                    'key_insights': self._generate_key_insights(criterion, avg_score, total_mentions, companies_affected),
                    'sample_quotes': sample_quotes,
                    'deal_impact_analysis': deal_impact
                }
                
                scorecard_data.append(scorecard_entry)
            
            # Sort by performance rating priority
            rating_priority = {'EXCEPTIONAL': 5, 'STRONG': 4, 'GOOD': 3, 'NEEDS ATTENTION': 2, 'CRITICAL ISSUE': 1}
            scorecard_data.sort(key=lambda x: rating_priority.get(x['performance_rating'], 0), reverse=True)
            
            return {
                'overall_performance': self._calculate_overall_performance(scorecard_data),
                'criteria_details': scorecard_data,
                'deal_impact_analysis': self._analyze_deal_impact(merged_df)
            }
            
        except Exception as e:
            logger.error(f"Error generating criteria scorecard: {e}")
            return {}

    def _calculate_performance_rating(self, avg_score: float, mentions: int, critical_mentions: int) -> str:
        """Calculate performance rating based on scores and mentions"""
        critical_ratio = critical_mentions / mentions if mentions > 0 else 0
        
        if avg_score >= 3.5 and critical_ratio >= 0.3:
            return "EXCEPTIONAL"
        elif avg_score >= 3.0 and critical_ratio >= 0.2:
            return "STRONG"
        elif avg_score >= 2.5:
            return "GOOD"
        elif avg_score >= 2.0:
            return "NEEDS ATTENTION"
        else:
            return "CRITICAL ISSUE"

    def _determine_executive_priority(self, avg_score: float, companies: int, critical_mentions: int) -> str:
        """Determine executive priority level"""
        if avg_score >= 4.0 and companies >= 5:
            return "IMMEDIATE ACTION"
        elif avg_score >= 3.5 and critical_mentions >= 3:
            return "HIGH PRIORITY"
        elif avg_score >= 3.0 and companies >= 3:
            return "MEDIUM PRIORITY"
        else:
            return "MONITOR"

    def _calculate_action_urgency(self, avg_score: float, critical_mentions: int, companies: int) -> str:
        """Calculate action urgency level"""
        if avg_score <= 2.0 or critical_mentions >= 5:
            return "HIGH"
        elif avg_score <= 2.5 or critical_mentions >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_key_insights(self, criterion: str, avg_score: float, mentions: int, companies: int) -> str:
        """Generate key insights for a criterion"""
        if avg_score >= 3.5:
            return f"Strong performance in {criterion.replace('_', ' ')} with high customer satisfaction across {companies} companies"
        elif avg_score >= 3.0:
            return f"Good performance in {criterion.replace('_', ' ')} with room for improvement"
        elif avg_score >= 2.5:
            return f"Moderate performance in {criterion.replace('_', ' ')} requiring attention"
        else:
            return f"Critical issues identified in {criterion.replace('_', ' ')} affecting {companies} companies"

    def _calculate_overall_performance(self, scorecard_data: List[Dict]) -> Dict:
        """Calculate overall performance metrics"""
        if not scorecard_data:
            return {}
        
        total_criteria = len(scorecard_data)
        exceptional_count = len([c for c in scorecard_data if c['performance_rating'] == 'EXCEPTIONAL'])
        strong_count = len([c for c in scorecard_data if c['performance_rating'] == 'STRONG'])
        critical_count = len([c for c in scorecard_data if c['performance_rating'] == 'CRITICAL ISSUE'])
        
        # Calculate average performance rating
        rating_scores = {'EXCEPTIONAL': 5, 'STRONG': 4, 'GOOD': 3, 'NEEDS ATTENTION': 2, 'CRITICAL ISSUE': 1}
        avg_rating_score = sum(rating_scores.get(c['performance_rating'], 0) for c in scorecard_data) / total_criteria
        
        if avg_rating_score >= 4.0:
            overall_rating = "EXCEPTIONAL"
        elif avg_rating_score >= 3.5:
            overall_rating = "STRONG"
        elif avg_rating_score >= 3.0:
            overall_rating = "GOOD"
        elif avg_rating_score >= 2.0:
            overall_rating = "NEEDS ATTENTION"
        else:
            overall_rating = "CRITICAL ISSUE"
        
        return {
            'total_criteria_analyzed': total_criteria,
            'average_performance_rating': overall_rating,
            'top_performing_criteria': [c['criterion'] for c in scorecard_data[:3] if c['performance_rating'] in ['EXCEPTIONAL', 'STRONG']],
            'critical_attention_needed': [c['criterion'] for c in scorecard_data if c['performance_rating'] in ['CRITICAL ISSUE', 'NEEDS ATTENTION']],
            'performance_trend': 'IMPROVING' if exceptional_count > critical_count else 'DECLINING' if critical_count > exceptional_count else 'STABLE'
        }

    def _analyze_deal_impact(self, merged_df: pd.DataFrame) -> Dict:
        """Analyze deal impact by criterion"""
        if merged_df.empty:
            return {}
        
        deal_impact = {}
        
        for criterion in merged_df['criterion'].unique():
            criterion_data = merged_df[merged_df['criterion'] == criterion]
            deal_counts = criterion_data['deal_status'].value_counts().to_dict()
            deal_impact[criterion] = deal_counts
        
        # Identify criteria affecting lost deals
        criteria_affecting_lost = []
        criteria_winning_deals = []
        
        for criterion, deals in deal_impact.items():
            lost_count = deals.get('closed_lost', 0)
            won_count = deals.get('closed_won', 0)
            
            if lost_count > won_count:
                criteria_affecting_lost.append(criterion)
            elif won_count > lost_count:
                criteria_winning_deals.append(criterion)
        
        return {
            'criteria_affecting_lost_deals': criteria_affecting_lost,
            'criteria_winning_deals': criteria_winning_deals,
            'deal_breakdown_by_criterion': deal_impact
        }

    def save_executive_theme(self, theme_data: Dict) -> bool:
        """Save executive theme to database"""
        try:
            response = self.supabase.table('executive_themes').insert(theme_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error saving executive theme: {e}")
            return False

    def save_criteria_scorecard(self, scorecard_data: Dict) -> bool:
        """Save criteria scorecard to database"""
        try:
            # Save individual criteria entries
            for criterion_data in scorecard_data.get('criteria_details', []):
                response = self.supabase.table('criteria_scorecard').insert(criterion_data).execute()
                if not response.data:
                    logger.warning(f"Failed to save scorecard entry for {criterion_data.get('criterion')}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving criteria scorecard: {e}")
            return False

    def get_executive_themes(self, client_id: str) -> pd.DataFrame:
        """Get all executive themes filtered by client_id"""
        try:
            response = self.supabase.table('executive_themes').select('*').eq('client_id', client_id).order('priority_score', desc=True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting executive themes: {e}")
            return pd.DataFrame()

    def get_criteria_scorecard(self) -> pd.DataFrame:
        """Get criteria scorecard data"""
        try:
            response = self.supabase.table('criteria_scorecard').select('*').order('generated_at', desc=True).limit(100).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting criteria scorecard: {e}")
            return pd.DataFrame()

    def get_executive_synthesis_summary(self, client_id: str) -> Dict:
        """Get summary statistics for executive synthesis, filtered by client_id"""
        try:
            # Get executive themes count filtered by client_id
            themes_response = self.supabase.table('executive_themes').select('id', count='exact').eq('client_id', client_id).execute()
            themes_count = themes_response.count if themes_response.count is not None else 0
            
            # Get scorecard count filtered by client_id
            scorecard_response = self.supabase.table('criteria_scorecard').select('id', count='exact').eq('client_id', client_id).execute()
            scorecard_count = scorecard_response.count if scorecard_response.count is not None else 0
            
            if themes_count == 0:
                return {
                    'total_executive_themes': 0,
                    'high_impact_themes': 0,
                    'presentation_ready': 0,
                    'competitive_themes': 0,
                    'criteria_analyzed': 0
                }
            
            # Get themes data for detailed stats filtered by client_id
            themes_data = self.supabase.table('executive_themes').select('*').eq('client_id', client_id).execute()
            df = pd.DataFrame(themes_data.data)
            
            high_impact = len(df[df['business_impact_level'] == 'High'])
            presentation_ready = len(df[df['executive_readiness'] == 'Presentation'])
            competitive_themes = len(df[df['theme_category'] == 'Competitive'])
            
            return {
                'total_executive_themes': themes_count,
                'high_impact_themes': high_impact,
                'presentation_ready': presentation_ready,
                'competitive_themes': competitive_themes,
                'criteria_analyzed': scorecard_count
            }
            
        except Exception as e:
            logger.error(f"Error getting executive synthesis summary: {e}")
            return {
                'total_executive_themes': 0,
                'high_impact_themes': 0,
                'presentation_ready': 0,
                'competitive_themes': 0,
                'criteria_analyzed': 0
            }

    def get_all_stage1_data_responses(self) -> pd.DataFrame:
        """Get ALL core responses from Supabase without client_id filtering (for debugging)"""
        try:
            query = self.supabase.table('stage1_data_responses').select('*')
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            logger.info(f"📊 Retrieved {len(df)} total core responses from Supabase (all clients)")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get all core responses: {e}")
            return pd.DataFrame()

    def get_client_summary(self) -> Dict[str, int]:
        """Get summary of data by client_id"""
        try:
            df = self.get_all_stage1_data_responses()
            if df.empty:
                return {}
            
            client_counts = df['client_id'].value_counts().to_dict()
            logger.info(f"📊 Client data summary: {client_counts}")
            return client_counts
            
        except Exception as e:
            logger.error(f"❌ Failed to get client summary: {e}")
            return {}

    def get_interview_metadata(self, client_id: str) -> pd.DataFrame:
        """Get interview metadata with deal outcomes for competitive intelligence analysis"""
        try:
            response = self.supabase.table('interview_metadata').select('*').eq('client_id', client_id).execute()
            df = pd.DataFrame(response.data)
            
            if not df.empty:
                logger.info(f"📊 Retrieved {len(df)} interview metadata records for client {client_id}")
            else:
                logger.info(f"📊 No interview metadata found for client {client_id}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get interview metadata: {e}")
            return pd.DataFrame()

    def upsert_interview_metadata(self,
                                   client_id: str,
                                   interview_id: str,
                                   interviewee_name: str,
                                   company: str = '',
                                   deal_status: str = '',
                                   date_of_interview: Optional[str] = None,
                                   industry: str = '',
                                   interviewee_role: str = '',
                                   firm_size: str = '',
                                   audio_video_link: str = '',
                                   contact_website: str = '',
                                   interview_overview: Optional[str] = None,
                                   interview_contact_website: Optional[str] = None,
                                   job_title: Optional[str] = None,
                                   contact_email: Optional[str] = None,
                                   client_name: Optional[str] = None,
                                   contact_id: Optional[str] = None,
                                   interview_list_id_deals: Optional[str] = None,
                                   interview_list_id_direct: Optional[str] = None) -> bool:
        """Create or update a minimal interview_metadata record so UI can surface interviews.
        Uses (client_id, interview_id) as the natural key.
        """
        try:
            data = {
                'client_id': client_id,
                'interview_id': interview_id,
                'interviewee_name': interviewee_name,
                'company': company,
                'deal_status': deal_status,
                'date_of_interview': date_of_interview,
                'industry': industry,
                'interviewee_role': interviewee_role,
                'firm_size': firm_size,
                'audio_video_link': audio_video_link,
                'contact_website': contact_website,
                'metadata_updated_at': datetime.now().isoformat()
            }
            if interview_overview is not None:
                data['interview_overview'] = interview_overview
            if interview_contact_website:
                data['interview_contact_website'] = interview_contact_website
            if job_title:
                data['job_title'] = job_title
            if contact_email:
                data['contact_email'] = contact_email
            if client_name:
                data['client_name'] = client_name
            if contact_id:
                data['contact_id'] = contact_id
            if interview_list_id_deals:
                data['interview_list_id_deals'] = interview_list_id_deals
            if interview_list_id_direct:
                data['interview_list_id_direct'] = interview_list_id_direct
            # Sanitize NaN/inf to None
            try:
                for k, v in list(data.items()):
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        data[k] = None
            except Exception:
                pass
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            result = self.supabase.table('interview_metadata').upsert(data).execute()
            logger.info(f"✅ Upserted interview_metadata for {interview_id} ({client_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to upsert interview_metadata for {interview_id} ({client_id}): {e}")
            return False

    def update_interview_overview(self, client_id: str, interview_id: str, interview_overview: str) -> bool:
        """Update interview_overview text if column exists; ignore if not present."""
        try:
            res = self.supabase.table('interview_metadata').update({'interview_overview': interview_overview}).eq('client_id', client_id).eq('interview_id', interview_id).execute()
            if getattr(res, 'data', None) is not None:
                logger.info(f"📝 Updated interview_overview for {interview_id}")
                return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ Could not update interview_overview for {interview_id}: {e}")
            return False

    def merge_client_data(self, from_client_id: str, to_client_id: str) -> bool:
        """Merge data from one client_id to another"""
        try:
            # Update stage1_data_responses
            result = self.supabase.table('stage1_data_responses').update(
                {'client_id': to_client_id}
            ).eq('client_id', from_client_id).execute()
            
            # Update stage2_response_labeling
            result2 = self.supabase.table('stage2_response_labeling').update(
                {'client_id': to_client_id}
            ).eq('client_id', from_client_id).execute()
            
            logger.info(f"✅ Merged data from {from_client_id} to {to_client_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to merge client data: {e}")
            return False

    def get_theme_quotes(self, theme_id: str, client_id: str) -> pd.DataFrame:
        """Get all quotes that contributed to a specific theme from stage4_themes"""
        try:
            # First get the theme to find supporting finding IDs
            theme_response = self.supabase.table('stage4_themes').select('*').eq('id', theme_id).eq('client_id', client_id).execute()
            if not theme_response.data:
                return pd.DataFrame()
            
            theme = theme_response.data[0]
            supporting_finding_ids = theme.get('supporting_finding_ids', [])
            
            if not supporting_finding_ids:
                return pd.DataFrame()
            
            # Get the findings
            findings_response = self.supabase.table('stage3_findings').select('*').in_('id', supporting_finding_ids).eq('client_id', client_id).execute()
            findings_df = pd.DataFrame(findings_response.data)
            
            if findings_df.empty:
                return pd.DataFrame()
            
            # Extract quotes from findings
            all_quotes = []
            for _, finding in findings_df.iterrows():
                selected_quotes = finding.get('selected_quotes', [])
                if selected_quotes:
                    for quote_obj in selected_quotes:
                        if isinstance(quote_obj, dict) and 'text' in quote_obj:
                            all_quotes.append({
                                'quote_text': quote_obj['text'],
                                'finding_id': finding['id'],
                                'finding_type': finding['finding_type'],
                                'criterion': finding['criterion'],
                                'impact_score': finding['impact_score'],
                                'enhanced_confidence': finding['enhanced_confidence']
                            })
                        elif isinstance(quote_obj, str):
                            all_quotes.append({
                                'quote_text': quote_obj,
                                'finding_id': finding['id'],
                                'finding_type': finding['finding_type'],
                                'criterion': finding['criterion'],
                                'impact_score': finding['impact_score'],
                                'enhanced_confidence': finding['enhanced_confidence']
                            })
            
            # Get interviewee names for quotes
            core_df = self.get_stage1_data_responses(client_id=client_id)
            quotes_with_attribution = []
            
            for quote_data in all_quotes:
                quote_text = quote_data['quote_text']
                # Find interviewee by matching quote text
                match = core_df[core_df['verbatim_response'].str.contains(quote_text[:50], na=False)]
                if not match.empty:
                    quote_data['interviewee_name'] = match.iloc[0]['interviewee_name']
                    quote_data['company'] = match.iloc[0]['company']
                    quote_data['subject'] = match.iloc[0]['subject']
                    quote_data['question'] = match.iloc[0]['question']
                else:
                    quote_data['interviewee_name'] = 'Unknown'
                    quote_data['company'] = 'Unknown'
                    quote_data['subject'] = 'Unknown'
                    quote_data['question'] = 'Unknown'
                
                quotes_with_attribution.append(quote_data)
            
            return pd.DataFrame(quotes_with_attribution)
            
        except Exception as e:
            logger.error(f"Error getting theme quotes: {e}")
            return pd.DataFrame()

    def get_themes_for_curation(self, client_id: str) -> pd.DataFrame:
        """Get themes that need human curation."""
        try:
            response = self.supabase.table('stage4_themes').select('*').eq('client_id', client_id).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting themes for curation: {e}")
            return pd.DataFrame()

    def save_theme_curation(self, theme_id: str, curation_status: str, curated_by: str, notes: str = "") -> bool:
        """Save curation decision for a theme."""
        try:
            update_data = {
                'curation_status': curation_status,
                'curated_by': curated_by,
                'curated_at': datetime.now().isoformat(),
                'curator_notes': notes
            }
            response = self.supabase.table('stage4_themes').update(update_data).eq('id', theme_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error saving theme curation: {e}")
            return False

    def get_curation_summary(self, client_id: str) -> dict:
        """Get summary of curation progress."""
        try:
            themes = self.get_themes_for_curation(client_id)
            if themes.empty:
                return {}
            
            total_themes = len(themes)
            pending_themes = len(themes[themes.get('curation_status', 'pending') == 'pending'])
            approved_themes = len(themes[themes.get('curation_status', 'pending') == 'approved'])
            denied_themes = len(themes[themes.get('curation_status', 'pending') == 'denied'])
            
            return {
                'total_themes': total_themes,
                'pending_themes': pending_themes,
                'approved_themes': approved_themes,
                'denied_themes': denied_themes,
                'progress_percent': int(((approved_themes + denied_themes) / total_themes) * 100) if total_themes > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting curation summary: {e}")
            return {}

    def get_approved_themes_for_export(self, client_id: str) -> pd.DataFrame:
        """Get approved themes for export."""
        try:
            response = self.supabase.table('stage4_themes').select('*').eq('client_id', client_id).eq('curation_status', 'approved').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting approved themes: {e}")
            return pd.DataFrame()

    def get_approved_quotes_for_export(self, theme_ids: list) -> pd.DataFrame:
        """Get approved quotes for specific themes."""
        try:
            response = self.supabase.table('quote_analysis').select('*').in_('theme_id', theme_ids).eq('curation_label', 'approve').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting approved quotes: {e}")
            return pd.DataFrame()

    def save_json_finding(self, finding_data: Dict[str, Any], client_id: str) -> bool:
        """Save a finding with JSON data structure to Supabase"""
        try:
            # Prepare data for Supabase with JSONB support
            data = {
                'finding_id': finding_data.get('finding_id'),
                'finding_statement': finding_data.get('finding_statement'),
                'finding_category': finding_data.get('finding_category'),
                'impact_score': finding_data.get('impact_score'),
                'confidence_score': finding_data.get('confidence_score'),
                'supporting_quotes': json.dumps(finding_data.get('supporting_quotes', [])),
                'companies_mentioned': json.dumps(finding_data.get('companies_mentioned', [])),
                'interview_company': finding_data.get('interview_company'),
                'interview_date': finding_data.get('interview_date'),
                'interview_type': finding_data.get('interview_type'),
                'interviewer_name': finding_data.get('interviewer_name'),
                'interviewee_role': finding_data.get('interviewee_role'),
                'interviewee_company': finding_data.get('interviewee_company'),
                'finding_data': json.dumps(finding_data),  # Complete finding as JSON
                'metadata': json.dumps(finding_data.get('metadata', {})),
                'created_at': datetime.now().isoformat()
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('stage3_findings').upsert(data).execute()
            
            logger.info(f"✅ Saved JSON finding: {finding_data.get('finding_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save JSON finding: {e}")
            return False
    
    def get_json_findings(self, client_id: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get findings with JSON data structure from Supabase"""
        try:
            query = self.supabase.table('stage3_findings').select('*')
            
            # Apply filters if provided
            if filters and isinstance(filters, dict):
                for key, value in filters.items():
                    if key in ['finding_category', 'interview_company', 'finding_id']:
                        query = query.eq(key, value)
                    elif key == 'date_from':
                        query = query.gte('interview_date', value)
                    elif key == 'date_to':
                        query = query.lte('interview_date', value)
                    elif key == 'min_impact':
                        query = query.gte('impact_score', value)
                    elif key == 'min_confidence':
                        query = query.gte('confidence_score', value)
            
            # Order by created_at desc
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            
            # Parse JSON data
            findings = []
            for row in result.data:
                finding = {
                    'finding_id': row.get('finding_id'),
                    'finding_statement': row.get('finding_statement'),
                    'finding_category': row.get('finding_category'),
                    'impact_score': row.get('impact_score'),
                    'confidence_score': row.get('confidence_score'),
                    'supporting_quotes': json.loads(row.get('supporting_quotes', '[]')),
                    'companies_mentioned': json.loads(row.get('companies_mentioned', '[]')),
                    'interview_company': row.get('interview_company'),
                    'interview_date': row.get('interview_date'),
                    'interview_type': row.get('interview_type'),
                    'interviewer_name': row.get('interviewer_name'),
                    'interviewee_role': row.get('interviewee_role'),
                    'interviewee_company': row.get('interviewee_company'),
                    'finding_data': json.loads(row.get('finding_data', '{}')),
                    'metadata': json.loads(row.get('metadata', '{}')),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
                findings.append(finding)
            
            logger.info(f"📊 Retrieved {len(findings)} JSON findings from Supabase")
            return findings
            
        except Exception as e:
            logger.error(f"❌ Failed to get JSON findings: {e}")
            return []
    
    def save_json_theme(self, theme_data: Dict[str, Any], client_id: str) -> bool:
        """Save a theme with JSON data structure to Supabase"""
        try:
            # Prepare data for Supabase with JSONB support
            data = {
                'theme_id': theme_data.get('theme_id'),
                'theme_name': theme_data.get('theme_name'),
                'theme_description': theme_data.get('theme_description'),
                'strategic_importance': theme_data.get('strategic_importance'),
                'action_items': json.dumps(theme_data.get('action_items', [])),
                'related_findings': json.dumps(theme_data.get('related_findings', [])),
                'alert_id': theme_data.get('alert_id'),
                'alert_type': theme_data.get('alert_type'),
                'alert_message': theme_data.get('alert_message'),
                'alert_priority': theme_data.get('alert_priority'),
                'recommended_actions': json.dumps(theme_data.get('recommended_actions', [])),
                'theme_data': json.dumps(theme_data.get('theme_data', {})),
                'alert_data': json.dumps(theme_data.get('alert_data', {})),
                'metadata': json.dumps(theme_data.get('metadata', {})),
                'analysis_date': theme_data.get('analysis_date'),
                'created_at': datetime.now().isoformat()
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('stage4_themes').upsert(data).execute()
            
            logger.info(f"✅ Saved JSON theme: {theme_data.get('theme_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save JSON theme: {e}")
            return False
    
    def get_json_themes(self, client_id: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get themes with JSON data structure from Supabase"""
        try:
            query = self.supabase.table('stage4_themes').select('*')
            
            # Apply filters if provided
            if filters and isinstance(filters, dict):
                for key, value in filters.items():
                    if key in ['theme_id', 'alert_id', 'strategic_importance', 'alert_priority']:
                        query = query.eq(key, value)
                    elif key == 'date_from':
                        query = query.gte('analysis_date', value)
                    elif key == 'date_to':
                        query = query.lte('analysis_date', value)
            
            # Order by created_at desc
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            
            # Parse JSON data
            themes = []
            for row in result.data:
                theme = {
                    'theme_id': row.get('theme_id'),
                    'theme_name': row.get('theme_name'),
                    'theme_description': row.get('theme_description'),
                    'strategic_importance': row.get('strategic_importance'),
                    'action_items': json.loads(row.get('action_items', '[]')),
                    'related_findings': json.loads(row.get('related_findings', '[]')),
                    'alert_id': row.get('alert_id'),
                    'alert_type': row.get('alert_type'),
                    'alert_message': row.get('alert_message'),
                    'alert_priority': row.get('alert_priority'),
                    'recommended_actions': json.loads(row.get('recommended_actions', '[]')),
                    'theme_data': json.loads(row.get('theme_data', '{}')),
                    'alert_data': json.loads(row.get('alert_data', '{}')),
                    'metadata': json.loads(row.get('metadata', '{}')),
                    'analysis_date': row.get('analysis_date'),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
                themes.append(theme)
            
            logger.info(f"📊 Retrieved {len(themes)} JSON themes from Supabase")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Failed to get JSON themes: {e}")
            return []
    
    def export_json_findings(self, client_id: str, filters: Optional[Dict] = None) -> str:
        """Export findings as JSON file"""
        try:
            findings = self.get_json_findings(client_id=client_id, filters=filters)
            
            # Create export data structure
            export_data = {
                "findings": findings,
                "metadata": {
                    "total_findings": len(findings),
                    "export_date": datetime.now().isoformat(),
                    "client_id": client_id,
                    "filters_applied": filters or {}
                }
            }
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"findings_export_{client_id}_{timestamp}.json"
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"✅ Exported {len(findings)} findings to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to export JSON findings: {e}")
            return ""
    
    def export_json_themes(self, client_id: str, filters: Optional[Dict] = None) -> str:
        """Export themes as JSON file"""
        try:
            themes = self.get_json_themes(client_id=client_id, filters=filters)
            
            # Create export data structure
            export_data = {
                "themes": themes,
                "metadata": {
                    "total_themes": len(themes),
                    "export_date": datetime.now().isoformat(),
                    "client_id": client_id,
                    "filters_applied": filters or {}
                }
            }
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"themes_export_{client_id}_{timestamp}.json"
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"✅ Exported {len(themes)} themes to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to export JSON themes: {e}")
            return ""

    # ==========================
    # Minimal writes for new tables
    # ==========================
    def upsert_quote_question_map(self, rows: List[Dict[str, Any]]) -> bool:
        """Bulk upsert rows into quote_question_map."""
        try:
            if not rows:
                return True
            # Remove None values per row
            payload = [{k: v for k, v in r.items() if v is not None} for r in rows]
            self.supabase.table('quote_question_map').upsert(payload).execute()
            logger.info(f"✅ Upserted {len(rows)} rows into quote_question_map")
            return True
        except Exception as e:
            logger.error(f"❌ Failed upsert_quote_question_map: {e}")
            return False

    def upsert_research_themes(self, rows: List[Dict[str, Any]]) -> bool:
        """Bulk upsert rows into research_themes."""
        try:
            if not rows:
                return True
            payload = [{k: v for k, v in r.items() if v is not None} for r in rows]
            self.supabase.table('research_themes').upsert(payload).execute()
            logger.info(f"✅ Upserted {len(rows)} rows into research_themes")
            return True
        except Exception as e:
            logger.error(f"❌ Failed upsert_research_themes: {e}")
            return False

    def upsert_research_theme_evidence(self, rows: List[Dict[str, Any]]) -> bool:
        """Bulk upsert rows into research_theme_evidence."""
        try:
            if not rows:
                return True
            payload = [{k: v for k, v in r.items() if v is not None} for r in rows]
            self.supabase.table('research_theme_evidence').upsert(payload).execute()
            logger.info(f"✅ Upserted {len(rows)} rows into research_theme_evidence")
            return True
        except Exception as e:
            logger.error(f"❌ Failed upsert_research_theme_evidence: {e}")
            return False

    def upsert_research_themes_return(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Upsert research_themes and return inserted/updated rows (including theme_id)."""
        try:
            if not rows:
                return []
            payload = [{k: v for k, v in r.items() if v is not None} for r in rows]
            result = self.supabase.table('research_themes').upsert(payload).execute()
            data = result.data or []
            logger.info(f"✅ Upserted {len(data)} rows into research_themes (returning theme_id)")
            return data
        except Exception as e:
            logger.error(f"❌ Failed upsert_research_themes_return: {e}")
            return []

    def fetch_stage1_responses(self, client_id: str) -> pd.DataFrame:
        """Wrapper: return Stage 1 responses for client (alias for get_stage1_data_responses)."""
        try:
            return self.get_stage1_data_responses(client_id=client_id)
        except Exception:
            return pd.DataFrame()

    def fetch_interview_metadata(self, client_id: str) -> pd.DataFrame:
        """Wrapper: return interview_metadata for client (alias for get_interview_metadata)."""
        try:
            return self.get_interview_metadata(client_id)
        except Exception:
            return pd.DataFrame()

    def upsert_interview_transcript(self,
                                    client_id: str,
                                    interview_id: str,
                                    company: str,
                                    interviewee_name: str,
                                    full_transcript: str) -> bool:
        """Upsert a full transcript into interview_transcripts (preferred). Fallback to interview_metadata.full_transcript if table missing."""
        try:
            data = {
                'client_id': client_id,
                'interview_id': interview_id,
                'company': company,
                'interviewee_name': interviewee_name,
                'full_transcript': full_transcript,
                'created_at': datetime.now().isoformat(),
            }
            # Try dedicated table first
            try:
                self.supabase.table('interview_transcripts').upsert(data).execute()
                logger.info(f"✅ Upserted full transcript for {interview_id} into interview_transcripts")
                return True
            except Exception as e:
                logger.warning(f"⚠️ interview_transcripts missing or upsert failed; trying interview_metadata.full_transcript: {e}")
                # Fallback: store on interview_metadata if column exists
                try:
                    # Use 'raw_transcripts' column as per schema preference
                    self.supabase.table('interview_metadata').upsert({
                        'client_id': client_id,
                        'interview_id': interview_id,
                        'company': company,
                        'interviewee_name': interviewee_name,
                        'raw_transcripts': full_transcript,
                        'metadata_updated_at': datetime.now().isoformat(),
                    }).execute()
                    logger.info(f"✅ Upserted full transcript for {interview_id} in interview_metadata.raw_transcripts")
                    return True
                except Exception as e2:
                    logger.error(f"❌ Failed to store full transcript for {interview_id}: {e2}")
                    return False
        except Exception as e:
            logger.error(f"❌ upsert_interview_transcript exception: {e}")
            return False

    def fetch_interview_transcripts(self, client_id: str) -> pd.DataFrame:
        """Fetch full transcripts from interview_transcripts; if table missing, try interview_metadata.full_transcript."""
        try:
            try:
                res = self.supabase.table('interview_transcripts').select('*').eq('client_id', client_id).execute()
                df = pd.DataFrame(res.data or [])
                if not df.empty:
                    return df
            except Exception:
                pass
            # Fallback
            try:
                # Select raw_transcripts and alias it as full_transcript for consumers
                res2 = self.supabase.table('interview_metadata').select('client_id,interview_id,company,interviewee_name,raw_transcripts').eq('client_id', client_id).execute()
                df2 = pd.DataFrame(res2.data or [])
                if not df2.empty and 'raw_transcripts' in df2.columns:
                    df2 = df2.rename(columns={'raw_transcripts': 'full_transcript'})
                return df2
            except Exception:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def upsert_interview_level_theme(self,
                                     client_id: str,
                                     interview_id: str,
                                     theme_statement: str,
                                     subject: str = '',
                                     sentiment: Optional[str] = None,
                                     impact_score: Optional[float] = None,
                                     notes: str = '') -> bool:
        """Upsert a per-interview theme into interview_level_themes."""
        try:
            data = {
                'client_id': client_id,
                'interview_id': interview_id,
                'theme_statement': theme_statement,
                'subject': subject,
                'sentiment': sentiment,
                'impact_score': impact_score,
                'notes': notes,
                'created_at': datetime.now().isoformat(),
            }
            self.supabase.table('interview_level_themes').upsert(data).execute()
            return True
        except Exception as e:
            logger.warning(f"⚠️ upsert_interview_level_theme failed (table may not exist): {e}")
            return False

    def fetch_interview_level_themes(self, client_id: str) -> pd.DataFrame:
        """Fetch per-interview themes if present."""
        try:
            res = self.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def upsert_interview_cluster_evidence(self,
                                          client_id: str,
                                          cluster_id: int,
                                          response_id: str,
                                          evidence_label: Optional[str] = None,
                                          notes: Optional[str] = None,
                                          rank: Optional[int] = None) -> bool:
        """Upsert one evidence decision for a cluster/response."""
        try:
            data = {
                'client_id': client_id,
                'cluster_id': int(cluster_id),
                'response_id': response_id,
                'evidence_label': evidence_label,
                'notes': notes,
                'rank': rank,
                'updated_at': datetime.now().isoformat()
            }
            # Remove None values so we don't overwrite unintentionally
            data = {k: v for k, v in data.items() if v is not None or k in ('client_id','cluster_id','response_id')}
            self.supabase.table('interview_cluster_evidence').upsert(data, on_conflict='client_id,cluster_id,response_id').execute()
            return True
        except Exception as e:
            logger.warning(f"⚠️ upsert_interview_cluster_evidence failed: {e}")
            return False

    def fetch_interview_cluster_evidence(self, client_id: str) -> pd.DataFrame:
        """Fetch existing evidence decisions for a client."""
        try:
            res = self.supabase.table('interview_cluster_evidence').select('*').eq('client_id', client_id).execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def fetch_research_themes_all(self, client_id: str) -> pd.DataFrame:
        """Fetch research_themes for a client (both research and discovered)."""
        try:
            res = self.supabase.table('research_themes').select('*').eq('client_id', client_id).execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def fetch_interview_level_themes(self, client_id: str) -> pd.DataFrame:
        """Fetch interview_level_themes."""
        try:
            res = self.supabase.table('interview_level_themes').select('*').eq('client_id', client_id).execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def upsert_theme_similarity(self, rows: list) -> int:
        """Bulk upsert into theme_similarity; rows are dicts with keys: client_id, theme_id, other_theme_id, subject, score, features_json."""
        try:
            if not rows:
                return 0
            inserted = 0
            # Upsert in chunks
            chunk = 500
            for i in range(0, len(rows), chunk):
                payload = rows[i:i+chunk]
                self.supabase.table('theme_similarity').upsert(payload, on_conflict='client_id,theme_id,other_theme_id').execute()
                inserted += len(payload)
            return inserted
        except Exception as e:
            logger.warning(f"⚠️ upsert_theme_similarity failed: {e}")
            return 0

    def fetch_theme_similarity(self, client_id: str, min_score: float = 0.7, use_llm: bool = False) -> pd.DataFrame:
        """
        Fetch theme similarity data.
        If use_llm=True, uses LLM-based analysis instead of stored similarity data.
        """
        if use_llm:
            return self._fetch_llm_theme_similarity(client_id, min_score)
        else:
            try:
                res = self.supabase.table('theme_similarity').select('*').eq('client_id', client_id).gte('score', min_score).order('score', desc=True).execute()
                return pd.DataFrame(res.data or [])
            except Exception:
                return pd.DataFrame()

    def _fetch_llm_theme_similarity(self, client_id: str, min_score: float = 0.7) -> pd.DataFrame:
        """Use LLM to analyze theme similarity and return results in the expected format."""
        try:
            # Import here to avoid circular imports
            from openai import OpenAI
            import os
            import json
            
            # Check if OpenAI API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("⚠️ OpenAI API key not found, falling back to rule-based similarity")
                return self._fetch_rule_based_similarity(client_id, min_score)
            
            openai_client = OpenAI(api_key=api_key)
            
            # Get all themes for analysis
            research_themes = self.fetch_research_themes_all(client_id)
            
            # Get canonical interview themes from rollup clusters
            try:
                from interview_theme_rollup import rollup_interview_themes
                rollup_result = rollup_interview_themes(self, client_id)
                canonical_interview_themes = rollup_result.clusters.copy()
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch rollup interview themes: {e}")
                canonical_interview_themes = pd.DataFrame(columns=['cluster_id', 'canonical_theme'])
            
            if research_themes.empty and canonical_interview_themes.empty:
                return pd.DataFrame()
            
            # Prepare themes for LLM analysis
            themes_list = []
            
            # Add research themes
            if not research_themes.empty:
                for _, theme in research_themes.iterrows():
                    source = 'discovered' if str(theme.get('origin', '')).startswith('DISCOVERED:') else 'research'
                    themes_list.append({
                        'theme_id': theme['theme_id'],
                        'theme_statement': theme['theme_statement'],
                        'subject': theme.get('harmonized_subject', 'Uncategorized'),
                        'source': source
                    })
            
            # Add canonical interview themes
            if not canonical_interview_themes.empty:
                for _, theme in canonical_interview_themes.iterrows():
                    themes_list.append({
                        'theme_id': f"interview_theme_{int(theme['cluster_id']):03d}",
                        'theme_statement': theme['canonical_theme'],
                        'subject': 'Interview',
                        'source': 'interview_canonical'
                    })
            
            if len(themes_list) < 2:
                return pd.DataFrame()
            
            # LLM prompt for theme deduplication
            dedup_prompt = """You are a strict qualitative-dedupe analyst for B2B SaaS win/loss themes. Your job: find redundant themes without losing specificity from interviews. Prefer precision over recall.

Key concepts:
- Subject ≈ parent topic (e.g., Integration, Pricing, Support, Efficiency).
- Discovered/Research themes can be merged. Interview themes can be merged with research themes or other interview themes.

Scoring rules:
- Cosine similarity threshold (LLM-estimated semantic similarity on 0–1 scale).
- Noun-phrase Jaccard overlap on extracted key phrases.
- Entity overlap on systems/brands/processes (e.g., Shopify, WMS, CRM, rate cards, carriers).
- Sentiment/polarity alignment (both problem or both praise).
- Domain facet match (Integration, Pricing, Support, Efficiency).

Within-Subject gate: cosine ≥ 0.74 AND noun Jaccard ≥ 0.35.
Cross-Subject gate: cosine ≥ 0.78 AND entity overlap ≥ 0.50.

Do-NOT-Merge rules (any one triggers DENY):
- Conflicting entities (e.g., Shopify vs WMS/CRM) without shared parent qualifier.
- Opposite sentiment/polarity.
- Different stakeholder focus (Ops vs Finance/Legal).
- Modality mismatch (Pricing vs Support; Discovery vs Implementation).
- Temporal mismatch (Pilot vs steady-state) unless explicitly the same.

Banding:
- High ≥ 0.80
- Medium 0.70–0.79
- Low < 0.70 (do not recommend)

Max cluster size: 7 (split by dominant entity if exceeded).
Per-subject cap: 12 suggestions max.

Output JSON schema (array of objects):
{
  "pair_type": "within_subject" | "cross_subject",
  "subject_A": "...",
  "subject_B": "...",
  "theme_id_A": "...",
  "theme_id_B": "...",
  "statement_A": "...",
  "statement_B": "...",
  "scores": {
    "cosine": 0.00,
    "noun_jaccard": 0.00,
    "entity_overlap": 0.00,
    "sentiment_align": true,
    "facet_match": true
  },
  "decision_band": "High" | "Medium" | "Low",
  "merge_recommendation": "MERGE" | "DO_NOT_MERGE",
  "canonical_label_suggestion": "...",
  "rationale": "Short, specific reason citing shared phrases/entities and alignment.",
  "evidence_policy": "If either is an interview_theme_* => treat as Evidence, not merged."
}

Return only valid JSON."""

            # Create analysis prompt
            analysis_prompt = dedup_prompt + "\n\nAnalyze these themes for duplicates:\n\n"
            for j, theme in enumerate(themes_list):
                analysis_prompt += f"Theme {j+1} ({theme['source']}): {theme['theme_statement']}\n"
                analysis_prompt += f"ID: {theme['theme_id']}\n"
                analysis_prompt += f"Subject: {theme['subject']}\n\n"
            
            analysis_prompt += "Investigate all possible pairs and return JSON array of duplicate analysis results."
            
            # Call OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise theme deduplication analyst. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse response
            content = response.choices[0].message.content
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end == -1:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                return self._fetch_rule_based_similarity(client_id, min_score)
            
            json_str = content[json_start:json_end]
            results = json.loads(json_str)
            
            # Convert LLM results to the expected DataFrame format
            similarity_rows = []
            for result in results:
                if result.get('merge_recommendation') == 'MERGE':
                    # Create similarity row in the expected format
                    score = result.get('scores', {}).get('cosine', 0.0)
                    if score >= min_score:
                        similarity_rows.append({
                            'client_id': client_id,
                            'theme_id': result['theme_id_A'],
                            'other_theme_id': result['theme_id_B'],
                            'subject': result['subject_A'],
                            'score': score,
                            'features_json': {
                                'cosine': result.get('scores', {}).get('cosine', 0.0),
                                'jaccard': result.get('scores', {}).get('noun_jaccard', 0.0),
                                'entity_overlap': result.get('scores', {}).get('entity_overlap', 0.0),
                                'sentiment_align': result.get('scores', {}).get('sentiment_align', False),
                                'facet_match': result.get('scores', {}).get('facet_match', False),
                                'decision_band': result.get('decision_band', 'Medium'),
                                'rationale': result.get('rationale', ''),
                                'canonical_suggestion': result.get('canonical_label_suggestion', '')
                            }
                        })
            
            # Convert to DataFrame and sort by score
            if similarity_rows:
                df = pd.DataFrame(similarity_rows)
                df = df.sort_values('score', ascending=False)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"⚠️ LLM similarity analysis failed: {e}, falling back to rule-based")
            return self._fetch_rule_based_similarity(client_id, min_score)

    def _fetch_rule_based_similarity(self, client_id: str, min_score: float = 0.7) -> pd.DataFrame:
        """Fallback to rule-based similarity when LLM is not available."""
        try:
            res = self.supabase.table('theme_similarity').select('*').eq('client_id', client_id).gte('score', min_score).order('score', desc=True).execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()

    def upsert_theme_link(self, client_id: str, theme_id: str, canonical_id: str, source: str, reason: str = '') -> bool:
        try:
            data = {
                'client_id': client_id,
                'theme_id': theme_id,
                'canonical_id': canonical_id,
                'source': source,
                'reason': reason,
                'updated_at': datetime.now().isoformat(),
            }
            self.supabase.table('theme_links').upsert(data, on_conflict='client_id,theme_id').execute()
            return True
        except Exception as e:
            logger.warning(f"⚠️ upsert_theme_link failed: {e}")
            return False

def create_supabase_database() -> SupabaseDatabase:
    """Factory function to create Supabase database instance"""
    return SupabaseDatabase() 