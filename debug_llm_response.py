#!/usr/bin/env python3
"""
Debug script to examine LLM response and fix parsing issues
"""

import os
import json
import pandas as pd
from enhanced_stage2_analyzer import SupabaseStage2Analyzer

def debug_llm_response():
    """Debug the LLM response parsing issue"""
    print("🔍 Debugging LLM Response Parsing")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = SupabaseStage2Analyzer(batch_size=1, max_workers=1)
    
    # Test with a simple quote
    test_quote = {
        'response_id': 'debug_test_1',
        'verbatim_response': 'I love the accuracy of the transcription service. It saves me hours every week.',
        'subject': 'Transcription Accuracy',
        'company': 'Test Law Firm',
        'interviewee_name': 'Test Attorney'
    }
    
    test_df = pd.DataFrame([test_quote])
    
    # Prepare batch text
    batch_text = analyzer._prepare_batch_for_llm(test_df)
    print(f"📝 Batch text length: {len(batch_text)}")
    print(f"📝 Batch text preview: {batch_text[:200]}...")
    
    try:
        # Call LLM
        print("\n🤖 Calling LLM...")
        llm_response = analyzer._call_llm_batch(batch_text)
        
        print(f"\n📄 Raw LLM Response:")
        print(f"Length: {len(llm_response)} characters")
        print(f"Response:\n{llm_response}")
        
        # Test cleaning
        print(f"\n🧹 Testing response cleaning...")
        cleaned_response = analyzer._clean_llm_response(llm_response)
        print(f"Cleaned response:\n{cleaned_response}")
        
        # Test JSON parsing
        print(f"\n🔧 Testing JSON parsing...")
        try:
            parsed_json = json.loads(cleaned_response)
            print(f"✅ JSON parsing successful!")
            print(f"Type: {type(parsed_json)}")
            if isinstance(parsed_json, list):
                print(f"Length: {len(parsed_json)}")
                if parsed_json:
                    print(f"First item: {parsed_json[0]}")
            else:
                print(f"Content: {parsed_json}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Error position: {e.pos}")
            print(f"Error line: {e.lineno}")
            print(f"Error column: {e.colno}")
            
            # Try to find the issue
            lines = cleaned_response.split('\n')
            if e.lineno <= len(lines):
                print(f"Problematic line {e.lineno}: {lines[e.lineno-1]}")
        
        # Test full parsing
        print(f"\n🔧 Testing full parsing...")
        parsed_results = analyzer._parse_llm_batch_response(llm_response, test_df)
        print(f"Parsed results: {len(parsed_results) if parsed_results else 0}")
        if parsed_results:
            print(f"First result: {parsed_results[0]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_response() 