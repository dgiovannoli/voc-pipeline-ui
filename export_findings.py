#!/usr/bin/env python3
"""
Export findings for comparison with gold standard
"""

from supabase_database import SupabaseDatabase
import pandas as pd

def export_findings():
    db = SupabaseDatabase()
    findings_df = db.get_stage3_findings(client_id='Rev')
    
    print("=== CURRENT FINDINGS (Rev Client) ===")
    print(f"Total findings: {len(findings_df)}")
    print()
    
    if findings_df.empty:
        print("No findings found.")
        return
    
    for i, (idx, row) in enumerate(findings_df.iterrows(), 1):
        statement = row.get('description', 'N/A')  # Use description field
        finding_type = row.get('finding_type', 'N/A')
        priority = row.get('priority_level', 'N/A')
        confidence = row.get('enhanced_confidence', 'N/A')
        criteria_met = row.get('criteria_met', 'N/A')
        
        print(f"F{i}: {statement}")
        print(f"   Type: {finding_type}, Priority: {priority}, Confidence: {confidence}, Criteria Met: {criteria_met}")
        print()

if __name__ == "__main__":
    export_findings() 