#!/usr/bin/env python3
"""
Purge old findings that don't meet credibility standards
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def purge_old_findings():
    """Purge findings created before credibility enforcement"""
    
    print("🧹 Purging old findings that don't meet credibility standards...")
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Get all findings
    findings_df = db.get_enhanced_findings('Rev')
    
    if findings_df.empty:
        print("✅ No findings to purge")
        return
    
    print(f"📊 Found {len(findings_df)} total findings")
    
    # Define the cutoff time (when credibility enforcement was implemented)
    # The new findings were created around 23:57-23:58, so we'll keep those
    cutoff_time = datetime.fromisoformat("2025-07-06T23:50:00")
    
    # Identify old findings to purge
    old_findings = []
    new_findings = []
    
    for _, finding in findings_df.iterrows():
        created_at = datetime.fromisoformat(finding['created_at'].replace('Z', '+00:00'))
        if created_at < cutoff_time:
            old_findings.append(finding['id'])
        else:
            new_findings.append(finding['id'])
    
    print(f"🗑️  Found {len(old_findings)} old findings to purge")
    print(f"✅ Found {len(new_findings)} new credible findings to keep")
    
    if not old_findings:
        print("✅ No old findings to purge")
        return
    
    # Purge old findings
    try:
        for finding_id in old_findings:
            response = db.supabase.table('enhanced_findings').delete().eq('id', finding_id).execute()
            print(f"🗑️  Purged finding ID: {finding_id}")
        
        print(f"✅ Successfully purged {len(old_findings)} old findings")
        
        # Verify the purge
        remaining_findings = db.get_enhanced_findings('Rev')
        print(f"📊 Remaining findings: {len(remaining_findings)}")
        
    except Exception as e:
        print(f"❌ Error purging findings: {e}")

if __name__ == "__main__":
    purge_old_findings() 