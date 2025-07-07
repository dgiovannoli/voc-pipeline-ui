#!/usr/bin/env python3

"""
Test script for enhanced Stage 2 analyzer with quality tracking and GPT-4o-mini
"""

import os
import sys
from datetime import datetime
from enhanced_stage2_analyzer import SupabaseStage2Analyzer

def test_enhanced_stage2():
    """Test the enhanced Stage 2 analyzer with new features"""
    
    print("🧪 TESTING ENHANCED STAGE 2 ANALYZER")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = SupabaseStage2Analyzer()
    
    # Test configuration loading
    print(f"\n📋 Configuration Test:")
    print(f"Model: {analyzer.config['processing'].get('model', 'unknown')}")
    print(f"Max quote length: {analyzer.config['processing']['max_quote_length']}")
    print(f"Max tokens: {analyzer.config['processing'].get('max_tokens', 'unknown')}")
    print(f"Quality tracking enabled: {analyzer.config.get('quality_tracking', {}).get('track_truncation', False)}")
    
    # Test with a sample quote that would have been truncated before
    test_quote = {
        'response_id': 'test_enhanced_1',
        'verbatim_response': """
        I think I'm the only one that's really using it right now, so I wouldn't say it's for the firm yet. 
        I've been using it and to test it out and see if it's something that I should push to have more widespread adoption. 
        But part of it for me is that historically, either we need to find a vendor who we send files to, and then they do human transcription services, and it takes time. 
        It's expensive. And I would rather, while doing an investigation, upload a series of videos, audio files, and then within minutes, have audio transcription, an actual transcript ready. 
        And have it mostly be. I mean, accuracy is important with this. So every time I've used it, I've needed to go through and edit, do some extensive editing. 
        Because we need as faithful a recreation as possible. Faithful transcription as possible. So yeah. I think it's the speed and expense that really turned me on to it. 
        Yeah, it lets me just get work done in a more timely manner instead of waiting and then checking emails with some other service and be like, is it ready yet? It's frustrating.
        """.strip(),
        'subject': 'Transcription Efficiency',
        'question': 'How has Rev improved your workflow?',
        'deal_status': 'closed won',
        'company': 'Test Company',
        'interviewee_name': 'Test User'
    }
    
    print(f"\n🔍 Testing quote analysis with enhanced features:")
    print(f"Original quote length: {len(test_quote['verbatim_response'])} characters")
    print(f"Max allowed length: {analyzer.config['processing']['max_quote_length']} characters")
    
    # Test the analysis
    try:
        result = analyzer.analyze_single_quote(test_quote)
        
        if result:
            print(f"✅ Analysis successful!")
            print(f"Criteria scored: {len(result.get('scores', {}))}")
            print(f"Quality metrics: {result.get('quality_metrics', {})}")
            
            # Check quality tracking
            quality_metrics = analyzer.quality_metrics
            print(f"\n📊 Quality Metrics:")
            print(f"Quotes exceeding length: {quality_metrics['quotes_exceeding_length']}")
            print(f"Truncated quotes: {quality_metrics['truncated_quotes']}")
            print(f"Context preservation issues: {quality_metrics['context_preservation_issues']}")
            
        else:
            print("❌ Analysis failed")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    
    print(f"\n✅ Enhanced Stage 2 test completed!")

if __name__ == "__main__":
    test_enhanced_stage2() 