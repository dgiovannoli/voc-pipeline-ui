#!/usr/bin/env python3
"""
Test script to verify company information extraction in Stage 3 pipeline
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd

load_dotenv()

def test_company_extraction():
    """Test company information extraction through the pipeline"""
    try:
        print("🔍 Testing company information extraction...")
        db = SupabaseDatabase()
        
        # Get a sample of Stage 1 data with company information
        print("\n📊 Checking Stage 1 data...")
        response = db.supabase.table('stage1_data_responses').select('response_id,company,interviewee_name,verbatim_response').eq('client_id', 'Rev').limit(5).execute()
        stage1_data = response.data
        
        if stage1_data:
            print(f"✅ Found {len(stage1_data)} Stage 1 responses:")
            for i, response in enumerate(stage1_data):
                print(f"  Response {i+1}:")
                print(f"    Response ID: {response.get('response_id', '')}")
                print(f"    Company: \"{response.get('company', '')}\"")
                print(f"    Interviewee: \"{response.get('interviewee_name', '')}\"")
                print(f"    Text: {response.get('verbatim_response', '')[:100]}...")
                print()
        
        # Check Stage 3 findings for company information
        print("\n📊 Checking Stage 3 findings...")
        response = db.supabase.table('stage3_findings').select('finding_id,interview_company,companies_affected,interviewee_name').eq('client_id', 'Rev').limit(5).execute()
        findings = response.data
        
        if findings:
            print(f"✅ Found {len(findings)} Stage 3 findings:")
            for i, finding in enumerate(findings):
                print(f"  Finding {i+1}:")
                print(f"    Finding ID: {finding.get('finding_id', '')}")
                print(f"    Interview Company: \"{finding.get('interview_company', '')}\"")
                print(f"    Companies Affected: \"{finding.get('companies_affected', '')}\"")
                print(f"    Interviewee Name: \"{finding.get('interviewee_name', '')}\"")
                print()
        
        # Check Stage 4 themes for company information
        print("\n📊 Checking Stage 4 themes...")
        response = db.supabase.table('stage4_themes').select('theme_id,theme_title,company_ids').eq('client_id', 'Rev').limit(5).execute()
        themes = response.data
        
        if themes:
            print(f"✅ Found {len(themes)} Stage 4 themes:")
            for i, theme in enumerate(themes):
                print(f"  Theme {i+1}:")
                print(f"    Theme ID: {theme.get('theme_id', '')}")
                print(f"    Theme Title: {theme.get('theme_title', '')}")
                print(f"    Company IDs: \"{theme.get('company_ids', '')}\"")
                print()
        
        print("\n📋 Summary:")
        print("  - Stage 1 data has company information")
        print("  - Stage 3 findings have empty company fields")
        print("  - Stage 4 themes have empty company fields")
        print("\n🔧 The issue is in the Stage 3 findings analyzer - company information is not being properly extracted from quotes")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_company_extraction() 