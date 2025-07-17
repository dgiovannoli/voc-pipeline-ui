import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase database
try:
    db = SupabaseDatabase()
    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    st.error(f"❌ Failed to connect to Supabase: {e}")

def get_client_id():
    """Safely get client_id from session state."""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        st.stop()
    return client_id

def run_stage3_analysis():
    """Run Stage 3 findings analysis using the production pipeline"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        from stage3_findings_analyzer_enhanced import EnhancedStage3FindingsAnalyzer
        client_id = get_client_id()
        analyzer = EnhancedStage3FindingsAnalyzer(client_id=client_id)
        
        # Use the enhanced pipeline that includes classification and generates CSV output
        result = analyzer.analyze_findings()
        
        # Check if CSV files were generated
        import os
        csv_files = []
        if os.path.exists('findings_after_clustering.csv'):
            csv_files.append('findings_after_clustering.csv')
        if os.path.exists('findings_before_clustering.csv'):
            csv_files.append('findings_before_clustering.csv')
        
        if csv_files:
            st.success(f"✅ Generated {len(csv_files)} CSV files: {', '.join(csv_files)}")
        
        # Show Supabase save status
        if result and result.get('findings_generated', 0) > 0:
            st.success(f"✅ Saved {result.get('findings_generated', 0)} findings to Supabase for client {client_id}")
        
        return result
    except Exception as e:
        st.error(f"❌ Stage 3 analysis failed: {e}")
        return None

def get_stage3_summary():
    """Get Stage 3 enhanced findings summary from database"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        client_id = get_client_id()
        summary = db.get_stage3_findings_summary(client_id=client_id)
        return summary
    except Exception as e:
        st.error(f"❌ Failed to get enhanced findings summary: {e}")
        return None

def show_findings():
    """Show findings with detailed information from CSV files"""
    st.subheader("🔍 Findings (Stage 3 Results)")
    
    # Try to load from CSV files first (preferred format)
    import os
    df = None
    
    if os.path.exists('findings_after_clustering.csv'):
        df = pd.read_csv('findings_after_clustering.csv')
        st.success("📊 Loading findings from production CSV file")
    elif os.path.exists('findings_before_clustering.csv'):
        df = pd.read_csv('findings_before_clustering.csv')
        st.info("📊 Loading findings from pre-clustering CSV file")
    else:
        # Fallback to database
        client_id = get_client_id()
        df = db.get_stage3_findings(client_id=client_id)
        if df.empty:
            st.info("No findings found. Run Stage 3 analysis.")
            return
        else:
            st.info("📊 Loading findings from database (fallback)")

    # Prepare columns: show finding statement and referenced quote
    def get_first_quote_text(selected_quotes):
        if isinstance(selected_quotes, list) and selected_quotes:
            quote = selected_quotes[0]
            if isinstance(quote, dict):
                return quote.get('text', '')
            return str(quote)
        return ''

    # Handle different column names from production pipeline
    if 'selected_quotes' in df.columns:
        df['Referenced Quote'] = df['selected_quotes'].apply(get_first_quote_text)
    else:
        df['Referenced Quote'] = ''

    # Use CSV format field names (Buried Wins format)
    display_cols = [
        'Finding_Statement', 'Interview_Company', 'Priority_Level', 'Evidence_Strength',
        'Finding_Category', 'Criteria_Met', 'Primary_Quote'
    ]
    display_cols = [col for col in display_cols if col in df.columns]

    # Rename columns for better display
    display_mapping = {
        'Finding_Statement': 'Finding Statement',
        'Interview_Company': 'Company',
        'Priority_Level': 'Priority',
        'Evidence_Strength': 'Evidence Strength',
        'Finding_Category': 'Category',
        'Criteria_Met': 'Criteria Met',
        'Primary_Quote': 'Primary Quote'
    }

    # Create a styled dataframe with color coding for priority levels
    styled_df = df[display_cols].copy()
    styled_df.columns = [display_mapping.get(col, col) for col in styled_df.columns]

    def color_priority(val):
        if pd.isna(val):
            return 'background-color: lightgray'
        elif val == 'Priority Finding':
            return 'background-color: lightcoral; color: darkred'
        elif val == 'Standard Finding':
            return 'background-color: lightyellow; color: darkorange'
        else:
            return 'background-color: lightblue'

    styled_df = styled_df.style.applymap(color_priority, subset=['Priority'])

    st.dataframe(styled_df, use_container_width=True)

    st.markdown("**🎨 Priority Level Color Coding:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔴 **Priority Finding** - High confidence findings requiring attention")
    with col2:
        st.markdown("🟡 **Standard Finding** - Important findings for consideration")
    with col3:
        st.markdown("🔵 **Other** - Additional priority levels")

    # Add detailed view expander
    with st.expander("📊 Detailed Findings View"):
        detailed_cols = [
            'Finding_ID', 'Finding_Statement', 'Interview_Company', 'Interviewee_Name',
            'Primary_Quote', 'Secondary_Quote', 'Quote_Attributions', 'Supporting_Response_IDs',
            'Evidence_Strength', 'Finding_Category', 'Criteria_Met', 'Priority_Level',
            'Date', 'Deal_Status'
        ]
        detailed_cols = [col for col in detailed_cols if col in df.columns]
        
        if detailed_cols:
            detailed_df = df[detailed_cols].copy()
            st.dataframe(detailed_df, use_container_width=True)

    # Download the actual CSV file if it exists
    import os
    if os.path.exists('findings_after_clustering.csv'):
        with open('findings_after_clustering.csv', 'r') as f:
            csv_data = f.read()
        st.download_button(
            label="📥 Download Production Findings CSV",
            data=csv_data,
            file_name="findings_after_clustering.csv",
            mime="text/csv",
            key="download_production_findings"
        )
    else:
        # Fallback to current dataframe
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Findings CSV",
            data=csv,
            file_name="findings.csv",
            mime="text/csv",
            key="download_findings"
        )

def show_stage3_findings():
    """Stage 3: Findings - Identify key findings and insights from labeled quotes"""
    st.title("🔍 Stage 3: Findings")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return
    
    # Check if we have Stage 2 data
    try:
        from stage2_ui import get_stage2_summary
        stage2_summary = get_stage2_summary()
        if not stage2_summary or stage2_summary.get('quotes_with_scores', 0) == 0:
            st.info("📊 Please run Stage 2 quote scoring first")
            return
    except Exception as e:
        st.error(f"❌ Error checking Stage 2 data: {e}")
        return
    
    # Check if we have existing findings
    findings_summary = get_stage3_summary()
    
    # Show current status
    if findings_summary and findings_summary.get('total_findings', 0) > 0:
        st.success(f"✅ Found {findings_summary.get('total_findings', 0)} existing findings")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Findings", findings_summary.get('total_findings', 0))
        with col2:
            st.metric("Priority Findings", findings_summary.get('priority_findings', 0))
        with col3:
            st.metric("Standard Findings", findings_summary.get('standard_findings', 0))
        with col4:
            st.metric("Avg Confidence", f"{findings_summary.get('average_confidence', 0):.1f}")
    
    # Run analysis buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 Identify Findings", type="primary", help="Identify key findings and insights from labeled quotes"):
            with st.spinner("Identifying findings and insights..."):
                result = run_stage3_analysis()
                if result and result.get('status') == 'success':
                    st.success(f"✅ Findings identification complete! Generated {result.get('findings_generated', 0)} findings")
                    st.rerun()
                else:
                    st.error("❌ Findings identification failed")
    
    with col2:
        if findings_summary and findings_summary.get('total_findings', 0) > 0:
            if st.button("🔄 Force Reprocess", help="Clear existing findings and run fresh analysis"):
                with st.spinner("Clearing existing findings and running fresh analysis..."):
                    # Clear existing findings and CSV files
                    try:
                        client_id = get_client_id()
                        db.supabase.table('stage3_findings').delete().eq('client_id', client_id).execute()
                        
                        # Clear CSV files
                        import os
                        csv_files = ['findings_after_clustering.csv', 'findings_before_clustering.csv']
                        for file in csv_files:
                            if os.path.exists(file):
                                os.remove(file)
                        
                        st.success("✅ Cleared existing findings and CSV files")
                        
                        # Run fresh analysis
                        result = run_stage3_analysis()
                        if result and result.get('status') == 'success':
                            st.success(f"✅ Fresh analysis complete! Generated {result.get('findings_generated', 0)} findings")
                            st.rerun()
                        else:
                            st.error("❌ Fresh analysis failed")
                    except Exception as e:
                        st.error(f"❌ Error during force reprocess: {e}")
    
    # Show findings (either existing or newly generated)
    findings_summary = get_stage3_summary()  # Refresh summary
    if findings_summary and findings_summary.get('total_findings', 0) > 0:
        show_findings()
        if st.button("🎨 Proceed to Stage 4: Generate Themes", type="primary"):
            st.session_state.current_step = 4
            st.rerun()
    else:
        st.info("📊 No findings available yet. Click 'Identify Findings' to run the analysis.")
    
    # Show production pipeline status
    st.subheader("🚀 Production Pipeline Status")
    
    # Check Supabase connection and findings count
    if SUPABASE_AVAILABLE:
        try:
            client_id = get_client_id()
            findings_count = db.get_stage3_findings(client_id=client_id).shape[0]
            st.success(f"✅ Supabase Connected - {findings_count} findings saved for client {client_id}")
        except Exception as e:
            st.error(f"❌ Supabase Error: {e}")
    else:
        st.error("❌ Supabase not available")
    
    # Check if we have the latest findings files
    import os
    findings_files = []
    if os.path.exists('findings_after_clustering.csv'):
        findings_files.append("✅ findings_after_clustering.csv")
    if os.path.exists('findings_before_clustering.csv'):
        findings_files.append("✅ findings_before_clustering.csv")
    
    if findings_files:
        st.success("Production files generated:")
        for file in findings_files:
            st.write(f"  {file}")
    else:
        st.info("No production files found yet. Run analysis to generate files.")
    
    # Show findings criteria information
    st.subheader("🔍 Buried Wins v4.0 Evaluation Criteria")
    evaluation_criteria = """
    **8 Core Evaluation Criteria:**
    1. **Novelty**: The observation is new/unexpected, challenging assumptions
    2. **Actionability**: Suggests clear steps, fixes, or actions to improve outcomes
    3. **Specificity**: Precise, detailed, not generic - references particular features or processes
    4. **Materiality**: Meaningful business impact affecting revenue, satisfaction, or positioning
    5. **Recurrence**: Same observation across multiple interviews or sources
    6. **Stakeholder Weight**: Comes from high-influence decision makers or critical personas
    7. **Tension/Contrast**: Exposes tensions, tradeoffs, or significant contrasts
    8. **Metric/Quantification**: Supported by tangible metrics, timeframes, or outcomes
    """
    st.markdown(evaluation_criteria)
    
    # Show LLM integration status
    st.subheader("🤖 LLM Integration Status")
    
    # Check if LLM integration is working
    try:
        from stage3_findings_analyzer_enhanced import EnhancedStage3FindingsAnalyzer
        analyzer = EnhancedStage3FindingsAnalyzer()
        prompt = analyzer._load_buried_wins_prompt()
        if prompt and len(prompt) > 100:
            st.success("✅ LLM Integration: Buried Wins prompt loaded successfully")
            st.info(f"📝 Prompt length: {len(prompt)} characters")
        else:
            st.warning("⚠️ LLM Integration: Prompt may be incomplete")
    except Exception as e:
        st.error(f"❌ LLM Integration: {e}")
    
    # Show finding types
    st.subheader("🎯 Finding Types")
    finding_types = """
    **Finding Classifications:**
    - **Strength**: High-performing areas (scores ≥ 3.5)
    - **Improvement**: Areas needing attention (scores ≤ 2.0)
    - **Positive Trend**: Consistent positive feedback across companies
    - **Negative Trend**: Consistent negative feedback across companies
    - **Priority Findings**: Enhanced confidence ≥ 4.0/10.0
    - **Standard Findings**: Enhanced confidence ≥ 3.0/10.0
    """
    st.markdown(finding_types)
    
    # Show confidence scoring
    st.subheader("📊 Enhanced Confidence Scoring")
    confidence_info = """
    **Confidence Calculation:**
    - **Base Score**: Number of criteria met (2-8 points)
    - **Stakeholder Multipliers**: Executive (1.5x), Budget Holder (1.5x), Champion (1.3x)
    - **Decision Impact Multipliers**: Deal Tipping Point (2.0x), Differentiator (1.5x), Blocker (1.5x)
    - **Evidence Strength Multipliers**: Strong Positive/Negative (1.3x), Perspective Shifting (1.3x)
    
    **Confidence Thresholds:**
    - **Priority Finding**: ≥ 4.0/10.0
    - **Standard Finding**: ≥ 3.0/10.0
    - **Minimum Confidence**: ≥ 2.0/10.0
    """
    st.markdown(confidence_info) 