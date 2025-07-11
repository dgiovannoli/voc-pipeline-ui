#!/usr/bin/env python3
"""
Debug script to check what's actually in the stage3_findings table
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

load_dotenv()

def debug_supabase_findings():
    """Debug what's in the stage3_findings table"""
    try:
        print("🔍 Debugging Supabase findings...")
        db = SupabaseDatabase()
        
        # Get ALL findings (no client filter)
        print("\n📊 Getting ALL findings from stage3_findings table...")
        result = db.supabase.table('stage3_findings').select('*').execute()
        all_findings = result.data
        print(f"✅ Found {len(all_findings)} total findings in table")
        
        if all_findings:
            print("\n📋 Sample findings:")
            for i, finding in enumerate(all_findings[:5]):  # Show first 5
                print(f"  Finding {i+1}:")
                print(f"    - finding_id: {finding.get('finding_id')}")
                print(f"    - client_id: {finding.get('client_id')}")
                print(f"    - finding_statement: {finding.get('finding_statement', '')[:50]}...")
                print(f"    - enhanced_confidence: {finding.get('enhanced_confidence')}")
                print()
        
        # Check findings by client
        print("\n📊 Checking findings by client...")
        clients = db.supabase.table('stage3_findings').select('client_id').execute()
        unique_clients = set(finding['client_id'] for finding in clients.data)
        print(f"✅ Found clients: {unique_clients}")
        
        for client in unique_clients:
            client_findings = db.supabase.table('stage3_findings').select('*').eq('client_id', client).execute()
            print(f"  - Client '{client}': {len(client_findings.data)} findings")
        
        # Test the get_stage3_findings method
        print("\n🔍 Testing get_stage3_findings method...")
        for client in ['Rev', 'default']:
            findings_df = db.get_stage3_findings(client_id=client)
            print(f"  - get_stage3_findings('{client}'): {len(findings_df)} findings")
        
        # Check for any finding_id duplicates
        print("\n🔍 Checking for finding_id duplicates...")
        finding_ids = [finding['finding_id'] for finding in all_findings]
        duplicates = set([x for x in finding_ids if finding_ids.count(x) > 1])
        if duplicates:
            print(f"❌ Found duplicate finding_ids: {duplicates}")
        else:
            print("✅ No duplicate finding_ids found")
        
        print("\n✅ Debug completed")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_supabase_findings() 