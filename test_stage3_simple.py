#!/usr/bin/env python3
"""
Simple test script to isolate Stage 3 issues
"""

import logging
import sys
from supabase_database import SupabaseDatabase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stage3_components():
    """Test each component of Stage 3 separately"""
    
    print("🔍 Testing Stage 3 Components...")
    
    # Test 1: Database connection
    print("\n1. Testing database connection...")
    try:
        db = SupabaseDatabase()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test 2: Get data
    print("\n2. Testing data retrieval...")
    try:
        df = db.get_stage1_data_responses(client_id='Rev')
        print(f"✅ Retrieved {len(df)} responses")
        if len(df) > 0:
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Sample: {df.head(1).to_dict('records')}")
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return
    
    # Test 3: Load prompt
    print("\n3. Testing prompt loading...")
    try:
        from stage3_findings_analyzer import Stage3FindingsAnalyzer
        analyzer = Stage3FindingsAnalyzer()
        prompt = analyzer.load_llm_prompt()
        print(f"✅ Prompt loaded successfully, length: {len(prompt)} chars")
    except Exception as e:
        print(f"❌ Prompt loading failed: {e}")
        return
    
    # Test 4: Test with minimal data
    print("\n4. Testing with minimal data...")
    try:
        # Take just 2 responses for testing
        test_df = df.head(2)
        print(f"   Testing with {len(test_df)} responses")
        
        # Create minimal CSV
        essential_cols = ['response_id', 'verbatim_response', 'question', 'company', 'interviewee_name', 'interview_date', 'client_id']
        test_df_minimal = test_df[essential_cols].copy()
        csv_data = test_df_minimal.to_csv(index=False)
        print(f"   CSV length: {len(csv_data)} chars")
        
        # Test LLM call with minimal data
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model_name="gpt-4o-mini", max_tokens=4000, temperature=0.3)
        
        short_prompt = """Analyze this CSV data and identify any recurring patterns. Return a simple JSON with findings.

CSV Data:
{csv_data}

Return JSON with format: {{"findings_csv": "F1,Test finding,Company,2024-01-01,won,Name,1,2,Test,1,2,3,standard,quote,quote,attribution"}}"""
        
        full_prompt = short_prompt.format(csv_data=csv_data)
        print(f"   Full prompt length: {len(full_prompt)} chars")
        
        response = llm.invoke(full_prompt)
        print(f"✅ LLM call successful")
        print(f"   Response length: {len(response.content)} chars")
        print(f"   Response preview: {response.content[:200]}...")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_stage3_components() 