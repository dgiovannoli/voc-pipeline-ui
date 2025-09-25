#!/usr/bin/env python3
"""
Search for Fragmented Themes and Company Personas
Look for the sophisticated theme patterns in existing ShipStation data
"""

from supabase_database import SupabaseDatabase
import pandas as pd
import re

def search_fragmented_themes():
    """Search for the sophisticated theme fragments in existing data"""
    db = SupabaseDatabase()
    client_id = "ShipStation API"
    
    print("🔍 Searching for Fragmented Themes in ShipStation Data")
    print("=" * 70)
    
    # 1. Search for infrastructure evolution patterns
    print("\n🏗️ 1. Infrastructure Evolution Patterns:")
    print("-" * 50)
    
    # Get all interview themes
    interview_themes = db.fetch_interview_level_themes(client_id)
    if not interview_themes.empty:
        print(f"✅ Found {len(interview_themes)} interview themes to analyze")
        
        # Search for infrastructure evolution keywords
        evolution_patterns = {
            'warehouse_management': [
                'warehouse', 'fulfillment', 'inventory', 'storage', 'logistics'
            ],
            'infrastructure_changes': [
                'used to', 'before', 'after', 'changed', 'moved', 'switched', 'evolved', 'grew'
            ],
            'technology_adoption': [
                'wms', 'warehouse management system', '3pl', 'third party logistics', 'automation'
            ],
            'scaling_mentions': [
                'scale', 'scaling', 'growth', 'grew', 'expanded', 'larger', 'bigger'
            ]
        }
        
        for pattern_name, keywords in evolution_patterns.items():
            print(f"\n🔍 {pattern_name.replace('_', ' ').title()}:")
            matches = []
            
            for _, theme in interview_themes.iterrows():
                theme_text = theme.get('theme_statement', '').lower()
                matches_found = [kw for kw in keywords if kw in theme_text]
                
                if matches_found:
                    matches.append({
                        'theme': theme.get('theme_statement', '')[:150] + '...',
                        'matches': matches_found,
                        'interview_id': theme.get('interview_id', 'N/A')
                    })
            
            if matches:
                print(f"  ✅ Found {len(matches)} themes with {pattern_name} mentions:")
                for match in matches[:3]:  # Show top 3
                    print(f"    - Interview {match['interview_id']}: {match['matches']}")
                    print(f"      Theme: {match['theme']}")
                    print()
            else:
                print(f"  ⚠️ No themes found with {pattern_name} mentions")
    
    # 2. Search for company persona patterns
    print("\n👥 2. Company Persona Patterns:")
    print("-" * 50)
    
    # Get interview metadata for company context
    metadata = db.fetch_interview_metadata(client_id)
    if not metadata.empty:
        print(f"✅ Found {len(metadata)} interview records with metadata")
        
        # Look for company size and role patterns
        if 'firm_size' in metadata.columns:
            size_distribution = metadata['firm_size'].value_counts()
            print(f"\n📊 Company Size Distribution:")
            for size, count in size_distribution.items():
                print(f"  - {size}: {count} companies")
        
        if 'interviewee_role' in metadata.columns:
            role_distribution = metadata['interviewee_role'].value_counts()
            print(f"\n👔 Role Distribution:")
            for role, count in role_distribution.items():
                print(f"  - {role}: {count} people")
        
        if 'industry' in metadata.columns:
            industry_distribution = metadata['industry'].value_counts()
            print(f"\n🏭 Industry Distribution:")
            for industry, count in industry_distribution.items():
                print(f"  - {industry}: {count} companies")
    
    # 3. Search for strategic decision patterns
    print("\n🎯 3. Strategic Decision Patterns:")
    print("-" * 50)
    
    if not interview_themes.empty:
        strategic_patterns = {
            'cost_vs_quality': [
                'cost', 'price', 'expensive', 'cheap', 'budget', 'affordable', 'value'
            ],
            'partnership_decisions': [
                'partner', 'partnership', 'vendor', 'supplier', 'relationship', 'collaboration'
            ],
            'build_vs_buy': [
                'build', 'buy', 'in-house', 'outsource', 'third party', 'external'
            ],
            'customer_focus': [
                'customer', 'client', 'user', 'end user', 'buyer', 'customer experience'
            ]
        }
        
        for pattern_name, keywords in strategic_patterns.items():
            print(f"\n🔍 {pattern_name.replace('_', ' ').title()}:")
            matches = []
            
            for _, theme in interview_themes.iterrows():
                theme_text = theme.get('theme_statement', '').lower()
                matches_found = [kw for kw in keywords if kw in theme_text]
                
                if matches_found:
                    matches.append({
                        'theme': theme.get('theme_statement', '')[:150] + '...',
                        'matches': matches_found,
                        'interview_id': theme.get('interview_id', 'N/A')
                    })
            
            if matches:
                print(f"  ✅ Found {len(matches)} themes with {pattern_name} mentions:")
                for match in matches[:3]:  # Show top 3
                    print(f"    - Interview {match['interview_id']}: {match['matches']}")
                    print(f"      Theme: {match['theme']}")
                    print()
            else:
                print(f"  ⚠️ No themes found with {pattern_name} mentions")
    
    # 4. Look for cross-interview patterns
    print("\n🔗 4. Cross-Interview Pattern Analysis:")
    print("-" * 50)
    
    if not interview_themes.empty:
        # Look for themes that might be fragments of the sophisticated theme
        sophisticated_fragments = {
            'small_company_pain': [
                'small', 'startup', 'early', 'beginning', 'manage', 'handle', 'do it ourselves'
            ],
            'scaling_challenges': [
                'grow', 'scale', 'expand', 'challenge', 'problem', 'issue', 'difficulty'
            ],
            'infrastructure_evolution': [
                'warehouse', 'fulfillment', 'logistics', 'system', 'process', 'workflow'
            ],
            'partnership_strategy': [
                'partner', '3pl', 'vendor', 'supplier', 'relationship', 'outsource'
            ]
        }
        
        print("🔍 Looking for sophisticated theme fragments:")
        
        for fragment_name, keywords in sophisticated_fragments.items():
            matches = []
            
            for _, theme in interview_themes.iterrows():
                theme_text = theme.get('theme_statement', '').lower()
                matches_found = [kw for kw in keywords if kw in theme_text]
                
                if len(matches_found) >= 2:  # At least 2 keywords match
                    matches.append({
                        'theme': theme.get('theme_statement', '')[:150] + '...',
                        'matches': matches_found,
                        'interview_id': theme.get('interview_id', 'N/A')
                    })
            
            if matches:
                print(f"\n  🎯 {fragment_name.replace('_', ' ').title()} - {len(matches)} potential fragments:")
                for match in matches[:2]:  # Show top 2
                    print(f"    - Interview {match['interview_id']}: {match['matches']}")
                    print(f"      Theme: {match['theme']}")
            else:
                print(f"\n  ⚠️ {fragment_name.replace('_', ' ').title()}: No fragments found")

def analyze_company_stories():
    """Analyze the company stories and personas in the data"""
    print("\n📖 5. Company Story Analysis:")
    print("-" * 50)
    
    db = SupabaseDatabase()
    client_id = "ShipStation API"
    
    # Get interview themes and metadata
    interview_themes = db.fetch_interview_level_themes(client_id)
    metadata = db.fetch_interview_metadata(client_id)
    
    if not interview_themes.empty and not metadata.empty:
        print("🔍 Looking for company evolution stories...")
        
        # Look for themes that contain company journey elements
        journey_keywords = [
            'started', 'began', 'originally', 'initially', 'first', 'early',
            'grew', 'expanded', 'scaled', 'developed', 'evolved', 'changed',
            'moved', 'switched', 'transitioned', 'upgraded', 'improved'
        ]
        
        company_stories = []
        
        for _, theme in interview_themes.iterrows():
            theme_text = theme.get('theme_statement', '').lower()
            journey_matches = [kw for kw in journey_keywords if kw in theme_text]
            
            if journey_matches:
                # Get company context if possible
                interview_id = theme.get('interview_id', '')
                company_info = metadata[metadata['interview_id'] == interview_id]
                
                company_name = company_info['company'].iloc[0] if not company_info.empty else 'Unknown'
                company_size = company_info['firm_size'].iloc[0] if not company_info.empty and 'firm_size' in company_info.columns else 'Unknown'
                
                company_stories.append({
                    'company': company_name,
                    'size': company_size,
                    'theme': theme.get('theme_statement', '')[:200] + '...',
                    'journey_elements': journey_matches
                })
        
        if company_stories:
            print(f"✅ Found {len(company_stories)} company evolution stories:")
            for story in company_stories[:5]:  # Show top 5
                print(f"\n  🏢 {story['company']} ({story['size']}):")
                print(f"    Journey elements: {story['journey_elements']}")
                print(f"    Story: {story['theme']}")
        else:
            print("⚠️ No company evolution stories found")

def main():
    """Run the fragmented theme search"""
    search_fragmented_themes()
    analyze_company_stories()
    
    print("\n🎯 Summary:")
    print("This analysis shows what's already in your data without any changes.")
    print("Look for:")
    print("- Infrastructure evolution mentions across interviews")
    print("- Company size patterns in metadata")
    print("- Strategic decision patterns in themes")
    print("- Cross-interview story fragments")
    print("\n💡 Next step: Use these patterns to identify the sophisticated theme!")

if __name__ == '__main__':
    main() 