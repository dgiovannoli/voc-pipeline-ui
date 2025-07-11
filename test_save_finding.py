#!/usr/bin/env python3
"""
Test script to try saving a single finding and debug the issue
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase
import json

load_dotenv()

def test_save_finding():
    """Test saving a single finding"""
    try:
        print("🔍 Testing finding save...")
        db = SupabaseDatabase()
        
        # Create a simple test finding
        test_finding = {
            'finding_id': 'TEST_001',
            'finding_statement': 'This is a test finding to debug the save issue',
            'interview_company': 'Test Company',
            'deal_status': 'closed won',
            'interviewee_name': 'Test User',
            'supporting_response_ids': 'TEST_RESPONSE_001',
            'evidence_strength': 3,
            'finding_category': 'Test Category',
            'criteria_met': 2,
            'priority_level': 'Standard Finding',
            'primary_quote': 'This is a test quote',
            'secondary_quote': '',
            'quote_attributions': 'Primary: TEST_001 - Test User',
            'criterion': 'test_criterion',
            'finding_type': 'test_type',
            'enhanced_confidence': 5.0,
            'criteria_scores': {'test': 1},
            'impact_score': 3.0,
            'companies_affected': 1,
            'quote_count': 1,
            'selected_quotes': [{'text': 'Test quote', 'response_id': 'TEST_001'}],
            'themes': ['test_theme'],
            'deal_impacts': {'test': 'impact'},
            'generated_at': '2025-01-11T16:45:00',
            'evidence_threshold_met': True,
            'evidence_strength_score': 3,
            'criteria_covered': 'test_criterion',
            'credibility_tier': 'High',
            'title': 'Test Finding',
            'description': 'This is a test finding description',
            'client_id': 'Rev'
        }
        
        print("📝 Test finding data:")
        for key, value in test_finding.items():
            print(f"  {key}: {value}")
        
        # Try to save the finding
        print("\n💾 Attempting to save finding...")
        success = db.save_enhanced_finding(test_finding, client_id='Rev')
        
        if success:
            print("✅ Save operation reported success")
        else:
            print("❌ Save operation reported failure")
        
        # Check if it was actually saved
        print("\n🔍 Checking if finding was actually saved...")
        result = db.supabase.table('stage3_findings').select('*').eq('client_id', 'Rev').eq('finding_id', 'TEST_001').execute()
        
        if result.data:
            print("✅ Finding was successfully saved to database")
            saved_finding = result.data[0]
            print(f"  - finding_id: {saved_finding.get('finding_id')}")
            print(f"  - client_id: {saved_finding.get('client_id')}")
            print(f"  - finding_statement: {saved_finding.get('finding_statement')}")
        else:
            print("❌ Finding was NOT saved to database")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        db.supabase.table('stage3_findings').delete().eq('finding_id', 'TEST_001').eq('client_id', 'Rev').execute()
        print("✅ Test data cleaned up")
        
        print("\n✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_finding() 