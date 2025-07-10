#!/usr/bin/env python3
"""
Debug script to check stage3_findings data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_database import SupabaseDatabase

def debug_stage3_findings():
    """Debug enhanced findings data"""
    
    print("🔍 Debugging Enhanced Findings")
    print("=" * 50)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Get enhanced findings
    findings_df = db.get_stage3_findings(client_id='Rev')
    
    if findings_df.empty:
        print("❌ No enhanced findings found")
        return
    
    print(f"✅ Found {len(findings_df)} enhanced findings")
    
    # Check each finding
    for i, (_, finding) in enumerate(findings_df.iterrows(), 1):
        print(f"\n🔍 Finding {i}: {finding['criterion']} - {finding['finding_type']}")
        
        # Check selected_quotes field
        if 'selected_quotes' in finding:
            selected_quotes = finding['selected_quotes']
            print(f"   📝 selected_quotes type: {type(selected_quotes)}")
            
            if isinstance(selected_quotes, list):
                print(f"   ✅ selected_quotes is a list with {len(selected_quotes)} items")
                
                if selected_quotes:
                    print(f"   📋 First quote: {selected_quotes[0]}")
                    
                    # Check quote structure
                    first_quote = selected_quotes[0]
                    if isinstance(first_quote, dict):
                        print(f"   ✅ Quote is a dictionary with keys: {list(first_quote.keys())}")
                        print(f"   📄 Quote text: {first_quote.get('text', 'No text')[:100]}...")
                    else:
                        print(f"   ❌ Quote is not a dictionary: {type(first_quote)}")
                else:
                    print(f"   ⚠️ selected_quotes list is empty")
            else:
                print(f"   ❌ selected_quotes is not a list: {type(selected_quotes)}")
                if isinstance(selected_quotes, str):
                    print(f"   📄 selected_quotes as string: {selected_quotes[:200]}...")
        else:
            print(f"   ❌ No 'selected_quotes' field found")
            print(f"   📋 Available fields: {list(finding.keys())}")

if __name__ == "__main__":
    debug_stage3_findings() 