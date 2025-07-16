#!/usr/bin/env python3
"""
Comprehensive fix for company extraction issue in Stage 3 findings
Updates all Stage 3 findings with proper company information from Stage 1 data
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import pandas as pd
from datetime import datetime

load_dotenv()

def fix_company_extraction_complete():
    """Fix company extraction issue in all Stage 3 findings"""
    try:
        print("🔧 Comprehensive company extraction fix...")
        db = SupabaseDatabase()
        
        # Step 1: Get Stage 1 data with company information
        print("\n📊 Step 1: Getting Stage 1 data with company information...")
        response = db.supabase.table('stage1_data_responses').select(
            'response_id,company,interviewee_name,verbatim_response'
        ).eq('client_id', 'Rev').execute()
        
        stage1_data = response.data
        if not stage1_data:
            print("❌ No Stage 1 data found")
            return False
        
        # Create mapping from response_id to company
        company_mapping = {}
        for response in stage1_data:
            response_id = response.get('response_id', '')
            company = response.get('company', '')
            interviewee = response.get('interviewee_name', '')
            if response_id and company:
                company_mapping[response_id] = {
                    'company': company,
                    'interviewee': interviewee
                }
        
        print(f"✅ Created company mapping for {len(company_mapping)} responses")
        
        # Step 2: Get all Stage 3 findings
        print("\n📊 Step 2: Getting Stage 3 findings...")
        response = db.supabase.table('stage3_findings').select('*').eq('client_id', 'Rev').execute()
        findings = response.data
        
        if not findings:
            print("❌ No Stage 3 findings found")
            return False
        
        print(f"✅ Found {len(findings)} Stage 3 findings to update")
        
        # Step 3: Update each finding with company information
        print("\n📊 Step 3: Updating findings with company information...")
        updated_count = 0
        
        for finding in findings:
            finding_id = finding.get('finding_id', '')
            supporting_response_ids = finding.get('supporting_response_ids', '')
            
            # Extract company information from supporting response IDs
            companies = []
            interviewees = []
            
            if supporting_response_ids:
                # Parse response IDs (could be comma-separated or JSON)
                try:
                    if supporting_response_ids.startswith('[') and supporting_response_ids.endswith(']'):
                        # JSON array format
                        import json
                        response_ids = json.loads(supporting_response_ids)
                    else:
                        # Comma-separated format
                        response_ids = [rid.strip() for rid in supporting_response_ids.split(',') if rid.strip()]
                    
                    for response_id in response_ids:
                        if response_id in company_mapping:
                            company_info = company_mapping[response_id]
                            companies.append(company_info['company'])
                            interviewees.append(company_info['interviewee'])
                except Exception as e:
                    print(f"⚠️ Error parsing response IDs for finding {finding_id}: {e}")
            
            # If no companies found from response IDs, try to extract from quotes
            if not companies:
                primary_quote = finding.get('primary_quote', '')
                secondary_quote = finding.get('secondary_quote', '')
                
                # Look for company information in quotes
                for quote in [primary_quote, secondary_quote]:
                    if quote:
                        # Try to find company information in the quote
                        for response_id, company_info in company_mapping.items():
                            if company_info['interviewee'] in quote:
                                companies.append(company_info['company'])
                                interviewees.append(company_info['interviewee'])
                                break
            
            # Update the finding with company information
            update_data = {
                'interview_company': companies[0] if companies else '',
                'companies_affected': companies,
                'interviewee_name': interviewees[0] if interviewees else finding.get('interviewee_name', ''),
                'updated_at': datetime.now().isoformat()
            }
            
            try:
                # Update the finding
                result = db.supabase.table('stage3_findings').update(update_data).eq('finding_id', finding_id).execute()
                
                if result.data:
                    updated_count += 1
                    print(f"✅ Updated finding {finding_id} with companies: {companies}")
                else:
                    print(f"⚠️ No update for finding {finding_id}")
                    
            except Exception as e:
                print(f"❌ Error updating finding {finding_id}: {e}")
        
        print(f"\n✅ Successfully updated {updated_count}/{len(findings)} findings with company information")
        
        # Step 4: Verify the updates
        print("\n📊 Step 4: Verifying updates...")
        response = db.supabase.table('stage3_findings').select('finding_id,interview_company,companies_affected').eq('client_id', 'Rev').limit(10).execute()
        updated_findings = response.data
        
        if updated_findings:
            print("Sample updated findings:")
            for finding in updated_findings[:5]:
                print(f"  Finding {finding.get('finding_id')}:")
                print(f"    Interview Company: \"{finding.get('interview_company')}\"")
                print(f"    Companies Affected: {finding.get('companies_affected')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in comprehensive fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_complete_pipeline():
    """Run the complete pipeline after fixing company extraction"""
    try:
        print("\n🚀 Running complete pipeline after company extraction fix...")
        
        # Step 1: Fix company extraction
        if not fix_company_extraction_complete():
            print("❌ Company extraction fix failed")
            return False
        
        # Step 2: Run Stage 3 analysis
        print("\n📊 Step 2: Running Stage 3 analysis...")
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
        
        print("\n✅ Complete pipeline finished successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in complete pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the complete fix and pipeline
    success = run_complete_pipeline()
    if success:
        print("\n🎉 Company extraction issue resolved and pipeline completed!")
    else:
        print("\n❌ Pipeline failed - check logs for details") 