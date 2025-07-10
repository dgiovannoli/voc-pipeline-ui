#!/usr/bin/env python3
"""
Debug script to understand Stage 3 findings generation
"""

from stage3_findings_analyzer import Stage3FindingsAnalyzer
from supabase_database import SupabaseDatabase
import pandas as pd

def debug_stage3():
    """Debug Stage 3 findings generation"""
    
    print("🔍 DEBUGGING STAGE 3 FINDINGS GENERATION")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = Stage3FindingsAnalyzer()
    db = SupabaseDatabase()
    
    # Get scored quotes
    df = analyzer.get_scored_quotes(client_id='Rev')
    print(f"📊 Total scored quotes: {len(df)}")
    
    # Check criteria distribution
    print(f"\n📈 Criteria distribution:")
    criteria_counts = df['criterion'].value_counts()
    for criterion, count in criteria_counts.items():
        print(f"  {criterion}: {count} quotes")
    
    # Check company distribution
    print(f"\n🏢 Company distribution:")
    company_counts = df['company'].value_counts()
    for company, count in company_counts.head(10).items():
        print(f"  {company}: {count} quotes")
    
    # Debug pattern identification for each criterion
    print(f"\n🔍 PATTERN IDENTIFICATION DEBUG:")
    print("-" * 60)
    
    thresholds = analyzer.config['stage3']['pattern_thresholds']
    print(f"Thresholds: {thresholds}")
    
    for criterion in criteria_counts.index:
        print(f"\n📋 Criterion: {criterion}")
        criterion_data = df[df['criterion'] == criterion].copy()
        print(f"  Total quotes: {len(criterion_data)}")
        
        if len(criterion_data) < thresholds['minimum_quotes']:
            print(f"  ❌ Skipped: Below minimum quotes threshold ({thresholds['minimum_quotes']})")
            continue
        
        # Group by company
        company_groups = criterion_data.groupby('company')
        print(f"  Companies: {len(company_groups)}")
        
        valid_companies = 0
        for company, company_quotes in company_groups:
            if len(company_quotes) >= 2:  # Need at least 2 quotes for pattern
                valid_companies += 1
                print(f"    {company}: {len(company_quotes)} quotes")
        
        print(f"  Valid companies (≥2 quotes): {valid_companies}")
        
        if valid_companies < thresholds['minimum_companies']:
            print(f"  ❌ Skipped: Below minimum companies threshold ({thresholds['minimum_companies']})")
            continue
        
        # Test pattern analysis
        try:
            company_patterns = analyzer._analyze_enhanced_company_patterns(criterion_data, criterion)
            print(f"  Patterns generated: {len(company_patterns)}")
            
            # Check each pattern
            valid_patterns = 0
            for i, pattern in enumerate(company_patterns):
                print(f"    Pattern {i+1}: {pattern['quote_count']} quotes, {pattern['company_count']} companies")
                
                if (pattern['quote_count'] >= thresholds['minimum_quotes'] and
                    pattern['company_count'] >= thresholds['minimum_companies']):
                    
                    # Check if pattern has quotes_data
                    if not pattern.get('quotes_data'):
                        print(f"      ❌ Skipped: No quotes_data")
                        continue
                    
                    # Evaluate criteria
                    criteria_scores = analyzer.evaluate_finding_criteria(pattern['quotes_data'])
                    criteria_met = sum(criteria_scores.values())
                    print(f"      Criteria met: {criteria_met}/8")
                    
                    if criteria_met >= thresholds['minimum_criteria_met']:
                        # Calculate confidence
                        enhanced_confidence = analyzer.calculate_enhanced_confidence_score(
                            pattern['quotes_data'], criteria_scores
                        )
                        print(f"      Confidence: {enhanced_confidence:.1f}")
                        
                        if enhanced_confidence >= analyzer.config['stage3']['confidence_thresholds']['minimum_confidence']:
                            # Check selected quotes
                            selected_quotes = analyzer.select_optimal_quotes(pattern['quotes_data'])
                            if selected_quotes:
                                valid_patterns += 1
                                print(f"      ✅ Valid pattern")
                            else:
                                print(f"      ❌ Skipped: No selected quotes")
                        else:
                            print(f"      ❌ Skipped: Below confidence threshold")
                    else:
                        print(f"      ❌ Skipped: Below criteria threshold")
                else:
                    print(f"      ❌ Skipped: Below quote/company thresholds")
            
            print(f"  Final valid patterns: {valid_patterns}")
            
        except Exception as e:
            print(f"  ❌ Error in pattern analysis: {e}")
    
    # Test full pattern identification
    print(f"\n🔍 FULL PATTERN IDENTIFICATION TEST:")
    print("-" * 60)
    
    try:
        patterns = analyzer.identify_enhanced_patterns(df)
        print(f"Total patterns identified: {sum(len(p) for p in patterns.values())}")
        for criterion, criterion_patterns in patterns.items():
            print(f"  {criterion}: {len(criterion_patterns)} patterns")
    except Exception as e:
        print(f"❌ Error in full pattern identification: {e}")

if __name__ == "__main__":
    debug_stage3() 