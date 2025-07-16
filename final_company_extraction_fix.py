#!/usr/bin/env python3
"""
Final Company Extraction Fix
Ensures all Stage 3 findings have proper company information by updating the analyzer code
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd
from datetime import datetime

load_dotenv()

def update_stage3_analyzer_company_extraction():
    """Update the Stage 3 analyzer to ensure proper company extraction"""
    try:
        print("🔧 Updating Stage 3 analyzer company extraction...")
        
        # Read the current Stage 3 analyzer file
        with open('stage3_findings_analyzer.py', 'r') as f:
            content = f.read()
        
        # Find and update the company extraction logic in the findings data creation section
        # Look for the section where findings_data is created (around line 1190-1220)
        
        # The issue is in the company extraction logic - we need to ensure it gets company from the quote properly
        old_company_extraction = '''                # Extract company information from the finding's quotes
                selected_quotes = finding.get('selected_quotes', [])
                interview_company = ""
                interviewee_name = ""
                supporting_response_ids = ""
                
                if selected_quotes:
                    # Get company and interviewee from the first quote
                    primary_quote_data = selected_quotes[0]
                    if isinstance(primary_quote_data, dict):
                        interview_company = primary_quote_data.get('company', '')
                        interviewee_name = primary_quote_data.get('interviewee_name', '')
                        response_id = primary_quote_data.get('response_id', '')
                        if response_id:
                            supporting_response_ids = response_id
                
                # If no company found in quotes, try to get from companies_affected
                if not interview_company and finding.get('companies_affected'):
                    companies_affected = finding.get('companies_affected', [])
                    if isinstance(companies_affected, list) and companies_affected:
                        interview_company = companies_affected[0]
                    elif isinstance(companies_affected, str) and companies_affected:
                        interview_company = companies_affected'''
        
        new_company_extraction = '''                # Extract company information from the finding's quotes
                selected_quotes = finding.get('selected_quotes', [])
                interview_company = ""
                interviewee_name = ""
                supporting_response_ids = ""
                
                if selected_quotes:
                    # Get company and interviewee from the first quote
                    primary_quote_data = selected_quotes[0]
                    if isinstance(primary_quote_data, dict):
                        interview_company = primary_quote_data.get('company', '')
                        interviewee_name = primary_quote_data.get('interviewee_name', '')
                        response_id = primary_quote_data.get('response_id', '')
                        if response_id:
                            supporting_response_ids = response_id
                
                # If no company found in quotes, try to get from companies_affected
                if not interview_company and finding.get('companies_affected'):
                    companies_affected = finding.get('companies_affected', [])
                    if isinstance(companies_affected, list) and companies_affected:
                        interview_company = companies_affected[0]
                    elif isinstance(companies_affected, str) and companies_affected:
                        interview_company = companies_affected
                
                # If still no company, try to get from the finding's direct company field
                if not interview_company:
                    interview_company = finding.get('company', '')
                
                # If still no company, try to get from interview_companies
                if not interview_company and finding.get('interview_companies'):
                    interview_companies = finding.get('interview_companies', [])
                    if isinstance(interview_companies, list) and interview_companies:
                        interview_company = interview_companies[0]
                
                # If still no company, try to get from interviewee_names to map to company
                if not interview_company and interviewee_name:
                    # Map interviewee to company based on Stage 1 data
                    db = SupabaseDatabase()
                    response = db.supabase.table('stage1_data_responses').select('company').eq('interviewee_name', interviewee_name).eq('client_id', 'Rev').limit(1).execute()
                    if response.data:
                        interview_company = response.data[0].get('company', '')'''
        
        # Replace the old company extraction logic
        if old_company_extraction in content:
            content = content.replace(old_company_extraction, new_company_extraction)
            print("✅ Updated company extraction logic in Stage 3 analyzer")
        else:
            print("⚠️ Could not find exact company extraction logic to replace")
            # Try a more targeted approach
            target_line = "                # Extract company information from the finding's quotes"
            if target_line in content:
                # Find the section and add the enhanced company extraction
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if target_line in line:
                        # Insert enhanced company extraction after the existing logic
                        enhanced_logic = '''                # Enhanced company extraction - try multiple sources
                if not interview_company:
                    interview_company = finding.get('company', '')
                
                if not interview_company and finding.get('interview_companies'):
                    interview_companies = finding.get('interview_companies', [])
                    if isinstance(interview_companies, list) and interview_companies:
                        interview_company = interview_companies[0]
                
                if not interview_company and interviewee_name:
                    # Map interviewee to company based on Stage 1 data
                    db = SupabaseDatabase()
                    response = db.supabase.table('stage1_data_responses').select('company').eq('interviewee_name', interviewee_name).eq('client_id', 'Rev').limit(1).execute()
                    if response.data:
                        interview_company = response.data[0].get('company', '')'''
                        
                        # Find where to insert (after the existing company extraction logic)
                        insert_index = i + 15  # Approximate location after existing logic
                        lines.insert(insert_index, enhanced_logic)
                        content = '\n'.join(lines)
                        print("✅ Added enhanced company extraction logic")
                        break
        
        # Write the updated content back to the file
        with open('stage3_findings_analyzer.py', 'w') as f:
            f.write(content)
        
        print("✅ Updated Stage 3 analyzer with enhanced company extraction")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Stage 3 analyzer: {e}")
        return False

def run_complete_pipeline_with_fix():
    """Run the complete pipeline with the company extraction fix"""
    try:
        print("\n🚀 Running complete pipeline with company extraction fix...")
        
        # Step 1: Update Stage 3 analyzer
        if not update_stage3_analyzer_company_extraction():
            print("❌ Failed to update Stage 3 analyzer")
            return False
        
        # Step 2: Run Stage 3 analysis
        print("\n📊 Step 2: Running Stage 3 analysis with enhanced company extraction...")
        from stage3_findings_analyzer import Stage3FindingsAnalyzer
        analyzer = Stage3FindingsAnalyzer()
        result = analyzer.process_stage3_findings(client_id='Rev')
        print(f"Stage 3 result: {result}")
        
        # Step 3: Run Stage 4 analysis
        print("\n📊 Step 3: Running Stage 4 analysis...")
        from stage4_theme_analyzer_json import Stage4ThemeAnalyzerJSON
        analyzer = Stage4ThemeAnalyzerJSON(client_id='Rev')
        result = analyzer.process_stage4_themes_json()
        print(f"Stage 4 result: {result}")
        
        print("\n✅ Complete pipeline with company extraction fix finished successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in complete pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_final_results():
    """Verify the final results after the fix"""
    try:
        print("\n📊 Verifying final results...")
        db = SupabaseDatabase()
        
        # Check Stage 3 findings with company information
        print('\n📊 Stage 3 Findings with Company Data:')
        response = db.supabase.table('stage3_findings').select('finding_id,interview_company,companies_affected').eq('client_id', 'Rev').limit(10).execute()
        findings = response.data
        
        if findings:
            company_count = 0
            for finding in findings:
                company = finding.get('interview_company', '')
                if company:
                    company_count += 1
                print(f'  Finding {finding.get("finding_id")}: "{company}"')
            
            print(f'\n📈 Company coverage: {company_count}/{len(findings)} findings have company data')
        
        # Check Stage 4 themes
        print('\n📊 Stage 4 Themes:')
        response = db.supabase.table('stage4_themes').select('theme_id,theme_title,company_ids,theme_type').eq('client_id', 'Rev').execute()
        themes = response.data
        
        if themes:
            theme_count = 0
            alert_count = 0
            cross_company_count = 0
            
            for theme in themes:
                theme_type = theme.get('theme_type', '')
                company_ids = theme.get('company_ids', '')
                
                if theme_type == 'theme':
                    theme_count += 1
                    if company_ids and ',' in company_ids:
                        cross_company_count += 1
                elif theme_type == 'strategic_alert':
                    alert_count += 1
                
                print(f'  {theme.get("theme_title", "No title")} ({theme_type})')
                print(f'    Companies: {company_ids}')
                print()
            
            print(f'📈 Summary:')
            print(f'  Total themes: {theme_count}')
            print(f'  Total alerts: {alert_count}')
            print(f'  Cross-company themes: {cross_company_count}')
            
        return True
        
    except Exception as e:
        print(f"❌ Error verifying results: {e}")
        return False

if __name__ == "__main__":
    # Run the complete fix and pipeline
    success = run_complete_pipeline_with_fix()
    if success:
        print("\n🎉 Company extraction fix completed successfully!")
        
        # Verify the results
        verify_final_results()
    else:
        print("\n❌ Company extraction fix failed - check logs for details") 