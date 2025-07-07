#!/usr/bin/env python3
"""
Regrade Altair Law responses by comparing automated output with manual output
"""

from supabase_database import SupabaseDatabase
import pandas as pd
import json

def get_altair_law_responses():
    """Retrieve Altair Law responses from the database"""
    
    print("🔍 Retrieving Altair Law responses from database...")
    print("=" * 60)
    
    try:
        db = SupabaseDatabase()
        
        # Get all responses for client 'Rev'
        responses = db.get_core_responses(client_id='Rev')
        print(f"📊 Total responses for client 'Rev': {len(responses)}")
        
        # Filter for Altair Law specifically
        altair_responses = responses[responses['company'].str.contains('Altair', case=False, na=False)]
        print(f"🏢 Altair Law responses: {len(altair_responses)}")
        
        if len(altair_responses) > 0:
            print(f"\n📋 Altair Law responses from database:")
            for i, (_, row) in enumerate(altair_responses.iterrows(), 1):
                print(f"\n{i}. {row.get('response_id', 'N/A')}")
                print(f"   Subject: {row.get('subject', 'N/A')}")
                print(f"   Question: {row.get('question', 'N/A')}")
                print(f"   Interviewee: {row.get('interviewee_name', 'N/A')}")
                print(f"   Verbatim: {row.get('verbatim_response', 'N/A')}")
                print(f"   Deal Status: {row.get('deal_status', 'N/A')}")
        
        return altair_responses
        
    except Exception as e:
        print(f"❌ Failed to retrieve Altair Law responses: {e}")
        return pd.DataFrame()

def compare_with_manual_output():
    """Compare automated output with manual output"""
    
    print(f"\n📊 COMPARISON: Automated vs Manual Output")
    print("=" * 60)
    
    # Manual output from user
    manual_output = [
        {
            "response_id": "AltairLaw_Unknown_1_1",
            "verbatim_response": "Rev SOC two compliant, HIPAA compliant, we use it for depositions and hearings, and it saves us time. We use it for depositions and hearings, and it saves us time.",
            "subject": "Compliance and Efficiency",
            "question": "How do you use Rev and what compliance features are important?",
            "deal_status": "closed_won",
            "company": "Altair Law",
            "interviewee_name": "Unknown",
            "date_of_interview": "2024-01-01"
        },
        {
            "response_id": "AltairLaw_Unknown_1_2", 
            "verbatim_response": "Sometimes the transcript isn't accurate. Sometimes the transcript isn't accurate.",
            "subject": "Transcription Accuracy",
            "question": "What are the main issues with Rev's transcription service?",
            "deal_status": "closed_won",
            "company": "Altair Law",
            "interviewee_name": "Unknown",
            "date_of_interview": "2024-01-01"
        },
        {
            "response_id": "AltairLaw_Unknown_1_3",
            "verbatim_response": "We use Dropbox and Clio. We use Dropbox and Clio.",
            "subject": "Integration Requirements",
            "question": "What integrations would be most helpful for your workflow?",
            "deal_status": "closed_won",
            "company": "Altair Law",
            "interviewee_name": "Unknown",
            "date_of_interview": "2024-01-01"
        },
        {
            "response_id": "AltairLaw_Unknown_1_4",
            "verbatim_response": "Speed and cost are most important, then security. Speed and cost are most important, then security.",
            "subject": "Decision Criteria",
            "question": "How do you rank the criteria when evaluating tools like Rev?",
            "deal_status": "closed_won",
            "company": "Altair Law",
            "interviewee_name": "Unknown",
            "date_of_interview": "2024-01-01"
        },
        {
            "response_id": "AltairLaw_Unknown_1_5",
            "verbatim_response": "Support is fine, but not a big factor. Support is fine, but not a big factor.",
            "subject": "Support Quality",
            "question": "How would you rate the support and service quality?",
            "deal_status": "closed_won",
            "company": "Altair Law",
            "interviewee_name": "Unknown",
            "date_of_interview": "2024-01-01"
        }
    ]
    
    # Get automated output
    automated_responses = get_altair_law_responses()
    
    if automated_responses.empty:
        print("❌ No automated responses found for Altair Law")
        return
    
    print(f"\n📈 COMPARISON METRICS:")
    print("-" * 40)
    print(f"Manual responses: {len(manual_output)}")
    print(f"Automated responses: {len(automated_responses)}")
    
    # Compare key aspects
    print(f"\n🔍 DETAILED COMPARISON:")
    print("-" * 40)
    
    # Check for compliance context preservation
    manual_compliance = any("SOC" in resp["verbatim_response"] or "HIPAA" in resp["verbatim_response"] for resp in manual_output)
    automated_compliance = any("SOC" in str(resp) or "HIPAA" in str(resp) for _, resp in automated_responses.iterrows())
    
    print(f"Compliance context (SOC/HIPAA):")
    print(f"  Manual: {'✅ Present' if manual_compliance else '❌ Missing'}")
    print(f"  Automated: {'✅ Present' if automated_compliance else '❌ Missing'}")
    
    # Check response count
    print(f"\nResponse count:")
    print(f"  Manual: {len(manual_output)} responses")
    print(f"  Automated: {len(automated_responses)} responses")
    
    # Check content preservation
    manual_content = [resp["verbatim_response"] for resp in manual_output]
    automated_content = automated_responses['verbatim_response'].tolist()
    
    print(f"\nContent preservation:")
    print(f"  Manual total words: {sum(len(content.split()) for content in manual_content)}")
    print(f"  Automated total words: {sum(len(str(content).split()) for content in automated_content)}")
    
    # Check subject/question quality
    manual_subjects = [resp["subject"] for resp in manual_output]
    automated_subjects = automated_responses['subject'].tolist()
    
    print(f"\nSubject quality:")
    print(f"  Manual subjects: {manual_subjects}")
    print(f"  Automated subjects: {automated_subjects}")
    
    # Grade the automated output
    grade = calculate_grade(manual_output, automated_responses)
    
    print(f"\n📊 FINAL GRADE: {grade}")
    print("=" * 60)
    
    return grade

def calculate_grade(manual_output, automated_responses):
    """Calculate grade based on comparison with manual output"""
    
    score = 0
    max_score = 100
    
    # 1. Response count (20 points)
    manual_count = len(manual_output)
    automated_count = len(automated_responses)
    count_ratio = min(automated_count / manual_count, 1.0) if manual_count > 0 else 0
    score += count_ratio * 20
    
    # 2. Content preservation (30 points)
    manual_content = [resp["verbatim_response"] for resp in manual_output]
    automated_content = automated_responses['verbatim_response'].tolist()
    
    # Check for key compliance terms
    compliance_terms = ["SOC", "HIPAA", "compliant"]
    manual_compliance = any(any(term in content for term in compliance_terms) for content in manual_content)
    automated_compliance = any(any(term in str(content) for term in compliance_terms) for content in automated_content)
    
    if manual_compliance and automated_compliance:
        score += 15  # Compliance preserved
    elif not manual_compliance and not automated_compliance:
        score += 15  # Neither had compliance
    else:
        score += 5   # Compliance lost
    
    # Content length preservation
    manual_words = sum(len(content.split()) for content in manual_content)
    automated_words = sum(len(str(content).split()) for content in automated_content)
    if automated_words > 0:
        length_ratio = min(automated_words / manual_words, 2.0)  # Allow up to 2x length
        score += length_ratio * 15
    
    # 3. Subject/question quality (25 points)
    manual_subjects = [resp["subject"] for resp in manual_output]
    automated_subjects = automated_responses['subject'].tolist()
    
    # Check for meaningful subjects
    meaningful_subjects = sum(1 for subject in automated_subjects if len(str(subject)) > 5)
    subject_quality = meaningful_subjects / len(automated_subjects) if automated_subjects else 0
    score += subject_quality * 25
    
    # 4. Context preservation (25 points)
    # Check if key themes are preserved
    key_themes = ["compliance", "accuracy", "integration", "speed", "cost", "security", "support"]
    manual_themes = sum(1 for content in manual_content if any(theme in content.lower() for theme in key_themes))
    automated_themes = sum(1 for content in automated_content if any(theme in str(content).lower() for theme in key_themes))
    
    if automated_themes > 0:
        theme_ratio = min(automated_themes / manual_themes, 1.5) if manual_themes > 0 else 1.0
        score += theme_ratio * 25
    
    # Convert to letter grade
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C+"
    elif score >= 50:
        return "C"
    else:
        return "D"

def main():
    """Main function to run the regrading"""
    
    print("🎯 ALTAIR LAW RESPONSE REGRADING")
    print("=" * 60)
    
    # Get automated responses
    automated_responses = get_altair_law_responses()
    
    if automated_responses.empty:
        print("❌ No Altair Law responses found in database")
        print("💡 Make sure to run the pipeline on Altair Law data first")
        return
    
    # Compare and grade
    grade = compare_with_manual_output()
    
    print(f"\n📋 SUMMARY:")
    print(f"Automated responses found: {len(automated_responses)}")
    print(f"Final grade: {grade}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if grade in ["A", "B+"]:
        print("✅ Excellent quality - automated extraction is working well")
    elif grade in ["B", "C+"]:
        print("⚠️ Good quality with room for improvement")
        print("   - Consider increasing max quote length")
        print("   - Review prompt for better context preservation")
    else:
        print("❌ Significant improvements needed")
        print("   - Increase max quote length significantly")
        print("   - Enhance prompt with compliance-specific instructions")
        print("   - Consider using GPT-4o for better context understanding")

if __name__ == "__main__":
    main() 