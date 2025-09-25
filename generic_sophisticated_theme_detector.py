#!/usr/bin/env python3
"""
Generic Sophisticated Theme Detector
Find scale-related, infrastructure, and business evolution patterns across all clients
"""

from supabase_database import SupabaseDatabase
import pandas as pd
import re

def get_all_clients():
    """Get all unique clients from the database"""
    db = SupabaseDatabase()
    
    try:
        # Try to get clients from research themes
        research_themes = db.supabase.table('research_themes').select('client_id').execute()
        if research_themes.data:
            clients = list(set([t['client_id'] for t in research_themes.data]))
            return clients
        
        # Fallback: try interview metadata
        metadata = db.supabase.table('interview_metadata').select('client_id').execute()
        if metadata.data:
            clients = list(set([m['client_id'] for m in metadata.data]))
            return clients
            
        return []
    except Exception as e:
        print(f"⚠️ Error getting clients: {e}")
        return []

def detect_sophisticated_patterns(client_id: str):
    """Detect sophisticated theme patterns for a specific client"""
    db = SupabaseDatabase()
    
    print(f"\n🔍 Analyzing {client_id}:")
    print("-" * 50)
    
    # Get all themes for this client
    research_themes = db.fetch_research_themes_all(client_id)
    interview_themes = db.fetch_interview_level_themes(client_id)
    
    all_themes = []
    if not research_themes.empty:
        all_themes.extend(research_themes['theme_statement'].tolist())
    if not interview_themes.empty:
        all_themes.extend(interview_themes['theme_statement'].tolist())
    
    if not all_themes:
        print("  ⚠️ No themes found")
        return None
    
    print(f"  📊 Found {len(all_themes)} total themes")
    
    # Define sophisticated pattern categories
    sophisticated_patterns = {
        'scale_evolution': {
            'keywords': [
                'scale', 'scaling', 'grew', 'grow', 'growth', 'expanded', 'expansion',
                'started', 'began', 'originally', 'initially', 'first', 'early',
                'evolved', 'evolving', 'changed', 'changed from', 'moved from',
                'startup', 'small', 'medium', 'large', 'enterprise', 'midmarket'
            ],
            'description': 'Company growth and evolution patterns'
        },
        'infrastructure_complexity': {
            'keywords': [
                'warehouse', 'fulfillment', 'logistics', 'supply chain', 'operations',
                'system', 'systems', 'platform', 'platforms', 'integration', 'integrations',
                'api', 'apis', 'edi', 'automation', 'workflow', 'workflows',
                'multi-node', 'multi-location', 'distributed', 'centralized'
            ],
            'description': 'Infrastructure and system complexity'
        },
        'strategic_decisions': {
            'keywords': [
                'vendor', 'vendors', 'partner', 'partnerships', 'supplier', 'suppliers',
                'build', 'buy', 'in-house', 'outsource', 'outsourcing', 'third party',
                'decision', 'decisions', 'strategy', 'strategic', 'evaluate', 'evaluation',
                'cost', 'costs', 'budget', 'investment', 'roi', 'value proposition'
            ],
            'description': 'Strategic decision-making patterns'
        },
        'customer_journey': {
            'keywords': [
                'customer', 'customers', 'client', 'clients', 'user', 'users',
                'needs', 'requirements', 'pain point', 'pain points', 'challenge', 'challenges',
                'experience', 'satisfaction', 'loyalty', 'retention', 'acquisition'
            ],
            'description': 'Customer journey and experience patterns'
        },
        'business_model_evolution': {
            'keywords': [
                'business model', 'revenue model', 'pricing', 'pricing model',
                'market', 'markets', 'segment', 'segmentation', 'target', 'targeting',
                'competitive', 'competition', 'differentiation', 'value', 'value add'
            ],
            'description': 'Business model and market evolution'
        }
    }
    
    # Analyze each pattern category
    pattern_results = {}
    
    for pattern_name, pattern_config in sophisticated_patterns.items():
        matches = []
        
        for theme in all_themes:
            if not theme:
                continue
                
            theme_lower = str(theme).lower()
            matches_found = [kw for kw in pattern_config['keywords'] if kw in theme_lower]
            
            if len(matches_found) >= 2:  # At least 2 keywords match
                matches.append({
                    'theme': theme[:200] + '...' if len(theme) > 200 else theme,
                    'matches': matches_found
                })
        
        pattern_results[pattern_name] = {
            'matches': matches,
            'count': len(matches),
            'description': pattern_config['description']
        }
    
    # Look for cross-pattern themes (the most sophisticated ones)
    cross_pattern_themes = []
    
    for theme in all_themes:
        if not theme:
            continue
            
        theme_lower = str(theme).lower()
        pattern_matches = {}
        
        for pattern_name, pattern_config in sophisticated_patterns.items():
            matches_found = [kw for kw in pattern_config['keywords'] if kw in theme_lower]
            if matches_found:
                pattern_matches[pattern_name] = matches_found
        
        # If theme matches multiple patterns, it's potentially sophisticated
        if len(pattern_matches) >= 3:  # Matches at least 3 pattern categories
            cross_pattern_themes.append({
                'theme': theme[:300] + '...' if len(theme) > 300 else theme,
                'patterns': pattern_matches,
                'pattern_count': len(pattern_matches)
            })
    
    # Display results
    print(f"  🎯 Pattern Analysis Results:")
    
    for pattern_name, result in pattern_results.items():
        if result['count'] > 0:
            print(f"    ✅ {pattern_name.replace('_', ' ').title()}: {result['count']} themes")
            print(f"       Description: {result['description']}")
            
            # Show top 2 examples
            for i, match in enumerate(result['matches'][:2]):
                print(f"         {i+1}. Matches: {match['matches']}")
                print(f"            Theme: {match['theme']}")
        else:
            print(f"    ⚠️ {pattern_name.replace('_', ' ').title()}: No themes found")
    
    # Show cross-pattern themes (most sophisticated)
    if cross_pattern_themes:
        print(f"\n  🧠 Cross-Pattern Sophisticated Themes ({len(cross_pattern_themes)} found):")
        for i, cross_theme in enumerate(cross_pattern_themes[:3]):  # Show top 3
            print(f"    {i+1}. Matches {cross_theme['pattern_count']} pattern categories:")
            for pattern, matches in cross_theme['patterns'].items():
                print(f"       - {pattern.replace('_', ' ').title()}: {matches}")
            print(f"       Theme: {cross_theme['theme']}")
            print()
    
    return {
        'client_id': client_id,
        'total_themes': len(all_themes),
        'pattern_results': pattern_results,
        'cross_pattern_themes': cross_pattern_themes
    }

def analyze_across_all_clients():
    """Analyze sophisticated patterns across all clients"""
    print("🚀 Generic Sophisticated Theme Detection Across All Clients")
    print("=" * 80)
    
    clients = get_all_clients()
    
    if not clients:
        print("❌ No clients found in database")
        return
    
    print(f"📊 Found {len(clients)} clients to analyze")
    
    all_results = []
    
    for client_id in clients:
        try:
            result = detect_sophisticated_patterns(client_id)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"  ❌ Error analyzing {client_id}: {e}")
    
    # Summary across all clients
    print("\n" + "=" * 80)
    print("📋 CROSS-CLIENT SOPHISTICATED THEME SUMMARY")
    print("=" * 80)
    
    total_themes = sum(r['total_themes'] for r in all_results)
    total_cross_pattern = sum(len(r['cross_pattern_themes']) for r in all_results)
    
    print(f"📊 Total Themes Analyzed: {total_themes}")
    print(f"🧠 Total Sophisticated Themes Found: {total_cross_pattern}")
    
    # Find the most sophisticated themes across all clients
    all_cross_pattern_themes = []
    for result in all_results:
        for theme in result['cross_pattern_themes']:
            theme['client_id'] = result['client_id']
            all_cross_pattern_themes.append(theme)
    
    if all_cross_pattern_themes:
        # Sort by pattern count (most sophisticated first)
        all_cross_pattern_themes.sort(key=lambda x: x['pattern_count'], reverse=True)
        
        print(f"\n🏆 TOP SOPHISTICATED THEMES ACROSS ALL CLIENTS:")
        for i, theme in enumerate(all_cross_pattern_themes[:5]):  # Top 5
            print(f"\n  {i+1}. Client: {theme['client_id']}")
            print(f"     Pattern Categories: {theme['pattern_count']}")
            print(f"     Patterns: {list(theme['patterns'].keys())}")
            print(f"     Theme: {theme['theme']}")
    
    # Pattern frequency across clients
    print(f"\n📈 PATTERN FREQUENCY ACROSS CLIENTS:")
    pattern_frequency = {}
    
    for result in all_results:
        for pattern_name, pattern_result in result['pattern_results'].items():
            if pattern_name not in pattern_frequency:
                pattern_frequency[pattern_name] = 0
            if pattern_result['count'] > 0:
                pattern_frequency[pattern_name] += 1
    
    for pattern_name, frequency in sorted(pattern_frequency.items(), key=lambda x: x[1], reverse=True):
        pattern_title = pattern_name.replace('_', ' ').title()
        print(f"  - {pattern_title}: Found in {frequency}/{len(clients)} clients")

def main():
    """Run the generic sophisticated theme detection"""
    analyze_across_all_clients()
    
    print("\n🎯 Summary:")
    print("This analysis shows sophisticated themes across ALL your clients.")
    print("Look for themes that match multiple pattern categories:")
    print("- Scale Evolution + Infrastructure Complexity + Strategic Decisions")
    print("- Customer Journey + Business Model Evolution + Strategic Decisions")
    print("- Any combination of 3+ pattern categories = Sophisticated Theme!")

if __name__ == '__main__':
    main() 