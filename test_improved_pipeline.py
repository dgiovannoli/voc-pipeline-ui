#!/usr/bin/env python3

"""
Test script for improved Stages 2, 3, and 4 pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stage3_findings_analyzer import run_stage3_analysis
from stage4_theme_analyzer import run_stage4_analysis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_improved_pipeline():
    """Test the improved pipeline with enhanced Stages 2, 3, and 4"""
    
    print("🔍 Testing Improved Pipeline: Stages 2, 3, and 4")
    print("=" * 80)
    
    # Run Stage 3 with improved configuration
    print("\n📊 Running Stage 3: Enhanced Findings Generation...")
    stage3_result = run_stage3_analysis(client_id='Rev')
    
    print(f"\n📈 Stage 3 Results:")
    print(f"Status: {stage3_result.get('status', 'unknown')}")
    print(f"Findings Generated: {stage3_result.get('findings_generated', 0)}")
    print(f"Priority Findings: {stage3_result.get('priority_findings', 0)}")
    print(f"Standard Findings: {stage3_result.get('standard_findings', 0)}")
    
    # Run Stage 4 with improved configuration
    print("\n📊 Running Stage 4: Enhanced Theme Generation...")
    stage4_result = run_stage4_analysis(client_id='Rev')
    
    print(f"\n📈 Stage 4 Results:")
    print(f"Status: {stage4_result.get('status', 'unknown')}")
    print(f"Themes Generated: {stage4_result.get('themes_generated', 0)}")
    print(f"Themes Saved: {stage4_result.get('themes_saved', 0)}")
    print(f"Patterns Analyzed: {stage4_result.get('patterns_analyzed', 0)}")
    
    # Summary
    print(f"\n🎯 Pipeline Summary:")
    print(f"Total Findings: {stage3_result.get('findings_generated', 0)}")
    print(f"Total Themes: {stage4_result.get('themes_generated', 0)}")
    print(f"Success Rate: {stage4_result.get('themes_saved', 0)}/{stage4_result.get('themes_generated', 0)} themes saved")
    
    return {
        'stage3': stage3_result,
        'stage4': stage4_result
    }

if __name__ == "__main__":
    test_improved_pipeline() 