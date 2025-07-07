#!/usr/bin/env python3

import os
import sys
from voc_pipeline.modular_processor import ModularProcessor

def test_enhanced_extraction():
    """Test the enhanced extraction with the Cyrus Nazarian transcript"""
    
    # Initialize processor with enhanced settings
    processor = ModularProcessor(
        model_name="gpt-4o-mini",
        max_tokens=8000,
        temperature=0.3
    )
    
    # Test file path
    transcript_path = "uploads/Interview with Cyrus Nazarian, Attorney at Altair Law.docx"
    
    if not os.path.exists(transcript_path):
        print(f"❌ Test file not found: {transcript_path}")
        return
    
    print("🧪 TESTING ENHANCED EXTRACTION")
    print("=" * 60)
    print(f"📄 Testing file: {transcript_path}")
    print(f"🤖 Model: {processor.model_name}")
    print(f"🌡️ Temperature: {processor.temperature}")
    print(f"📝 Max tokens: {processor.max_tokens}")
    print()
    
    try:
        # Run Stage 1 extraction
        print("🚀 Running enhanced Stage 1 extraction...")
        responses = processor.stage1_core_extraction(
            transcript_path=transcript_path,
            company="Altair Law",
            interviewee="Cyrus Nazarian",
            deal_status="closed won",
            date_of_interview="01/01/2024"
        )
        
        print(f"\n✅ Extraction complete!")
        print(f"📊 Total responses extracted: {len(responses)}")
        print()
        
        # Display results
        print("📋 EXTRACTED RESPONSES:")
        print("=" * 60)
        
        for i, response in enumerate(responses, 1):
            print(f"\n{i}. Response ID: {response['response_id']}")
            print(f"   Subject: {response['subject']}")
            print(f"   Question: {response['question']}")
            print(f"   Response (first 200 chars): {response['verbatim_response'][:200]}...")
            print("-" * 40)
        
        # Check for the specific missing questions
        print("\n🔍 CHECKING FOR PREVIOUSLY MISSING QUESTIONS:")
        print("=" * 60)
        
        missing_questions = [
            "When you went to find a vendor, did you already know about Rev",
            "Speed and cost were your top two priority",
            "When it comes to the transcription work they had done",
            "With accuracy rating so high. Are there any files"
        ]
        
        found_count = 0
        for question in missing_questions:
            found = False
            for response in responses:
                if question.lower() in response['question'].lower():
                    found = True
                    found_count += 1
                    print(f"✅ FOUND: {question}")
                    break
            if not found:
                print(f"❌ MISSING: {question}")
        
        print(f"\n📈 IMPROVEMENT SUMMARY:")
        print(f"   Previously missing questions found: {found_count}/4")
        print(f"   Total responses: {len(responses)} (target: 11)")
        print(f"   Success rate: {found_count/4*100:.1f}% for missing questions")
        
        if found_count >= 2:
            print("🎉 SIGNIFICANT IMPROVEMENT DETECTED!")
        elif found_count >= 1:
            print("📈 MODERATE IMPROVEMENT DETECTED!")
        else:
            print("⚠️ NEEDS FURTHER REFINEMENT")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_extraction() 