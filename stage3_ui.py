#!/usr/bin/env python3
"""
🎯 STAGE 3 THEME PROCESSING UI
Streamlit interface for Stage 3 theme processing and workbook generation.
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from stage3_theme_processor import Stage3ThemeProcessor
from supio_harmonized_workbook_generator import SupioHarmonizedWorkbookGenerator

def show_stage3_processing_page():
    """
    Stage 3 Theme Processing and Workbook Generation Page
    """
    st.title("🎯 Stage 3 — Generate Research & Discovered Themes")
    st.markdown("Create high-quality themes and generate Supio HARMONIZED workbooks")

    # Client selection
    st.subheader("📋 Client Selection")
    client_id = st.selectbox(
        "Select Client",
        ["Endicia", "Supio", "Rev"],
        index=0
    )

    # Stage 3 Processing Section
    st.subheader("🔬 Stage 3 Theme Processing")
    
    # Advanced options
    with st.expander("Advanced options", expanded=False):
        clear_first = st.checkbox("🧹 Clear existing themes before processing", value=True,
                                  help="Deletes all existing themes for the selected client, then regenerates.")
        disable_tighten = st.checkbox("✅ Preserve Stage 4 two-sentence statements (skip headline tightening)", value=True,
                                      help="Skips the Step 7 tightening so the Stage 4-style theme statements remain intact.")
    
    # Apply environment flags for processing
    if disable_tighten:
        os.environ['STAGE3_TIGHTEN_HEADLINES'] = 'false'
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Process Stage 3 Themes", type="primary"):
            with st.spinner("Processing Stage 3 themes..."):
                try:
                    processor = Stage3ThemeProcessor(client_id)
                    # Optional clear-first
                    if clear_first:
                        deleted = processor.clear_existing_themes()
                        st.info(f"🧹 Cleared {deleted} existing themes for {client_id}")
                    result = processor.process_stage3_themes()
                    
                    if result["success"]:
                        st.success(f"✅ Stage 3 processing completed!")
                        st.json(result)
                        
                        # Store result in session state
                        st.session_state.stage3_result = result
                        st.session_state.stage3_completed = True
                    else:
                        st.error(f"❌ Stage 3 processing failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error during Stage 3 processing: {e}")

    with col2:
        if st.button("📊 Check Processing Status"):
            with st.spinner("Checking status..."):
                try:
                    processor = Stage3ThemeProcessor(client_id)
                    status = processor.get_processing_status()
                    
                    if status.get("has_themes"):
                        st.success(f"✅ Themes found for {client_id}")
                        st.json(status)
                    else:
                        st.warning(f"⚠️ No themes found for {client_id}")
                        st.json(status)
                except Exception as e:
                    st.error(f"❌ Error checking status: {e}")
        
    # Display current status
    if st.button("🔄 Refresh Status"):
        st.rerun()

    # Workbook Generation Section
    st.subheader("📊 Workbook Generation")
    
    # Check if Stage 3 is completed
    stage3_completed = st.session_state.get('stage3_completed', False)
    
    if stage3_completed:
        st.success("✅ Stage 3 processing completed - ready for workbook generation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Generate Supio HARMONIZED Workbook", type="primary"):
                with st.spinner("Generating workbook..."):
                    try:
                        generator = SupioHarmonizedWorkbookGenerator(client_id)
                        workbook_path = generator.generate_workbook()
                        
                        st.success(f"✅ Workbook generated successfully!")
                        st.info(f"📁 File: {workbook_path}")
                        
                        # Get workbook stats
                        stats = generator.get_generation_stats()
                        st.json(stats)
                        
                        # Store in session state
                        st.session_state.workbook_path = workbook_path
                        st.session_state.workbook_stats = stats
                    except Exception as e:
                        st.error(f"❌ Error generating workbook: {e}")
        
        with col2:
            if st.button("📊 View Workbook Stats"):
                if 'workbook_stats' in st.session_state:
                    st.json(st.session_state.workbook_stats)
                else:
                    st.info("Generate a workbook first to view stats")
    
    else:
        st.info("ℹ️ Complete Stage 3 processing first to generate workbooks")

    # Processing Pipeline Overview
    st.subheader("🔄 Processing Pipeline")
    
    with st.expander("📋 Pipeline Overview", expanded=True):
        st.markdown("""
        ### **Stage 3 Processing Pipeline**
        
        1. **📋 Extract Discussion Questions**
           - Parse interview metadata for discussion guides
           - Extract research questions using LLM
           - Fallback to default questions if needed
        
        2. **🔬 Generate Research Themes**
           - Match quotes to research questions
           - Create theme statements using LLM
           - Link supporting quotes and metadata
        
        3. **🔍 Generate Discovered Themes**
           - Analyze patterns in sentiment, deal status, company data
           - Create pattern-based themes using LLM
           - Link supporting quotes and metadata
        
        4. **✨ Enhance Themes**
           - Calculate evidence strength and sentiment coherence
           - Add company coverage and deal status breakdown
           - Generate harmonized subjects
        
        5. **💾 Save to Database**
           - Store all themes in research_themes table
           - Link supporting quotes properly
           - Ready for workbook generation
        
        ### **Workbook Generation**
        
        - **Supio HARMONIZED Quality**: Matches exact Supio report structure
        - **Research Themes Tab**: Guide-seeded themes with supporting quotes
        - **Discovered Themes Tab**: Pattern-based themes with supporting quotes
        - **Professional Styling**: Auto-adjusted columns, borders, formatting
        - **Fast Generation**: Uses pre-processed themes (no LLM calls during generation)
        """)

    # Performance Metrics
    st.subheader("📈 Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'stage3_result' in st.session_state:
            result = st.session_state.stage3_result
            st.metric("Research Themes", result.get("research_themes", 0))
    
    with col2:
        if 'stage3_result' in st.session_state:
            result = st.session_state.stage3_result
            st.metric("Discovered Themes", result.get("discovered_themes", 0))
    
    with col3:
        if 'stage3_result' in st.session_state:
            result = st.session_state.stage3_result
            st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")

    # File Management
    st.subheader("📁 File Management")
    
    if st.button("🗂️ List Generated Files"):
        import glob
        files = glob.glob(f"*{client_id}*HARMONIZED*.xlsx")
        
        if files:
            st.success(f"Found {len(files)} generated workbooks:")
            for file in sorted(files, reverse=True):
                st.write(f"📄 {file}")
        else:
            st.info("No generated workbooks found")

    # Configuration
    st.subheader("⚙️ Configuration")
    
    with st.expander("🔧 Advanced Settings"):
        st.markdown("""
        ### **LLM Configuration**
        - **Model**: gpt-4o-mini
        - **Temperature**: 0.3 (balanced creativity/consistency)
        - **Max Tokens**: 200 (concise theme statements)
        
        ### **Theme Generation**
        - **Minimum Quotes**: 2 for research themes, 3-5 for discovered themes
        - **Confidence Scores**: 0.9 for research, 0.8 for discovered
        - **Evidence Strength**: Calculated from quote count, company coverage, confidence
        
        ### **Database Schema**
        - **Theme ID**: UUID format
        - **Status**: 'draft' (database constraint)
        - **Origin**: 'research' (database constraint)
        - **Supporting Quotes**: Array of response_id strings
        """)

def show_stage3_findings():
    """
    Stage 3: Findings - Identify key findings and insights from labeled quotes
    This is the original Stage 3 findings function that the main app expects
    """
    st.title("🔍 Stage 3 — Generate Themes")
    st.markdown("Creates research-seeded and discovered themes from Stage 2 analysis; use the processing screen if not yet generated.")
    
    # Get client ID from session state
    client_id = st.session_state.get('client_id', '')
    
    if not client_id:
        st.warning("⚠️ Please set a Client ID in the sidebar first")
        st.info("💡 Enter a unique identifier for this client's data (e.g., 'Supio', 'Rev')")
        return
    
    # Display client info
    st.subheader(f"🏢 Client: {client_id}")
    
    # Check if Stage 3 themes exist
    try:
        from stage3_theme_processor import Stage3ThemeProcessor
        processor = Stage3ThemeProcessor(client_id)
        status = processor.get_processing_status()
        
        if status.get("has_themes"):
            st.success(f"✅ Found {status.get('total_themes', 0)} themes for {client_id}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Research Themes", status.get("research_themes", 0))
            with col2:
                st.metric("Discovered Themes", status.get("discovered_themes", 0))
            with col3:
                st.metric("Total Quotes Linked", status.get("total_quotes_linked", 0))
            
            # Show theme processing status
            st.info("🎯 Stage 3 themes have been processed. You can now generate workbooks.")
        else:
            st.info("📊 No Stage 3 themes found yet. Process themes first to generate findings.")
            
        # Inline processing controls
        st.markdown("---")
        st.subheader("🚀 Generate Themes Now")
        with st.expander("Advanced options", expanded=False):
            clear_first = st.checkbox(
                "🧹 Clear existing themes before processing",
                value=not status.get("has_themes", False),
                help="Deletes existing themes for this client, then regenerates"
            )
            preserve_stage4_style = st.checkbox(
                "✅ Preserve Stage 4 two-sentence statements (skip headline tightening)",
                value=True,
                help="Skips extra tightening so Stage 4-style statements remain intact"
            )
        if st.button("🚀 Process Stage 3 Themes", type="primary"):
            with st.spinner("Processing Stage 3 themes..."):
                try:
                    if preserve_stage4_style:
                        os.environ['STAGE3_TIGHTEN_HEADLINES'] = 'false'
                    proc = Stage3ThemeProcessor(client_id)
                    if clear_first:
                        deleted = proc.clear_existing_themes()
                        st.info(f"🧹 Cleared {deleted} existing themes for {client_id}")
                    result = proc.process_stage3_themes()
                    if result.get("success"):
                        st.success("✅ Stage 3 processing completed!")
                        st.json(result)
                        st.rerun()
                    else:
                        st.error(f"❌ Stage 3 processing failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error during Stage 3 processing: {e}")
     
    except Exception as e:
        st.error(f"❌ Error checking Stage 3 status: {e}")
        st.info("📊 Please ensure Stage 3 theme processing is completed first")

def main():
    """Main entry point for standalone Stage 3 UI"""
    st.set_page_config(
        page_title="Stage 3 Theme Processing",
        page_icon="🎯",
        layout="wide"
    )
    
    show_stage3_processing_page()

if __name__ == "__main__":
    main() 