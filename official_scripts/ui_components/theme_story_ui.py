import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def show_theme_story_scorecard():
    """Show the theme story scorecard interface"""
    
    st.title("🎯 Theme Story Scorecard Report Generator")
    st.markdown("Generate theme-driven story reports where themes tell the story, evidence supports the narrative, and scorecard framework anchors the analysis.")
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Report Configuration")
    
    # Client selection
    client_id = st.sidebar.selectbox(
        "Select Client:",
        ["Rev", "Client_A", "Client_B", "Custom"],
        help="Choose the client for analysis"
    )
    
    if client_id == "Custom":
        client_id = st.sidebar.text_input("Enter Custom Client ID:", value="")
    
    # Report type selection
    report_type = st.sidebar.selectbox(
        "Report Type:",
        ["Theme Story Scorecard", "Executive Summary", "Detailed Analysis"],
        help="Choose the type of report to generate"
    )
    
    # Analysis depth
    analysis_depth = st.sidebar.selectbox(
        "Analysis Depth:",
        ["Standard", "Comprehensive", "Executive"],
        help="Choose the depth of analysis"
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Report Generation")
        
        # Generate report button
        if st.button("🚀 Generate Theme Story Report", type="primary", use_container_width=True):
            if not client_id:
                st.error("❌ Please select a client ID")
                return
            
            with st.spinner("🎯 Generating theme story scorecard report..."):
                try:
                    # Import and run the theme story scorecard
                    from official_scripts.rev_theme_story_scorecard import RevThemeStoryScorecard
                    
                    # Create generator instance
                    generator = RevThemeStoryScorecard()
                    generator.client_id = client_id
                    
                    # Generate the report
                    scorecard = generator.generate_theme_story_report()
                    
                    # Display results
                    st.success("✅ Report generated successfully!")
                    
                    # Show executive summary
                    show_executive_summary(scorecard)
                    
                    # Show detailed analysis
                    show_detailed_analysis(scorecard)
                    
                    # Show download options
                    show_download_options(scorecard, client_id)
                    
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    st.exception(e)
        
        # Report outline development
        st.markdown("---")
        st.header("📋 Develop Report Outline")
        
        if st.button("🎨 Create Report Outline", use_container_width=True):
            if not client_id:
                st.error("❌ Please select a client ID")
                return
            
            with st.spinner("📋 Developing report outline..."):
                try:
                    outline = create_report_outline(client_id)
                    show_report_outline(outline)
                except Exception as e:
                    st.error(f"❌ Error creating outline: {str(e)}")
                    st.exception(e)
    
    with col2:
        st.header("📈 Quick Stats")
        
        # Placeholder for quick stats
        if client_id:
            try:
                from official_scripts.database.supabase_database import SupabaseDatabase
                db = SupabaseDatabase()
                
                # Get data counts
                themes = db.get_themes(client_id)
                findings = db.get_stage3_findings(client_id)
                stage1_data = db.get_all_stage1_data_responses()
                client_data = stage1_data[stage1_data['client_id'] == client_id]
                
                st.metric("Themes", len(themes))
                st.metric("Findings", len(findings))
                st.metric("Quotes", len(client_data))
                
                # Recent activity
                st.subheader("🕒 Recent Activity")
                st.info("Report generation ready")
                
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
        total_themes = sum(len(data['story_themes']) for data in scorecard.values())
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
            
            # Story theme
            narrative = data['narrative_analysis']
            st.write(f"**Story Theme:** {narrative['story_theme']}")
            
            # Win/Loss narratives
            if narrative['win_narrative'] != "No clear winning themes identified in this area.":
                st.success(f"**Win Narrative:** {narrative['win_narrative']}")
            
            if narrative['loss_narrative'] != "No significant challenges identified in this area.":
                st.error(f"**Loss Narrative:** {narrative['loss_narrative']}")

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
            st.metric("Win Themes", dist['win_themes'])
        with col2:
            st.metric("Loss Themes", dist['loss_themes'])
        with col3:
            st.metric("Neutral Themes", dist['neutral_themes'])
        
        # Key themes
        st.write("**Key Themes:**")
        for theme in data['story_themes'][:3]:  # Top 3 themes
            evidence = data['theme_evidence'].get(theme['theme_id'], {})
            evidence_summary = evidence.get('evidence_summary', {})
            
            with st.expander(f"• {theme['title']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Direction:** {theme['story_direction']['direction']}")
                    st.write(f"**Story Type:** {theme['story_direction']['story_type']}")
                    st.write(f"**Evidence:** {evidence_summary.get('total_evidence', 0)} items")
                    st.write(f"**Strength:** {evidence_summary.get('strength', 'none')}")
                
                with col2:
                    # Top supporting evidence
                    if evidence.get('quotes'):
                        top_quote = evidence['quotes'][0]
                        st.write(f"**Key Quote:** {top_quote['quote'][:100]}...")
                        st.caption(f"Source: {top_quote['company']} - {top_quote['interviewee']}")
                    
                    if evidence.get('findings'):
                        top_finding = evidence['findings'][0]
                        st.write(f"**Key Finding:** {top_finding['statement'][:100]}...")
                        st.caption(f"Source: {top_finding['company']} - {top_finding['interviewee']}")

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

def create_report_outline(client_id):
    """Create a report outline based on the theme analysis"""
    
    try:
        from official_scripts.rev_theme_story_scorecard import RevThemeStoryScorecard
        
        # Create generator instance
        generator = RevThemeStoryScorecard()
        generator.client_id = client_id
        
        # Generate the report to get data
        scorecard = generator.generate_theme_story_report()
        
        # Create outline structure
        outline = {
            'client_id': client_id,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': calculate_overall_score(scorecard),
            'sections': []
        }
        
        # Add sections based on scorecard criteria
        for criterion, data in scorecard.items():
            section = {
                'title': data['framework']['title'],
                'weight': data['scorecard_metrics']['weight'],
                'score': data['scorecard_metrics']['score'],
                'performance': data['scorecard_metrics']['performance'],
                'story_theme': data['narrative_analysis']['story_theme'],
                'win_narrative': data['narrative_analysis']['win_narrative'],
                'loss_narrative': data['narrative_analysis']['loss_narrative'],
                'key_themes': []
            }
            
            # Add key themes
            for theme in data['story_themes'][:3]:
                section['key_themes'].append({
                    'title': theme['title'],
                    'direction': theme['story_direction']['direction'],
                    'story_type': theme['story_direction']['story_type']
                })
            
            outline['sections'].append(section)
        
        return outline
        
    except Exception as e:
        st.error(f"Error creating outline: {str(e)}")
        return None

def show_report_outline(outline):
    """Display the report outline"""
    
    if not outline:
        return
    
    st.header("📋 Report Outline")
    
    # Overall summary
    st.subheader("📊 Overall Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Client", outline['client_id'])
    
    with col2:
        st.metric("Overall Score", f"{outline['overall_score']:.1f}/10")
    
    with col3:
        st.metric("Generated", outline['generated_date'])
    
    # Sections
    st.subheader("📋 Report Sections")
    
    for i, section in enumerate(outline['sections'], 1):
        with st.expander(f"{i}. {section['title']} (Score: {section['score']:.1f}/10)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Weight:** {section['weight']*100:.0f}%")
                st.write(f"**Performance:** {section['performance']}")
                st.write(f"**Story Theme:** {section['story_theme']}")
            
            with col2:
                if section['win_narrative'] != "No clear winning themes identified in this area.":
                    st.success(f"**Win:** {section['win_narrative'][:100]}...")
                
                if section['loss_narrative'] != "No significant challenges identified in this area.":
                    st.error(f"**Loss:** {section['loss_narrative'][:100]}...")
            
            # Key themes
            st.write("**Key Themes:**")
            for theme in section['key_themes']:
                direction_color = "🟢" if theme['direction'] == 'positive' else "🔴" if theme['direction'] == 'negative' else "🟡"
                st.write(f"{direction_color} {theme['title']} ({theme['story_type']})")

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
    report_lines.append(f"🎯 {client_id.upper()} THEME-STORY SCORECARD REPORT")
    report_lines.append("Themes Tell the Story, Evidence Supports, Scorecard Anchors")
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
        report_lines.append(f"     🎭 Story Theme: {narrative['story_theme']}")
        report_lines.append(f"     🏆 Win Narrative: {narrative['win_narrative']}")
        report_lines.append(f"     ❌ Loss Narrative: {narrative['loss_narrative']}")
        report_lines.append(f"     📖 Overall Story: {narrative['overall_story']}")
        
        dist = narrative['theme_distribution']
        report_lines.append(f"     📊 Theme Distribution: {dist['win_themes']} wins, {dist['loss_themes']} losses, {dist['neutral_themes']} neutral")
    
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
            summary_lines.append(f"• {data['framework']['title']}: {narrative['loss_narrative']}")
        elif metrics['performance'] in ['excellent', 'good']:
            summary_lines.append(f"• {data['framework']['title']}: {narrative['win_narrative']}")
    
    return "\n".join(summary_lines) 