#!/usr/bin/env python3
"""
Test diversity-aware approach with real Rev data
"""

import pandas as pd
from supabase_database import SupabaseDatabase
from redesigned_stage2_analyzer import RedesignedStage2Analyzer

def test_diversity_with_real_data():
    """Test diversity approach with real Rev data"""
    
    print("🎯 TESTING DIVERSITY APPROACH WITH REAL REV DATA")
    print("=" * 60)
    
    # Get real Stage 1 data
    db = SupabaseDatabase()
    stage1_data = db.get_all_stage1_data_responses()
    
    # Filter for Rev data
    rev_data = stage1_data[stage1_data['client_id'] == 'Rev']
    
    print(f"📊 REAL DATA ANALYSIS:")
    print(f"   Total Stage 1 records: {len(stage1_data)}")
    print(f"   Rev records: {len(rev_data)}")
    
    if rev_data.empty:
        print("❌ No Rev data found")
        return
    
    # Analyze interview diversity in real data
    print(f"\n📋 INTERVIEW DIVERSITY ANALYSIS:")
    
    # Group by interview (using company + interviewee as interview identifier)
    interview_groups = {}
    for _, row in rev_data.iterrows():
        interview_key = f"{row['company']}_{row['interviewee_name']}"
        if interview_key not in interview_groups:
            interview_groups[interview_key] = []
        interview_groups[interview_key].append(row)
    
    print(f"   Total interviews: {len(interview_groups)}")
    
    # Analyze each interview
    interview_analysis = {}
    for interview_key, quotes in interview_groups.items():
        company = quotes[0]['company']
        interviewee = quotes[0]['interviewee_name']
        quote_count = len(quotes)
        
        # Simple sentiment analysis
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for quote in quotes:
            text = quote['verbatim_response'].lower()
            if any(word in text for word in ['love', 'excellent', 'amazing', 'outstanding', 'perfect', 'great']):
                positive_count += 1
            elif any(word in text for word in ['hate', 'terrible', 'awful', 'horrible', 'worst', 'bad']):
                negative_count += 1
            else:
                neutral_count += 1
        
        interview_analysis[interview_key] = {
            'company': company,
            'interviewee': interviewee,
            'quote_count': quote_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'dominant_sentiment': 'positive' if positive_count > negative_count and positive_count > neutral_count else 
                                'negative' if negative_count > positive_count and negative_count > neutral_count else 'neutral'
        }
    
    # Show interview diversity
    print(f"\n📋 INTERVIEW BREAKDOWN:")
    for interview_key, analysis in interview_analysis.items():
        print(f"   {analysis['company']} - {analysis['interviewee']}:")
        print(f"     Quotes: {analysis['quote_count']}")
        print(f"     Sentiment: {analysis['positive_count']} pos, {analysis['negative_count']} neg, {analysis['neutral_count']} neutral")
        print(f"     Dominant: {analysis['dominant_sentiment']}")
    
    # Calculate diversity metrics
    total_interviews = len(interview_groups)
    total_quotes = sum(len(quotes) for quotes in interview_groups.values())
    companies = set(analysis['company'] for analysis in interview_analysis.values())
    interviewees = set(analysis['interviewee'] for analysis in interview_analysis.values())
    
    print(f"\n📊 DIVERSITY METRICS:")
    print(f"   Total Interviews: {total_interviews}")
    print(f"   Total Quotes: {total_quotes}")
    print(f"   Unique Companies: {len(companies)}")
    print(f"   Unique Interviewees: {len(interviewees)}")
    print(f"   Average Quotes per Interview: {total_quotes/total_interviews:.1f}")
    
    # Identify potential over-valuation risks
    print(f"\n⚠️  POTENTIAL OVER-VALUATION RISKS:")
    
    high_volume_interviews = []
    sentiment_dominance = []
    
    for interview_key, analysis in interview_analysis.items():
        if analysis['quote_count'] > 5:
            high_volume_interviews.append(interview_key)
        
        # Check for sentiment dominance
        total = analysis['quote_count']
        dominant_pct = max(analysis['positive_count'], analysis['negative_count'], analysis['neutral_count']) / total
        if dominant_pct > 0.8:  # 80%+ same sentiment
            sentiment_dominance.append(interview_key)
    
    if high_volume_interviews:
        print(f"   High volume interviews (>5 quotes): {len(high_volume_interviews)}")
        for interview in high_volume_interviews:
            analysis = interview_analysis[interview]
            print(f"     - {analysis['company']}: {analysis['quote_count']} quotes")
    
    if sentiment_dominance:
        print(f"   Sentiment dominance (>80% same sentiment): {len(sentiment_dominance)}")
        for interview in sentiment_dominance:
            analysis = interview_analysis[interview]
            print(f"     - {analysis['company']}: {analysis['dominant_sentiment']} dominant")
    
    # Demonstrate diversity-aware quote selection
    print(f"\n🎯 DIVERSITY-AWARE QUOTE SELECTION STRATEGY:")
    
    # Select quotes based on diversity principles
    selected_quotes = []
    max_quotes_per_interview = 3  # Limit to prevent domination
    
    for interview_key, quotes in interview_groups.items():
        analysis = interview_analysis[interview_key]
        
        if analysis['quote_count'] <= max_quotes_per_interview:
            # Include all quotes from smaller interviews
            selected_quotes.extend(quotes)
            print(f"   {analysis['company']}: Include all {analysis['quote_count']} quotes (small interview)")
        else:
            # Select strategically from larger interviews
            # Prioritize quotes with different sentiment
            sentiment_quotes = {'positive': [], 'negative': [], 'neutral': []}
            
            for quote in quotes:
                text = quote['verbatim_response'].lower()
                if any(word in text for word in ['love', 'excellent', 'amazing', 'outstanding', 'perfect', 'great']):
                    sentiment_quotes['positive'].append(quote)
                elif any(word in text for word in ['hate', 'terrible', 'awful', 'horrible', 'worst', 'bad']):
                    sentiment_quotes['negative'].append(quote)
                else:
                    sentiment_quotes['neutral'].append(quote)
            
            # Select balanced representation
            selected = []
            for sentiment, sentiment_quotes_list in sentiment_quotes.items():
                if sentiment_quotes_list:
                    # Take up to 1 quote per sentiment type
                    selected.extend(sentiment_quotes_list[:1])
            
            # If we still need more quotes, add from any sentiment
            remaining_needed = max_quotes_per_interview - len(selected)
            if remaining_needed > 0:
                all_remaining = [q for sentiment_list in sentiment_quotes.values() for q in sentiment_list[1:]]
                selected.extend(all_remaining[:remaining_needed])
            
            selected_quotes.extend(selected)
            print(f"   {analysis['company']}: Select {len(selected)} quotes from {analysis['quote_count']} (large interview)")
    
    print(f"\n📈 DIVERSITY-AWARE SELECTION RESULTS:")
    print(f"   Original quotes: {total_quotes}")
    print(f"   Selected quotes: {len(selected_quotes)}")
    print(f"   Selection rate: {len(selected_quotes)/total_quotes*100:.1f}%")
    
    # Show what the diversity-aware approach would analyze
    print(f"\n🔍 QUOTES SELECTED FOR ANALYSIS:")
    for i, quote in enumerate(selected_quotes[:5], 1):  # Show first 5
        company = quote['company']
        interviewee = quote['interviewee_name']
        text = quote['verbatim_response'][:100] + "..." if len(quote['verbatim_response']) > 100 else quote['verbatim_response']
        print(f"   {i}. {company} - {interviewee}: {text}")
    
    if len(selected_quotes) > 5:
        print(f"   ... and {len(selected_quotes) - 5} more quotes")
    
    # Demonstrate the value of diversity
    print(f"\n💰 DIVERSITY VALUE DEMONSTRATION:")
    
    diversity_benefits = [
        "✅ Prevents single interview domination",
        "✅ Ensures balanced sentiment representation", 
        "✅ Captures insights from all companies",
        "✅ Provides comprehensive competitive intelligence",
        "✅ Avoids false signals from over-represented interviews"
    ]
    
    for benefit in diversity_benefits:
        print(f"   {benefit}")
    
    # Show comparison with non-diversity approach
    print(f"\n🔄 COMPARISON: DIVERSITY vs NON-DIVERSITY")
    
    # Simulate non-diversity approach (just take all quotes)
    non_diversity_quotes = list(rev_data.iterrows())
    
    print(f"   NON-DIVERSITY APPROACH:")
    print(f"     - Process all {total_quotes} quotes equally")
    print(f"     - Risk: High-volume interviews dominate")
    print(f"     - Risk: Sentiment skew from dominant interviews")
    print(f"     - Risk: Missing insights from smaller interviews")
    
    print(f"\n   DIVERSITY-AWARE APPROACH:")
    print(f"     - Process {len(selected_quotes)} strategically selected quotes")
    print(f"     - Benefit: Balanced interview representation")
    print(f"     - Benefit: Realistic sentiment distribution")
    print(f"     - Benefit: Comprehensive competitive intelligence")
    
    return {
        'total_interviews': total_interviews,
        'total_quotes': total_quotes,
        'selected_quotes': len(selected_quotes),
        'interview_analysis': interview_analysis,
        'high_volume_risks': len(high_volume_interviews),
        'sentiment_dominance_risks': len(sentiment_dominance)
    }

if __name__ == "__main__":
    results = test_diversity_with_real_data()
    print(f"\n🎯 TEST COMPLETE")
    print("=" * 60) 