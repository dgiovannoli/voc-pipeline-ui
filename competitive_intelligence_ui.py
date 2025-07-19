#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from enhanced_competitive_intelligence import EnhancedCompetitiveIntelligence
from supabase_database import SupabaseDatabase
import json
from datetime import datetime

def get_client_id():
    """Safely get client_id from session state."""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.warning("⚠️ **Client ID Required**")
        st.info("Please set a Client ID in the sidebar before proceeding.")
        st.stop()
    return client_id

def show_competitive_intelligence_dashboard():
    """Display the competitive intelligence dashboard"""
    st.title("🎯 Enhanced Competitive Intelligence Dashboard")
    
    client_id = get_client_id()
    
    # Initialize analyzer
    analyzer = EnhancedCompetitiveIntelligence(client_id)
    
    # Detect data type
    data_type = analyzer.detect_data_type()
    
    # Display data type info
    if data_type == "satisfaction":
        st.info("📊 **Satisfaction Analysis Mode** - Analyzing customer satisfaction and engagement patterns")
    elif data_type == "win_loss":
        st.info("🏆 **Win/Loss Analysis Mode** - Analyzing competitive performance and deal outcomes")
    else:
        st.warning("⚠️ **Unknown Data Type** - Unable to determine analysis mode")
    
    # Generate dashboard data
    with st.spinner("Analyzing competitive intelligence data..."):
        dashboard_data = analyzer.generate_executive_dashboard()
    
    if 'error' in dashboard_data:
        st.error(dashboard_data['error'])
        st.info("💡 **Next Steps:**")
        st.info("1. Run Stage 2: Response Labeling to score quotes against criteria")
        st.info("2. Return here to view competitive intelligence insights")
        return
    
    # Display summary metrics
    summary = dashboard_data['summary_metrics']
    
    st.success(f"✅ **Analysis Complete** - {summary['total_quotes']} quotes across {summary['total_deals']} deals")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if data_type == "win_loss":
            st.metric("Competitive Health Score", f"{summary['overall_score']}/100")
        else:
            st.metric("Overall Satisfaction Score", f"{summary['overall_score']}/100")
    with col2:
        if data_type == "win_loss":
            st.metric("Win Rate", f"{summary['win_rate']}%")
        else:
            st.metric("Customer Satisfaction", f"{summary['win_rate']}%")
    with col3:
        st.metric("Critical Issues", summary['critical_issues_count'])
    with col4:
        st.metric("Key Strengths", summary['strengths_count'])
    
    st.markdown("---")
    
    # Metrics visualization
    metrics = dashboard_data['metrics']
    
    if metrics:
        # Create radar chart
        st.subheader("📊 Performance Score by Criterion")
        fig = create_radar_chart(metrics, data_type)
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics table
        st.subheader("📋 Detailed Performance Metrics")
        metrics_df = create_metrics_dataframe(metrics, data_type)
        st.dataframe(metrics_df, use_container_width=True)
    else:
        st.warning("No metrics available. Please run Stage 2 analysis first.")
    
    # Insights Analysis
    st.markdown("---")
    st.subheader("🎯 Key Insights Analysis")
    
    insights = dashboard_data['insights']
    
    # Strengths
    if insights.get('strengths'):
        st.markdown("**🟢 Top Strengths**")
        strengths_df = pd.DataFrame(insights['strengths'])
        if data_type == "win_loss":
            strengths_df = strengths_df[['criterion', 'avg_score', 'sample_size', 'category']]
            strengths_df.columns = ['Criterion', 'Average Score', 'Sample Size', 'Category']
        else:
            strengths_df = strengths_df[['criterion', 'satisfaction_score', 'positive_rate', 'category']]
            strengths_df.columns = ['Criterion', 'Satisfaction Score', 'Positive Rate (%)', 'Category']
        st.dataframe(strengths_df, use_container_width=True)
    else:
        st.info("No significant strengths identified yet.")
    
    # Weaknesses
    if insights.get('weaknesses'):
        st.markdown("**🔴 Areas for Improvement**")
        weaknesses_df = pd.DataFrame(insights['weaknesses'])
        if data_type == "win_loss":
            weaknesses_df = weaknesses_df[['criterion', 'avg_score', 'sample_size', 'category']]
            weaknesses_df.columns = ['Criterion', 'Average Score', 'Sample Size', 'Category']
        else:
            weaknesses_df = weaknesses_df[['criterion', 'satisfaction_score', 'negative_rate', 'category']]
            weaknesses_df.columns = ['Criterion', 'Satisfaction Score', 'Negative Rate (%)', 'Category']
        st.dataframe(weaknesses_df, use_container_width=True)
    else:
        st.info("No significant weaknesses identified yet.")
    
    # Critical Issues
    if insights.get('critical_issues'):
        st.markdown("**⚠️ Critical Issues Requiring Immediate Attention**")
        issues_df = pd.DataFrame(insights['critical_issues'])
        if data_type == "win_loss":
            issues_df = issues_df[['criterion', 'deal_breaker_rate', 'category']]
            issues_df.columns = ['Criterion', 'Deal Breaker Rate (%)', 'Category']
        else:
            issues_df = issues_df[['criterion', 'critical_issue_rate', 'category']]
            issues_df.columns = ['Criterion', 'Critical Issue Rate (%)', 'Category']
        st.dataframe(issues_df, use_container_width=True)
    else:
        st.info("No critical issues identified.")
    
    # Opportunities
    if insights.get('opportunities'):
        st.markdown("**🏆 Opportunities for Growth**")
        opps_df = pd.DataFrame(insights['opportunities'])
        if data_type == "win_loss":
            opps_df = opps_df[['criterion', 'win_loss_gap', 'category']]
            opps_df.columns = ['Criterion', 'Win/Loss Gap', 'Category']
        else:
            opps_df = opps_df[['criterion', 'positive_rate', 'satisfaction_score', 'category']]
            opps_df.columns = ['Criterion', 'Positive Rate (%)', 'Satisfaction Score', 'Category']
        st.dataframe(opps_df, use_container_width=True)
    else:
        st.info("No opportunities identified yet.")
    
    # Executive Insights
    st.markdown("---")
    st.subheader("💡 Executive Insights")
    
    executive_insights = generate_executive_insights(dashboard_data)
    
    for insight in executive_insights:
        if insight['type'] == 'positive':
            st.success(insight['message'])
        elif insight['type'] == 'warning':
            st.warning(insight['message'])
        elif insight['type'] == 'info':
            st.info(insight['message'])
    
    # Export functionality
    st.markdown("---")
    st.subheader("📤 Export Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Analysis to Database"):
            if save_competitive_analysis(dashboard_data, client_id):
                st.success("✅ Analysis saved to database!")
            else:
                st.error("❌ Failed to save analysis")
    
    with col2:
        # Export to CSV
        if metrics:
            export_df = pd.DataFrame.from_dict(metrics, orient='index')
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Metrics CSV",
                data=csv,
                file_name=f"competitive_intelligence_{client_id}_{data_type}.csv",
                mime="text/csv"
            )

def create_radar_chart(metrics: dict, data_type: str) -> go.Figure:
    """Create radar chart for metrics"""
    if not metrics:
        return go.Figure()
    
    # Prepare data for radar chart
    criteria_names = [metric['criterion_name'] for metric in metrics.values()]
    
    if data_type == "win_loss":
        values = [metric['health_score'] for metric in metrics.values()]
        title = "Competitive Health Score by Criterion"
    else:
        values = [metric['satisfaction_score'] for metric in metrics.values()]
        title = "Satisfaction Score by Criterion"
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=criteria_names,
        fill='toself',
        name='Performance Score',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title=title,
        height=500
    )
    
    return fig

def create_metrics_dataframe(metrics: dict, data_type: str) -> pd.DataFrame:
    """Create metrics dataframe based on data type"""
    if data_type == "win_loss":
        metrics_df = pd.DataFrame.from_dict(metrics, orient='index')
        display_cols = ['criterion_name', 'category', 'health_score', 'overall_avg', 'win_avg', 'loss_avg', 'win_loss_gap', 'deal_breaker_rate', 'deal_winner_rate', 'sample_size']
        display_cols = [col for col in display_cols if col in metrics_df.columns]
        metrics_df = metrics_df[display_cols]
        metrics_df.columns = ['Criterion', 'Category', 'Health Score', 'Overall Avg', 'Win Avg', 'Loss Avg', 'Win/Loss Gap', 'Deal Breaker %', 'Deal Winner %', 'Sample Size']
    else:
        metrics_df = pd.DataFrame.from_dict(metrics, orient='index')
        display_cols = ['criterion_name', 'category', 'satisfaction_score', 'overall_avg', 'positive_rate', 'negative_rate', 'critical_issue_rate', 'strength_rate', 'sample_size']
        display_cols = [col for col in display_cols if col in metrics_df.columns]
        metrics_df = metrics_df[display_cols]
        metrics_df.columns = ['Criterion', 'Category', 'Satisfaction Score', 'Overall Avg', 'Positive %', 'Negative %', 'Critical Issues %', 'Strengths %', 'Sample Size']
    
    # Sort by score
    if data_type == "win_loss":
        metrics_df = metrics_df.sort_values('Health Score', ascending=False)
    else:
        metrics_df = metrics_df.sort_values('Satisfaction Score', ascending=False)
    
    return metrics_df

def generate_executive_insights(dashboard_data: dict) -> list:
    """Generate executive insights from the analysis"""
    insights = []
    summary = dashboard_data['summary_metrics']
    data_type = summary['data_type']
    metrics = dashboard_data['metrics']
    insights_data = dashboard_data['insights']
    
    if data_type == "win_loss":
        # Win/loss insights
        if summary['overall_score'] >= 70:
            insights.append({
                'type': 'positive',
                'message': f"Strong competitive position with {summary['overall_score']}/100 health score"
            })
        elif summary['overall_score'] >= 50:
            insights.append({
                'type': 'info',
                'message': f"Moderate competitive position with {summary['overall_score']}/100 health score - room for improvement"
            })
        else:
            insights.append({
                'type': 'warning',
                'message': f"Competitive position needs attention with {summary['overall_score']}/100 health score"
            })
        
        if summary['win_rate'] >= 60:
            insights.append({
                'type': 'positive',
                'message': f"Strong win rate of {summary['win_rate']}% indicates effective competitive positioning"
            })
        elif summary['win_rate'] >= 40:
            insights.append({
                'type': 'info',
                'message': f"Win rate of {summary['win_rate']}% suggests competitive parity - focus on differentiation"
            })
        else:
            insights.append({
                'type': 'warning',
                'message': f"Low win rate of {summary['win_rate']}% indicates competitive challenges requiring immediate attention"
            })
    
    else:
        # Satisfaction insights
        if summary['overall_score'] >= 70:
            insights.append({
                'type': 'positive',
                'message': f"High customer satisfaction with {summary['overall_score']}/100 satisfaction score"
            })
        elif summary['overall_score'] >= 50:
            insights.append({
                'type': 'info',
                'message': f"Moderate customer satisfaction with {summary['overall_score']}/100 score - opportunities for improvement"
            })
        else:
            insights.append({
                'type': 'warning',
                'message': f"Low customer satisfaction with {summary['overall_score']}/100 score - immediate action required"
            })
    
    # Critical issues insights
    if insights_data.get('critical_issues'):
        insights.append({
            'type': 'warning',
            'message': f"Found {len(insights_data['critical_issues'])} critical issues requiring immediate attention"
        })
    
    # Strengths insights
    if insights_data.get('strengths'):
        insights.append({
            'type': 'positive',
            'message': f"Identified {len(insights_data['strengths'])} key strengths to leverage"
        })
    
    # Sample size insights
    if summary['total_deals'] < 10:
        insights.append({
            'type': 'info',
            'message': f"Limited sample size ({summary['total_deals']} deals) - consider collecting more data for statistical significance"
        })
    
    return insights

def save_competitive_analysis(dashboard_data: dict, client_id: str) -> bool:
    """Save competitive analysis results to database"""
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        
        analysis_data = {
            'client_id': client_id,
            'generated_at': datetime.now().isoformat(),
            'data_type': dashboard_data['data_type'],
            'summary_metrics': json.dumps(dashboard_data['summary_metrics']),
            'metrics': json.dumps(dashboard_data['metrics']),
            'insights': json.dumps(dashboard_data['insights']),
            'total_quotes_analyzed': dashboard_data['summary_metrics']['total_quotes'],
            'total_deals_analyzed': dashboard_data['summary_metrics']['total_deals'],
            'overall_score': dashboard_data['summary_metrics']['overall_score']
        }
        
        # Save to competitive_analysis table
        result = db.supabase.table('competitive_analysis').insert(analysis_data).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error saving competitive analysis: {e}")
        return False

def show_competitive_intelligence_setup():
    """Show setup instructions for competitive intelligence"""
    st.title("🎯 Enhanced Competitive Intelligence Setup")
    
    st.markdown("""
    ### What is Enhanced Competitive Intelligence?
    
    This dashboard automatically adapts to your data type and provides actionable insights:
    
    **🏆 Win/Loss Analysis Mode** (for competitive deals):
    - Competitive health scores (0-100) for each criterion
    - Win/loss drivers - what's causing wins and losses
    - Critical gaps - deal-breaking issues to fix
    - Competitive advantages - strengths to leverage
    
    **📊 Satisfaction Analysis Mode** (for self-serve customers):
    - Customer satisfaction scores (0-100) for each criterion
    - Satisfaction drivers - what customers love and hate
    - Critical issues - problems causing dissatisfaction
    - Opportunities - areas for improvement
    
    ### Prerequisites:
    
    1. **Stage 2 Analysis Complete**: Quotes must be labeled against the 10 criteria
    2. **Sufficient Sample Size**: Ideally 10+ deals for meaningful analysis
    
    ### What You'll Get:
    
    - **Adaptive Analysis**: Automatically detects your data type
    - **Executive Insights**: Actionable recommendations
    - **Performance Metrics**: Quantified competitive health or satisfaction scores
    - **Key Drivers**: What's working and what needs improvement
    """)
    
    # Check current status
    client_id = get_client_id()
    
    try:
        db = SupabaseDatabase()
        
        # Check Stage 2 data
        stage2_data = db.get_stage2_response_labeling(client_id)
        stage2_count = len(stage2_data) if not stage2_data.empty else 0
        
        # Check Stage 1 data
        stage1_data = db.get_stage1_data_responses(client_id=client_id)
        stage1_count = len(stage1_data) if not stage1_data.empty else 0
        
        st.subheader("📊 Current Status")
        
        col1, col2 = st.columns(2)
        with col1:
            if stage2_count > 0:
                st.success(f"✅ Stage 2 Data: {stage2_count} labeled quotes")
            else:
                st.error("❌ Stage 2 Data: No labeled quotes found")
        
        with col2:
            if stage1_count > 0:
                st.success(f"✅ Stage 1 Data: {stage1_count} responses")
            else:
                st.error("❌ Stage 1 Data: No responses found")
        
        if stage2_count > 0 and stage1_count > 0:
            st.success("🎉 Ready for Enhanced Competitive Intelligence Analysis!")
            if st.button("🚀 Go to Competitive Intelligence Dashboard"):
                st.session_state.show_competitive_dashboard = True
                st.rerun()
        else:
            st.warning("⚠️ Please complete the prerequisites before proceeding")
            
    except Exception as e:
        st.error(f"Error checking status: {e}")

def show_competitive_intelligence():
    """Main competitive intelligence interface"""
    
    # Check if we should show the dashboard or setup
    if st.session_state.get('show_competitive_dashboard', False):
        show_competitive_intelligence_dashboard()
    else:
        show_competitive_intelligence_setup() 