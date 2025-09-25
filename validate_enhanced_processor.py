#!/usr/bin/env python3
"""
Production Validation Script for Enhanced Processor with Timestamp Extraction
Tests the enhanced processor to ensure it's working correctly in production.
"""

import sys
import os
import tempfile
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
        
        test_text = """
        Speaker 1 (01:00):
        [00:01:00] Hi, Brian. What was your current solution at the time?

        Speaker 2 (01:10):
        [00:01:10] We had our own warehouse, own software, own negotiated rates.
        """
        
        cleaned_text, start_ts, end_ts = clean_verbatim_response_with_timestamps(test_text)
        
        # Check that timestamps were extracted
        if start_ts and end_ts:
            print(f"✅ Timestamps extracted: {start_ts} - {end_ts}")
        else:
            print("❌ Failed to extract timestamps")
            return False
        
        # Check that text was cleaned
        if "Speaker 1" not in cleaned_text and "[00:01:00]" not in cleaned_text:
            print("✅ Text cleaned successfully")
        else:
            print("❌ Text cleaning failed")
            return False
        
        print("✅ Enhanced cleaning function test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced cleaning test failed: {e}")
        return False

def test_full_processor():
    """Test the full processor with a sample transcript"""
    print("\n🧪 Testing full processor...")
    
    try:
        from voc_pipeline.processor import process_transcript
        
        # Create a test transcript file
        test_transcript = """
        Speaker 1 (01:00):
        [00:01:00] Hi, Brian. Thanks for taking the time to speak with us today. Can you tell us about your current solution?

        Speaker 2 (01:10):
        [00:01:10] We had our own warehouse, own software, own negotiated rates. It was working well for a while.

        Speaker 1 (01:15):
        [00:01:15] And what prompted you to consider options outside of that?

        Speaker 2 (01:20):
        [00:01:20] We're at the point where I either need to open up other warehouses or find someone that has a three PL network.
        """
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_transcript)
            temp_path = f.name
        
        try:
            # Process the transcript
            result = process_transcript(
                transcript_path=temp_path,
                client="test_client",
                company="Test Company",
                interviewee="Test Person",
                deal_status="Won",
                date_of_interview="2024-01-15"
            )
            
            if result and "start_timestamp" in result and "end_timestamp" in result:
                print("✅ Full processor test passed!")
                print(f"✅ Result contains timestamp columns")
                return True
            else:
                print("❌ Full processor test failed - no timestamp columns in output")
                return False
                
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ Full processor test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🎬 Enhanced Processor Production Validation")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_timestamp_extraction,
        test_enhanced_cleaning,
        test_full_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced processor is ready for production.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deploying to production.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
