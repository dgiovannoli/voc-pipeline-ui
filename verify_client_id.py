#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

load_dotenv()

def verify_client_id_consistency():
    """Verify that client_id is working correctly across all tables"""
    
    print("🔍 VERIFYING CLIENT ID CONSISTENCY")
    print("=" * 50)
    
    try:
        db = SupabaseDatabase()
        
        # Check all tables for client_id distribution
        tables = ['core_responses', 'quote_analysis', 'enhanced_findings', 'themes']
        
        for table in tables:
            print(f"\n📊 {table.upper()} TABLE:")
            print("-" * 30)
            
            try:
                # Get all records from the table
                result = db.supabase.table(table).select('client_id').execute()
                records = result.data
                
                if not records:
                    print(f"  No records found in {table}")
                    continue
                
                # Count by client_id
                client_counts = {}
                for record in records:
                    client_id = record.get('client_id', 'missing')
                    client_counts[client_id] = client_counts.get(client_id, 0) + 1
                
                # Display counts
                for client_id, count in client_counts.items():
                    print(f"  {client_id}: {count} records")
                
                # Check for issues
                if 'default' in client_counts:
                    print(f"  ⚠️  Found {client_counts['default']} records with 'default' client_id")
                
                if 'missing' in client_counts:
                    print(f"  ⚠️  Found {client_counts['missing']} records with missing client_id")
                
            except Exception as e:
                print(f"  ❌ Error checking {table}: {e}")
        
        # Test client_id filtering
        print(f"\n🧪 TESTING CLIENT ID FILTERING:")
        print("-" * 30)
        
        # Test with 'Rev' client_id
        print("Testing 'Rev' client_id filtering:")
        
        # Core responses
        core_df = db.get_core_responses(client_id='Rev')
        print(f"  Core responses: {len(core_df)} records")
        
        # Quote analysis
        quote_df = db.get_quote_analysis(client_id='Rev')
        print(f"  Quote analysis: {len(quote_df)} records")
        
        # Enhanced findings
        findings_df = db.get_enhanced_findings(client_id='Rev')
        print(f"  Enhanced findings: {len(findings_df)} records")
        
        # Themes
        themes_df = db.get_themes(client_id='Rev')
        print(f"  Themes: {len(themes_df)} records")
        
        # Test with 'default' client_id (should be empty now)
        print("\nTesting 'default' client_id filtering (should be empty):")
        
        core_df_default = db.get_core_responses(client_id='default')
        print(f"  Core responses: {len(core_df_default)} records")
        
        quote_df_default = db.get_quote_analysis(client_id='default')
        print(f"  Quote analysis: {len(quote_df_default)} records")
        
        findings_df_default = db.get_enhanced_findings(client_id='default')
        print(f"  Enhanced findings: {len(findings_df_default)} records")
        
        themes_df_default = db.get_themes(client_id='default')
        print(f"  Themes: {len(themes_df_default)} records")
        
        # Summary
        print(f"\n✅ VERIFICATION SUMMARY:")
        print("-" * 30)
        
        if len(findings_df_default) == 0:
            print("✅ All 'default' findings have been successfully updated to 'Rev'")
        else:
            print(f"⚠️  {len(findings_df_default)} findings still have 'default' client_id")
        
        if len(findings_df) > 0:
            print(f"✅ Found {len(findings_df)} findings for 'Rev' client_id")
        else:
            print("⚠️  No findings found for 'Rev' client_id")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 30)
        print("1. Always set client_id in the Streamlit sidebar before running analysis")
        print("2. Use the enhanced client_id validation in the app")
        print("3. Check the database status page to verify client_id filtering")
        print("4. If you see 'default' client_id data, run the fix script again")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    verify_client_id_consistency() 