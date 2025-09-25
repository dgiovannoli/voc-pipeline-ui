#!/usr/bin/env python3
"""
Data Quality Dashboard
Comprehensive data quality monitoring and issue detection for VOC pipeline
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_database import SupabaseDatabase

class DataQualityDashboard:
    """Comprehensive data quality monitoring and issue detection"""
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id
        self.db = None
        self.quality_metrics = {}
        self.issues = []
        self.warnings = []
        
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.db = SupabaseDatabase()
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def check_data_completeness(self) -> Dict[str, Any]:
        """Check data completeness across all tables"""
        if not self.db:
            return {}
        
        print(f"📊 Checking data completeness...")
        
        completeness_metrics = {}
        
        # Check interview_metadata
        try:
            interviews = self.db.supabase.table('interview_metadata').select('*').execute()
            total_interviews = len(interviews.data) if interviews.data else 0
            
            if self.client_id:
                client_interviews = self.db.supabase.table('interview_metadata').select('*').eq('client_id', self.client_id).execute()
                client_interview_count = len(client_interviews.data) if client_interviews.data else 0
            else:
                client_interview_count = total_interviews
            
            # Check for missing required fields
            missing_fields = {}
            if client_interviews.data:
                for field in ['company', 'interviewee_name', 'deal_status']:
                    missing_count = sum(1 for i in client_interviews.data if not i.get(field))
                    if missing_count > 0:
                        missing_fields[field] = missing_count
            
            completeness_metrics['interview_metadata'] = {
                'total': total_interviews,
                'client_total': client_interview_count,
                'missing_fields': missing_fields
            }
            
        except Exception as e:
            completeness_metrics['interview_metadata'] = {'error': str(e)}
        
        # Check stage1_data_responses
        try:
            responses = self.db.supabase.table('stage1_data_responses').select('*').execute()
            total_responses = len(responses.data) if responses.data else 0
            
            if self.client_id:
                client_responses = self.db.supabase.table('stage1_data_responses').select('*').eq('client_id', self.client_id).execute()
                client_response_count = len(client_responses.data) if client_responses.data else 0
                
                # Check for unlinked responses
                unlinked_responses = [r for r in client_responses.data if not r.get('interview_id')]
                unlinked_count = len(unlinked_responses)
            else:
                client_response_count = total_responses
                unlinked_count = 0
            
            completeness_metrics['stage1_data_responses'] = {
                'total': total_responses,
                'client_total': client_response_count,
                'unlinked_count': unlinked_count
            }
            
        except Exception as e:
            completeness_metrics['stage1_data_responses'] = {'error': str(e)}
        
        # Check research_themes
        try:
            research_themes = self.db.supabase.table('research_themes').select('*').execute()
            total_research = len(research_themes.data) if research_themes.data else 0
            
            if self.client_id:
                client_research = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).execute()
                client_research_count = len(client_research.data) if client_research.data else 0
            else:
                client_research_count = total_research
            
            completeness_metrics['research_themes'] = {
                'total': total_research,
                'client_total': client_research_count
            }
            
        except Exception as e:
            completeness_metrics['research_themes'] = {'error': str(e)}
        
        # Check interview_level_themes
        try:
            interview_themes = self.db.supabase.table('interview_level_themes').select('*').execute()
            total_interview_themes = len(interview_themes.data) if interview_themes.data else 0
            
            if self.client_id:
                client_interview_themes = self.db.supabase.table('interview_level_themes').select('*').eq('client_id', self.client_id).execute()
                client_interview_theme_count = len(client_interview_themes.data) if client_interview_themes.data else 0
            else:
                client_interview_theme_count = total_interview_themes
            
            completeness_metrics['interview_level_themes'] = {
                'total': total_interview_themes,
                'client_total': client_interview_theme_count
            }
            
        except Exception as e:
            completeness_metrics['interview_level_themes'] = {'error': str(e)}
        
        return completeness_metrics
    
    def check_data_consistency(self) -> List[str]:
        """Check data consistency across tables"""
        if not self.db:
            return []
        
        print(f"🔗 Checking data consistency...")
        
        consistency_issues = []
        
        if self.client_id:
            try:
                # Check if all interviews have responses
                interviews = self.db.supabase.table('interview_metadata').select('interview_id').eq('client_id', self.client_id).execute()
                responses = self.db.supabase.table('stage1_data_responses').select('interview_id').eq('client_id', self.client_id).not_.is_('interview_id', 'null').execute()
                
                interview_ids = {i['interview_id'] for i in interviews.data}
                response_interview_ids = {r['interview_id'] for r in responses.data}
                
                interviews_without_responses = interview_ids - response_interview_ids
                if interviews_without_responses:
                    consistency_issues.append(f"⚠️ {len(interviews_without_responses)} interviews have no linked responses")
                
                # Check if all responses have interviews
                responses_without_interviews = response_interview_ids - interview_ids
                if responses_without_interviews:
                    consistency_issues.append(f"⚠️ {len(responses_without_interviews)} responses reference non-existent interviews")
                
            except Exception as e:
                consistency_issues.append(f"⚠️ Could not check interview-response consistency: {e}")
            
            try:
                # Check if all interviews have themes
                interviews = self.db.supabase.table('interview_metadata').select('interview_id').eq('client_id', self.client_id).execute()
                themes = self.db.supabase.table('interview_level_themes').select('interview_id').eq('client_id', self.client_id).execute()
                
                interview_ids = {i['interview_id'] for i in interviews.data}
                theme_interview_ids = {t['interview_id'] for t in themes.data}
                
                interviews_without_themes = interview_ids - theme_interview_ids
                if interviews_without_themes:
                    consistency_issues.append(f"⚠️ {len(interviews_without_themes)} interviews have no themes")
                
            except Exception as e:
                consistency_issues.append(f"⚠️ Could not check interview-theme consistency: {e}")
        
        return consistency_issues
    
    def check_data_quality(self) -> List[str]:
        """Check data quality issues"""
        if not self.db:
            return []
        
        print(f"🔍 Checking data quality...")
        
        quality_issues = []
        
        if self.client_id:
            try:
                # Check for very short transcripts
                responses = self.db.supabase.table('stage1_data_responses').select('verbatim_response').eq('client_id', self.client_id).execute()
                
                short_transcripts = 0
                empty_transcripts = 0
                
                for response in responses.data:
                    transcript = response.get('verbatim_response', '')
                    if not transcript or transcript.strip() == '':
                        empty_transcripts += 1
                    elif len(str(transcript).strip()) < 50:
                        short_transcripts += 1
                
                if empty_transcripts > 0:
                    quality_issues.append(f"⚠️ {empty_transcripts} responses have empty transcripts")
                
                if short_transcripts > 0:
                    quality_issues.append(f"⚠️ {short_transcripts} responses have very short transcripts (<50 chars)")
                
            except Exception as e:
                quality_issues.append(f"⚠️ Could not check transcript quality: {e}")
            
            try:
                # Check for missing company information
                interviews = self.db.supabase.table('interview_metadata').select('company').eq('client_id', self.client_id).execute()
                
                missing_companies = sum(1 for i in interviews.data if not i.get('company'))
                if missing_companies > 0:
                    quality_issues.append(f"⚠️ {missing_companies} interviews missing company names")
                
            except Exception as e:
                quality_issues.append(f"⚠️ Could not check company information: {e}")
            
            try:
                # Check for missing interviewee information
                interviews = self.db.supabase.table('interview_metadata').select('interviewee_name').eq('client_id', self.client_id).execute()
                
                missing_names = sum(1 for i in interviews.data if not i.get('interviewee_name'))
                if missing_names > 0:
                    quality_issues.append(f"⚠️ {missing_names} interviews missing interviewee names")
                
            except Exception as e:
                quality_issues.append(f"⚠️ Could not check interviewee information: {e}")
        
        return quality_issues
    
    def check_processing_status(self) -> Dict[str, Any]:
        """Check the status of each processing stage"""
        if not self.db:
            return {}
        
        print(f"⚙️ Checking processing status...")
        
        processing_status = {}
        
        if self.client_id:
            try:
                # Stage 1: Data ingestion
                responses = self.db.supabase.table('stage1_data_responses').select('*').eq('client_id', self.client_id).execute()
                linked_responses = self.db.supabase.table('stage1_data_responses').select('*').eq('client_id', self.client_id).not_.is_('interview_id', 'null').execute()
                
                stage1_status = {
                    'total_responses': len(responses.data) if responses.data else 0,
                    'linked_responses': len(linked_responses.data) if linked_responses.data else 0,
                    'completion_rate': len(linked_responses.data) / len(responses.data) * 100 if responses.data else 0
                }
                
                if stage1_status['completion_rate'] < 80:
                    self.warnings.append(f"Stage 1 completion rate is low: {stage1_status['completion_rate']:.1f}%")
                
                processing_status['stage1'] = stage1_status
                
            except Exception as e:
                processing_status['stage1'] = {'error': str(e)}
            
            try:
                # Stage 3: Theme generation
                research_themes = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).execute()
                interview_themes = self.db.supabase.table('interview_level_themes').select('*').eq('client_id', self.client_id).execute()
                
                stage3_status = {
                    'research_themes': len(research_themes.data) if research_themes.data else 0,
                    'interview_themes': len(interview_themes.data) if interview_themes.data else 0,
                    'total_themes': (len(research_themes.data) if research_themes.data else 0) + 
                                   (len(interview_themes.data) if interview_themes.data else 0)
                }
                
                processing_status['stage3'] = stage3_status
                
            except Exception as e:
                processing_status['stage3'] = {'error': str(e)}
            
            try:
                # Stage 4: Theme analysis
                stage4_themes = self.db.supabase.table('stage4_themes').select('*').eq('client_id', self.client_id).execute()
                
                stage4_status = {
                    'themes': len(stage4_themes.data) if stage4_themes.data else 0
                }
                
                processing_status['stage4'] = stage4_status
                
            except Exception as e:
                processing_status['stage4'] = {'error': str(e)}
        
        return processing_status
    
    def generate_quality_report(self) -> str:
        """Generate comprehensive quality report"""
        if not self.connect_database():
            return "❌ Failed to connect to database"
        
        report = []
        report.append("=" * 80)
        report.append("DATA QUALITY DASHBOARD")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Client: {self.client_id or 'All clients'}")
        report.append("")
        
        # Data completeness
        completeness = self.check_data_completeness()
        report.append("📊 DATA COMPLETENESS:")
        for table, metrics in completeness.items():
            if 'error' in metrics:
                report.append(f"   ❌ {table}: {metrics['error']}")
            else:
                report.append(f"   ✅ {table}: {metrics.get('client_total', metrics.get('total', 0))} records")
                if 'missing_fields' in metrics and metrics['missing_fields']:
                    for field, count in metrics['missing_fields'].items():
                        report.append(f"      ⚠️ Missing {field}: {count}")
        report.append("")
        
        # Data consistency
        consistency_issues = self.check_data_consistency()
        report.append("🔗 DATA CONSISTENCY:")
        if consistency_issues:
            for issue in consistency_issues:
                report.append(f"   {issue}")
        else:
            report.append("   ✅ No consistency issues detected")
        report.append("")
        
        # Data quality
        quality_issues = self.check_data_quality()
        report.append("🔍 DATA QUALITY:")
        if quality_issues:
            for issue in quality_issues:
                report.append(f"   {issue}")
        else:
            report.append("   ✅ No quality issues detected")
        report.append("")
        
        # Processing status
        processing_status = self.check_processing_status()
        report.append("⚙️ PROCESSING STATUS:")
        for stage, status in processing_status.items():
            if 'error' in status:
                report.append(f"   ❌ {stage.upper()}: {status['error']}")
            else:
                if stage == 'stage1':
                    completion = status.get('completion_rate', 0)
                    status_icon = "✅" if completion >= 80 else "⚠️"
                    report.append(f"   {status_icon} {stage.upper()}: {completion:.1f}% complete")
                else:
                    total = status.get('total_themes', status.get('themes', 0))
                    report.append(f"   ✅ {stage.upper()}: {total} themes generated")
        report.append("")
        
        # Overall assessment
        total_issues = len(consistency_issues) + len(quality_issues)
        total_warnings = len(self.warnings)
        
        if total_issues == 0 and total_warnings == 0:
            report.append("🎉 EXCELLENT DATA QUALITY")
            report.append("   All systems are functioning properly")
        elif total_issues == 0:
            report.append("✅ GOOD DATA QUALITY")
            report.append("   Minor warnings detected, but no critical issues")
        else:
            report.append("❌ DATA QUALITY ISSUES DETECTED")
            report.append(f"   {total_issues} issues need attention")
            if total_warnings > 0:
                report.append(f"   {total_warnings} additional warnings")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_quality_check(self) -> Tuple[bool, str]:
        """Run complete quality check"""
        print(f"🔍 Running data quality check...")
        
        # Generate comprehensive report
        report = self.generate_quality_report()
        
        # Determine if quality check passed
        has_critical_issues = any('❌' in line for line in report)
        quality_passed = not has_critical_issues
        
        return quality_passed, report

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run data quality dashboard')
    parser.add_argument('--client', help='Client ID to check (optional)')
    args = parser.parse_args()
    
    # Run quality check
    dashboard = DataQualityDashboard(args.client)
    success, report = dashboard.run_quality_check()
    
    # Print report
    print(report)
    
    if success:
        print(f"\n🎉 Data quality check passed!")
    else:
        print(f"\n❌ Data quality issues detected - review and fix before processing")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 