#!/usr/bin/env python3
"""
Theme Merge Workflow UI
Streamlit interface for analysts to review and approve theme merge suggestions
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).resolve().parents[1]))
from supabase_database import SupabaseDatabase
from enhanced_theme_deduplication import EnhancedThemeDeduplicator, MergeSuggestion

def main():
    st.set_page_config(
        page_title="Theme Merge Workflow",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Theme Merge Workflow")
    st.markdown("Review and approve theme merge suggestions to consolidate duplicates")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    client_id = st.sidebar.text_input("Client ID", value="ShipStation API")
    min_cosine = st.sidebar.slider("Minimum Cosine Threshold", 0.65, 0.90, 0.75, 0.01)
    
    if st.sidebar.button("🔄 Generate Merge Suggestions"):
        with st.spinner("Generating merge suggestions..."):
            generate_merge_suggestions(client_id, min_cosine)
    
    # Main content
    if 'merge_suggestions' in st.session_state:
        display_merge_workflow()
    else:
        st.info("Click 'Generate Merge Suggestions' to start the workflow")
        
    # Export decisions if available
    if 'merge_decisions' in st.session_state and st.session_state.merge_decisions:
        export_decisions()

def generate_merge_suggestions(client_id: str, min_cosine: float):
    """Generate merge suggestions and store in session state"""
    try:
        db = SupabaseDatabase()
        deduplicator = EnhancedThemeDeduplicator(db, client_id)
        
        suggestions = deduplicator.build_merge_suggestions(min_cosine=min_cosine)
        
        if not suggestions:
            st.warning("No merge suggestions found. Try lowering the cosine threshold.")
            return
        
        # Store in session state
        st.session_state.merge_suggestions = suggestions
        st.session_state.client_id = client_id
        
        st.success(f"Generated {len(suggestions)} merge suggestions!")
        
    except Exception as e:
        st.error(f"Error generating suggestions: {str(e)}")

def display_merge_workflow():
    """Display the main merge workflow interface"""
    suggestions = st.session_state.merge_suggestions
    client_id = st.session_state.client_id
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    high_conf = [s for s in suggestions if s.confidence_level == 'high']
    medium_conf = [s for s in suggestions if s.confidence_level == 'medium']
    low_conf = [s for s in suggestions if s.confidence_level == 'low']
    
    with col1:
        st.metric("Total Suggestions", len(suggestions))
    with col2:
        st.metric("High Confidence", len(high_conf), delta=f"{len(high_conf)/len(suggestions)*100:.1f}%")
    with col3:
        st.metric("Medium Confidence", len(medium_conf), delta=f"{len(medium_conf)/len(suggestions)*100:.1f}%")
    with col4:
        st.metric("Low Confidence", len(low_conf), delta=f"{len(low_conf)/len(suggestions)*100:.1f}%")
    
    # Filter options
    st.subheader("📊 Filter & Review")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confidence_filter = st.selectbox(
            "Confidence Level",
            ["High", "Medium", "Low", "All"],  # Default to High first
            index=0
        )
    
    with col2:
        facet_filter = st.selectbox(
            "Primary Facet",
            ["All"] + list(set(s.primary_facet for s in suggestions)),
            index=0
        )
    
    with col3:
        subject_filter = st.selectbox(
            "Subject",
            ["All"] + list(set(s.subject for s in suggestions)),
            index=0
        )
    
    # Apply filters
    filtered_suggestions = suggestions
    if confidence_filter != "All":
        filtered_suggestions = [s for s in filtered_suggestions if s.confidence_level == confidence_filter]
    if facet_filter != "All":
        filtered_suggestions = [s for s in filtered_suggestions if s.primary_facet == facet_filter]
    if subject_filter != "All":
        filtered_suggestions = [s for s in filtered_suggestions if s.subject == subject_filter]
    
    st.write(f"Showing {len(filtered_suggestions)} of {len(suggestions)} suggestions")
    
    # Display suggestions
    for i, suggestion in enumerate(filtered_suggestions):
        display_merge_suggestion(i, suggestion, client_id)

def display_merge_suggestion(index: int, suggestion: MergeSuggestion, client_id: str):
    """Display a single merge suggestion with approval controls"""
    
    # Create expandable section
    with st.expander(
        f"**{suggestion.primary_facet}** - {suggestion.subject} "
        f"({suggestion.confidence_level.upper()} confidence)",
        expanded=suggestion.confidence_level == 'high'
    ):
        # Two-column layout for theme comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Theme A")
            st.write(f"**ID:** `{suggestion.theme_a_id[:8]}...`")
            st.write(f"**Statement:** {suggestion.theme_a_statement}")
        
        with col2:
            st.subheader("🎯 Theme B")
            st.write(f"**ID:** `{suggestion.theme_b_id[:8]}...`")
            st.write(f"**Statement:** {suggestion.theme_b_statement}")
        
        # Similarity scores
        st.subheader("📊 Similarity Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cosine Score", f"{suggestion.cosine_score:.3f}")
        with col2:
            st.metric("Noun Overlap", f"{suggestion.noun_overlap_score:.3f}")
        with col3:
            st.metric("Sentiment Align", f"{suggestion.sentiment_alignment:.3f}")
        with col4:
            st.metric("Domain Overlap", suggestion.domain_overlap)
        
        # Merge rationale
        st.write(f"**Merge Rationale:** {suggestion.merge_rationale}")
        
        # Suggested canonical theme
        st.subheader("💡 Suggested Canonical Theme")
        st.write(suggestion.suggested_canonical)
        
        # Analyst decision
        st.subheader("✅ Analyst Decision")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            decision = st.selectbox(
                "Decision",
                ["Pending", "Approve", "Deny", "Custom Canonical"],
                key=f"decision_{index}"
            )
        
        with col2:
            if decision == "Custom Canonical":
                custom_canonical = st.text_area(
                    "Custom Canonical Statement",
                    value=suggestion.suggested_canonical,
                    key=f"custom_{index}"
                )
            else:
                custom_canonical = None
        
        with col3:
            if decision in ["Approve", "Custom Canonical"]:
                if st.button("💾 Save Decision", key=f"save_{index}"):
                    save_merge_decision(suggestion, decision, custom_canonical, client_id)
                    st.success("Decision saved!")
        
        # Notes
        notes = st.text_area(
            "Analyst Notes",
            placeholder="Add any notes about this merge decision...",
            key=f"notes_{index}"
        )
        
        st.divider()

def save_merge_decision(suggestion: MergeSuggestion, decision: str, 
                       custom_canonical: Optional[str], client_id: str):
    """Save the analyst's merge decision to the database"""
    try:
        # This would integrate with the three-table schema
        # For now, just store in session state
        if 'merge_decisions' not in st.session_state:
            st.session_state.merge_decisions = []
        
        decision_record = {
            'theme_a_id': suggestion.theme_a_id,
            'theme_b_id': suggestion.theme_b_id,
            'decision': decision,
            'custom_canonical': custom_canonical,
            'confidence_level': suggestion.confidence_level,
            'composite_score': suggestion.composite_score,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        st.session_state.merge_decisions.append(decision_record)
        
        # TODO: Implement actual database save using the three-table schema
        # This would involve:
        # 1. Creating canonical themes in themes_canonical table
        # 2. Mapping raw themes to canonical themes in themes_mapping table
        # 3. Preserving original themes in themes_raw table
        
    except Exception as e:
        st.error(f"Error saving decision: {str(e)}")

def export_decisions():
    """Export merge decisions to CSV"""
    if 'merge_decisions' in st.session_state and st.session_state.merge_decisions:
        df = pd.DataFrame(st.session_state.merge_decisions)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Merge Decisions",
            data=csv,
            file_name=f"merge_decisions_{st.session_state.client_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Display summary
        st.subheader("📋 Merge Decisions Summary")
        st.dataframe(df)

if __name__ == "__main__":
    main() 