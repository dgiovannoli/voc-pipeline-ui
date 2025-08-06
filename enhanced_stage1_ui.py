import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from supabase_database import SupabaseDatabase
from metadata_stage1_processor import MetadataStage1Processor

# Constants
SUPABASE_AVAILABLE = True
db = None

def get_database():
    """Get database connection with lazy loading"""
    global db
    if db is None:
        try:
            db = SupabaseDatabase()
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            return None
    return db

def get_client_id():
    """Get client ID from session state or sidebar"""
    if 'client_id' in st.session_state and st.session_state.client_id:
        return st.session_state.client_id
    
    st.warning("⚠️ **Client ID Required**")
    st.info("Please set a Client ID in the sidebar before proceeding.")
    st.stop()
    return None

def show_harmonized_subjects_view():
    """Enhanced view showing both original and harmonized subjects"""
    st.title("🎯 Stage 1: Enhanced Subject Analysis")
    st.markdown("View original customer language **and** LLM-harmonized business categories for cross-interview analysis.")
    
    client_id = get_client_id()
    
    if SUPABASE_AVAILABLE:
        try:
            db = get_database()
            if db is None:
                st.error("❌ Database not available")
                return
            
            # Get all Stage 1 data
            df = db.get_stage1_data_responses(client_id=client_id)
            if df.empty:
                st.info(f"📭 No Stage 1 data found for client: **{client_id}**")
                st.info("Process interviews in the main Stage 1 tab first.")
                return
            
            # Check if harmonization has been run
            harmonized_count = df[df['harmonized_subject'].notna()].shape[0] if 'harmonized_subject' in df.columns else 0
            total_count = len(df)
            
            # Status metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Responses", total_count)
            with col2:
                st.metric("Harmonized", harmonized_count)
            with col3:
                coverage = (harmonized_count / total_count * 100) if total_count > 0 else 0
                st.metric("Coverage", f"{coverage:.1f}%")
            with col4:
                unique_subjects = df['subject'].nunique() if 'subject' in df.columns else 0
                st.metric("Unique Subjects", unique_subjects)
            
            # Harmonization status and action
            if harmonized_count == 0:
                st.warning("⚠️ **Harmonization Not Run Yet**")
                st.info("🎯 **Run LLM harmonization** to see intelligent subject mapping for cross-interview analysis.")
                
                if st.button("🚀 Run LLM Harmonization", type="primary"):
                    with st.spinner("Running LLM harmonization on all responses..."):
                        try:
                            from integrate_llm_harmonization import LLMHarmonizationIntegrator
                            integrator = LLMHarmonizationIntegrator(batch_size=20, max_workers=3)
                            result = integrator.harmonize_existing_data(client_id=client_id)
                            
                            if result and result.get('successful_harmonizations', 0) > 0:
                                st.success(f"✅ Harmonized {result['successful_harmonizations']} responses!")
                                st.info(f"📊 Average confidence: {result.get('average_confidence', 0):.3f}")
                                if result.get('new_categories_suggested'):
                                    st.info(f"💡 New categories suggested: {', '.join(result['new_categories_suggested'])}")
                                st.rerun()
                            else:
                                st.error("❌ Harmonization completed but no successful mappings")
                        except Exception as e:
                            st.error(f"❌ Harmonization failed: {e}")
            
            elif harmonized_count < total_count:
                st.warning(f"⚠️ **Partial Harmonization**: {harmonized_count}/{total_count} responses harmonized")
                if st.button("🔄 Complete Harmonization", type="secondary"):
                    with st.spinner("Completing harmonization..."):
                        try:
                            from integrate_llm_harmonization import LLMHarmonizationIntegrator
                            integrator = LLMHarmonizationIntegrator(batch_size=20, max_workers=3)
                            result = integrator.harmonize_existing_data(client_id=client_id)
                            st.success("✅ Harmonization completed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            else:
                st.success("✅ **Full Harmonization Complete!**")
                
                # Show harmonization analytics
                if st.button("📊 View Harmonization Analytics"):
                    try:
                        from integrate_llm_harmonization import LLMHarmonizationIntegrator
                        integrator = LLMHarmonizationIntegrator()
                        analytics = integrator.get_harmonization_analytics(client_id=client_id)
                        
                        if 'error' not in analytics:
                            st.subheader("📈 Harmonization Quality Metrics")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Average Confidence", f"{analytics.get('average_confidence', 0):.3f}")
                            with col2:
                                st.metric("Categories Used", analytics.get('unique_categories_used', 0))
                            with col3:
                                high_conf = analytics.get('confidence_distribution', {}).get('high (≥0.7)', 0)
                                st.metric("High Confidence", f"{high_conf}")
                            
                            # Category distribution
                            st.subheader("🎯 Category Distribution")
                            category_dist = analytics.get('category_distribution', {})
                            if category_dist:
                                cat_df = pd.DataFrame(list(category_dist.items()), columns=['Category', 'Count'])
                                cat_df['Percentage'] = (cat_df['Count'] / cat_df['Count'].sum() * 100).round(1)
                                st.dataframe(cat_df, use_container_width=True)
                                
                            # New categories
                            new_cats = analytics.get('new_categories_suggested', [])
                            if new_cats:
                                st.subheader("💡 New Categories Suggested")
                                for cat in new_cats:
                                    st.info(f"• {cat}")
                    except Exception as e:
                        st.error(f"❌ Analytics error: {e}")
            
            # Enhanced data view with harmonized subjects
            st.subheader("📋 Enhanced Subject Analysis")
            
            # Filter and display options
            col1, col2 = st.columns(2)
            with col1:
                show_mode = st.selectbox(
                    "View Mode",
                    ["All Responses", "Harmonized Only", "Not Harmonized", "High Confidence", "Needs Review"],
                    help="Filter responses by harmonization status"
                )
            with col2:
                display_limit = st.selectbox("Display Limit", [20, 50, 100, "All"], index=0)
            
            # Apply filters
            filtered_df = df.copy()
            
            if 'harmonized_subject' in df.columns:
                if show_mode == "Harmonized Only":
                    filtered_df = df[df['harmonized_subject'].notna()]
                elif show_mode == "Not Harmonized":
                    filtered_df = df[df['harmonized_subject'].isna()]
                elif show_mode == "High Confidence":
                    filtered_df = df[(df['harmonized_subject'].notna()) & (df['harmonization_confidence'] >= 0.7)]
                elif show_mode == "Needs Review":
                    filtered_df = df[(df['harmonized_subject'].notna()) & (df['harmonization_confidence'] < 0.5)]
            
            # Limit display
            if display_limit != "All":
                filtered_df = filtered_df.head(display_limit)
            
            if filtered_df.empty:
                st.info("No responses match the selected filters.")
                return
            
            # Prepare display columns
            display_cols = ['response_id', 'subject', 'verbatim_response']
            
            # Add harmonization columns if available
            if 'harmonized_subject' in filtered_df.columns:
                display_cols.extend(['harmonized_subject', 'harmonization_confidence', 'harmonization_method'])
            
            # Add company and interview info
            if 'company' in filtered_df.columns:
                display_cols.append('company')
            if 'interview_id' in filtered_df.columns:
                display_cols.append('interview_id')
            
            # Filter to available columns
            display_cols = [col for col in display_cols if col in filtered_df.columns]
            display_df = filtered_df[display_cols].copy()
            
            # Enhance display
            if 'harmonization_confidence' in display_df.columns:
                # Round confidence scores
                display_df['harmonization_confidence'] = display_df['harmonization_confidence'].round(3)
                
                # Add confidence icons
                def add_confidence_icon(row):
                    if pd.isna(row.get('harmonization_confidence')):
                        return "❓"
                    conf = row['harmonization_confidence']
                    if conf >= 0.7:
                        return "🎯"
                    elif conf >= 0.4:
                        return "⚠️"
                    else:
                        return "❌"
                
                display_df['Confidence'] = display_df.apply(add_confidence_icon, axis=1)
                
                # Reorder columns to put confidence icon first
                cols = display_df.columns.tolist()
                cols = ['Confidence'] + [col for col in cols if col != 'Confidence']
                display_df = display_df[cols]
            
            # Truncate long responses for better display
            if 'verbatim_response' in display_df.columns:
                display_df['verbatim_response'] = display_df['verbatim_response'].str[:200] + '...'
            
            # Display the enhanced dataframe
            st.dataframe(display_df, use_container_width=True, height=600)
            
            # Download options
            st.subheader("📥 Download Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download filtered data
                csv_filtered = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download Filtered Data",
                    data=csv_filtered,
                    file_name=f"stage1_filtered_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download all harmonized data
                if 'harmonized_subject' in df.columns:
                    harmonized_df = df[df['harmonized_subject'].notna()]
                    if not harmonized_df.empty:
                        csv_harmonized = harmonized_df.to_csv(index=False)
                        st.download_button(
                            label="🎯 Download Harmonized Data",
                            data=csv_harmonized,
                            file_name=f"stage1_harmonized_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
            
            with col3:
                # Download summary report
                if 'harmonized_subject' in df.columns:
                    summary_data = create_harmonization_summary(df)
                    st.download_button(
                        label="📊 Download Summary Report",
                        data=summary_data,
                        file_name=f"harmonization_summary_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            import traceback
            st.text(traceback.format_exc())

def create_harmonization_summary(df):
    """Create a summary report of harmonization results"""
    if 'harmonized_subject' not in df.columns:
        return "No harmonization data available"
    
    # Summary statistics
    total = len(df)
    harmonized = df['harmonized_subject'].notna().sum()
    
    # Category distribution
    category_counts = df['harmonized_subject'].value_counts()
    
    # Confidence distribution
    confidence_stats = df['harmonization_confidence'].describe() if 'harmonization_confidence' in df.columns else None
    
    # Create summary dataframe
    summary_rows = []
    summary_rows.append(['Metric', 'Value'])
    summary_rows.append(['Total Responses', total])
    summary_rows.append(['Harmonized Responses', harmonized])
    summary_rows.append(['Coverage Percentage', f"{(harmonized/total*100):.1f}%"])
    
    if confidence_stats is not None:
        summary_rows.append(['Average Confidence', f"{confidence_stats['mean']:.3f}"])
        summary_rows.append(['Min Confidence', f"{confidence_stats['min']:.3f}"])
        summary_rows.append(['Max Confidence', f"{confidence_stats['max']:.3f}"])
    
    summary_rows.append(['', ''])
    summary_rows.append(['Category', 'Count'])
    
    for category, count in category_counts.items():
        if pd.notna(category):
            summary_rows.append([category, count])
    
    # Convert to CSV
    summary_df = pd.DataFrame(summary_rows)
    return summary_df.to_csv(index=False, header=False)

if __name__ == "__main__":
    show_harmonized_subjects_view() 