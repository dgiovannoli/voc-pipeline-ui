#!/usr/bin/env python3

import pandas as pd
from supabase_database import SupabaseDatabase
import json

def analyze_specific_issues():
    """Analyze specific issues with the enhanced extraction"""
    
    print("🔍 DETAILED ANALYSIS: Altair Law Enhanced Extraction Issues")
    print("=" * 80)
    
    # Get database responses
    db = SupabaseDatabase()
    df = db.get_core_responses(client_id='Rev')
    cyrus_responses = df[df['interviewee_name'].str.contains('Cyrus', case=False, na=False)]
    
    print(f"📊 TOTAL CYRUS RESPONSES: {len(cyrus_responses)}")
    print()
    
    # 1. Analyze question quality
    print("❓ QUESTION QUALITY ANALYSIS:")
    print("-" * 40)
    
    unknown_questions = cyrus_responses[cyrus_responses['question'] == 'UNKNOWN']
    print(f"UNKNOWN questions: {len(unknown_questions)}")
    
    if len(unknown_questions) > 0:
        print("Examples of UNKNOWN questions:")
        for _, row in unknown_questions.head(3).iterrows():
            print(f"  - Response ID: {row['response_id']}")
            print(f"    Subject: {row['subject']}")
            print(f"    Response preview: {row['verbatim_response'][:100]}...")
            print()
    
    # 2. Analyze complex question capture
    print("🔍 COMPLEX QUESTION CAPTURE ANALYSIS:")
    print("-" * 40)
    
    complex_questions = [
        "Speed and cost were your top two priority. And you just mentioned layout",
        "When it comes to the transcription work they had done",
        "With accuracy rating so high. Are there any files",
        "When you went to find a vendor, did you already know about Rev"
    ]
    
    for complex_q in complex_questions:
        found = False
        for _, row in cyrus_responses.iterrows():
            if complex_q.lower() in row['question'].lower():
                print(f"✅ FOUND: '{complex_q[:50]}...'")
                print(f"   Matched to: {row['question']}")
                found = True
                break
        if not found:
            print(f"❌ MISSING: '{complex_q[:50]}...'")
        print()
    
    # 3. Analyze response length distribution
    print("📏 RESPONSE LENGTH ANALYSIS:")
    print("-" * 40)
    
    response_lengths = cyrus_responses['verbatim_response'].str.len()
    print(f"Average length: {response_lengths.mean():.0f} characters")
    print(f"Median length: {response_lengths.median():.0f} characters")
    print(f"Min length: {response_lengths.min():.0f} characters")
    print(f"Max length: {response_lengths.max():.0f} characters")
    print()
    
    # 4. Analyze subject diversity
    print("🏷️ SUBJECT DIVERSITY ANALYSIS:")
    print("-" * 40)
    
    subjects = cyrus_responses['subject'].value_counts()
    print("Top 10 subjects:")
    for subject, count in subjects.head(10).items():
        print(f"  {subject}: {count}")
    print()
    
    # 5. Check for compliance/privacy content
    print("🔒 COMPLIANCE/PRIVACY CONTENT CHECK:")
    print("-" * 40)
    
    compliance_keywords = ['SOC', 'HIPAA', 'compliant', 'privacy', 'security', 'attorney-client']
    compliance_found = 0
    
    for _, row in cyrus_responses.iterrows():
        response_lower = row['verbatim_response'].lower()
        for keyword in compliance_keywords:
            if keyword.lower() in response_lower:
                compliance_found += 1
                print(f"✅ Found '{keyword}' in response: {row['response_id']}")
                break
    
    print(f"Total responses with compliance content: {compliance_found}")
    print()
    
    # 6. Analyze specific response examples
    print("📋 SPECIFIC RESPONSE EXAMPLES:")
    print("-" * 40)
    
    # Show a few examples of good and problematic responses
    print("GOOD RESPONSE EXAMPLE:")
    good_response = cyrus_responses[cyrus_responses['question'] != 'UNKNOWN'].iloc[0]
    print(f"Response ID: {good_response['response_id']}")
    print(f"Subject: {good_response['subject']}")
    print(f"Question: {good_response['question']}")
    print(f"Response: {good_response['verbatim_response'][:200]}...")
    print()
    
    if len(unknown_questions) > 0:
        print("PROBLEMATIC RESPONSE EXAMPLE:")
        bad_response = unknown_questions.iloc[0]
        print(f"Response ID: {bad_response['response_id']}")
        print(f"Subject: {bad_response['subject']}")
        print(f"Question: {bad_response['question']}")
        print(f"Response: {bad_response['verbatim_response'][:200]}...")
        print()
    
    # 7. Overall assessment
    print("🎯 OVERALL ASSESSMENT:")
    print("-" * 40)
    
    total_responses = len(cyrus_responses)
    valid_questions = len(cyrus_responses[cyrus_responses['question'] != 'UNKNOWN'])
    question_accuracy = valid_questions / total_responses
    
    print(f"Total responses: {total_responses}")
    print(f"Valid questions: {valid_questions}")
    print(f"Question accuracy: {question_accuracy:.1%}")
    print(f"Compliance content found: {compliance_found}")
    print(f"Average response length: {response_lengths.mean():.0f} characters")
    print()
    
    # Grade calculation
    if question_accuracy >= 0.95 and compliance_found >= 3:
        grade = "A-"
    elif question_accuracy >= 0.90 and compliance_found >= 2:
        grade = "B+"
    elif question_accuracy >= 0.85:
        grade = "B"
    elif question_accuracy >= 0.80:
        grade = "B-"
    else:
        grade = "C+"
    
    print(f"FINAL GRADE: {grade}")
    
    if grade in ["A-", "B+"]:
        print("✅ EXCELLENT: Significant improvement over previous version")
    elif grade == "B":
        print("📈 GOOD: Moderate improvement, some areas need refinement")
    else:
        print("⚠️ NEEDS WORK: Several issues need to be addressed")

if __name__ == "__main__":
    analyze_specific_issues() 