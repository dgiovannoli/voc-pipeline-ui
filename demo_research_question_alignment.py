#!/usr/bin/env python3
"""
Demo research question alignment with actual Supio data
"""

import sys
import os
from pathlib import Path
import json
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_stage2_with_research_questions import EnhancedStage2WithResearchQuestions
from supabase_database import SupabaseDatabase

def demo_research_question_alignment_with_supio():
    """Demo research question alignment with actual Supio data"""
    
    print("🎯 Research Question Alignment Demo with Supio Data")
    print("=" * 60)
    
    # Initialize the enhanced processor
    processor = EnhancedStage2WithResearchQuestions()
    
    # Load research questions
    research_questions = processor._load_research_questions('Supio')
    print(f"📋 Loaded {len(research_questions)} research questions from Supio discussion guide")
    print()
    
    # Get actual Supio responses
    db = SupabaseDatabase()
    df = db.get_stage1_data_responses(client_id='Supio')
    
    print(f"📊 Found {len(df)} Supio responses in database")
    
    # Take a sample of 5 responses for demo
    sample_responses = df.head(5).to_dict('records')
    
    print(f"🔍 Analyzing {len(sample_responses)} sample responses...")
    print()
    
    # Process each sample response
    for i, response in enumerate(sample_responses, 1):
        print(f"🔍 Analyzing Response {i}:")
        print(f"   Text: {response['verbatim_response'][:100]}...")
        print(f"   Subject: {response.get('harmonized_subject', 'Unknown')}")
        print(f"   Company: {response.get('company', 'Unknown')}")
        print()
        
        # Analyze the response
        analysis_result = processor._analyze_sentiment_impact_and_research_questions(response, research_questions)
        
        # Display results
        print(f"   📊 Analysis Results:")
        print(f"      Sentiment: {analysis_result['sentiment']}")
        print(f"      Impact Score: {analysis_result['impact_score']}/5")
        print(f"      Questions Addressed: {analysis_result['total_questions_addressed']}")
        print(f"      Coverage Summary: {analysis_result['coverage_summary']}")
        
        # Show research question alignments
        if analysis_result['research_question_alignment']:
            print(f"      📋 Research Question Alignments:")
            for alignment in analysis_result['research_question_alignment']:
                print(f"         • {alignment['question_text'][:50]}...")
                print(f"           Alignment Score: {alignment['alignment_score']}/5")
                print(f"           Priority: {alignment['coverage_priority']}")
                print(f"           Keywords: {', '.join(alignment['keywords_matched'])}")
        else:
            print(f"      ❌ No research question alignments found")
        
        print()
        print("-" * 60)
        print()
    
    # Show summary statistics
    print("📊 Demo Summary:")
    print(f"   • Analyzed {len(sample_responses)} Supio responses")
    print(f"   • Against {len(research_questions)} research questions")
    print(f"   • Enhanced Stage 2 processor ready for production use")
    print()
    print("✅ Research Question Alignment Demo Complete!")
    
    # Now generate the Excel workbook
    print("\n📊 Generating Excel workbook with research question alignment...")
    from excel_win_loss_exporter import ExcelWinLossExporter
    from win_loss_ui import WinLossReportGenerator
    
    # Generate themes data
    generator = WinLossReportGenerator()
    themes_data = generator.generate_analyst_report('Supio')
    
    # Create Excel workbook
    exporter = ExcelWinLossExporter()
    output_path = exporter.export_analyst_workbook(themes_data)
    
    print(f"✅ Excel workbook created: {output_path}")
    print("📋 The workbook includes:")
    print("   • Research Question Alignment tab")
    print("   • Enhanced section tabs with research alignment")
    print("   • Coverage analysis and statistics")

if __name__ == "__main__":
    demo_research_question_alignment_with_supio() 