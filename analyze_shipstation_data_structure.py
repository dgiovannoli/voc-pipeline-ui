#!/usr/bin/env python3
"""
Analyze ShipStation API Data Structure
Identify what would be needed for sophisticated themes to emerge
"""

from supabase_database import SupabaseDatabase
import pandas as pd

def analyze_data_structure():
    """Analyze the current data structure for ShipStation API"""
    db = SupabaseDatabase()
    client_id = "ShipStation API"
    
    print("🔍 Analyzing ShipStation API Data Structure")
    print("=" * 60)
    
    # 1. Check interview metadata for company size/scale indicators
    print("\n📊 1. Interview Metadata Analysis:")
    print("-" * 40)
    try:
        metadata = db.fetch_interview_metadata(client_id)
        if not metadata.empty:
            print(f"✅ Found {len(metadata)} interview records")
            print("Columns available:")
            for col in metadata.columns:
                print(f"  - {col}")
            
            # Check for company size indicators
            size_indicators = []
            for col in metadata.columns:
                if any(keyword in col.lower() for keyword in ['size', 'scale', 'employee', 'revenue', 'volume', 'growth']):
                    size_indicators.append(col)
            
            if size_indicators:
                print(f"\n🎯 Company size indicators found: {size_indicators}")
            else:
                print("\n⚠️ No company size indicators found")
                
        else:
            print("❌ No interview metadata found")
    except Exception as e:
        print(f"❌ Error accessing metadata: {e}")
    
    # 2. Check stage1 responses for infrastructure mentions
    print("\n📊 2. Stage 1 Responses Analysis:")
    print("-" * 40)
    try:
        responses = db.fetch_stage1_data_responses(client_id)
        if not responses.empty:
            print(f"✅ Found {len(responses)} response records")
            
            # Look for infrastructure-related keywords
            infrastructure_keywords = ['warehouse', 'wms', '3pl', 'fulfillment', 'logistics', 'scale', 'growth', 'partnership']
            infrastructure_mentions = []
            
            for keyword in infrastructure_keywords:
                count = responses['verbatim_response'].str.contains(keyword, case=False, na=False).sum()
                if count > 0:
                    infrastructure_mentions.append((keyword, count))
            
            if infrastructure_mentions:
                print(f"\n🏗️ Infrastructure mentions found:")
                for keyword, count in infrastructure_mentions:
                    print(f"  - {keyword}: {count} mentions")
            else:
                print("\n⚠️ No infrastructure mentions found")
                
        else:
            print("❌ No stage1 responses found")
    except Exception as e:
        print(f"❌ Error accessing responses: {e}")
    
    # 3. Check existing themes for similar patterns
    print("\n📊 3. Existing Themes Analysis:")
    print("-" * 40)
    try:
        research_themes = db.fetch_research_themes_all(client_id)
        if not research_themes.empty:
            print(f"✅ Found {len(research_themes)} research themes")
            
            # Look for themes that might relate to the sophisticated theme
            sophisticated_keywords = ['customer', 'segmentation', 'scale', 'growth', 'warehouse', 'wms', '3pl', 'partnership', 'midmarket']
            related_themes = []
            
            for _, theme in research_themes.iterrows():
                theme_text = theme.get('theme_statement', '').lower()
                matches = [kw for kw in sophisticated_keywords if kw in theme_text]
                if len(matches) >= 2:  # At least 2 keywords match
                    related_themes.append({
                        'theme': theme.get('theme_statement', '')[:100] + '...',
                        'matches': matches,
                        'subject': theme.get('harmonized_subject', 'N/A')
                    })
            
            if related_themes:
                print(f"\n🎯 Related themes found:")
                for rt in related_themes[:5]:  # Show top 5
                    print(f"  - Matches: {rt['matches']}")
                    print(f"    Subject: {rt['subject']}")
                    print(f"    Theme: {rt['theme']}")
                    print()
            else:
                print("\n⚠️ No related themes found")
                
        else:
            print("❌ No research themes found")
    except Exception as e:
        print(f"❌ Error accessing themes: {e}")
    
    # 4. Check interview themes for customer journey patterns
    print("\n📊 4. Interview Themes Analysis:")
    print("-" * 40)
    try:
        interview_themes = db.fetch_interview_level_themes(client_id)
        if not interview_themes.empty:
            print(f"✅ Found {len(interview_themes)} interview themes")
            
            # Look for customer journey or evolution patterns
            journey_keywords = ['before', 'after', 'moved', 'changed', 'evolved', 'grew', 'scaled', 'started', 'became']
            journey_mentions = []
            
            for _, theme in interview_themes.iterrows():
                theme_text = theme.get('theme_statement', '').lower()
                matches = [kw for kw in journey_keywords if kw in theme_text]
                if matches:
                    journey_mentions.append({
                        'theme': theme.get('theme_statement', '')[:100] + '...',
                        'matches': matches
                    })
            
            if journey_mentions:
                print(f"\n🔄 Customer journey patterns found:")
                for jm in journey_mentions[:3]:  # Show top 3
                    print(f"  - Matches: {jm['matches']}")
                    print(f"    Theme: {jm['theme']}")
                    print()
            else:
                print("\n⚠️ No customer journey patterns found")
                
        else:
            print("❌ No interview themes found")
    except Exception as e:
        print(f"❌ Error accessing interview themes: {e}")

def suggest_improvements():
    """Suggest improvements to capture sophisticated themes"""
    print("\n💡 Suggestions for Capturing Sophisticated Themes:")
    print("=" * 60)
    
    print("\n1. 📊 Enhanced Interview Metadata:")
    print("   - Add company size indicators (employees, revenue, order volume)")
    print("   - Add infrastructure maturity (self-managed, WMS, 3PL)")
    print("   - Add growth stage (startup, scaling, enterprise)")
    print("   - Add industry vertical and business model")
    
    print("\n2. 🎯 Improved Interview Questions:")
    print("   - 'How has your shipping/fulfillment approach evolved as you grew?'")
    print("   - 'What infrastructure changes were needed when you scaled?'")
    print("   - 'How do you evaluate shipping partnerships vs. in-house solutions?'")
    print("   - 'What's your customer segmentation strategy for shipping?'")
    
    print("\n3. 🔍 Enhanced Theme Generation:")
    print("   - Look for patterns across company size segments")
    print("   - Identify infrastructure evolution stories")
    print("   - Connect partnership decisions to customer segments")
    print("   - Map growth stages to technology adoption")
    
    print("\n4. 📈 Data Enrichment:")
    print("   - Add external company data (size, industry, growth stage)")
    print("   - Implement customer journey mapping")
    print("   - Track infrastructure decision timelines")
    print("   - Monitor partnership strategy evolution")

def main():
    """Run the analysis"""
    analyze_data_structure()
    suggest_improvements()
    
    print("\n🎯 Summary:")
    print("The sophisticated theme you described requires:")
    print("- Customer segmentation data (company size, growth stage)")
    print("- Infrastructure evolution stories (before/after scenarios)")
    print("- Strategic decision-making context (partnerships, scaling)")
    print("- Cross-interview pattern recognition")
    print("- Enhanced theme generation that looks for business evolution")

if __name__ == '__main__':
    main() 