import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def show_theme_story_scorecard():
    """Show the theme story scorecard interface"""
    
    st.title("📋 Create Report Outline")
    st.markdown("Generate comprehensive report outlines with theme-driven narratives, evidence matrix, and scorecard framework for executive presentations.")
    
    # Get client ID from session state
    client_id = st.session_state.get('client_id', 'Rev')
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Report Outline Creation")
        
        # Generate report button
        if st.button("📋 Create Report Outline", type="primary", use_container_width=True):
            if not client_id:
                st.error("❌ Please select a client ID")
                return
            
            with st.spinner("📋 Creating report outline..."):
                try:
                    # Import and run the enhanced theme story scorecard
                    from official_scripts.enhanced_theme_story_scorecard import EnhancedThemeStoryScorecard
                    
                    # Create generator instance
                    generator = EnhancedThemeStoryScorecard()
                    generator.client_id = client_id
                    
                    # Generate the enhanced report
                    scorecard = generator.generate_enhanced_report()
                    
                    # Display results
                    st.success("✅ Report outline created successfully!")
                    
                    # Show executive summary
                    show_executive_summary(scorecard)
                    
                    # Show detailed analysis
                    show_detailed_analysis(scorecard)
                    
                    # Show download options
                    show_download_options(scorecard, client_id)
                    
                except Exception as e:
                    st.error(f"❌ Error creating report outline: {str(e)}")
                    st.exception(e)
        

    
    with col2:
        st.header("📈 Quick Stats")
        
        # Placeholder for quick stats
        if client_id:
            try:
                from official_scripts.database.supabase_database import SupabaseDatabase
                from official_scripts.core_analytics.interview_weighted_base import InterviewWeightedBase
                db = SupabaseDatabase()
                
                # Get data counts
                themes = db.get_themes(client_id)
                findings = db.get_stage3_findings(client_id)
                stage1_data = db.get_all_stage1_data_responses()
                client_data = stage1_data[stage1_data['client_id'] == client_id]
                
                st.metric("Themes", len(themes))
                st.metric("Findings", len(findings))
                st.metric("Quotes", len(client_data))
                
                # Interview-Weighted VOC Metrics
                st.subheader("🎯 Interview-Weighted VOC")
                analyzer = InterviewWeightedBase(db)
                metrics = analyzer.get_customer_metrics(client_id)
                
                st.metric(
                    "Customer Satisfaction", 
                    f"{metrics['customer_satisfaction_rate']}%",
                    help="Percentage of satisfied customers"
                )
                st.metric(
                    "Overall Score", 
                    f"{metrics['overall_score']}/10",
                    help="Interview-weighted score"
                )
                st.metric(
                    "Problem Customers", 
                    f"{metrics['problem_customers']}",
                    help="Customers with issues"
                )
                
                # Performance indicator
                performance_color = {
                    "Excellent": "green",
                    "Good": "blue", 
                    "Fair": "orange",
                    "Poor": "red",
                    "Critical": "red"
                }.get(metrics['performance_level'], "gray")
                
                st.markdown(f"""
                <div style="padding: 8px; border-radius: 4px; background-color: {performance_color}20; border-left: 3px solid {performance_color}; font-size: 0.9em;">
                    <strong>{metrics['performance_level']}</strong> ({metrics['overall_score']}/10)
                </div>
                """, unsafe_allow_html=True)
                
                # Recent activity
                st.subheader("🕒 Recent Activity")
                st.info("Outline creation ready")
                
            except Exception as e:
                st.warning("⚠️ Unable to load stats")
                st.caption(f"Error: {str(e)}")

def show_executive_summary(scorecard):
    """Display the executive summary"""
    
    st.header("📋 Executive Summary")
    
    # Calculate overall score
    total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
    total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
    
    # Overall performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Score", f"{overall_score:.1f}/10")
    
    with col2:
        performance_level = get_performance_level(overall_score)
        st.metric("Performance", performance_level.split(" - ")[0])
    
    with col3:
        total_themes = sum(len(data['all_themes']) for data in scorecard.values())
        st.metric("Total Themes", total_themes)
    
    # Scorecard framework
    st.subheader("📊 Scorecard Framework")
    
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        
        with st.expander(f"{data['framework']['title']} (Weight: {metrics['weight']*100:.0f}%)"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Score", f"{metrics['score']:.1f}/10")
            
            with col2:
                st.metric("Performance", metrics['performance'])
            
            with col3:
                st.metric("Evidence", f"{metrics.get('total_evidence', 0)} items")
            
            # Executive narrative
            narrative = data['narrative_analysis']
            st.write(f"**Strengths:** {narrative['strengths_narrative']}")
            st.write(f"**Areas for Improvement:** {narrative['weaknesses_narrative']}")
            st.write(f"**Opportunities:** {narrative['opportunities_narrative']}")

def show_detailed_analysis(scorecard):
    """Display detailed theme analysis"""
    
    st.header("🎯 Detailed Theme Analysis")
    
    for criterion, data in scorecard.items():
        st.subheader(f"📋 {data['framework']['title']}")
        
        # Theme distribution
        narrative = data['narrative_analysis']
        dist = narrative['theme_distribution']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Positive Themes", dist['positive_themes'])
        with col2:
            st.metric("Negative Themes", dist['negative_themes'])
        with col3:
            st.metric("Neutral Themes", dist['neutral_themes'])
        
        # Key themes
        st.write("**Key Themes:**")
        for theme in data['all_themes'][:3]:  # Top 3 themes
            evidence = data['theme_evidence'].get(theme['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            with st.expander(f"• {theme['title']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Direction:** {theme['direction']['direction']}")
                    st.write(f"**Business Impact:** {theme['business_impact']['description']}")
                    st.write(f"**Evidence:** {evidence_summary.get('total_evidence', 0)} items")
                    st.write(f"**Strength:** {evidence_summary.get('strength', 'none')}")
                    st.write(f"**Executive Summary:** {theme['executive_summary']}")
                
                with col2:
                    # Top supporting evidence
                    if evidence.get('quotes'):
                        top_quote = evidence['quotes'][0]
                        st.write(f"**Key Quote:** {top_quote['quote'][:100]}...")
                        st.caption(f"Source: {top_quote['company']} - {top_quote['interviewee_name']}")
                    
                    if evidence.get('findings'):
                        top_finding = evidence['findings'][0]
                        st.write(f"**Key Finding:** {top_finding['statement'][:100]}...")
                        st.caption(f"Source: {top_finding['company']} - {top_finding['interviewee_name']}")

def show_download_options(scorecard, client_id):
    """Show download options for the report"""
    
    st.header("📥 Download Options")
    
    # Generate report text
    report_text = generate_report_text(scorecard, client_id)
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download Report (TXT)",
            data=report_text,
            file_name=f"{client_id}_THEME_STORY_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        # Generate executive summary
        exec_summary = generate_executive_summary_text(scorecard, client_id)
        st.download_button(
            label="📋 Download Executive Summary (TXT)",
            data=exec_summary,
            file_name=f"{client_id}_EXECUTIVE_SUMMARY_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )



def get_performance_level(score):
    """Get performance level description"""
    if score >= 7.5:
        return 'Excellent - Strong theme-driven competitive advantages'
    elif score >= 6.0:
        return 'Good - Theme-supported competitive positioning'
    elif score >= 4.5:
        return 'Fair - Mixed theme impact on competitive position'
    elif score >= 3.0:
        return 'Poor - Theme-identified competitive disadvantages'
    else:
        return 'Critical - Major theme-driven competitive vulnerabilities'

def calculate_overall_score(scorecard):
    """Calculate overall score from scorecard"""
    total_weighted_score = sum(data['scorecard_metrics']['weighted_score'] for data in scorecard.values())
    total_weight = sum(data['scorecard_metrics']['weight'] for data in scorecard.values())
    return total_weighted_score / total_weight if total_weight > 0 else 0

def generate_report_text(scorecard, client_id):
    """Generate the full report text"""
    
    report_lines = []
    report_lines.append(f"🎯 {client_id.upper()} ENHANCED THEME-STORY SCORECARD REPORT")
    report_lines.append("Executive-Ready: Themes, Evidence, Credibility, Actionable Insights")
    report_lines.append("="*80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Executive Summary
    overall_score = calculate_overall_score(scorecard)
    performance_level = get_performance_level(overall_score)
    
    report_lines.append("📋 EXECUTIVE SUMMARY")
    report_lines.append(f"   Overall Score: {overall_score:.1f}/10")
    report_lines.append(f"   Performance Level: {performance_level}")
    report_lines.append("")
    
    # Scorecard Framework
    report_lines.append("   📊 SCORECARD FRAMEWORK:")
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        report_lines.append(f"     • {data['framework']['title']} (Weight: {metrics['weight']*100:.0f}%)")
        report_lines.append(f"       Score: {metrics['score']:.1f}/10, Performance: {metrics['performance']}")
        report_lines.append(f"       Evidence: {metrics.get('total_evidence', 0)} items, Coverage: {metrics.get('evidence_coverage', 'none')}")
    report_lines.append("")
    
    # Theme-Driven Stories
    report_lines.append("🎯 THEME-DRIVEN STORIES BY CRITERION")
    for criterion, data in scorecard.items():
        report_lines.append(f"\n   📋 {data['framework']['title']}")
        report_lines.append(f"     Weight: {data['scorecard_metrics']['weight']*100:.0f}%")
        report_lines.append(f"     Score: {data['scorecard_metrics']['score']:.1f}/10")
        report_lines.append(f"     Performance: {data['scorecard_metrics']['performance']}")
        
        narrative = data['narrative_analysis']
        report_lines.append(f"     🏆 Strengths: {narrative['strengths_narrative']}")
        report_lines.append(f"     🔧 Areas for Improvement: {narrative['weaknesses_narrative']}")
        report_lines.append(f"     💡 Opportunities: {narrative['opportunities_narrative']}")
        report_lines.append(f"     📖 Overall Story: {narrative['overall_story']}")
        
        dist = narrative['theme_distribution']
        report_lines.append(f"     📊 Theme Distribution: {dist['positive_themes']} positive, {dist['negative_themes']} negative, {dist['neutral_themes']} neutral")
    
    return "\n".join(report_lines)

def generate_executive_summary_text(scorecard, client_id):
    """Generate executive summary text"""
    
    summary_lines = []
    summary_lines.append(f"📋 {client_id.upper()} EXECUTIVE SUMMARY")
    summary_lines.append("="*50)
    summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append("")
    
    # Overall score
    overall_score = calculate_overall_score(scorecard)
    performance_level = get_performance_level(overall_score)
    
    summary_lines.append(f"Overall Score: {overall_score:.1f}/10")
    summary_lines.append(f"Performance Level: {performance_level}")
    summary_lines.append("")
    
    # Key insights
    summary_lines.append("KEY INSIGHTS:")
    for criterion, data in scorecard.items():
        metrics = data['scorecard_metrics']
        narrative = data['narrative_analysis']
        
        if metrics['performance'] in ['poor', 'critical']:
            summary_lines.append(f"• {data['framework']['title']}: {narrative['weaknesses_narrative']}")
        elif metrics['performance'] in ['excellent', 'good']:
            summary_lines.append(f"• {data['framework']['title']}: {narrative['strengths_narrative']}")
    
    return "\n".join(summary_lines) 