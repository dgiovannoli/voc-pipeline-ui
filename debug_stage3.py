#!/usr/bin/env python3

from stage3_findings_analyzer import Stage3FindingsAnalyzer

def debug_stage3():
    analyzer = Stage3FindingsAnalyzer()
    df = analyzer.get_scored_quotes('Rev.')
    print(f"Loaded {len(df)} scored quotes")
    
    patterns = analyzer.identify_enhanced_patterns(df)
    print(f"Total criteria with patterns: {len(patterns)}")
    
    for criterion, pattern_list in patterns.items():
        print(f"{criterion}: {len(pattern_list)} patterns")
        for i, pattern in enumerate(pattern_list):
            print(f"  Pattern {i+1}:")
            print(f"    Quote count: {pattern['quote_count']}")
            print(f"    Average score: {pattern['avg_score']:.2f}")
            print(f"    Confidence: {pattern.get('enhanced_confidence', 'N/A')}")
            print(f"    Criteria met: {pattern.get('criteria_met', 'N/A')}")
            print(f"    Company: {pattern.get('company', 'N/A')}")
            
            # Check if this would qualify for findings
            if pattern['avg_score'] >= 3.5:
                print(f"    → Would generate STRENGTH finding")
            elif pattern['avg_score'] <= 2.0:
                print(f"    → Would generate IMPROVEMENT finding")
            else:
                print(f"    → Would generate NEUTRAL finding (score: {pattern['avg_score']:.2f})")

if __name__ == "__main__":
    debug_stage3() 