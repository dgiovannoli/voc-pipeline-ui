#!/usr/bin/env python3
"""
Debug script to isolate the unhashable type error in theme generation
"""

import sys
import traceback
from win_loss_report_generator import WinLossReportGenerator

def debug_theme_generation():
    """Debug the theme generation process step by step"""
    try:
        print("🔍 Starting debug of theme generation...")
        
        # Initialize generator
        gen = WinLossReportGenerator('Supio')
        print("✅ Generator initialized")
        
        # Load data
        print("📊 Loading data...")
        quotes_data = gen._load_enhanced_data()
        print(f"✅ Loaded {len(quotes_data)} quotes")
        
        # Set quality gates
        print("🎯 Setting quality gates...")
        gen._set_adaptive_quality_gates(quotes_data)
        print("✅ Quality gates set")
        
        # Group by subjects
        print("📋 Grouping by subjects...")
        subject_groups = gen._group_by_harmonized_subjects(quotes_data)
        print(f"✅ Grouped into {len(subject_groups)} subjects")
        
        # Identify theme clusters
        print("🔍 Identifying theme clusters...")
        theme_clusters = gen._identify_theme_clusters(subject_groups)
        print(f"✅ Identified {len(theme_clusters)} theme clusters")
        
        # Apply quality gates
        print("🚪 Applying quality gates...")
        validated_themes = gen._apply_quality_gates(theme_clusters)
        print(f"✅ {len(validated_themes)} themes passed quality gates")
        
        # Test theme statement generation for first theme
        if validated_themes:
            print("📝 Testing theme statement generation...")
            first_theme = validated_themes[0]
            
            # Test each step individually
            print("  - Testing research alignment analysis...")
            quotes = first_theme["quotes"]
            research_alignment = gen._analyze_theme_research_alignment(quotes)
            print("    ✅ Research alignment analysis completed")
            
            print("  - Testing customer quote analysis...")
            quote_analysis = gen._analyze_customer_quotes(quotes)
            print("    ✅ Customer quote analysis completed")
            
            print("  - Testing theme statement generation...")
            theme_statement = gen._generate_research_driven_theme_statement(
                quotes, first_theme["theme_type"], first_theme["harmonized_subject"], research_alignment
            )
            print("    ✅ Theme statement generation completed")
            
            print("  - Testing theme title generation...")
            theme_title = gen._generate_research_driven_theme_title(
                research_alignment, first_theme["theme_type"], first_theme["harmonized_subject"]
            )
            print("    ✅ Theme title generation completed")
            
            print("  - Testing company distribution calculation...")
            company_distribution = gen._calculate_company_distribution(quotes)
            print("    ✅ Company distribution calculation completed")
            
            print("  - Testing full theme generation...")
            final_themes = gen._generate_theme_statements([first_theme])
            print(f"    ✅ Full theme generation completed: {len(final_themes)} themes")
            
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = debug_theme_generation()
    if success:
        print("✅ Debug completed successfully")
    else:
        print("❌ Debug failed") 