import streamlit as st
import re
from datetime import datetime
from stage1_ui import show_stage1_data_responses
from stage2_ui import show_stage2_analysis
from stage3_ui import show_stage3_findings
from stage4_ui import show_stage4_themes
from admin_ui import show_admin_utilities, show_admin_panel

def show_excel_generation():
    """Excel Workbook Generation - Create comprehensive Excel workbooks for analyst curation"""
    
    st.title("📊 Excel Workbook Generation")
    st.markdown("**Generate comprehensive Excel workbooks with cross-section theme handling**")
    st.markdown("---")
    
    # Get client ID from session state
    client_id = st.session_state.get('client_id', '')
    
    if not client_id:
        st.warning("⚠️ Please set a Client ID in the sidebar first")
        st.info("💡 Enter a unique identifier for this client's data (e.g., 'Supio', 'Rev')")
        return
    
    # Display client info
    st.subheader(f"🏢 Client: {client_id}")
    
    # Information about the Excel workbook
    st.markdown("""
    ### 📋 What's Included in the Excel Workbook:
    
    **🔄 Cross-Section Themes Tab**
    - Identifies themes that appear in multiple sections
    - Shows primary vs. secondary sections for each theme
    - Tracks processing status to avoid duplicate work
    
    **📊 Section Validation Tabs**
    - **Win Drivers**: Why customers choose your solution
    - **Loss Factors**: Why customers choose competitors  
    - **Competitive Intelligence**: Market dynamics and competitive landscape
    - **Implementation Insights**: Deployment challenges and success factors
    
    **📈 Analysis & Planning Tabs**
    - Executive summary with key metrics
    - Quote curation interface
    - Theme validation tools
    - Research question alignment
    """)
    
    st.markdown("---")
    
    # Generation options
    st.subheader("⚙️ Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Custom filename option
        use_custom_filename = st.checkbox("Use custom filename", value=False)
        custom_filename = None
        if use_custom_filename:
            custom_filename = st.text_input(
                "Custom filename:",
                value=f"Win_Loss_Analyst_Workbook_{client_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                help="Enter the desired filename for the Excel workbook"
            )
        
        # Alignment threshold
        research_alignment_min = st.slider("Min Research Alignment (fraction of quotes aligned in a group)", 0.0, 0.5, 0.15, 0.05,
                                           help="Only generate research-seeded themes when at least this fraction of quotes in a group explicitly align to the primary research question.")
    
    with col2:
        # Quality gate options
        st.markdown("**Quality Settings:**")
        st.info("""
        - **Cross-Company**: Minimum 2 companies per theme
        - **Evidence**: Minimum 3 quotes per theme  
        - **Impact**: Adaptive threshold based on data quality
        - **Coherence**: Sentiment consistency check
        """)
    
    st.markdown("---")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Generate Excel Workbook", type="primary", use_container_width=True):
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Import required modules
                status_text.text("📦 Loading modules...")
                progress_bar.progress(10)
                
                # Use the new Supio Harmonized generator which pulls Stage 3 themes and adds grouped tabs
                status_text.text("📋 Creating Excel workbook (Supio Harmonized)...")
                progress_bar.progress(80)
                from supio_harmonized_workbook_generator import SupioHarmonizedWorkbookGenerator
                shg = SupioHarmonizedWorkbookGenerator(client_id)
                output_path = shg.generate_workbook()
                # If a custom filename was requested, rename the generated file
                if custom_filename:
                    import os
                    try:
                        if os.path.exists(output_path):
                            os.replace(output_path, custom_filename)
                            output_path = custom_filename
                    except Exception:
                        pass
                
                # Verify file was created
                import os
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    progress_bar.progress(100)
                    status_text.text("✅ Excel workbook created successfully!")
                    
                    st.success(f"🎉 Excel workbook generated successfully!")
                    
                    # Display file info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("File Size", f"{file_size:,} bytes")
                    # Additional metrics removed for compatibility with SupioHarmonizedWorkbookGenerator
                    
                    # Download button
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Excel Workbook",
                            data=f.read(),
                            file_name=os.path.basename(output_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Success message with next steps
                    st.info("""
                    **📋 Next Steps:**
                    1. **Open the Excel workbook**
                    2. **Start with the '🔄 Cross-Section Themes' tab**
                    3. **Process themes in their primary sections**
                    4. **Mark processing status as you complete each theme**
                    5. **Use the curated themes in your final report**
                    """)
                    
                else:
                    st.error("❌ Excel file was not created")
                    
            except Exception as e:
                st.error(f"❌ Error generating workbook: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

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

def show_decision_tracking():
    """Decision Tracking and Workbook Regeneration - Make validation decisions and regenerate workbooks"""
    
    st.title("📋 Decision Tracking & Workbook Regeneration")
    st.markdown("**Make validation decisions and regenerate workbooks with your choices applied**")
    st.markdown("---")
    
    # Get client ID from session state
    client_id = st.session_state.get('client_id', '')
    
    if not client_id:
        st.warning("⚠️ Please set a Client ID in the sidebar first")
        st.info("💡 Enter a unique identifier for this client's data (e.g., 'Supio', 'Rev')")
        return
    
    # Display client info
    st.subheader(f"🏢 Client: {client_id}")
    
    # Information about the decision tracking process
    st.markdown("""
    ### 🔄 How Decision Tracking Works:
    
    **1. Review Themes**: First, generate a workbook to see all available themes
    **2. Make Decisions**: Use this interface to mark themes as VALIDATED, REJECTED, etc.
    **3. Regenerate**: Create a new workbook with your decisions applied
    **4. View Results**: Check the Report Outline Generator to see your validated themes
    
    **📊 Decision Options:**
    - **VALIDATED**: Include in final report
    - **FEATURED**: Highlight in executive summary  
    - **REJECTED**: Exclude from report
    - **NEEDS REVISION**: Requires changes before inclusion
    - **PENDING**: Not yet reviewed
    """)
    
    st.markdown("---")
    
    # Step 1: Generate initial workbook
    st.subheader("📊 Step 1: Generate Initial Workbook")
    
    col1, col2 = st.columns(2)
    
    with col1:
        initial_filename = st.text_input(
            "Initial workbook filename:",
            value=f"Initial_Workbook_{client_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            help="Filename for the initial workbook with all themes"
        )
    
    with col2:
        if st.button("🚀 Generate Initial Workbook", type="primary"):
            try:
                # Import required modules
                with st.spinner("📦 Loading modules..."):
                    from win_loss_report_generator import WinLossReportGenerator
                    from excel_win_loss_exporter import ExcelWinLossExporter
                
                # Generate themes and workbook
                with st.spinner("📊 Generating themes and analysis..."):
                    generator = WinLossReportGenerator(client_id)
                    themes_data = generator.generate_win_loss_report()
                
                with st.spinner("📋 Creating Excel workbook..."):
                    exporter = ExcelWinLossExporter()
                    output_path = exporter.export_analyst_workbook(themes_data, initial_filename)
                
                st.success(f"✅ Initial workbook created successfully!")
                st.info(f"📁 File: {output_path}")
                st.info("💡 Download the file and review themes in the 'Decision Tracking' tab")
                
                # Store themes data in session state for decision tracking
                st.session_state['themes_data'] = themes_data
                st.session_state['initial_workbook_path'] = output_path
                
            except Exception as e:
                st.error(f"❌ Error generating initial workbook: {str(e)}")
    
    st.markdown("---")
    
    # Step 2: Decision tracking interface
    st.subheader("📋 Step 2: Make Validation Decisions")
    
    if 'themes_data' not in st.session_state:
        st.info("💡 Generate an initial workbook first to see available themes")
        return
    
    themes_data = st.session_state['themes_data']
    themes = themes_data.get('themes', [])
    
    if not themes:
        st.warning("⚠️ No themes available. Please generate an initial workbook first.")
        return
    
    # Initialize decisions in session state if not exists
    if 'theme_decisions' not in st.session_state:
        st.session_state['theme_decisions'] = {}
    
    # Display themes for decision making
    st.markdown(f"**Found {len(themes)} themes to review:**")
    
    # Create decision interface
    decisions_made = 0
    for i, theme in enumerate(themes):
        theme_id = theme.get('theme_id', f'theme_{i}')
        theme_statement = theme.get('theme_statement', 'No statement')
        quality_score = theme.get('validation_metrics', {}).get('quality_score', 0)
        section = theme.get('win_loss_category', 'unknown')
        
        # Create expander for each theme
        with st.expander(f"🎯 {theme_id} ({section}) - Quality: {quality_score:.1f}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Statement:** {theme_statement[:100]}...")
                st.markdown(f"**Section:** {section}")
                st.markdown(f"**Quality Score:** {quality_score:.1f}")
            
            with col2:
                # Decision dropdown
                decision_key = f"decision_{theme_id}"
                current_decision = st.session_state['theme_decisions'].get(decision_key, 'PENDING')
                
                decision = st.selectbox(
                    "Decision:",
                    options=['PENDING', 'VALIDATED', 'FEATURED', 'REJECTED', 'NEEDS REVISION'],
                    index=['PENDING', 'VALIDATED', 'FEATURED', 'REJECTED', 'NEEDS REVISION'].index(current_decision),
                    key=f"select_{theme_id}"
                )
                
                # Update session state
                st.session_state['theme_decisions'][decision_key] = decision
                if decision != 'PENDING':
                    decisions_made += 1
            
            with col3:
                # Notes field
                notes_key = f"notes_{theme_id}"
                notes = st.text_area(
                    "Notes:",
                    value=st.session_state.get(notes_key, ""),
                    key=f"notes_{theme_id}",
                    height=100
                )
                st.session_state[notes_key] = notes
    
    # Decision summary
    st.markdown("---")
    st.subheader("📊 Decision Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    validated_count = sum(1 for v in st.session_state['theme_decisions'].values() if v == 'VALIDATED')
    featured_count = sum(1 for v in st.session_state['theme_decisions'].values() if v == 'FEATURED')
    rejected_count = sum(1 for v in st.session_state['theme_decisions'].values() if v == 'REJECTED')
    revision_count = sum(1 for v in st.session_state['theme_decisions'].values() if v == 'NEEDS REVISION')
    pending_count = len(themes) - validated_count - featured_count - rejected_count - revision_count
    
    with col1:
        st.metric("Validated", validated_count)
    with col2:
        st.metric("Featured", featured_count)
    with col3:
        st.metric("Rejected", rejected_count)
    with col4:
        st.metric("Needs Revision", revision_count)
    with col5:
        st.metric("Pending", pending_count)
    
    st.markdown("---")
    
    # Step 3: Regenerate workbook with decisions
    st.subheader("🔄 Step 3: Regenerate Workbook with Decisions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        final_filename = st.text_input(
            "Final workbook filename:",
            value=f"Validated_Workbook_{client_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            help="Filename for the workbook with your decisions applied"
        )
    
    with col2:
        if st.button("🚀 Regenerate with Decisions", type="primary", disabled=decisions_made == 0):
            try:
                # Apply decisions to themes data
                with st.spinner("📊 Applying your decisions..."):
                    # Create a copy of themes data with decisions applied
                    validated_themes = []
                    for theme in themes:
                        theme_id = theme.get('theme_id')
                        decision_key = f"decision_{theme_id}"
                        decision = st.session_state['theme_decisions'].get(decision_key, 'PENDING')
                        
                        if decision in ['VALIDATED', 'FEATURED']:
                            # Add decision info to theme
                            theme['analyst_decision'] = decision
                            validated_themes.append(theme)
                    
                    # Update themes data
                    updated_themes_data = themes_data.copy()
                    updated_themes_data['themes'] = validated_themes
                
                with st.spinner("📋 Creating final workbook..."):
                    from excel_win_loss_exporter import ExcelWinLossExporter
                    exporter = ExcelWinLossExporter()
                    output_path = exporter.export_analyst_workbook(updated_themes_data, final_filename)
                
                st.success(f"✅ Final workbook created with your decisions!")
                st.info(f"📁 File: {output_path}")
                st.info(f"📊 Applied {validated_count + featured_count} validated themes")
                st.info("💡 Check the 'Report Outline Generator' tab to see your validated themes")
                
            except Exception as e:
                st.error(f"❌ Error regenerating workbook: {str(e)}")
    
    # Instructions for next steps
    st.markdown("---")
    st.subheader("📋 Next Steps")
    
    st.markdown("""
    1. **Download the final workbook** and open it in Excel
    2. **Go to 'Report Outline Generator' tab** to see your validated themes
    3. **Review the structure** - it will show only themes you marked as VALIDATED
    4. **Copy the outline** to share with your design team
    5. **Use the page counts and specifications** for design planning
    """)

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
    st.sidebar.subheader("🏢 Client")
    
    # Check if client_id is properly set
    current_client_id = st.session_state.get('client_id', '')
    if not current_client_id or current_client_id == 'default':
        st.sidebar.warning("⚠️ Please set a Client ID")
        st.sidebar.info("💡 Enter a unique identifier for this client's data")
        st.sidebar.info("📝 Examples: 'Rev', 'Client_A', 'Project_Alpha'")
    
    # Client ID input with validation
    new_client_id = st.sidebar.text_input(
        "Client:",
        value=current_client_id,
        help="Sets which client's data is read/written (must match CSV and DB)"
    )
    
    # Validate client ID format
    if new_client_id:
        # Allow letters, numbers, spaces, underscores, and hyphens; normalize to strip leading/trailing spaces
        if re.match(r'^[a-zA-Z0-9 _-]+$', new_client_id):
            normalized = new_client_id.strip()
            if normalized != current_client_id:
                st.session_state.client_id = normalized
                st.sidebar.success(f"✅ Client ID set to: {normalized}")
                st.rerun()
        else:
            st.sidebar.error("❌ Client ID can only contain letters, numbers, spaces, underscores, and hyphens")
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Pipeline Stages")
    
    page = st.sidebar.radio(
        "Go to:",
        [
            "Stage 1 · Upload & Parse",
            "Stage 2 · Score & Harmonize",
            "Stage 3 · Generate Themes",
            "Stage 4 · Consolidate & Strategy",
            "Workbook · Export",
            "📋 Decision Tracking",
            "Admin · Data Explorer"
        ]
    )

    if page == "Stage 1 · Upload & Parse":
        show_stage1_data_responses()
    elif page == "Stage 2 · Score & Harmonize":
        show_stage2_analysis()
    elif page == "Stage 3 · Generate Themes":
        show_stage3_findings()
    elif page == "Stage 4 · Consolidate & Strategy":
        show_stage4_themes()
    elif page == "Stage 5: Generate Analyst Report":
        show_stage4_analyst_report()
    elif page == "Workbook · Export":
        show_excel_generation()
    elif page == "📋 Decision Tracking":
        show_decision_tracking()
    elif page == "Admin · Data Explorer":
        show_admin_panel()

if __name__ == "__main__":
    main()


