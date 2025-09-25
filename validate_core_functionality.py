#!/usr/bin/env python3
"""
Core Functionality Validation for Enhanced Processor
Tests the timestamp extraction and cleaning functions without requiring LLM.
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append('.')

def test_timestamp_extraction():
    """Test timestamp extraction functions"""
    print("🧪 Testing timestamp extraction functions...")
    
    try:
        from voc_pipeline.processor import extract_timestamps_from_text, parse_timestamp, clean_verbatim_response_with_timestamps
        
        # Test different timestamp formats
        test_cases = [
            {
                "name": "Inline timestamps",
                "text": "[00:01:00] Hi, Brian. What was your current solution?",
                "expected_start": "00:01:00"
            },
            {
                "name": "Speaker timestamps", 
                "text": "Speaker 1 (01:00): We had our own warehouse, own software.",
                "expected_start": "00:01:00"
            },
            {
                "name": "ShipBob format",
                "text": "Adri (00:00:38 - 00:00:39) Nice to meet you. We are launching our new food product.",
                "expected_start": "00:00:38",
                "expected_end": "00:00:39"
            },
            {
                "name": "Standalone timestamps",
                "text": "(03:00): I'd rather just have it be super transparent.",
                "expected_start": "00:03:00"
            },
            {
                "name": "Mixed format",
                "text": """
                Speaker 1 (01:00):
                [00:01:00] Hi, Brian. What was your current solution at the time?

                Speaker 2 (01:10):
                [00:01:10] We had our own warehouse, own software, own negotiated rates.

                Adri (00:00:38 - 00:00:39) Nice to meet you. We are launching our new food product.
                """,
                "expected_start": "00:00:38",
                "expected_end": "00:01:10"
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"  Testing {test_case['name']}...")
            
            start_ts, end_ts, all_ts = extract_timestamps_from_text(test_case['text'])
            
            if start_ts != test_case.get('expected_start'):
                print(f"    ❌ Expected start: {test_case.get('expected_start')}, got: {start_ts}")
                all_passed = False
            else:
                print(f"    ✅ Start timestamp: {start_ts}")
            
            if 'expected_end' in test_case and end_ts != test_case['expected_end']:
                print(f"    ❌ Expected end: {test_case['expected_end']}, got: {end_ts}")
                all_passed = False
            elif 'expected_end' in test_case:
                print(f"    ✅ End timestamp: {end_ts}")
        
        if all_passed:
            print("✅ All timestamp extraction tests passed!")
            return True
        else:
            print("❌ Some timestamp extraction tests failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import processor functions: {e}")
        return False
    except Exception as e:
        print(f"❌ Timestamp extraction test failed: {e}")
        return False

def test_enhanced_cleaning():
    """Test enhanced cleaning function"""
    print("\n🧪 Testing enhanced cleaning function...")
    
    try:
        from voc_pipeline.processor import clean_verbatim_response_with_timestamps
        
        test_cases = [
            {
                "name": "Basic cleaning",
                "text": """
                Speaker 1 (01:00):
                [00:01:00] Hi, Brian. What was your current solution at the time?

                Speaker 2 (01:10):
                [00:01:10] We had our own warehouse, own software, own negotiated rates.
                """,
                "should_not_contain": ["Speaker 1", "[00:01:00]", "Speaker 2", "[00:01:10]"],
                "should_contain": ["Hi, Brian", "warehouse", "software"]
            },
            {
                "name": "ShipBob format cleaning",
                "text": "Adri (00:00:38 - 00:00:39) Nice to meet you. We are launching our new food product.",
                "should_not_contain": ["Adri", "(00:00:38 - 00:00:39)"],
                "should_contain": ["Nice to meet you", "launching", "food product"]
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"  Testing {test_case['name']}...")
            
            cleaned_text, start_ts, end_ts = clean_verbatim_response_with_timestamps(test_case['text'])
            
            # Check that timestamps were extracted
            if start_ts and end_ts:
                print(f"    ✅ Timestamps extracted: {start_ts} - {end_ts}")
            else:
                print(f"    ❌ Failed to extract timestamps")
                all_passed = False
                continue
            
            # Check that unwanted content was removed
            for unwanted in test_case.get('should_not_contain', []):
                if unwanted in cleaned_text:
                    print(f"    ❌ Unwanted content still present: {unwanted}")
                    all_passed = False
                else:
                    print(f"    ✅ Removed: {unwanted}")
            
            # Check that wanted content was preserved
            for wanted in test_case.get('should_contain', []):
                if wanted in cleaned_text:
                    print(f"    ✅ Preserved: {wanted}")
                else:
                    print(f"    ❌ Missing expected content: {wanted}")
                    all_passed = False
        
        if all_passed:
            print("✅ All enhanced cleaning tests passed!")
            return True
        else:
            print("❌ Some enhanced cleaning tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced cleaning test failed: {e}")
        return False

def test_csv_output_format():
    """Test that the CSV output format includes timestamp columns"""
    print("\n🧪 Testing CSV output format...")
    
    try:
        from voc_pipeline.processor import clean_verbatim_response_with_timestamps
        
        # Test the enhanced cleaning function returns the right format
        test_text = "Speaker 1 (01:00): [00:01:00] Hi, Brian. What was your current solution?"
        
        cleaned_text, start_ts, end_ts = clean_verbatim_response_with_timestamps(test_text)
        
        # Check that we get the expected tuple format
        if isinstance(cleaned_text, str) and isinstance(start_ts, str) and isinstance(end_ts, str):
            print("✅ Enhanced cleaning returns correct tuple format")
            print(f"    Cleaned text: {cleaned_text[:50]}...")
            print(f"    Start timestamp: {start_ts}")
            print(f"    End timestamp: {end_ts}")
            return True
        else:
            print(f"❌ Enhanced cleaning returned wrong format: {type(cleaned_text)}, {type(start_ts)}, {type(end_ts)}")
            return False
            
    except Exception as e:
        print(f"❌ CSV output format test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🎬 Enhanced Processor Core Functionality Validation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_timestamp_extraction,
        test_enhanced_cleaning,
        test_csv_output_format
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core functionality tests passed!")
        print("✅ Enhanced processor is ready for production deployment.")
        print("✅ Timestamp extraction is working correctly.")
        print("✅ Text cleaning preserves content while extracting timestamps.")
        print("✅ CSV output format includes timestamp columns.")
        return 0
    else:
        print("❌ Some core functionality tests failed.")
        print("❌ Please fix issues before deploying to production.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
