#!/usr/bin/env python3

"""
Test script for Phase 1: Context-Driven Extraction
Verifies that the updated Stage 1 extraction prompts work correctly
"""

import os
import sys
import json
from datetime import datetime
from prompts.core_extraction import CORE_EXTRACTION_PROMPT, get_core_extraction_prompt

def test_context_driven_prompt():
    """Test the updated context-driven extraction prompt"""
    
    print("🧪 TESTING PHASE 1: CONTEXT-DRIVEN EXTRACTION")
    print("=" * 60)
    
    # Test parameters
    test_params = {
        "response_id": "TestCompany_JohnDoe_1",
        "company": "Test Company",
        "interviewee_name": "John Doe",
        "deal_status": "closed won",
        "date_of_interview": "01/01/2024",
        "chunk_text": """
        Interviewer: How do you currently handle transcription in your legal practice?
        
        John Doe: Well, we've been using a mix of approaches. For depositions, we used to rely on court reporters, but that was expensive and time-consuming. We'd have to wait sometimes weeks to get the transcripts back, and by then the case had moved on. So about two years ago, we started experimenting with digital solutions.
        
        Interviewer: What made you decide to try digital transcription?
        
        John Doe: It was really about speed and cost. We had a big case where we needed to review multiple depositions quickly, and the traditional court reporter approach just wasn't working. We were spending $3-4 per page for transcripts, and with some depositions running 200-300 pages, that adds up fast. Plus, we needed the transcripts within 24-48 hours to keep the case moving.
        
        Interviewer: How has that worked out for you?
        
        John Doe: Honestly, it's been a game-changer. We're now getting transcripts back in hours instead of weeks, and the cost is about 60% less. The accuracy is actually better than what we were getting from some court reporters, especially for technical legal terms. We've been able to handle more cases simultaneously because we're not waiting on transcripts anymore.
        
        Interviewer: What about the quality and accuracy?
        
        John Doe: That was our biggest concern initially. We started with a pilot program on smaller cases, maybe 10-15 depositions, and we were pleasantly surprised. The accuracy rate is consistently above 95%, and for legal terminology, it's actually better than human transcription because it doesn't get tired or distracted. We've had cases where the AI caught nuances that human transcribers missed.
        """
    }
    
    # Generate prompt
    generated_prompt = get_core_extraction_prompt(**test_params)
    
    print("✅ Generated prompt successfully")
    print(f"📏 Prompt length: {len(generated_prompt)} characters")
    
    # Check for key improvements
    improvements = [
        ("CRITICAL FIELD DEFINITIONS", "Field definitions added"),
        ("SUBJECT: The main topic or area being discussed", "Subject definition clear"),
        ("QUESTION: The actual question that was asked", "Question definition clear"),
        ("✅ CORRECT:", "Correct examples provided"),
        ("❌ INCORRECT:", "Incorrect examples provided"),
        ("Question Format: Must be an actual question", "Question format requirement"),
        ("How do you currently use the product?", "Proper question example"),
        ("What challenges did you face during setup?", "Proper question example")
    ]
    
    print("\n🔍 CHECKING IMPROVEMENTS:")
    print("-" * 40)
    
    all_passed = True
    for check, description in improvements:
        if check in generated_prompt:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False
    
    return all_passed

def test_field_distinction():
    """Test that the prompt clearly distinguishes between subject and question fields"""
    
    print("\n🎯 TESTING FIELD DISTINCTION")
    print("=" * 40)
    
    # Check for clear field definitions
    field_checks = [
        ("SUBJECT: The main topic or area being discussed", "Subject definition"),
        ("QUESTION: The actual question that was asked", "Question definition"),
        ("Subject: \"Product Features\"", "Subject example"),
        ("Question: \"How do you use Rev in your daily workflow?\"", "Question example"),
        ("Question: \"Feedback on product features and their importance\" (This is a subject description, not a question)", "Incorrect example"),
        ("Question Format: Must be an actual question (interrogative format), not a description", "Format requirement")
    ]
    
    all_passed = True
    for check, description in field_checks:
        if check in CORE_EXTRACTION_PROMPT:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False
    
    return all_passed

def test_prompt_consistency():
    """Test that all Stage 1 prompts are consistent"""
    
    print("\n🔍 TESTING PROMPT CONSISTENCY")
    print("=" * 40)
    
    # Check if the main prompt file is updated
    with open("prompts/core_extraction.py", "r") as f:
        core_prompt_content = f.read()
    
    # Check if processor.py is updated
    with open("voc_pipeline/processor.py", "r") as f:
        processor_content = f.read()
    
    # Check for context-driven language in both files
    core_has_context = "CONTEXT-DRIVEN EXTRACTION" in core_prompt_content
    processor_has_context = "CONTEXT-DRIVEN EXTRACTION" in processor_content
    
    print(f"Core extraction prompt updated: {'✅' if core_has_context else '❌'}")
    print(f"Processor prompt updated: {'✅' if processor_has_context else '❌'}")
    
    if core_has_context and processor_has_context:
        print("✅ All Stage 1 prompts are consistent")
        return True
    else:
        print("❌ Stage 1 prompts are inconsistent")
        return False

def test_quantity_guidance():
    """Test that the prompt provides proper quantity guidance"""
    
    print("\n📊 TESTING QUANTITY GUIDANCE")
    print("=" * 40)
    
    quantity_checks = [
        ("quantity varies by content quality", "Variable quantity guidance"),
        ("Extract 1-8 responses based on the richness", "Quantity range specified"),
        ("Some chunks may have 2 valuable Q&A pairs, others may have 8", "Variable output explanation"),
        ("Variable Output: Some chunks may produce 2 responses, others 8", "Output variability"),
        ("let the content guide you", "Content-driven approach")
    ]
    
    all_passed = True
    for check, description in quantity_checks:
        if check in CORE_EXTRACTION_PROMPT:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    
    print("🚀 PHASE 1: CONTEXT-DRIVEN EXTRACTION TEST SUITE")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Context-Driven Prompt", test_context_driven_prompt),
        ("Field Distinction", test_field_distinction),
        ("Prompt Consistency", test_prompt_consistency),
        ("Quantity Guidance", test_quantity_guidance)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 50)
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Phase 1 implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 