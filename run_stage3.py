#!/usr/bin/env python3
"""
Stage 3: Enhanced Findings Identification Runner (Buried Wins v4.0)
Run this script to generate executive findings with automated confidence scoring
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run enhanced Stage 3 analysis"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Stage 3: Enhanced Findings Identification')
    parser.add_argument('--client_id', type=str, default='default', 
                       help='Client ID to process (default: default)')
    args = parser.parse_args()
    
    print("🎯 Stage 3: Enhanced Findings Identification (Buried Wins v4.0)")
    print("=" * 70)
    print(f"📋 Processing client: {args.client_id}")
    
    try:
        from stage3_findings_analyzer import Stage3FindingsAnalyzer
        
        # Initialize analyzer
        analyzer = Stage3FindingsAnalyzer()
        
        # Run enhanced analysis with specified client ID
        print("🔍 Processing scored quotes and generating enhanced findings...")
        result = analyzer.process_enhanced_findings(client_id='Rev')  # Changed from 'default' to 'Rev'
        
        if result and result.get('status') == 'success':
            print(f"✅ Enhanced Stage 3 complete!")
            print(f"📊 Quotes processed: {result.get('quotes_processed', 0)}")
            print(f"🔍 Patterns identified: {result.get('patterns_identified', 0)}")
            print(f"🎯 Findings generated: {result.get('findings_generated', 0)}")
            print(f"⭐ Priority findings: {result.get('priority_findings', 0)}")
            print(f"📋 Standard findings: {result.get('standard_findings', 0)}")
            
            # Show enhanced summary
            summary = result.get('summary', {})
            if summary:
                print(f"\n📈 Enhanced Summary:")
                print(f"   Total findings: {summary.get('total_findings', 0)}")
                print(f"   Priority findings (≥4.0): {summary.get('priority_findings', 0)}")
                print(f"   Standard findings (≥3.0): {summary.get('standard_findings', 0)}")
                print(f"   Criteria covered: {summary.get('criteria_covered', 0)}/10")
                print(f"   Average confidence score: {summary.get('average_confidence_score', 0):.2f}/10.0")
                print(f"   Average criteria met: {summary.get('average_criteria_met', 0):.1f}/8")
                print(f"   Companies affected: {summary.get('total_companies_affected', 0)}")
                
                # Show finding type distribution
                finding_types = summary.get('finding_type_distribution', {})
                if finding_types:
                    print(f"\n📊 Finding Type Distribution:")
                    for finding_type, count in finding_types.items():
                        print(f"   {finding_type}: {count}")
                
                # Show priority level distribution
                priority_levels = summary.get('priority_level_distribution', {})
                if priority_levels:
                    print(f"\n🎯 Priority Level Distribution:")
                    for priority, count in priority_levels.items():
                        print(f"   {priority}: {count}")
        else:
            print("❌ Enhanced Stage 3 analysis failed or no data found")
            if result:
                print(f"   Status: {result.get('status')}")
                print(f"   Message: {result.get('message', 'No message')}")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required packages are installed:")
        print("   pip install supabase langchain-openai pandas pyyaml")
    except Exception as e:
        print(f"❌ Error running enhanced Stage 3 analysis: {e}")

if __name__ == "__main__":
    main() 