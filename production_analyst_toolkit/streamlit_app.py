import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add the parent directory to the path to import the toolkit
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    st.set_page_config(
        page_title="Production Analyst Toolkit",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎯 Production Analyst Toolkit")
    st.markdown("**Executive-Ready Voice of Customer Analysis with Competitive Intelligence**")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("📊 Quick Stats")
    
    # Get data counts
    try:
        from official_scripts.database.supabase_database import SupabaseDatabase
        from official_scripts.core_analytics.interview_weighted_base import InterviewWeightedBase
        
        db = SupabaseDatabase()
        
        # Get data counts
        themes = db.get_themes('Rev')
        findings = db.get_stage3_findings('Rev')
        stage1_data = db.get_all_stage1_data_responses()
        client_data = stage1_data[stage1_data['client_id'] == 'Rev']
        
        st.sidebar.metric("Themes", len(themes))
        st.sidebar.metric("Findings", len(findings))
        st.sidebar.metric("Quotes", len(client_data))
        
        # Interview-Weighted VOC Metrics
        st.sidebar.subheader("🎯 Interview-Weighted VOC")
        analyzer = InterviewWeightedBase(db)
        metrics = analyzer.get_customer_metrics('Rev')
        
        st.sidebar.metric(
            "Customer Satisfaction", 
            f"{metrics['customer_satisfaction_rate']}%",
            help="Percentage of satisfied customers"
        )
        st.sidebar.metric(
            "Overall Score", 
            f"{metrics['overall_score']}/10",
            help="Interview-weighted score"
        )
        st.sidebar.metric(
            "Problem Customers", 
            f"{metrics['problem_customers']}",
            help="Customers with issues"
        )
        
    except Exception as e:
        st.sidebar.error(f"Database connection error: {str(e)}")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 Generate Analyst Report")
        
        # Client selection
        client_id = st.selectbox(
            "Select Client:",
            ["Rev", "Other Client"],
            help="Choose the client for analysis"
        )
        
        # Generate report button
        if st.button("🎯 Generate Enhanced Analyst Report", type="primary"):
            with st.spinner("Generating executive-ready analyst report..."):
                try:
                    from generate_enhanced_analyst_toolkit import generate_enhanced_analyst_toolkit
                    
                    # Generate the report
                    filename = generate_enhanced_analyst_toolkit(client_id)
                    
                    if filename:
                        st.success(f"✅ Report generated successfully!")
                        st.info(f"📄 File: {filename}")
                        
                        # Read and display the report
                        with open(filename, 'r', encoding='utf-8') as f:
                            report_content = f.read()
                        
                        # Save to production folder
                        production_filename = f"production_analyst_toolkit/latest_{client_id}_report.txt"
                        with open(production_filename, 'w', encoding='utf-8') as f:
                            f.write(report_content)
                        
                        st.success(f"📁 Saved to production folder: {production_filename}")
                        
                        # Display report sections
                        display_report_sections(report_content)
                        
                    else:
                        st.error("❌ Failed to generate report")
                        
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    st.exception(e)
    
    with col2:
        st.header("📋 Report Features")
        
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
        if os.path.exists("production_analyst_toolkit/latest_Rev_report.txt"):
            st.subheader("📄 Latest Report")
            st.markdown("**Rev Analysis Report**")
            
            # Get file size
            file_size = os.path.getsize("production_analyst_toolkit/latest_Rev_report.txt")
            st.caption(f"File size: {file_size:,} characters")
            
            # Download button
            with open("production_analyst_toolkit/latest_Rev_report.txt", "r") as f:
                st.download_button(
                    label="📥 Download Latest Report",
                    data=f.read(),
                    file_name=f"Rev_Analyst_Report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )

def display_report_sections(report_content):
    """Display the report in organized sections"""
    
    st.header("📋 Generated Report")
    
    # Split content into sections
    sections = report_content.split("="*50)
    
    if len(sections) >= 2:
        # Executive Summary
        st.subheader("📋 Executive Summary")
        st.markdown(sections[1])
        
        # Competitive Performance Scorecard
        if len(sections) >= 3:
            st.subheader("📊 Competitive Performance Scorecard")
            st.markdown(sections[2])
            
            # Show criteria sections
            if len(sections) > 3:
                st.subheader("🎯 Individual Criteria Analysis")
                
                # Create tabs for each criterion
                criteria_sections = sections[3:]
                if criteria_sections:
                    tab_names = [f"Criterion {i+1}" for i in range(len(criteria_sections))]
                    tabs = st.tabs(tab_names)
                    
                    for i, (tab, section) in enumerate(zip(tabs, criteria_sections)):
                        with tab:
                            st.markdown(section)

if __name__ == "__main__":
    main() 