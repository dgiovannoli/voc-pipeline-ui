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
    """Run Stage 3 findings analysis using database"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        from stage3_findings_analyzer import Stage3FindingsAnalyzer
        client_id = get_client_id()
        analyzer = Stage3FindingsAnalyzer()
        result = analyzer.process_stage3_findings(client_id=client_id)
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
    """Show findings with detailed information"""
    st.subheader("🔍 Findings (Stage 3 Results)")
    client_id = get_client_id()
    df = db.get_stage3_findings(client_id=client_id)
    if df.empty:
        st.info("No findings found. Run Stage 3 analysis.")
        return

    # Prepare columns: show description and referenced quote
    def get_first_quote_text(selected_quotes):
        if isinstance(selected_quotes, list) and selected_quotes:
            quote = selected_quotes[0]
            if isinstance(quote, dict):
                return quote.get('text', '')
            return str(quote)
        return ''

    df['Referenced Quote'] = df['selected_quotes'].apply(get_first_quote_text) if 'selected_quotes' in df.columns else ''

    display_cols = [
        'criterion', 'finding_type', 'priority_level', 'enhanced_confidence',
        'description', 'Referenced Quote'
    ]
    display_cols = [col for col in display_cols if col in df.columns]

    # Create a styled dataframe with color coding for priority levels
    styled_df = df[display_cols].copy()

    def color_priority(val):
        if pd.isna(val):
            return 'background-color: lightgray'
        elif val == 'High':
            return 'background-color: lightcoral; color: darkred'
        elif val == 'Medium':
            return 'background-color: lightyellow; color: darkorange'
        elif val == 'Low':
            return 'background-color: lightgreen; color: darkgreen'
        else:
            return 'background-color: lightblue'

    styled_df = styled_df.style.applymap(color_priority, subset=['priority_level'])

    st.dataframe(styled_df, use_container_width=True)

    st.markdown("**🎨 Priority Level Color Coding:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🔴 **High** - Critical findings requiring immediate attention")
    with col2:
        st.markdown("🟡 **Medium** - Important findings needing consideration")
    with col3:
        st.markdown("🟢 **Low** - Minor findings for monitoring")
    with col4:
        st.markdown("🔵 **Other** - Additional priority levels")

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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Findings", findings_summary.get('total_findings', 0))
        with col2:
            st.metric("Priority Findings", findings_summary.get('priority_findings', 0))
        with col3:
            st.metric("High Confidence", findings_summary.get('high_confidence_findings', findings_summary.get('priority_findings', 0)))
    
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
                    # Clear existing findings
                    try:
                        client_id = get_client_id()
                        db.supabase.table('stage3_findings').delete().eq('client_id', client_id).execute()
                        st.success("✅ Cleared existing findings")
                        
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