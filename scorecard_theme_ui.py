#!/usr/bin/env python3

"""
UI Component for Scorecard-Driven Theme Display

This module provides Streamlit components to display scorecard-driven themes
alongside existing similarity-based themes for comprehensive analysis.
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional
from supabase_database import SupabaseDatabase
import re
from collections import Counter

def make_executive_title(theme_title, criterion, sentiment):
    # Example: "Positive: Security_Compliance Excellence" -> "Rev’s Security Compliance Drives Client Trust and Efficiency"
    # Remove generic prefixes and make concise
    title = theme_title
    # Remove prefixes like 'Positive:', 'Mixed:', etc.
    title = re.sub(r'^(Positive|Mixed|Negative):\s*', '', title, flags=re.IGNORECASE)
    # Replace underscores and make more readable
    title = title.replace('_', ' ').replace('Excellence', '').strip()
    # Add punchy executive language
    if sentiment == 'positive':
        return f"{title}: A Key Differentiator for Clients"
    elif sentiment == 'negative':
        return f"{title}: Barrier to Client Satisfaction"
    elif sentiment == 'mixed':
        return f"{title}: Mixed Client Experiences"
    else:
        return title

def enrich_performance_summary(summary, quotes):
    """Extract actual insights from quotes to enrich performance summary"""
    if not quotes:
        return summary
    
    companies = set(q.get('company', 'Unknown') for q in quotes if isinstance(q, dict))
    key_points = []
    
    for q in quotes:
        if isinstance(q, dict):
            text = q.get('text', '').lower()
            if 'turnaround' in text or 'speed' in text or 'fast' in text or 'quick' in text:
                key_points.append('rapid turnaround')
            if 'accuracy' in text or 'precise' in text or 'correct' in text:
                key_points.append('high accuracy')
            if 'cost' in text or 'price' in text or 'billing' in text or 'expensive' in text or 'cheap' in text:
                key_points.append('cost efficiency')
            if 'security' in text or 'compliance' in text or 'encryption' in text:
                key_points.append('secure & compliant')
            if 'support' in text or 'help' in text or 'assistance' in text:
                key_points.append('excellent support')
            if 'integration' in text or 'api' in text or 'connect' in text:
                key_points.append('seamless integration')
            if 'ease' in text or 'easy' in text or 'simple' in text:
                key_points.append('user-friendly')
    
    # Remove duplicates and limit to top 3
    key_points = list(set(key_points))[:3]
    
    if key_points:
        return f"Clients from {len(companies)} companies highlight {', '.join(key_points)}."
    else:
        return summary

def deduplicate_quotes(quotes):
    """Robust deduplication of quotes with text normalization"""
    seen = set()
    deduped = []
    
    for q in quotes:
        if isinstance(q, dict):
            text = q.get('text', '').strip()
        else:
            text = str(q).strip()
        
        if not text:
            continue
        
        # Normalize text (remove extra spaces, punctuation, convert to lowercase)
        normalized = re.sub(r'\s+', ' ', text.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        if normalized and normalized not in seen:
            deduped.append(q)
            seen.add(normalized)
    
    return deduped

def display_scorecard_themes(client_id: str = 'default'):
    """Display scorecard-driven themes in the UI"""
    
    st.subheader("🎯 Scorecard-Driven Themes")
    st.markdown("""
    **Strategic Context**: These themes are anchored to the buyer's prioritized scorecard criteria, 
    using high-relevance quotes as illustrative evidence—regardless of whether those quotes are similar to one another.
    """)
    
    # Get scorecard themes from database
    db = SupabaseDatabase()
    
    try:
        response = db.supabase.table('scorecard_themes').select('*').eq('client_id', client_id).order('overall_quality_score', desc=True).execute()
        themes_data = response.data
        
        if not themes_data:
            st.info("No scorecard themes found. Run Stage 4B analysis to generate themes.")
            return
        
        # Convert to DataFrame for easier manipulation
        themes_df = pd.DataFrame(themes_data)
        
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Themes", len(themes_df))
        
        with col2:
            high_quality = len(themes_df[themes_df['overall_quality_score'] >= 0.7])
            st.metric("High Quality", high_quality)
        
        with col3:
            avg_quality = themes_df['overall_quality_score'].mean()
            st.metric("Avg Quality", f"{avg_quality:.2f}" if avg_quality is not None else "N/A")
        
        with col4:
            criteria_covered = themes_df['scorecard_criterion'].nunique()
            st.metric("Criteria Covered", criteria_covered)
        
        # Filter options
        st.subheader("🔍 Filter Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_criteria = st.multiselect(
                "Filter by Criteria",
                options=sorted(themes_df['scorecard_criterion'].unique()),
                default=sorted(themes_df['scorecard_criterion'].unique()),
                key=f"scorecard_theme_criteria_multiselect_{client_id}"
            )
        
        with col2:
            selected_sentiment = st.multiselect(
                "Filter by Sentiment",
                options=sorted(themes_df['sentiment_direction'].unique()),
                default=sorted(themes_df['sentiment_direction'].unique()),
                key=f"scorecard_theme_sentiment_multiselect_{client_id}"
            )
        
        with col3:
            min_quality = st.slider(
                "Minimum Quality Score",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                key=f"scorecard_theme_min_quality_slider_{client_id}"
            )
        
        # Apply filters
        filtered_df = themes_df[
            (themes_df['scorecard_criterion'].isin(selected_criteria)) &
            (themes_df['sentiment_direction'].isin(selected_sentiment)) &
            (themes_df['overall_quality_score'] >= min_quality)
        ]
        
        st.subheader(f"📋 Scorecard Themes ({len(filtered_df)} found)")
        
        # Display themes
        for idx, theme in filtered_df.iterrows():
            with st.expander(f"🎯 {make_executive_title(theme['theme_title'], theme['scorecard_criterion'], theme['sentiment_direction'])} (Quality: {theme['overall_quality_score']:.2f}" if theme['overall_quality_score'] is not None else "N/A"):
                
                # Theme details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Enrich performance summary
                    quotes = theme['supporting_quotes']
                    if isinstance(quotes, str):
                        import json
                        quotes = json.loads(quotes)
                    quotes = deduplicate_quotes(quotes)[:5]  # Limit to 5 diverse quotes
                    st.markdown(f"**Criterion:** {theme['scorecard_criterion']}")
                    st.markdown(f"**Sentiment:** {theme['sentiment_direction'].title()}")
                    st.markdown(f"**Performance Summary:** {enrich_performance_summary(theme['client_performance_summary'], quotes)}")
                    
                    if theme.get('strategic_note'):
                        st.markdown(f"**Strategic Note:** {theme['strategic_note']}")
                    
                    if theme.get('competitive_positioning'):
                        st.markdown(f"**Competitive Positioning:** {theme['competitive_positioning']}")
                
                with col2:
                    st.metric("Quote Count", theme['quote_count'])
                    st.metric("Companies", theme['companies_represented'])
                    evidence_strength = theme.get('evidence_strength')
                    st.metric("Evidence Strength", f"{evidence_strength:.2f}" if evidence_strength is not None else "N/A")
                
                # Supporting quotes
                st.subheader("💬 Supporting Quotes")
                
                for i, quote in enumerate(quotes[:5], 1):  # Show first 5 deduped quotes
                    if isinstance(quote, dict):
                        quote_text = quote.get('text', str(quote))
                        company = quote.get('company', 'Unknown')
                        relevance = quote.get('relevance_score', 0)
                        sentiment = quote.get('sentiment', 'neutral')
                    else:
                        quote_text = str(quote)
                        company = 'Unknown'
                        relevance = 0
                        sentiment = 'neutral'
                    
                    st.markdown(f"""
                    **Quote {i}** ({company}) - Relevance: {relevance}, Sentiment: {sentiment}
                    > {quote_text}
                    """)
                
                # Quality metrics
                st.subheader("📊 Quality Metrics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Overall Quality", f"{theme['overall_quality_score']:.2f}" if theme['overall_quality_score'] is not None else "N/A")
                
                with col2:
                    evidence_strength = theme.get('evidence_strength')
                    st.metric("Evidence Strength", f"{evidence_strength:.2f}" if evidence_strength is not None else "N/A")
                
                with col3:
                    sentiment_consistency = theme.get('sentiment_consistency_score')
                    st.metric("Sentiment Consistency", f"{sentiment_consistency:.2f}" if sentiment_consistency is not None else "N/A")
                
                with col4:
                    quote_diversity = theme.get('quote_diversity_score')
                    st.metric("Quote Diversity", f"{quote_diversity:.2f}" if quote_diversity is not None else "N/A")
        
        # Download option
        if st.button("📥 Download Scorecard Themes"):
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"scorecard_themes_{client_id}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading scorecard themes: {e}")

def display_criteria_prioritization(client_id: str = 'default'):
    """Display criteria prioritization analysis"""
    
    st.subheader("📊 Criteria Prioritization Analysis")
    st.markdown("""
    **Purpose**: Identify which criteria were prioritized in buyer decisions based on high-relevance quotes and company coverage.
    """)
    
    # Get criteria prioritization data
    db = SupabaseDatabase()
    
    try:
        response = db.supabase.table('criteria_prioritization').select('*').eq('client_id', client_id).order('priority_rank').execute()
        criteria_data = response.data
        
        if not criteria_data:
            st.info("No criteria prioritization data found. Run Stage 4B analysis to generate prioritization.")
            return
        
        # Convert to DataFrame
        criteria_df = pd.DataFrame(criteria_data)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Criteria", len(criteria_df))
        
        with col2:
            prioritized = len(criteria_df[criteria_df['priority_rank'] <= 6])  # Top 6
            st.metric("Prioritized (Top 6)", prioritized)
        
        with col3:
            avg_priority_score = criteria_df['priority_score'].mean()
            st.metric("Avg Priority Score", f"{avg_priority_score:.2f}" if avg_priority_score is not None else "N/A")
        
        # Display prioritized criteria
        st.subheader("🎯 Prioritized Criteria (Top 6)")
        
        top_criteria = criteria_df[criteria_df['priority_rank'] <= 6].sort_values('priority_rank')
        
        for idx, criterion in top_criteria.iterrows():
            priority_score = criterion['priority_score']
            with st.expander(f"#{criterion['priority_rank']} {criterion['criterion']} (Score: {priority_score:.2f}" if priority_score is not None else "N/A"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("High Relevance Quotes", criterion['high_relevance_quotes'])
                    st.metric("Total Quotes", criterion['total_quotes'])
                    st.metric("Relevance Ratio", f"{criterion['relevance_ratio']:.1%}" if criterion['relevance_ratio'] is not None else "N/A")
                
                with col2:
                    st.metric("Companies Affected", criterion['companies_affected'])
                    st.metric("Positive Quotes", criterion['positive_quotes'])
                    st.metric("Negative Quotes", criterion['negative_quotes'])
                
                # Sentiment distribution
                st.subheader("😊 Sentiment Distribution")
                
                sentiment_data = {
                    'Positive': criterion['positive_quotes'],
                    'Negative': criterion['negative_quotes'],
                    'Neutral': criterion['neutral_quotes'],
                    'Mixed': criterion['mixed_quotes']
                }
                
                # Create a simple bar chart
                sentiment_df = pd.DataFrame(list(sentiment_data.items()), columns=['Sentiment', 'Count'])
                st.bar_chart(sentiment_df.set_index('Sentiment'))
        
        # Full criteria table
        st.subheader("📋 All Criteria Analysis")
        
        # Create a summary table
        summary_df = criteria_df[['criterion', 'priority_rank', 'priority_score', 'high_relevance_quotes', 'total_quotes', 'companies_affected']].copy()
        summary_df['relevance_ratio'] = summary_df['relevance_ratio'].apply(lambda x: f"{x:.1%}" if x is not None else "N/A")
        summary_df['priority_score'] = summary_df['priority_score'].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
        
        st.dataframe(summary_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading criteria prioritization: {e}")

def display_enhanced_synthesis(client_id: str = 'default'):
    """Display enhanced theme synthesis"""
    
    st.subheader("🔄 Enhanced Theme Synthesis")
    st.markdown("""
    **Purpose**: Combined insights from both scorecard-driven and similarity-based approaches for comprehensive analysis.
    """)
    
    # Get enhanced synthesis data
    db = SupabaseDatabase()
    
    try:
        response = db.supabase.table('enhanced_theme_synthesis').select('*').eq('client_id', client_id).order('synthesis_quality_score', desc=True).execute()
        synthesis_data = response.data
        
        if not synthesis_data:
            st.info("No enhanced synthesis data found. Run enhanced synthesis to generate combined insights.")
            return
        
        # Convert to DataFrame
        synthesis_df = pd.DataFrame(synthesis_data)
        
        # Display summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Syntheses", len(synthesis_df))
        
        with col2:
            hybrid_count = len(synthesis_df[synthesis_df['synthesis_type'] == 'hybrid'])
            st.metric("Hybrid Syntheses", hybrid_count)
        
        with col3:
            high_quality = len(synthesis_df[synthesis_df['synthesis_quality_score'] >= 0.7])
            st.metric("High Quality", high_quality)
        
        with col4:
            avg_quality = synthesis_df['synthesis_quality_score'].mean()
            st.metric("Avg Quality", f"{avg_quality:.2f}" if avg_quality is not None else "N/A")
        
        # Filter options
        st.subheader("🔍 Filter Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_type = st.multiselect(
                "Filter by Type",
                options=sorted(synthesis_df['synthesis_type'].unique()),
                default=sorted(synthesis_df['synthesis_type'].unique())
            )
        
        with col2:
            min_quality = st.slider(
                "Minimum Quality Score",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1
            )
        
        with col3:
            min_confidence = st.slider(
                "Minimum Hybrid Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1
            )
        
        # Apply filters
        filtered_df = synthesis_df[
            (synthesis_df['synthesis_type'].isin(selected_type)) &
            (synthesis_df['synthesis_quality_score'] >= min_quality) &
            (synthesis_df['hybrid_confidence'] >= min_confidence)
        ]
        
        st.subheader(f"📋 Enhanced Syntheses ({len(filtered_df)} found)")
        
        # Display syntheses
        for idx, synthesis in filtered_df.iterrows():
            synthesis_quality = synthesis['synthesis_quality_score']
            with st.expander(f"🔄 {synthesis['synthesis_title']} (Quality: {synthesis_quality:.2f}" if synthesis_quality is not None else "N/A"):
                
                # Synthesis details
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Type:** {synthesis['synthesis_type'].replace('_', ' ').title()}")
                    st.markdown(f"**Executive Insight:** {synthesis['executive_insight']}")
                    
                    if synthesis.get('strategic_implications'):
                        st.markdown(f"**Strategic Implications:** {synthesis['strategic_implications']}")
                    
                    if synthesis.get('action_recommendations'):
                        st.markdown(f"**Action Recommendations:** {synthesis['action_recommendations']}")
                
                with col2:
                    quality_score = synthesis['synthesis_quality_score']
                    evidence_convergence = synthesis['evidence_convergence_score']
                    stakeholder_alignment = synthesis['stakeholder_alignment_score']
                    
                    st.metric("Quality Score", f"{quality_score:.2f}" if quality_score is not None else "N/A")
                    st.metric("Evidence Convergence", f"{evidence_convergence:.2f}" if evidence_convergence is not None else "N/A")
                    st.metric("Stakeholder Alignment", f"{stakeholder_alignment:.2f}" if stakeholder_alignment is not None else "N/A")
                    
                    if synthesis['synthesis_type'] == 'hybrid':
                        hybrid_confidence = synthesis['hybrid_confidence']
                        st.metric("Hybrid Confidence", f"{hybrid_confidence:.2f}" if hybrid_confidence is not None else "N/A")
                
                # Source themes
                st.subheader("🔗 Source Themes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if synthesis.get('scorecard_theme_ids'):
                        st.markdown("**Scorecard Themes:**")
                        for theme_id in synthesis['scorecard_theme_ids']:
                            st.markdown(f"- Theme ID: {theme_id}")
                
                with col2:
                    if synthesis.get('similarity_theme_ids'):
                        st.markdown("**Similarity Themes:**")
                        for theme_id in synthesis['similarity_theme_ids']:
                            st.markdown(f"- Theme ID: {theme_id}")
        
        # Download option
        if st.button("📥 Download Enhanced Syntheses"):
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"enhanced_syntheses_{client_id}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading enhanced synthesis: {e}")

def display_comparison_view(client_id: str = 'default'):
    """Display comparison view between scorecard and similarity themes"""
    
    st.subheader("📊 Theme Comparison View")
    st.markdown("""
    **Purpose**: Compare insights from scorecard-driven vs similarity-based approaches.
    """)
    
    db = SupabaseDatabase()
    
    try:
        # Get both types of themes
        scorecard_response = db.supabase.table('scorecard_themes').select('*').eq('client_id', client_id).execute()
        scorecard_themes = scorecard_response.data
        
        similarity_response = db.supabase.table('themes').select('*').eq('client_id', client_id).execute()
        similarity_themes = similarity_response.data
        
        if not scorecard_themes and not similarity_themes:
            st.info("No themes found for comparison.")
            return
        
        # Create comparison metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scorecard Themes", len(scorecard_themes))
        
        with col2:
            st.metric("Similarity Themes", len(similarity_themes))
        
        with col3:
            total_themes = len(scorecard_themes) + len(similarity_themes)
            st.metric("Total Themes", total_themes)
        
        # Quality comparison
        st.subheader("📈 Quality Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if scorecard_themes:
                scorecard_df = pd.DataFrame(scorecard_themes)
                avg_quality = scorecard_df['overall_quality_score'].mean()
                high_quality = len(scorecard_df[scorecard_df['overall_quality_score'] >= 0.7])
                
                st.markdown("**Scorecard Themes Quality:**")
                st.metric("Average Quality", f"{avg_quality:.2f}" if avg_quality is not None else "N/A")
                st.metric("High Quality Count", high_quality)
                st.metric("High Quality %", f"{high_quality/len(scorecard_df)*100:.1f}%" if len(scorecard_df) > 0 else "N/A")
        
        with col2:
            if similarity_themes:
                similarity_df = pd.DataFrame(similarity_themes)
                avg_confidence = similarity_df['avg_confidence_score'].mean()
                high_confidence = len(similarity_df[similarity_df['avg_confidence_score'] >= 0.7])
                
                st.markdown("**Similarity Themes Quality:**")
                st.metric("Average Confidence", f"{avg_confidence:.2f}" if avg_confidence is not None else "N/A")
                st.metric("High Confidence Count", high_confidence)
                st.metric("High Confidence %", f"{high_confidence/len(similarity_df)*100:.1f}%" if len(similarity_df) > 0 else "N/A")
        
        # Criteria coverage comparison
        st.subheader("🎯 Criteria Coverage Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if scorecard_themes:
                scorecard_df = pd.DataFrame(scorecard_themes)
                criteria_counts = scorecard_df['scorecard_criterion'].value_counts()
                
                st.markdown("**Scorecard Themes by Criteria:**")
                for criterion, count in criteria_counts.items():
                    st.markdown(f"- {criterion}: {count} themes")
        
        with col2:
            if similarity_themes:
                similarity_df = pd.DataFrame(similarity_themes)
                category_counts = similarity_df['theme_category'].value_counts()
                
                st.markdown("**Similarity Themes by Category:**")
                for category, count in category_counts.items():
                    st.markdown(f"- {category}: {count} themes")
        
        # Sentiment distribution comparison
        st.subheader("😊 Sentiment Distribution Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if scorecard_themes:
                scorecard_df = pd.DataFrame(scorecard_themes)
                sentiment_counts = scorecard_df['sentiment_direction'].value_counts()
                
                st.markdown("**Scorecard Themes Sentiment:**")
                for sentiment, count in sentiment_counts.items():
                    st.markdown(f"- {sentiment.title()}: {count} themes")
        
        with col2:
            if similarity_themes:
                similarity_df = pd.DataFrame(similarity_themes)
                strength_counts = similarity_df['theme_strength'].value_counts()
                
                st.markdown("**Similarity Themes Strength:**")
                for strength, count in strength_counts.items():
                    st.markdown(f"- {strength}: {count} themes")
    
    except Exception as e:
        st.error(f"Error loading comparison data: {e}")

def main_scorecard_theme_ui(client_id: str = 'default'):
    """Main UI function for scorecard theme display"""
    
    st.title("🎯 Scorecard-Driven Theme Analysis")
    st.markdown("""
    This interface provides comprehensive analysis of scorecard-driven themes that complement 
    the existing similarity-based theme generation approach.
    """)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Scorecard Themes", 
        "📊 Criteria Prioritization", 
        "🔄 Enhanced Synthesis",
        "📈 Comparison View"
    ])
    
    with tab1:
        display_scorecard_themes(client_id)
    
    with tab2:
        display_criteria_prioritization(client_id)
    
    with tab3:
        display_enhanced_synthesis(client_id)
    
    with tab4:
        display_comparison_view(client_id)

if __name__ == "__main__":
    # This can be imported and used in the main app
    pass 