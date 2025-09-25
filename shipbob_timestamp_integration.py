"""
ShipBob Timestamp Integration for Main App
Add this to your main app.py to include timestamp processing.
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_parser import EnhancedTimestampParser
from enhanced_database_save import create_timestamp_enhanced_response_data, format_timestamp_for_database
from supabase_database import SupabaseDatabase

def show_shipbob_timestamp_processing():
    """Add this function to your main app.py"""
    
    st.title("🎬 ShipBob Timestamp Processing")
    st.markdown("**Process ShipBob interviews with timestamp extraction**")
    st.markdown("---")
    
    # Get client ID
    client_id = st.session_state.get('client_id', 'shipbob')
    
    # Upload CSV
    uploaded_file = st.file_uploader(
        "Upload ShipBob CSV with transcripts",
        type=['csv'],
        help="CSV should contain 'Raw Transcript' column"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded {len(df)} interviews")
            
            if 'Raw Transcript' not in df.columns:
                st.error("❌ CSV must contain 'Raw Transcript' column")
                return
            
            # Show preview
            st.dataframe(df[['Interview ID', 'Interview Contact Company Name', 'Interview Contact Full Name', 'Deal Status']].head())
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                max_interviews = st.number_input(
                    "Max interviews to process",
                    min_value=1,
                    max_value=len(df),
                    value=min(5, len(df))
                )
            
            with col2:
                dry_run = st.checkbox("Dry run (no database save)", value=False)
            
            if st.button("🔄 Process with Timestamps", type="primary"):
                process_shipbob_with_timestamps(df, client_id, max_interviews, dry_run)
                
        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")

def process_shipbob_with_timestamps(df, client_id, max_interviews, dry_run):
    """Process ShipBob data with timestamps"""
    
    # Initialize parser
    parser = EnhancedTimestampParser()
    
    # Initialize database
    db = None
    if not dry_run:
        try:
            db = SupabaseDatabase()
            st.success("✅ Database connected")
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            return
    
    # Process interviews
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_responses = 0
    total_with_timestamps = 0
    
    df_to_process = df.head(max_interviews)
    
    for index, row in df_to_process.iterrows():
        progress = (index + 1) / len(df_to_process)
        progress_bar.progress(progress)
        status_text.text(f"Processing interview {index + 1}/{len(df_to_process)}")
        
        # Process transcript
        transcript = row.get('Raw Transcript', '')
        if not transcript or pd.isna(transcript):
            continue
        
        # Extract metadata
        company = row.get('Interview Contact Company Name', f'Company_{index + 1}')
        interviewee = row.get('Interview Contact Full Name', f'Interviewee_{index + 1}')
        deal_status = row.get('Deal Status', 'closed_won')
        interview_date = row.get('Completion Date', datetime.now().strftime('%Y-%m-%d'))
        interview_id = row.get('Interview ID', f'IVW-{index + 1:05d}')
        
        # Process with timestamps
        responses = process_shipbob_transcript_with_timestamps(
            transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser
        )
        
        if responses:
            total_responses += len(responses)
            timestamped_responses = [r for r in responses if r.get('start_timestamp') or r.get('end_timestamp')]
            total_with_timestamps += len(timestamped_responses)
            
            # Save to database
            if not dry_run and db:
                for response in responses:
                    try:
                        db.save_core_response(response)
                    except Exception as e:
                        st.error(f"Error saving response: {e}")
    
    # Show results
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Responses", total_responses)
    
    with col2:
        st.metric("With Timestamps", total_with_timestamps)
    
    with col3:
        if total_responses > 0:
            timestamp_percentage = (total_with_timestamps / total_responses) * 100
            st.metric("Coverage", f"{timestamp_percentage:.1f}%")
    
    if not dry_run:
        st.success("✅ All responses saved to database with timestamps")

def process_shipbob_transcript_with_timestamps(transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser):
    """Process a ShipBob transcript and extract responses with timestamps"""
    
    try:
        segments = parser.parse_transcript_segments(transcript)
        if not segments:
            return []
        
        qa_pairs = parser.find_qa_segments(segments)
        
        responses = []
        for i, (question_seg, answer_seg) in enumerate(qa_pairs):
            response_id = f"{client_id}_{interview_id}_{i+1}"
            
            response = {
                "response_id": response_id,
                "verbatim_response": answer_seg.text,
                "subject": "Interview Response",
                "question": question_seg.text,
                "deal_status": deal_status,
                "company": company,
                "interviewee_name": interviewee,
                "interview_date": interview_date,
                "client_id": client_id,
                "interview_id": interview_id,
                "start_timestamp": format_timestamp_for_database(answer_seg.start_timestamp),
                "end_timestamp": format_timestamp_for_database(answer_seg.end_timestamp)
            }
            
            responses.append(response)
        
        return responses
        
    except Exception as e:
        st.error(f"Error processing transcript: {e}")
        return []

if __name__ == "__main__":
    show_shipbob_timestamp_processing()
