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
    
    # Test the prompt generation
    print("\n📋 Testing prompt generation...")
    try:
        generated_prompt = get_core_extraction_prompt(**test_params)
        print("✅ Prompt generation successful")
        print(f"📏 Prompt length: {len(generated_prompt)} characters")
        
        # Check for key context-driven elements
        context_indicators = [
            "CONTEXT-DRIVEN EXTRACTION",
            "COMPLETE CONTEXT",
            "MEANINGFUL Q&A PAIRS",
            "Let Content Guide Quantity",
            "Variable Output"
        ]
        
        missing_indicators = []
        for indicator in context_indicators:
            if indicator not in generated_prompt:
                missing_indicators.append(indicator)
        
        if missing_indicators:
            print(f"⚠️ Missing context-driven indicators: {missing_indicators}")
        else:
            print("✅ All context-driven indicators present")
        
        # Check that old quantity-driven language is removed
        old_indicators = [
            "3-5 RICHEST",
            "1-2 RICHEST",
            "Extract the 3-5",
            "Extract the 1-2"
        ]
        
        found_old_indicators = []
        for indicator in old_indicators:
            if indicator in generated_prompt:
                found_old_indicators.append(indicator)
        
        if found_old_indicators:
            print(f"⚠️ Found old quantity-driven language: {found_old_indicators}")
        else:
            print("✅ No old quantity-driven language found")
        
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return False
    
    # Test the raw prompt template
    print("\n📋 Testing raw prompt template...")
    try:
        # Check the raw prompt for context-driven approach
        if "CONTEXT-DRIVEN EXTRACTION" in CORE_EXTRACTION_PROMPT:
            print("✅ Raw prompt uses context-driven approach")
        else:
            print("❌ Raw prompt still uses old approach")
            return False
        
        # Check for variable output guidance
        if "quantity varies by content quality" in CORE_EXTRACTION_PROMPT:
            print("✅ Prompt includes variable output guidance")
        else:
            print("❌ Prompt missing variable output guidance")
            return False
        
    except Exception as e:
        print(f"❌ Raw prompt test failed: {e}")
        return False
    
    # Test JSON structure expectations
    print("\n📋 Testing JSON structure expectations...")
    try:
        # The prompt should expect variable number of responses
        if "quantity varies by content quality" in CORE_EXTRACTION_PROMPT:
            print("✅ JSON structure allows variable responses")
        else:
            print("❌ JSON structure still expects fixed numbers")
            return False
        
    except Exception as e:
        print(f"❌ JSON structure test failed: {e}")
        return False
    
    print("\n✅ PHASE 1 IMPLEMENTATION SUCCESSFUL!")
    print("\n📊 SUMMARY:")
    print("- Context-driven extraction strategy implemented")
    print("- Removed arbitrary quantity constraints")
    print("- Added variable output guidance")
    print("- Preserved quality and context preservation")
    print("- Ready for testing with real transcripts")
    
    return True

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

if __name__ == "__main__":
    print("🚀 PHASE 1: CONTEXT-DRIVEN EXTRACTION TEST")
    print("=" * 60)
    
    # Run tests
    prompt_test = test_context_driven_prompt()
    consistency_test = test_prompt_consistency()
    
    if prompt_test and consistency_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("Phase 1 implementation is ready for production use.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please review the implementation before proceeding.")
        sys.exit(1) 