import streamlit as st
import pandas as pd
from supabase_database import SupabaseDatabase
import json

def load_themes(client_id='Rev'):
    """Load themes from database"""
    db = SupabaseDatabase()
    themes = db.get_themes(client_id)
    return themes

def save_theme_decision(theme_id, decision, notes=""):
    """Save theme decision to database"""
    db = SupabaseDatabase()
    # Update theme with decision
    db.supabase.table('stage4_themes').update({
        'quality_decision': decision,
        'quality_notes': notes,
        'reviewed_at': pd.Timestamp.now().isoformat()
    }).eq('id', theme_id).execute()

def main():
    st.title("🎯 Theme Quality Control Dashboard")
    st.markdown("Review and approve/reject themes for business intelligence")
    
    # Load themes
    themes = load_themes()
    
    if themes.empty:
        st.warning("No themes found for review")
        return
    
    # Filter by decision status
    decision_filter = st.sidebar.selectbox(
        "Filter by Decision",
        ["All", "Pending", "Approved", "Rejected", "Featured"]
    )
    
    # Display themes
    for idx, theme in themes.iterrows():
        with st.expander(f"Theme {idx+1}: {theme.get('theme_statement', 'No statement')[:100]}..."):
            
            # Theme details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Statement:** {theme.get('theme_statement', 'No statement')}")
                st.markdown(f"**Category:** {theme.get('theme_category', 'Unknown')}")
                st.markdown(f"**Strength:** {theme.get('theme_strength', 'Unknown')}")
                st.markdown(f"**Companies:** {len(theme.get('interview_companies', []))}")
                st.markdown(f"**Findings:** {theme.get('finding_count', 0)}")
                
                # Quality scores
                quality_scores = theme.get('quality_scores')
                if quality_scores:
                    try:
                        scores = json.loads(quality_scores)
                        st.markdown("**Quality Scores:**")
                        st.markdown(f"- Specificity: {scores.get('specificity', 0):.1f}")
                        st.markdown(f"- Actionability: {scores.get('actionability', 0):.1f}")
                        st.markdown(f"- Evidence: {scores.get('evidence_strength', 0):.1f}")
                        st.markdown(f"- Business Impact: {scores.get('business_impact', 0):.1f}")
                        st.markdown(f"- Overall: {scores.get('overall', 0):.1f}")
                    except:
                        st.markdown("Quality scores not available")
            
            with col2:
                # Decision buttons
                current_decision = theme.get('quality_decision', 'Pending')
                
                if current_decision == 'Pending':
                    col_a, col_r, col_f = st.columns(3)
                    
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{idx}"):
                            save_theme_decision(theme['id'], 'Approved')
                            st.success("Approved!")
                            st.rerun()
                    
                    with col_r:
                        if st.button("❌ Reject", key=f"reject_{idx}"):
                            save_theme_decision(theme['id'], 'Rejected')
                            st.error("Rejected!")
                            st.rerun()
                    
                    with col_f:
                        if st.button("⭐ Feature", key=f"feature_{idx}"):
                            save_theme_decision(theme['id'], 'Featured')
                            st.success("Featured!")
                            st.rerun()
                
                else:
                    st.markdown(f"**Decision:** {current_decision}")
                    if st.button("🔄 Reset", key=f"reset_{idx}"):
                        save_theme_decision(theme['id'], 'Pending')
                        st.info("Reset to pending")
                        st.rerun()
            
            # Notes
            notes = st.text_area(
                "Review Notes",
                value=theme.get('quality_notes', ''),
                key=f"notes_{idx}",
                help="Add notes about why you approved/rejected this theme"
            )
            
            if notes != theme.get('quality_notes', ''):
                if st.button("💾 Save Notes", key=f"save_notes_{idx}"):
                    save_theme_decision(theme['id'], current_decision, notes)
                    st.success("Notes saved!")
    
    # Summary
    st.markdown("---")
    st.markdown("## 📊 Review Summary")
    
    decisions = themes['quality_decision'].value_counts()
    st.markdown(f"**Pending:** {decisions.get('Pending', 0)}")
    st.markdown(f"**Approved:** {decisions.get('Approved', 0)}")
    st.markdown(f"**Rejected:** {decisions.get('Rejected', 0)}")
    st.markdown(f"**Featured:** {decisions.get('Featured', 0)}")

if __name__ == "__main__":
    main() 