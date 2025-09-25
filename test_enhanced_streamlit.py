#!/usr/bin/env python3
"""
Streamlit test interface for the enhanced processor with timestamp extraction
"""

import streamlit as st
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime

# Add the current directory to the path so we can import the processor
sys.path.append('.')

try:
    from voc_pipeline.processor import process_transcript
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    st.error(f"Could not import processor: {e}")
    PROCESSOR_AVAILABLE = False

st.set_page_config(
    page_title="Enhanced Stage 1 Processor Test",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Enhanced Stage 1 Processor with Timestamps")
st.markdown("Test the enhanced processor that automatically extracts timestamps from any transcript format.")

if not PROCESSOR_AVAILABLE:
    st.error("❌ Processor not available. Please check the import path.")
    st.stop()

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# Client selection
client_options = ["puzzle_client", "shipbob", "rev_client", "test_client"]
selected_client = st.sidebar.selectbox("Client ID", client_options, index=0)

# Company name
company_name = st.sidebar.text_input("Company Name", value="Test Company")

# Interviewee name  
interviewee_name = st.sidebar.text_input("Interviewee Name", value="Test Person")

# Deal status
deal_status_options = ["Won", "Lost", "In Progress", "No Decision"]
deal_status = st.sidebar.selectbox("Deal Status", deal_status_options, index=0)

# Interview date
interview_date = st.sidebar.date_input("Interview Date", value=datetime.now().date())

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload Transcript")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a transcript file",
        type=['txt', 'docx'],
        help="Upload any transcript format - timestamps will be automatically detected and extracted"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        
        # Show file preview
        if uploaded_file.name.endswith('.txt'):
            content = uploaded_file.read().decode('utf-8')
            st.text_area("File Preview (first 500 chars)", content[:500], height=200)
        else:
            st.info("📄 DOCX file uploaded - content will be processed")
    
    # Process button
    if st.button("🚀 Process Transcript", type="primary", disabled=uploaded_file is None):
        if uploaded_file is not None:
            with st.spinner("Processing transcript with timestamp extraction..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name
                    
                    # Process the transcript
                    result = process_transcript(
                        transcript_path=tmp_path,
                        client=selected_client,
                        company=company_name,
                        interviewee=interviewee_name,
                        deal_status=deal_status,
                        date_of_interview=interview_date.strftime('%Y-%m-%d')
                    )
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    if result:
                        st.success("✅ Processing completed!")
                        
                        # Parse CSV result
                        from io import StringIO
                        df = pd.read_csv(StringIO(result))
                        
                        # Store results in session state
                        st.session_state['processed_results'] = df
                        st.session_state['raw_csv'] = result
                        
                    else:
                        st.error("❌ No results extracted from transcript")
                        
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")
                    st.exception(e)

with col2:
    st.header("📊 Results")
    
    if 'processed_results' in st.session_state:
        df = st.session_state['processed_results']
        
        # Summary stats
        col2a, col2b, col2c = st.columns(3)
        with col2a:
            st.metric("Total Responses", len(df))
        with col2b:
            timestamp_coverage = (df['start_timestamp'].notna().sum() / len(df) * 100) if len(df) > 0 else 0
            st.metric("Timestamp Coverage", f"{timestamp_coverage:.1f}%")
        with col2c:
            unique_subjects = df['subject'].nunique() if 'subject' in df.columns else 0
            st.metric("Unique Subjects", unique_subjects)
        
        # Show timestamp info
        if 'start_timestamp' in df.columns and 'end_timestamp' in df.columns:
            st.subheader("🎬 Timestamp Information")
            
            # Show responses with timestamps
            timestamped_responses = df[df['start_timestamp'].notna()].copy()
            
            if len(timestamped_responses) > 0:
                st.success(f"✅ {len(timestamped_responses)} responses have timestamps")
                
                # Show sample with timestamps
                sample_cols = ['response_id', 'start_timestamp', 'end_timestamp', 'subject', 'verbatim_response']
                available_cols = [col for col in sample_cols if col in timestamped_responses.columns]
                
                st.dataframe(
                    timestamped_responses[available_cols].head(10),
                    use_container_width=True,
                    height=300
                )
            else:
                st.warning("⚠️ No timestamps found in responses")
        
        # Show all results
        st.subheader("📋 All Extracted Responses")
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download options
        st.subheader("💾 Download Results")
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            st.download_button(
                label="📄 Download CSV",
                data=st.session_state['raw_csv'],
                file_name=f"enhanced_stage1_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col_dl2:
            # Convert to Excel for better formatting
            excel_buffer = StringIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"enhanced_stage1_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.info("👆 Upload a transcript and click 'Process Transcript' to see results")

# Footer
st.markdown("---")
st.markdown("**🎬 Enhanced Stage 1 Processor** - Automatically extracts timestamps from any transcript format")
st.markdown("**Supported formats:** `[HH:MM:SS]`, `Speaker (MM:SS):`, `(HH:MM:SS - HH:MM:SS)`, and more!")
