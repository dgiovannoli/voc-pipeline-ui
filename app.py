import streamlit as st
import re
from datetime import datetime
from stage1_ui import show_stage1_data_responses
from stage2_ui import show_stage2_response_labeling
from stage3_ui import show_stage3_findings
from stage4_ui import show_stage4_themes
from admin_ui import show_admin_utilities, show_admin_panel

def show_stage4_analyst_report():
    """Stage 5: Generate Analyst Report - Simple interface for generating executive-ready reports"""
    
    st.title("📋 Stage 5: Generate Analyst Report")
    st.markdown("**Executive-Ready Voice of Customer Analysis with Strategic Insights**")
    st.markdown("---")
    
    # Get client ID from session state
    client_id = st.session_state.get('client_id', '')
    
    if not client_id:
        st.warning("⚠️ Please set a Client ID in the sidebar first")
        st.info("💡 Enter a unique identifier for this client's data (e.g., 'Rev', 'Client_A')")
        return
    
    # Display client info
    st.subheader(f"🏢 Client: {client_id}")
    
    # Quick stats
    try:
        from official_scripts.database.supabase_database import SupabaseDatabase
        from official_scripts.core_analytics.interview_weighted_base import InterviewWeightedBase
        
        db = SupabaseDatabase()
        
        # Get data counts
        themes = db.get_themes(client_id)
        findings = db.get_stage3_findings(client_id)
        stage1_data = db.get_all_stage1_data_responses()
        client_data = stage1_data[stage1_data['client_id'] == client_id]
        
        # Interview-weighted metrics
        analyzer = InterviewWeightedBase(db)
        metrics = analyzer.get_customer_metrics(client_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Themes", len(themes))
        with col2:
            st.metric("Findings", len(findings))
        with col3:
            st.metric("Quotes", len(client_data))
        with col4:
            st.metric("Satisfaction", f"{metrics['customer_satisfaction_rate']}%")
            
    except Exception as e:
        st.error(f"❌ Database connection error: {str(e)}")
        return
    
    st.markdown("---")
    
    # Generate report section
    st.subheader("🎯 Generate Executive Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **This will generate an executive-ready report with:**
        - ✅ Strategic customer voice synthesis
        - ✅ Competitive positioning analysis
        - ✅ Actionable recommendations
        - ✅ Curated quotes and evidence
        - ✅ Competitive intelligence framework
        """)
        
        # Generate button
        if st.button("🚀 Generate Analyst Report", type="primary", use_container_width=True):
            with st.spinner("Generating executive-ready analyst report..."):
                try:
                    from production_analyst_toolkit.generate_enhanced_analyst_toolkit import generate_enhanced_analyst_toolkit
                    
                    # Generate the report
                    filename = generate_enhanced_analyst_toolkit(client_id)
                    
                    if filename:
                        st.success(f"✅ Report generated successfully!")
                        
                        # Read the report content
                        with open(filename, 'r', encoding='utf-8') as f:
                            report_content = f.read()
                        
                        # Save to production folder
                        production_filename = f"production_analyst_toolkit/latest_{client_id}_report.txt"
                        with open(production_filename, 'w', encoding='utf-8') as f:
                            f.write(report_content)
                        
                        st.success(f"📁 Saved to production folder: {production_filename}")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Executive Report",
                            data=report_content,
                            file_name=f"{client_id}_Executive_Report_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                        # Show file info
                        st.info(f"📄 File size: {len(report_content):,} characters")
                        
                    else:
                        st.error("❌ Failed to generate report")
                        
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    st.exception(e)
    
    with col2:
        st.subheader("📊 Report Features")
        st.markdown("""
        ### ✅ Executive Summary
        - Strategic customer voice synthesis
        - Competitive positioning
        - Actionable recommendations
        
        ### 📊 Criteria Analysis
        - Individual performance metrics
        - Key themes from customer feedback
        - Voice of customer evidence
        - Competitive intelligence research
        
        ### 🎯 Enhanced Features
        - Quote deduplication
        - Quality scoring
        - Sentiment categorization
        - Executive summary templates
        """)
        
        # Show latest report if available
        import os
        latest_file = f"production_analyst_toolkit/latest_{client_id}_report.txt"
        if os.path.exists(latest_file):
            st.subheader("📄 Latest Report")
            
            # Get file size
            file_size = os.path.getsize(latest_file)
            st.caption(f"File size: {file_size:,} characters")
            
            # Download latest
            with open(latest_file, "r") as f:
                st.download_button(
                    label="📥 Download Latest Report",
                    data=f.read(),
                    file_name=f"{client_id}_Latest_Report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )

def main():
    st.set_page_config(page_title="VOC Pipeline", layout="wide")
    
    # Initialize session state
    if 'client_id' not in st.session_state:
        st.session_state.client_id = ''
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Sidebar navigation
    st.sidebar.title("VOC Pipeline Navigation")
    
    # Production status indicator
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Production Status")
    
    # Check production readiness
    try:
        from test_production_setup import test_environment_variables, test_database_connection
        env_ok = test_environment_variables()
        db_ok = test_database_connection()
        
        if env_ok and db_ok:
            st.sidebar.success("✅ Production Ready")
        else:
            st.sidebar.warning("⚠️ Production Issues")
    except:
        st.sidebar.info("ℹ️ Production status unknown")
    
    # Client ID management
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Client Settings")
    
    # Check if client_id is properly set
    current_client_id = st.session_state.get('client_id', '')
    if not current_client_id or current_client_id == 'default':
        st.sidebar.warning("⚠️ Please set a Client ID")
        st.sidebar.info("💡 Enter a unique identifier for this client's data")
        st.sidebar.info("📝 Examples: 'Rev', 'Client_A', 'Project_Alpha'")
    
    # Client ID input with validation
    new_client_id = st.sidebar.text_input(
        "Client ID:",
        value=current_client_id,
        help="Enter a unique identifier for this client's data"
    )
    
    # Validate client ID format
    if new_client_id:
        if re.match(r'^[a-zA-Z0-9_-]+$', new_client_id):
            if new_client_id != current_client_id:
                st.session_state.client_id = new_client_id
                st.sidebar.success(f"✅ Client ID set to: {new_client_id}")
                st.rerun()
        else:
            st.sidebar.error("❌ Client ID can only contain letters, numbers, underscores, and hyphens")
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Pipeline Stages")
    
    page = st.sidebar.radio(
        "Go to:",
        [
            "Stage 1: Data Response Table",
            "Stage 2: Response Labeling",
            "Stage 3: Findings",
            "Stage 4: Themes",
            "Stage 5: Generate Analyst Report",
            "Admin / Utilities"
        ]
    )

    if page == "Stage 1: Data Response Table":
        show_stage1_data_responses()
    elif page == "Stage 2: Response Labeling":
        show_stage2_response_labeling()
    elif page == "Stage 3: Findings":
        show_stage3_findings()
    elif page == "Stage 4: Themes":
        show_stage4_themes()
    elif page == "Stage 5: Generate Analyst Report":
        show_stage4_analyst_report()
    elif page == "Admin / Utilities":
        show_admin_panel()

if __name__ == "__main__":
    main()


