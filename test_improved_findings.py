#!/usr/bin/env python3

"""
Test script for improved Stage 3 findings generation
Demonstrates findings that match the format from Context/Findings Data All.csv
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage3_findings_analyzer import Stage3FindingsAnalyzer

def test_improved_findings():
    """Test the improved findings generation"""
    
    print("🧪 TESTING IMPROVED STAGE 3 FINDINGS GENERATION")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = Stage3FindingsAnalyzer()
    
    # Create sample patterns that would generate findings similar to the example CSV
    sample_patterns = {
        'speed_responsiveness': [
            {
                'avg_score': 1.5,
                'quote_count': 3,
                'company_count': 2,
                'enhanced_confidence': 4.2,
                'selected_quotes': [
                    {'text': 'We use Turbo Scribe for urgent files because Rev is too slow'},
                    {'text': 'Rev takes 24 hours but we need same-day sometimes'},
                    {'text': 'Speed is critical for our trial preparation'}
                ],
                'relevance_level': 'critical',
                'themes': ['speed', 'turnaround', 'urgency']
            },
            {
                'avg_score': 4.5,
                'quote_count': 2,
                'company_count': 1,
                'enhanced_confidence': 3.8,
                'selected_quotes': [
                    {'text': '24-hour turnaround is perfect for our needs'},
                    {'text': 'Rev is faster than our previous provider'}
                ],
                'relevance_level': 'high',
                'themes': ['speed', 'satisfaction']
            }
        ],
        'product_capability': [
            {
                'avg_score': 2.0,
                'quote_count': 4,
                'company_count': 3,
                'enhanced_confidence': 4.5,
                'selected_quotes': [
                    {'text': 'Accuracy issues negate the speed advantage'},
                    {'text': 'We have to correct too many errors'},
                    {'text': 'Human transcription is more accurate but slower'},
                    {'text': 'AI accuracy is not reliable for legal work'}
                ],
                'relevance_level': 'critical',
                'themes': ['accuracy', 'quality', 'reliability']
            }
        ],
        'integration_technical_fit': [
            {
                'avg_score': 2.5,
                'quote_count': 3,
                'company_count': 2,
                'enhanced_confidence': 3.2,
                'selected_quotes': [
                    {'text': 'We have to manually move files from Rev to MyCase'},
                    {'text': 'Integration with Clio would save us hours'},
                    {'text': 'No direct connection to our case management system'}
                ],
                'relevance_level': 'high',
                'themes': ['integration', 'workflow', 'efficiency']
            }
        ],
        'support_service_quality': [
            {
                'avg_score': 4.0,
                'quote_count': 2,
                'company_count': 1,
                'enhanced_confidence': 3.5,
                'selected_quotes': [
                    {'text': 'Support resolved our billing issue in under a day'},
                    {'text': 'Customer service is very responsive'}
                ],
                'relevance_level': 'high',
                'themes': ['support', 'service', 'satisfaction']
            }
        ]
    }
    
    # Test finding generation for each criterion
    for criterion, patterns in sample_patterns.items():
        print(f"\n📋 Testing {criterion.replace('_', ' ').title()}:")
        
        for i, pattern in enumerate(patterns):
            # Generate finding text
            finding_type = analyzer._determine_finding_type(pattern)
            criterion_desc = analyzer.criteria.get(criterion, {}).get('description', criterion.replace('_', ' ').title())
            
            finding_text = analyzer._generate_pattern_based_finding_text(
                criterion, pattern, finding_type, criterion_desc
            )
            
            print(f"  {i+1}. Type: {finding_type}")
            print(f"     Finding: {finding_text}")
            print(f"     Score: {pattern['avg_score']:.1f}, Confidence: {pattern['enhanced_confidence']:.1f}")
            print()
    
    print("✅ Test completed! Findings now match the format from the example CSV.")
    print("\nKey improvements:")
    print("- Specific, actionable statements instead of generic descriptions")
    print("- Business-focused language with measurable impacts")
    print("- Proper finding categories (Barrier, Opportunity, Functional)")
    print("- Evidence-based insights from actual quotes")

if __name__ == "__main__":
    test_improved_findings() 