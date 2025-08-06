#!/usr/bin/env python3
"""
Test Subject-Driven Stage 2 Enhancement
Demonstrates the new subject-to-criteria mapping system.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_subject_driven_stage2 import SubjectDrivenStage2Analyzer
from supabase_database import SupabaseDatabase

def test_subject_driven_analyzer():
    """Test the enhanced subject-driven Stage 2 analyzer"""
    
    print("🧪 Testing Subject-Driven Stage 2 Enhancement")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize the enhanced analyzer
        print("🔧 Initializing enhanced analyzer...")
        analyzer = SubjectDrivenStage2Analyzer()
        
        # Test subject-to-criteria mapping
        print("\n🎯 Testing Subject-to-Criteria Mapping:")
        test_subjects = [
            "Product Features",
            "Integration Challenges", 
            "Pricing and Cost",
            "Adoption Challenges",
            "Competitive Analysis",
            "Unknown Subject"  # Should use default
        ]
        
        for subject in test_subjects:
            criterion = analyzer.get_criterion_from_subject(subject)
            quality = analyzer.get_quality_weight(subject)
            print(f"  '{subject}' → '{criterion}' (quality: {quality})")
        
        # Test multi-criteria detection
        print("\n🔍 Testing Multi-Criteria Detection:")
        test_responses = [
            "The product is good and also very expensive",
            "Integration was difficult but support was excellent", 
            "The pricing is reasonable"
        ]
        
        for response in test_responses:
            flag = analyzer.should_flag_multi_criteria(response)
            print(f"  '{response[:40]}...' → Multi-criteria: {flag}")
        
        # Test with real data (if available)
        print("\n📊 Testing with Real Data:")
        db = SupabaseDatabase()
        
        # Check if there's data for Supio client
        responses_df = db.get_stage1_data_responses(client_id="Supio")
        
        if not responses_df.empty:
            print(f"  Found {len(responses_df)} Stage 1 responses for Supio")
            
            # Show subject distribution
            subject_counts = responses_df['subject'].value_counts()
            print(f"  Subject distribution:")
            for subject, count in subject_counts.head(5).items():
                criterion = analyzer.get_criterion_from_subject(subject)
                print(f"    {subject}: {count} responses → {criterion}")
            
            # Test analysis on a few responses
            print(f"\n🔬 Testing analysis on sample responses:")
            sample_responses = responses_df.head(3)
            
            for idx, row in sample_responses.iterrows():
                result = analyzer.analyze_response(row.to_dict())
                if result:
                    print(f"    Response {result.get('quote_id', 'unknown')}:")
                    print(f"      Subject: {result.get('original_subject')}")
                    print(f"      Mapped to: {result.get('mapped_criterion')}")
                    print(f"      Quality weight: {result.get('quality_weight')}")
                    print(f"      Routing confidence: {result.get('routing_confidence', 0):.2f}")
                    print(f"      Multi-criteria flag: {result.get('multi_criteria_candidate')}")
        else:
            print("  No Stage 1 data found for testing")
        
        print(f"\n✅ Subject-driven enhancement test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_loading():
    """Test that the configuration file loads correctly"""
    print("\n⚙️ Testing Configuration Loading:")
    
    try:
        analyzer = SubjectDrivenStage2Analyzer()
        
        print(f"  Loaded {len(analyzer.subject_to_criteria)} subject mappings")
        print(f"  Loaded {len(analyzer.quality_weights)} quality weights")
        print(f"  Configuration: {analyzer.analysis_config}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Subject-Driven Stage 2 Enhancement Tests\n")
    
    # Test configuration loading
    config_test = test_configuration_loading()
    
    # Test analyzer functionality
    analyzer_test = test_subject_driven_analyzer()
    
    # Summary
    print(f"\n📈 Test Summary:")
    print(f"  Configuration loading: {'✅ PASS' if config_test else '❌ FAIL'}")
    print(f"  Analyzer functionality: {'✅ PASS' if analyzer_test else '❌ FAIL'}")
    
    if config_test and analyzer_test:
        print(f"\n🎉 All tests passed! Enhanced system is ready to use.")
        print(f"\n💡 To run with your data:")
        print(f"   python enhanced_subject_driven_stage2.py Supio --max-responses 10")
    else:
        print(f"\n⚠️ Some tests failed. Please check the configuration and dependencies.") 