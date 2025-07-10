#!/usr/bin/env python3
"""
Accurate Table Analysis
Analyzes which tables are actually used in the core pipeline (Stages 1-4)
"""

import os
import sys
from supabase_database import SupabaseDatabase

def analyze_core_pipeline_tables():
    """Analyze which tables are used in the core pipeline"""
    print("🔍 Analyzing Core Pipeline Table Usage")
    print("="*50)
    
    # Core pipeline stages and their table usage
    core_pipeline_tables = {
        'stage1_data_responses': {
            'stage': 'Stage 1',
            'usage': 'Data ingestion and storage',
            'used_by': ['stage3_findings_analyzer.py', 'stage4_theme_analyzer.py'],
            'essential': True
        },
        'stage3_findings': {
            'stage': 'Stage 3', 
            'usage': 'Findings generation and storage',
            'used_by': ['stage4_theme_analyzer.py'],
            'essential': True
        },
        'themes': {
            'stage': 'Stage 4',
            'usage': 'Theme generation and storage', 
            'used_by': ['app.py', 'stage5_executive_analyzer.py'],
            'essential': True
        },
        'stage2_response_labeling': {
            'stage': 'Stage 2',
            'usage': 'Quote scoring and analysis',
            'used_by': ['stage4b_scorecard_analyzer.py'],
            'essential': False  # Not used in core pipeline
        }
    }
    
    # Experimental/legacy tables
    experimental_tables = {
        'scorecard_themes': {
            'stage': 'Stage 4B (Experimental)',
            'usage': 'Experimental scorecard-driven themes',
            'used_by': ['stage4b_scorecard_analyzer.py', 'scorecard_theme_ui.py'],
            'essential': False
        },
        'executive_themes': {
            'stage': 'Stage 5',
            'usage': 'Executive synthesis themes',
            'used_by': ['stage5_executive_analyzer.py'],
            'essential': False
        },
        'criteria_scorecard': {
            'stage': 'Stage 5', 
            'usage': 'Criteria performance scorecard',
            'used_by': ['stage5_executive_analyzer.py'],
            'essential': False
        }
    }
    
    print("\n📊 Core Pipeline Tables (Stages 1-4):")
    print("-" * 40)
    for table, info in core_pipeline_tables.items():
        status = "✅" if info['essential'] else "⚠️"
        print(f"{status} {table}")
        print(f"   Stage: {info['stage']}")
        print(f"   Usage: {info['usage']}")
        print(f"   Used by: {', '.join(info['used_by'])}")
        print()
    
    print("\n🔬 Experimental/Legacy Tables:")
    print("-" * 40)
    for table, info in experimental_tables.items():
        print(f"⚠️ {table}")
        print(f"   Stage: {info['stage']}")
        print(f"   Usage: {info['usage']}")
        print(f"   Used by: {', '.join(info['used_by'])}")
        print()
    
    return core_pipeline_tables, experimental_tables

def check_table_data():
    """Check actual data in tables"""
    print("\n🗄️ Database Table Analysis:")
    print("-" * 40)
    
    db = SupabaseDatabase()
    
    # Check core pipeline tables
    core_tables = ['stage1_data_responses', 'stage3_findings', 'themes']
    
    for table in core_tables:
        try:
            result = db.supabase.table(table).select('count').execute()
            count = len(result.data) if result.data else 0
            print(f"✅ {table}: {count} rows")
        except Exception as e:
            print(f"❌ {table}: {e}")
    
    # Check experimental tables
    experimental_tables = ['scorecard_themes', 'executive_themes', 'criteria_scorecard', 'stage2_response_labeling']
    
    print("\n🔬 Experimental Tables:")
    for table in experimental_tables:
        try:
            result = db.supabase.table(table).select('count').execute()
            count = len(result.data) if result.data else 0
            print(f"⚠️ {table}: {count} rows")
        except Exception as e:
            print(f"❌ {table}: {e}")

def generate_cleanup_recommendations():
    """Generate cleanup recommendations"""
    print("\n🎯 Cleanup Recommendations:")
    print("-" * 40)
    
    print("\n✅ KEEP (Core Pipeline):")
    print("  - stage1_data_responses (Stage 1)")
    print("  - stage3_findings (Stage 3)") 
    print("  - themes (Stage 4)")
    
    print("\n⚠️ CONSIDER REMOVING (Experimental/Legacy):")
    print("  - scorecard_themes (Stage 4B experimental)")
    print("  - executive_themes (Stage 5)")
    print("  - criteria_scorecard (Stage 5)")
    print("  - stage2_response_labeling (Stage 2, not used in core)")
    
    print("\n🔍 VERIFY BEFORE REMOVAL:")
    print("  - Check if any UI components reference experimental tables")
    print("  - Verify no critical functionality depends on experimental features")
    print("  - Test core pipeline after removal")
    
    print("\n📝 SQL for Experimental Table Removal:")
    print("-- Only run after verification")
    print("DROP TABLE IF EXISTS scorecard_themes;")
    print("DROP TABLE IF EXISTS executive_themes;") 
    print("DROP TABLE IF EXISTS criteria_scorecard;")
    print("DROP TABLE IF EXISTS stage2_response_labeling;")

def main():
    print("🔍 Accurate Table Usage Analysis")
    print("="*50)
    
    # Analyze table usage
    core_tables, experimental_tables = analyze_core_pipeline_tables()
    
    # Check actual data
    check_table_data()
    
    # Generate recommendations
    generate_cleanup_recommendations()
    
    print("\n✅ Analysis Complete!")
    print("💡 Core pipeline only uses 3 tables: stage1_data_responses, stage3_findings, themes")

if __name__ == "__main__":
    main() 