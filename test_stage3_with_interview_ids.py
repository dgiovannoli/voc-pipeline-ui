#!/usr/bin/env python3

from supabase_database import SupabaseDatabase
from stage3_findings_analyzer import Stage3FindingsAnalyzer

def test_stage3_with_interview_ids():
    """Test Stage 3 analysis with properly linked interview IDs"""
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    # Check Stage 1 data with interview IDs
    print("🔍 Checking Stage 1 data with interview IDs...")
    try:
        stage1_response = db.supabase.table('stage1_data_responses').select('*').eq('client_id', 'Rev').not_.is_('interview_id', 'null').execute()
        stage1_records = len(stage1_response.data)
        print(f"📊 Found {stage1_records} Stage 1 records with interview IDs")
        
        if stage1_records > 0:
            # Show sample records
            print(f"\n📋 Sample Stage 1 records with interview IDs:")
            for i, record in enumerate(stage1_response.data[:5]):
                print(f"  {i+1}. Interview ID: {record.get('interview_id')}, Interviewee: {record.get('interviewee_name')}, Company: {record.get('company')}")
        
    except Exception as e:
        print(f"❌ Error checking Stage 1 data: {e}")
        return False
    
    # Test Stage 3 analysis
    print(f"\n🎯 Testing Stage 3 analysis for client Rev...")
    try:
        analyzer = Stage3FindingsAnalyzer()
        
        # Run Stage 3 analysis
        result = analyzer.process_stage3_findings('Rev')
        
        if result:
            print(f"✅ Stage 3 analysis completed successfully!")
            print(f"📊 Analysis result: {result}")
        else:
            print(f"❌ Stage 3 analysis failed")
            
    except Exception as e:
        print(f"❌ Error running Stage 3 analysis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Stage 3 with interview ID linking...")
    success = test_stage3_with_interview_ids()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!") 