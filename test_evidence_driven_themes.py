#!/usr/bin/env python3
"""
Test script for evidence-driven theme analysis
"""

import os
import sys
from stage4_theme_analyzer_evidence_driven import EvidenceDrivenStage4Analyzer

def test_evidence_driven_themes():
    """Test the evidence-driven theme analysis"""
    
    print("🧪 Testing Evidence-Driven Theme Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = EvidenceDrivenStage4Analyzer('Rev')
    
    # Run analysis
    print("🔄 Running evidence-driven theme analysis...")
    success = analyzer.analyze_themes_evidence_driven()
    
    if success:
        print("✅ Evidence-driven theme analysis completed successfully")
        print("\n📊 Key Improvements:")
        print("- Removed artificial theme counts")
        print("- Added evidence strength validation")
        print("- Separated market themes from product themes")
        print("- Enhanced quality criteria")
        print("- Preserved Rev-specific feedback")
    else:
        print("❌ Evidence-driven theme analysis failed")
    
    # Fetch and display the latest 3 themes for Rev
    from supabase_database import SupabaseDatabase
    db = SupabaseDatabase()
    df = db.get_themes(client_id='Rev')
    print("\n[DEBUG] Raw DataFrame:")
    print(df)
    if hasattr(df, 'to_dict'):
        print("\n[DEBUG] DataFrame as dict:")
        print(df.to_dict())
    if not df.empty:
        print("\n=== Latest Stage 4 Themes for Rev ===")
        for i, row in df.head(3).iterrows():
            print(f"\nTheme ID: {row.get('theme_id', '')}")
            print(f"Title: {row.get('theme_title', '')}")
            print(f"Statement: {row.get('theme_statement', '')}")
            print(f"Primary Quote: {row.get('primary_quote', '')}")
            print(f"Evidence Strength: {row.get('theme_evidence_strength', '')}")
    else:
        print("No Stage 4 themes found for Rev.")

    # Fetch and display the latest 10 themes for all clients (no client_id filter)
    print("\n[DEBUG] Fetching all themes (no client_id filter):")
    df_all = db.get_themes(client_id=None)
    print(f"Raw DataFrame shape: {df_all.shape}")
    print(f"Raw DataFrame columns: {list(df_all.columns)}")
    if not df_all.empty:
        print(f"Raw DataFrame head: {df_all.head()}")
        print("\n=== Latest 10 Stage 4 Themes (All Clients) ===")
        for i, row in df_all.head(10).iterrows():
            print(f"\nTheme ID: {row.get('theme_id', '')}")
            print(f"Client ID: {row.get('client_id', '')}")
            print(f"Title: {row.get('theme_title', '')}")
            print(f"Statement: {row.get('theme_statement', '')}")
            print(f"Primary Quote: {row.get('primary_quote', '')}")
            print(f"Evidence Strength: {row.get('theme_evidence_strength', '')}")
    else:
        print("No Stage 4 themes found in the database.")

    return success

if __name__ == "__main__":
    test_evidence_driven_themes() 