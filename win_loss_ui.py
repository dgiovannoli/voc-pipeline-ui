#!/usr/bin/env python3
"""
Win-Loss Report Generator UI
Streamlit interface for generating analyst-ready win-loss curation spreadsheets.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import time
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from win_loss_report_generator import WinLossReportGenerator, winloss_progress_data, winloss_progress_lock
from excel_win_loss_exporter import ExcelWinLossExporter

# Page configuration
st.set_page_config(
    page_title="Win-Loss Report Generator",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main Streamlit application"""
    
    # Title and description
    st.title("🏆 Win-Loss Report Generator")
    st.markdown("""
    **Transform your voice-of-customer data into executive-ready win-loss analysis spreadsheets.**
    
    This system generates high-quality themes using Stage 4 quality gates and creates comprehensive 
    Excel workbooks for analyst curation workflow.
    """)
    
    # Sidebar for client selection and controls
    with st.sidebar:
        st.header("🎯 Generation Controls")
        
        # Client selection
        client_id = st.selectbox(
            "Select Client",
            ["Supio", "Rev", "default"],
            index=0,
            help="Choose the client for win-loss analysis"
        )
        
        # Generation options
        st.subheader("📊 Analysis Options")
        
        adaptive_mode = st.checkbox(
            "Adaptive Quality Gates",
            value=True,
            help="Automatically adjust quality thresholds based on dataset characteristics"
        )
        
        include_competitive = st.checkbox(
            "Enhanced Competitive Intelligence",
            value=True,
            help="Include specialized competitive analysis tabs"
        )
        
        # Advanced settings (collapsible)
        with st.expander("⚙️ Advanced Settings"):
            min_companies = st.slider(
                "Minimum Companies per Theme",
                min_value=1,
                max_value=5,
                value=2,
                help="Minimum number of companies required for theme validation"
            )
            
            min_quotes = st.slider(
                "Minimum Quotes per Theme", 
                min_value=2,
                max_value=10,
                value=3,
                help="Minimum number of quotes required for evidence significance"
            )
            
            min_impact = st.slider(
                "Minimum Impact Score",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.1,
                help="Minimum average impact score for theme inclusion"
            )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Report Generation")
        
        # Generation button
        if st.button("🚀 Generate Win-Loss Report", type="primary", use_container_width=True):
            generate_report(client_id, adaptive_mode, min_companies, min_quotes, min_impact)
        
        # Status and results section
        if 'report_data' in st.session_state:
            display_results()
        
    with col2:
        st.header("📈 Analysis Overview")
        display_quick_stats(client_id)
        
        # Recent files section
        display_recent_files()

def generate_report(client_id: str, adaptive_mode: bool, min_companies: int, min_quotes: int, min_impact: float):
    """Generate the win-loss report with progress tracking"""
    
    # Initialize progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize generator
        generator = WinLossReportGenerator(client_id=client_id)
        
        # Apply manual settings if adaptive mode is disabled
        if not adaptive_mode:
            generator.min_companies_per_theme = min_companies
            generator.min_quotes_per_theme = min_quotes
            generator.min_impact_threshold = min_impact
        
        status_text.text("🔄 Initializing win-loss analysis...")
        
        # Generate report with progress tracking
        with st.spinner("Generating themes and preparing analysis..."):
            start_time = time.time()
            
            # Start generation in a separate thread to track progress
            report_data = generator.generate_analyst_report()
            
            # Update progress (simplified for demo)
            for i in range(6):
                progress_bar.progress((i + 1) / 6)
                time.sleep(0.2)  # Brief delay for visual feedback
            
            generation_time = time.time() - start_time
        
        if report_data["success"]:
            st.success(f"✅ Report generated successfully in {generation_time:.1f} seconds!")
            
            # Store in session state
            st.session_state.report_data = report_data
            st.session_state.generation_time = generation_time
            
            # Generate Excel workbook
            with st.spinner("Creating Excel workbook..."):
                exporter = ExcelWinLossExporter()
                excel_path = exporter.export_analyst_workbook(report_data)
                st.session_state.excel_path = excel_path
            
            st.rerun()
            
        else:
            st.error(f"❌ Error generating report: {report_data['error']}")
            
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
    
    finally:
        progress_bar.empty()
        status_text.empty()

def display_results():
    """Display the generated report results"""
    
    report_data = st.session_state.report_data
    metadata = report_data["metadata"]
    themes = report_data["themes"]
    
    # Summary metrics
    st.subheader("📊 Generation Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Themes Generated", metadata["total_themes"])
    
    with col2:
        st.metric("Quotes Analyzed", metadata["total_quotes"])
    
    with col3:
        st.metric("Companies", metadata["companies_analyzed"])
        
    with col4:
        st.metric("Generation Time", f"{st.session_state.get('generation_time', 0):.1f}s")
    
    # Download section
    st.subheader("📥 Download Results")
    
    if 'excel_path' in st.session_state:
        excel_path = st.session_state.excel_path
        
        # Read the Excel file for download
        with open(excel_path, 'rb') as file:
            excel_data = file.read()
        
        st.download_button(
            label="📊 Download Excel Workbook",
            data=excel_data,
            file_name=os.path.basename(excel_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
        
        st.info(f"💡 **File created**: `{excel_path}`")
    
    # Themes overview
    st.subheader("🎯 Generated Themes Overview")
    
    themes_df = []
    for theme in themes:
        themes_df.append({
            "Theme ID": theme["theme_id"],
            "Type": theme["theme_type"].replace("_", " ").title(),
            "Subject": theme["harmonized_subject"],
            "Quality Score": f"{theme['validation_metrics']['quality_score']:.1f}",
            "Quotes": theme['validation_metrics']['quotes_count'],
            "Companies": theme['validation_metrics']['companies_count'],
            "Competitive": "Yes" if theme.get('competitive_flag', False) else "No"
        })
    
    if themes_df:
        df = pd.DataFrame(themes_df)
        
        # Style the dataframe
        styled_df = df.style.apply(lambda x: [
            'background-color: #90EE90' if 'Strength' in str(x['Type']) else
            'background-color: #FFB6C1' if 'Weakness' in str(x['Type']) else
            'background-color: #FFD700' if 'Mixed' in str(x['Type']) else ''
            for _ in x
        ], axis=1)
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Detailed theme viewer
        with st.expander("🔍 View Detailed Theme Statements"):
            for theme in themes:
                st.markdown(f"**{theme['theme_id']} - {theme['theme_type'].replace('_', ' ').title()}**")
                st.markdown(f"*{theme['harmonized_subject']}*")
                st.write(theme['theme_statement'])
                
                # Show top supporting quotes
                if theme.get('supporting_quotes'):
                    st.markdown("**Top Supporting Quotes:**")
                    for i, quote in enumerate(theme['supporting_quotes'][:2], 1):
                        st.markdown(f"{i}. \"{quote['quote_text'][:150]}...\" - {quote['company']}")
                
                st.divider()
    
    else:
        st.warning("⚠️ No themes were generated that passed the quality gates.")

def display_quick_stats(client_id: str):
    """Display quick statistics about the client data"""
    
    try:
        # Get basic stats from database
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        df = db.get_stage1_data_responses(client_id=client_id)
        
        if not df.empty:
            # Basic stats
            total_quotes = len(df)
            analyzed_quotes = len(df[df['sentiment'].notna()])
            company_col = 'company' if 'company' in df.columns else 'company_name'
            total_companies = df[company_col].nunique() if company_col in df.columns else 0
            
            # Sentiment breakdown
            sentiment_counts = df['sentiment'].value_counts() if 'sentiment' in df.columns else pd.Series()
            
            # Display stats
            st.metric("Total Quotes", total_quotes)
            st.metric("Analyzed Quotes", analyzed_quotes)
            st.metric("Companies", total_companies)
            
            if not sentiment_counts.empty:
                st.markdown("**Sentiment Breakdown:**")
                for sentiment, count in sentiment_counts.items():
                    if pd.notna(sentiment):
                        percentage = (count / analyzed_quotes) * 100 if analyzed_quotes > 0 else 0
                        st.markdown(f"• {sentiment.title()}: {count} ({percentage:.1f}%)")
        else:
            st.warning(f"⚠️ No data found for client: {client_id}")
            
    except Exception as e:
        st.error(f"❌ Error loading stats: {str(e)}")

def display_recent_files():
    """Display recently generated files"""
    
    st.subheader("📁 Recent Files")
    
    # Look for Excel files in current directory
    excel_files = []
    current_dir = Path(".")
    
    for file_path in current_dir.glob("Win_Loss_Analyst_Workbook_*.xlsx"):
        try:
            stat = file_path.stat()
            excel_files.append({
                "name": file_path.name,
                "size": f"{stat.st_size / 1024:.1f} KB",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(file_path)
            })
        except:
            continue
    
    # Sort by modification time (newest first)
    excel_files.sort(key=lambda x: x["modified"], reverse=True)
    
    if excel_files:
        for file_info in excel_files[:5]:  # Show only last 5 files
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file_info['name'][:40]}...**" if len(file_info['name']) > 40 else f"**{file_info['name']}**")
                    st.caption(f"Size: {file_info['size']} | Modified: {file_info['modified']}")
                
                with col2:
                    if st.button("📥", key=f"download_{file_info['name']}", help="Download file"):
                        try:
                            with open(file_info['path'], 'rb') as file:
                                excel_data = file.read()
                            
                            st.download_button(
                                label="Download",
                                data=excel_data,
                                file_name=file_info['name'],
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_{file_info['name']}"
                            )
                        except Exception as e:
                            st.error(f"Error downloading file: {e}")
    else:
        st.info("No recent files found.")

def display_help_section():
    """Display help and instructions"""
    
    st.header("📚 How to Use the Win-Loss Report Generator")
    
    with st.expander("🎯 Getting Started"):
        st.markdown("""
        1. **Select your client** from the sidebar dropdown
        2. **Configure analysis settings** (or use adaptive mode)
        3. **Click "Generate Win-Loss Report"** to start analysis
        4. **Download the Excel workbook** when generation completes
        5. **Use the workbook** for analyst curation workflow
        """)
    
    with st.expander("📊 Understanding the Output"):
        st.markdown("""
        **Excel Workbook Tabs:**
        - **📊 Executive Summary**: High-level overview and key metrics
        - **🎯 Theme Curation**: Main workspace for Include/Exclude decisions
        - **💬 Quote Analysis**: Detailed quote selection for final report
        - **🏆 Competitive Intel**: Competitive intelligence deep dive
        - **📋 Raw Data**: Complete reference data
        - **📝 Report Builder**: Template for executive presentation
        """)
    
    with st.expander("⚙️ Quality Gates Explained"):
        st.markdown("""
        **Adaptive Quality Gates** automatically adjust based on your data:
        - **Cross-Company Validation**: Ensures themes span multiple companies (when possible)
        - **Evidence Significance**: Requires sufficient quotes for statistical validity
        - **Impact Threshold**: Filters for business-relevant insights
        - **Narrative Coherence**: Validates theme consistency (for strength/weakness themes)
        """)

# Sidebar navigation
with st.sidebar:
    st.markdown("---")
    page = st.radio(
        "📋 Navigation",
        ["🏆 Generate Report", "📚 Help & Instructions"],
        index=0
    )

if page == "🏆 Generate Report":
    main()
elif page == "📚 Help & Instructions":
    display_help_section()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    Win-Loss Report Generator | Powered by Enhanced Stage 1 & 2 Data | 
    Uses Stage 4 Quality Gates for High-Quality Themes
</div>
""", unsafe_allow_html=True) 