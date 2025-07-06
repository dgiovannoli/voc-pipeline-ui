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
    
    def get_scored_quotes(self) -> pd.DataFrame:
        """Get all quotes with scores from Supabase for Stage 3 analysis"""
        try:
            # Get core responses
            core_df = self.get_core_responses()
            
            # Get quote analysis
            analysis_df = self.get_quote_analysis()
            
            if core_df.empty or analysis_df.empty:
                return pd.DataFrame()
            
            # Filter analysis to only scored quotes
            scored_analysis = analysis_df[analysis_df['score'] > 0].copy()
            
            # Join the dataframes
            merged_df = scored_analysis.merge(
                core_df, 
                left_on='quote_id', 
                right_on='response_id', 
                how='inner'
            )
            
            # Add original_quote column
            merged_df['original_quote'] = merged_df['verbatim_response'].str[:200]
            
            logger.info(f"📊 Retrieved {len(merged_df)} scored quotes for Stage 3 analysis")
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
    
    def save_enhanced_finding(self, finding_data: Dict[str, Any]) -> bool:
        """Save an enhanced finding to Supabase with Buried Wins v4.0 framework"""
        try:
            # Prepare data for Supabase
            data = {
                'criterion': finding_data.get('criterion'),
                'finding_type': finding_data.get('finding_type'),
                'priority_level': finding_data.get('priority_level', 'standard'),
                'title': finding_data.get('title'),
                'description': finding_data.get('description'),
                'enhanced_confidence': finding_data.get('enhanced_confidence'),
                'criteria_scores': finding_data.get('criteria_scores', '{}'),
                'criteria_met': finding_data.get('criteria_met', 0),
                'impact_score': finding_data.get('impact_score'),
                'companies_affected': finding_data.get('companies_affected'),
                'quote_count': finding_data.get('quote_count'),
                'selected_quotes': finding_data.get('selected_quotes', '[]'),
                'themes': finding_data.get('themes', '[]'),
                'deal_impacts': finding_data.get('deal_impacts', '{}'),
                'generated_at': finding_data.get('generated_at', datetime.now().isoformat())
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Upsert to Supabase
            result = self.supabase.table('enhanced_findings').upsert(data).execute()
            
            logger.info(f"✅ Saved enhanced finding: {finding_data.get('title')} (Confidence: {finding_data.get('enhanced_confidence', 0):.1f})")
            return True
            
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
    
    def get_enhanced_findings(self, criterion: Optional[str] = None, finding_type: Optional[str] = None, priority_level: Optional[str] = None) -> pd.DataFrame:
        """Get enhanced findings from Supabase"""
        try:
            query = self.supabase.table('enhanced_findings').select('*')
            
            if criterion:
                query = query.eq('criterion', criterion)
            
            if finding_type:
                query = query.eq('finding_type', finding_type)
            
            if priority_level:
                query = query.eq('priority_level', priority_level)
            
            # Order by enhanced_confidence desc
            query = query.order('enhanced_confidence', desc=True)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            # Parse JSON fields
            if not df.empty:
                if 'criteria_scores' in df.columns:
                    df['criteria_scores'] = df['criteria_scores'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                if 'selected_quotes' in df.columns:
                    df['selected_quotes'] = df['selected_quotes'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                if 'themes' in df.columns:
                    df['themes'] = df['themes'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                if 'deal_impacts' in df.columns:
                    df['deal_impacts'] = df['deal_impacts'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            
            logger.info(f"📊 Retrieved {len(df)} enhanced findings from Supabase")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced findings: {e}")
            return pd.DataFrame()
    
    def get_findings_summary(self) -> Dict:
        """Get summary statistics for findings"""
        try:
            # Get total findings count
            total_findings = self.supabase.table('findings').select('id', count='exact').execute()
            total_count = total_findings.count if total_findings.count is not None else 0
            
            if total_count == 0:
                return {
                    'total_findings': 0,
                    'criteria_covered': 0,
                    'finding_type_distribution': {},
                    'average_impact_score': 0,
                    'total_companies_affected': 0
                }
            
            # Get findings by type
            findings_data = self.supabase.table('findings').select('*').execute()
            df = pd.DataFrame(findings_data.data)
            
            # Calculate statistics
            criteria_covered = df['criterion'].nunique()
            finding_types = df['finding_type'].value_counts().to_dict()
            avg_impact = df['impact_score'].mean() if 'impact_score' in df.columns else 0
            total_companies = df['companies_affected'].sum() if 'companies_affected' in df.columns else 0
            
            return {
                'total_findings': total_count,
                'criteria_covered': criteria_covered,
                'finding_type_distribution': finding_types,
                'average_impact_score': avg_impact,
                'total_companies_affected': total_companies
            }
            
        except Exception as e:
            logger.error(f"Error getting findings summary: {e}")
            return {
                'total_findings': 0,
                'criteria_covered': 0,
                'finding_type_distribution': {},
                'average_impact_score': 0,
                'total_companies_affected': 0
            }

    def get_enhanced_findings_summary(self) -> Dict:
        """Get enhanced findings summary statistics"""
        try:
            # Get all enhanced findings
            df = self.get_enhanced_findings()
            
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
            
            # Calculate summary statistics
            total_findings = len(df)
            priority_findings = len(df[df['priority_level'] == 'priority'])
            standard_findings = len(df[df['priority_level'] == 'standard'])
            low_findings = len(df[df['priority_level'] == 'low'])
            
            criteria_covered = df['criterion'].nunique()
            average_confidence = df['enhanced_confidence'].mean()
            average_criteria_met = df['criteria_met'].mean()
            
            # Finding type distribution
            finding_type_distribution = df['finding_type'].value_counts().to_dict()
            
            # Priority level distribution
            priority_level_distribution = df['priority_level'].value_counts().to_dict()
            
            # Criteria performance
            criteria_performance = {}
            for criterion in df['criterion'].unique():
                criterion_df = df[df['criterion'] == criterion]
                criteria_performance[criterion] = {
                    'findings_count': len(criterion_df),
                    'average_confidence': criterion_df['enhanced_confidence'].mean(),
                    'priority_findings': len(criterion_df[criterion_df['priority_level'] == 'priority'])
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
            df = self.get_enhanced_findings()
            
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

    def save_theme(self, theme_data: Dict) -> bool:
        """Save a theme to the themes table"""
        try:
            response = self.supabase.table('themes').insert(theme_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error saving theme: {e}")
            return False

    def get_themes(self) -> pd.DataFrame:
        """Get all themes from the themes table"""
        try:
            response = self.supabase.table('themes').select('*').order('created_at', desc=True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting themes: {e}")
            return pd.DataFrame()

    def get_themes_summary(self) -> Dict:
        """Get summary statistics for themes"""
        try:
            # Get total themes count
            total_themes = self.supabase.table('themes').select('id', count='exact').execute()
            total_count = total_themes.count if total_themes.count is not None else 0
            
            if total_count == 0:
                return {
                    'total_themes': 0,
                    'high_strength': 0,
                    'competitive_themes': 0,
                    'companies_covered': 0,
                    'theme_categories': {}
                }
            
            # Get themes data
            themes_data = self.supabase.table('themes').select('*').execute()
            df = pd.DataFrame(themes_data.data)
            
            # Calculate statistics
            high_strength = len(df[df['theme_strength'] == 'High'])
            competitive_themes = len(df[df['competitive_flag'] == True])
            theme_categories = df['theme_category'].value_counts().to_dict()
            
            # Count unique companies across all themes
            all_companies = []
            for companies in df['interview_companies']:
                if companies:
                    all_companies.extend(companies)
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
            quote_analysis_response = self.supabase.table('quote_analysis').select('*').execute()
            quote_df = pd.DataFrame(quote_analysis_response.data)
            
            # Get core responses for additional context
            core_responses_response = self.supabase.table('core_responses').select('*').execute()
            core_df = pd.DataFrame(core_responses_response.data)
            
            return findings_df
            
        except Exception as e:
            logger.error(f"Error getting findings for theme analysis: {e}")
            return pd.DataFrame()

    # Stage 5: Executive Synthesis Methods
    def get_themes_for_executive_synthesis(self) -> pd.DataFrame:
        """Get themes ready for executive synthesis"""
        try:
            # Get themes with high/medium strength
            response = self.supabase.table('themes').select('*').in_('theme_strength', ['High', 'Medium']).execute()
            df = pd.DataFrame(response.data)
            
            if df.empty:
                return pd.DataFrame()
            
            # Get related findings data for context
            findings_response = self.supabase.table('findings').select('*').execute()
            findings_df = pd.DataFrame(findings_response.data)
            
            # Get quote analysis data for additional context
            quote_analysis_response = self.supabase.table('quote_analysis').select('*').execute()
            quote_df = pd.DataFrame(quote_analysis_response.data)
            
            logger.info(f"📊 Loaded {len(df)} themes for executive synthesis")
            return df
            
        except Exception as e:
            logger.error(f"Error getting themes for executive synthesis: {e}")
            return pd.DataFrame()

    def generate_criteria_scorecard(self) -> Dict:
        """Generate executive criteria scorecard from Stage 2 data"""
        try:
            # Get quote analysis data
            quote_analysis_response = self.supabase.table('quote_analysis').select('*').execute()
            quote_df = pd.DataFrame(quote_analysis_response.data)
            
            if quote_df.empty:
                return {}
            
            # Get core responses for company information
            core_responses_response = self.supabase.table('core_responses').select('*').execute()
            core_df = pd.DataFrame(core_responses_response.data)
            
            # Merge data for analysis
            merged_df = quote_df.merge(core_df, left_on='quote_id', right_on='response_id', how='left')
            
            # Group by criterion and calculate metrics
            scorecard_data = []
            
            for criterion in merged_df['criterion'].unique():
                criterion_data = merged_df[merged_df['criterion'] == criterion]
                
                if len(criterion_data) == 0:
                    continue
                
                # Calculate metrics
                avg_score = criterion_data['score'].mean()
                total_mentions = len(criterion_data)
                companies_affected = criterion_data['company'].nunique()
                critical_mentions = len(criterion_data[criterion_data['score'] >= 4])
                
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

    def get_executive_themes(self) -> pd.DataFrame:
        """Get all executive themes"""
        try:
            response = self.supabase.table('executive_themes').select('*').order('priority_score', desc=True).execute()
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

    def get_executive_synthesis_summary(self) -> Dict:
        """Get summary statistics for executive synthesis"""
        try:
            # Get executive themes count
            themes_response = self.supabase.table('executive_themes').select('id', count='exact').execute()
            themes_count = themes_response.count if themes_response.count is not None else 0
            
            # Get scorecard count
            scorecard_response = self.supabase.table('criteria_scorecard').select('id', count='exact').execute()
            scorecard_count = scorecard_response.count if scorecard_response.count is not None else 0
            
            if themes_count == 0:
                return {
                    'total_executive_themes': 0,
                    'high_impact_themes': 0,
                    'presentation_ready': 0,
                    'competitive_themes': 0,
                    'criteria_analyzed': 0
                }
            
            # Get themes data for detailed stats
            themes_data = self.supabase.table('executive_themes').select('*').execute()
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

def create_supabase_database() -> SupabaseDatabase:
    """Factory function to create Supabase database instance"""
    return SupabaseDatabase() 