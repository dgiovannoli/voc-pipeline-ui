#!/usr/bin/env python3
"""
Database Schema Validator
Validates database schema and constraints before VOC pipeline processing
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase_database import SupabaseDatabase

class DatabaseValidator:
    """Validates database schema and constraints for VOC pipeline"""
    
    # Required tables and their expected columns
    REQUIRED_TABLES = {
        'interview_metadata': [
            'client_id', 'interview_id', 'company', 'interviewee_name', 
            'interviewee_role', 'deal_status', 'interview_overview'
        ],
        'stage1_data_responses': [
            'client_id', 'response_id', 'interview_id', 'company', 
            'interviewee_name', 'verbatim_response', 'question', 'sentiment', 'impact_score'
        ],
        'research_themes': [
            'client_id', 'theme_id', 'theme_statement', 'question_text', 
            'harmonized_subject', 'supporting_quotes', 'company_coverage', 
            'impact_score', 'evidence_strength', 'origin'
        ],
        'stage4_themes': [
            'client_id', 'theme_id', 'theme_statement', 'theme_type', 
            'supporting_finding_ids', 'company_ids', 'impact_score', 'evidence_strength'
        ],
        'interview_level_themes': [
            'client_id', 'interview_id', 'theme_statement', 'subject', 
            'sentiment', 'impact_score', 'notes'
        ]
    }
    
    # Expected constraints
    EXPECTED_CONSTRAINTS = {
        'research_themes': {
            'origin_check': "origin IN ('research', 'discovered')"
        }
    }
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id
        self.db = None
        self.issues = []
        self.warnings = []
        
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.db = SupabaseDatabase()
            print(f"✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def validate_tables_exist(self) -> Dict[str, bool]:
        """Check if all required tables exist"""
        if not self.db:
            return {}
        
        print(f"🔍 Checking required tables...")
        table_status = {}
        
        for table_name in self.REQUIRED_TABLES.keys():
            try:
                # Try to query the table
                result = self.db.supabase.table(table_name).select('*').limit(1).execute()
                table_status[table_name] = True
                print(f"   ✅ {table_name} - exists")
            except Exception as e:
                table_status[table_name] = False
                self.issues.append(f"Table '{table_name}' does not exist: {e}")
                print(f"   ❌ {table_name} - missing")
        
        return table_status
    
    def validate_table_columns(self, table_name: str) -> Dict[str, bool]:
        """Validate columns exist in a specific table"""
        if not self.db:
            return {}
        
        try:
            # Get table schema by querying with select *
            result = self.db.supabase.table(table_name).select('*').limit(1).execute()
            
            if not result.data:
                # Table is empty, try to get schema from error message or use expected columns
                return {col: False for col in self.REQUIRED_TABLES.get(table_name, [])}
            
            # Get actual columns from first row
            actual_columns = list(result.data[0].keys()) if result.data else []
            expected_columns = self.REQUIRED_TABLES.get(table_name, [])
            
            column_status = {}
            for col in expected_columns:
                if col in actual_columns:
                    column_status[col] = True
                else:
                    column_status[col] = False
                    self.issues.append(f"Column '{col}' missing in table '{table_name}'")
            
            return column_status
            
        except Exception as e:
            self.issues.append(f"Failed to validate columns for table '{table_name}': {e}")
            return {}
    
    def validate_constraints(self) -> Dict[str, bool]:
        """Validate expected constraints"""
        if not self.db:
            return {}
        
        print(f"🔒 Checking table constraints...")
        constraint_status = {}
        
        # Check research_themes origin constraint
        try:
            # Try to insert a test record with 'discovered' origin
            test_data = {
                'client_id': 'TEST_VALIDATION',
                'theme_id': 'test_theme_validation',
                'theme_statement': 'Test theme for validation',
                'origin': 'discovered'
            }
            
            # This should fail if constraint is too restrictive
            result = self.db.supabase.table('research_themes').insert(test_data).execute()
            
            # If we get here, constraint might be too permissive
            self.warnings.append("research_themes origin constraint may be too permissive")
            constraint_status['research_themes_origin'] = True
            
            # Clean up test data
            try:
                self.db.supabase.table('research_themes').delete().eq('client_id', 'TEST_VALIDATION').execute()
            except:
                pass
                
        except Exception as e:
            if 'origin' in str(e).lower():
                constraint_status['research_themes_origin'] = False
                self.issues.append(f"research_themes origin constraint issue: {e}")
            else:
                constraint_status['research_themes_origin'] = True
        
        return constraint_status
    
    def validate_data_quality(self) -> List[str]:
        """Check data quality issues"""
        if not self.db:
            return []
        
        quality_issues = []
        
        # Check for orphaned records
        try:
            # Check stage1_data_responses without interview_id
            orphaned_responses = self.db.supabase.table('stage1_data_responses').select('*').is_('interview_id', 'null').execute()
            if orphaned_responses.data:
                quality_issues.append(f"⚠️ {len(orphaned_responses.data)} responses without interview_id")
        except Exception as e:
            quality_issues.append(f"⚠️ Could not check orphaned responses: {e}")
        
        # Check for interviews without responses
        try:
            interviews = self.db.supabase.table('interview_metadata').select('interview_id').execute()
            responses = self.db.supabase.table('stage1_data_responses').select('interview_id').not_.is_('interview_id', 'null').execute()
            
            interview_ids = {i['interview_id'] for i in interviews.data}
            response_interview_ids = {r['interview_id'] for r in responses.data}
            
            interviews_without_responses = interview_ids - response_interview_ids
            if interviews_without_responses:
                quality_issues.append(f"⚠️ {len(interviews_without_responses)} interviews without responses")
        except Exception as e:
            quality_issues.append(f"⚠️ Could not check interviews without responses: {e}")
        
        return quality_issues
    
    def check_client_data(self) -> Dict[str, Any]:
        """Check data specific to the current client"""
        if not self.db or not self.client_id:
            return {}
        
        print(f"🔍 Checking client data for: {self.client_id}")
        
        client_stats = {}
        
        try:
            # Check interview count
            interviews = self.db.supabase.table('interview_metadata').select('*').eq('client_id', self.client_id).execute()
            client_stats['interviews'] = len(interviews.data)
            print(f"   📊 Interviews: {len(interviews.data)}")
            
            # Check response count
            responses = self.db.supabase.table('stage1_data_responses').select('*').eq('client_id', self.client_id).execute()
            client_stats['responses'] = len(responses.data)
            print(f"   📝 Responses: {len(responses.data)}")
            
            # Check linked responses
            linked_responses = self.db.supabase.table('stage1_data_responses').select('*').eq('client_id', self.client_id).not_.is_('interview_id', 'null').execute()
            client_stats['linked_responses'] = len(linked_responses.data)
            print(f"   🔗 Linked responses: {len(linked_responses.data)}")
            
            # Check research themes
            research_themes = self.db.supabase.table('research_themes').select('*').eq('client_id', self.client_id).execute()
            client_stats['research_themes'] = len(research_themes.data)
            print(f"   🔬 Research themes: {len(research_themes.data)}")
            
            # Check interview themes
            interview_themes = self.db.supabase.table('interview_level_themes').select('*').eq('client_id', self.client_id).execute()
            client_stats['interview_themes'] = len(interview_themes.data)
            print(f"   💬 Interview themes: {len(interview_themes.data)}")
            
        except Exception as e:
            print(f"   ⚠️ Error checking client data: {e}")
        
        return client_stats
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("DATABASE SCHEMA VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Client: {self.client_id or 'Not specified'}")
        report.append("")
        
        # Table validation results
        table_status = self.validate_tables_exist()
        if table_status:
            report.append("📋 TABLE VALIDATION:")
            for table, exists in table_status.items():
                status = "✅ EXISTS" if exists else "❌ MISSING"
                report.append(f"   {table}: {status}")
            report.append("")
        
        # Column validation results
        if table_status:
            report.append("🔍 COLUMN VALIDATION:")
            for table, exists in table_status.items():
                if exists:
                    column_status = self.validate_table_columns(table)
                    if column_status:
                        for col, col_exists in column_status.items():
                            status = "✅" if col_exists else "❌"
                            report.append(f"   {table}.{col}: {status}")
            report.append("")
        
        # Constraint validation results
        constraint_status = self.validate_constraints()
        if constraint_status:
            report.append("🔒 CONSTRAINT VALIDATION:")
            for constraint, valid in constraint_status.items():
                status = "✅ VALID" if valid else "❌ INVALID"
                report.append(f"   {constraint}: {status}")
            report.append("")
        
        # Data quality issues
        quality_issues = self.validate_data_quality()
        if quality_issues:
            report.append("⚠️ DATA QUALITY ISSUES:")
            for issue in quality_issues:
                report.append(f"   - {issue}")
            report.append("")
        
        # Client data summary
        if self.client_id:
            client_stats = self.check_client_data()
            if client_stats:
                report.append("📊 CLIENT DATA SUMMARY:")
                for metric, value in client_stats.items():
                    report.append(f"   {metric.replace('_', ' ').title()}: {value}")
                report.append("")
        
        # Overall validation status
        has_critical_issues = any('❌' in line for line in report)
        has_warnings = bool(self.warnings or quality_issues)
        
        if has_critical_issues:
            report.append("❌ VALIDATION FAILED - Critical issues found")
            report.append("   Fix these issues before processing")
        elif has_warnings:
            report.append("⚠️ VALIDATION PASSED with warnings")
            report.append("   Review warnings before processing")
        else:
            report.append("✅ VALIDATION PASSED - Database ready for processing")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def validate_schema(self) -> Tuple[bool, str]:
        """Main validation process"""
        print(f"🔍 Validating database schema...")
        
        # Connect to database
        if not self.connect_database():
            return False, "Failed to connect to database"
        
        # Generate comprehensive report
        report = self.generate_report()
        
        # Determine if validation passed
        has_critical_issues = any('❌' in line for line in report)
        validation_passed = not has_critical_issues
        
        return validation_passed, report

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate database schema for VOC pipeline')
    parser.add_argument('--client', help='Client ID to check data for')
    args = parser.parse_args()
    
    # Run validation
    validator = DatabaseValidator(args.client)
    success, report = validator.validate_schema()
    
    # Print report
    print(report)
    
    if success:
        print(f"\n🎉 Database validation passed!")
    else:
        print(f"\n❌ Database validation failed - fix issues before processing")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 