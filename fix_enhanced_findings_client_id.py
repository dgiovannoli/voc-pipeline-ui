#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

load_dotenv()

def fix_stage3_findings_client_id():
    """Fix client_id issues in stage3_findings table"""
    
    print("🔧 FIXING ENHANCED FINDINGS CLIENT ID")
    print("=" * 50)
    
    try:
        db = SupabaseDatabase()
        
        # Get all findings with 'default' client_id
        print("📊 Finding all 'default' client_id findings...")
        result = db.supabase.table('stage3_findings').select('*').eq('client_id', 'default').execute()
        default_findings = result.data
        
        if not default_findings:
            print("✅ No findings with 'default' client_id found")
            return
        
        print(f"🔍 Found {len(default_findings)} findings with 'default' client_id")
        
        # Update all 'default' findings to 'Rev'
        print("🔄 Updating all 'default' findings to 'Rev'...")
        
        for finding in default_findings:
            finding_id = finding['id']
            update_data = {'client_id': 'Rev'}
            
            try:
                db.supabase.table('stage3_findings').update(update_data).eq('id', finding_id).execute()
                print(f"✅ Updated finding {finding_id}: {finding.get('title', 'N/A')}")
            except Exception as e:
                print(f"❌ Failed to update finding {finding_id}: {e}")
        
        print(f"\n✅ Successfully updated {len(default_findings)} findings from 'default' to 'Rev'")
        
        # Verify the fix
        print("\n🔍 Verifying the fix...")
        result = db.supabase.table('stage3_findings').select('*').eq('client_id', 'default').execute()
        remaining_default = len(result.data)
        
        if remaining_default == 0:
            print("✅ All 'default' findings have been successfully updated to 'Rev'")
        else:
            print(f"⚠️  {remaining_default} findings still have 'default' client_id")
        
        # Show final distribution
        print("\n📊 Final client_id distribution:")
        result = db.supabase.table('stage3_findings').select('client_id').execute()
        all_findings = result.data
        
        client_counts = {}
        for finding in all_findings:
            client_id = finding['client_id']
            client_counts[client_id] = client_counts.get(client_id, 0) + 1
        
        for client_id, count in client_counts.items():
            print(f"  {client_id}: {count} findings")
        
    except Exception as e:
        print(f"❌ Error fixing client ID issues: {e}")

if __name__ == "__main__":
    fix_stage3_findings_client_id() 