"""
Simple Streamlit Test App for Timestamp Integration
Run this to test timestamp functionality with your CSV data.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_processor import process_chunk_with_timestamps
from enhanced_database_save import create_timestamp_enhanced_response_data, format_timestamp_for_database
from timestamp_parser import TimestampParser
from supabase_database import SupabaseDatabase

def main():
    st.set_page_config(
        page_title="Timestamp Integration Test",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Timestamp Integration Test")
    st.markdown("**Test timestamp extraction and database integration**")
    st.markdown("---")
    
    # Sidebar for client ID
    with st.sidebar:
        st.header("🏢 Client Settings")
        client_id = st.text_input("Client ID", value="test_client", help="Enter a unique client identifier")
        
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("1. Upload your CSV file with 'Raw Transcript' column")
        st.markdown("2. Configure processing options")
        st.markdown("3. Process transcripts to extract timestamps")
        st.markdown("4. View results and save to database")
    
    # Main content
    st.markdown("### 📁 Step 1: Upload CSV with Transcripts")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file with 'Raw Transcript' column",
        type=['csv'],
        help="The CSV should contain a 'Raw Transcript' column with interview transcripts"
    )
    
    if uploaded_file is not None:
        try:
            # Load the CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded CSV with {len(df)} rows")
            
            # Check for required columns
            if 'Raw Transcript' not in df.columns:
                st.error("❌ CSV must contain 'Raw Transcript' column")
                st.info("Available columns:")
                st.write(df.columns.tolist())
                return
            
            # Show preview
            st.markdown("#### 📋 Data Preview")
            st.dataframe(df.head())
            
            # Store in session state
            st.session_state.df_uploaded = df
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")
            return
    
    # Step 2: Process transcripts
    if 'df_uploaded' in st.session_state:
        st.markdown("### 🚀 Step 2: Process Transcripts with Timestamps")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_interviews = st.number_input(
                "Max interviews to process",
                min_value=1,
                max_value=len(st.session_state.df_uploaded),
                value=min(2, len(st.session_state.df_uploaded)),
                help="Limit processing for testing"
            )
        
        with col2:
            dry_run = st.checkbox("Dry run (no database save)", value=True)
        
        if st.button("🔄 Process Transcripts", type="primary"):
            process_transcripts(
                st.session_state.df_uploaded,
                client_id,
                max_interviews,
                dry_run
            )

def process_transcripts(df, client_id, max_interviews, dry_run):
    """Process transcripts with timestamp extraction"""
    
    st.markdown("#### 🔄 Processing Status")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize database
    db = None
    if not dry_run:
        try:
            db = SupabaseDatabase()
            st.success("✅ Database connected")
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            st.info("Continuing with dry run...")
            dry_run = True
    
    # Process interviews
    processed_count = 0
    total_responses = 0
    total_with_timestamps = 0
    all_responses = []
    
    # Limit to max_interviews
    df_to_process = df.head(max_interviews)
    
    for index, row in df_to_process.iterrows():
        try:
            # Update progress
            progress = (index + 1) / len(df_to_process)
            progress_bar.progress(progress)
            status_text.text(f"Processing interview {index + 1}/{len(df_to_process)}")
            
            # Get transcript
            transcript = row.get('Raw Transcript', '')
            if not transcript or pd.isna(transcript):
                st.warning(f"⚠️ Skipping row {index + 1}: No transcript data")
                continue
            
            # Extract metadata
            company = row.get('Company', f'Company_{index + 1}')
            interviewee = row.get('Interviewee', f'Interviewee_{index + 1}')
            deal_status = row.get('Deal Status', 'closed_won')
            interview_date = row.get('Interview Date', datetime.now().strftime('%Y-%m-%d'))
            
            # Process transcript with timestamps
            responses = process_single_transcript_with_timestamps(
                transcript, company, interviewee, deal_status, interview_date, client_id
            )
            
            if responses:
                processed_count += 1
                total_responses += len(responses)
                all_responses.extend(responses)
                
                # Count responses with timestamps
                timestamped_responses = [r for r in responses if r.get('start_timestamp') or r.get('end_timestamp')]
                total_with_timestamps += len(timestamped_responses)
                
                # Save to database if not dry run
                if not dry_run and db:
                    save_responses_to_database(db, responses)
                
                # Show sample response
                if len(responses) > 0:
                    with st.expander(f"📝 Sample Response from {company}"):
                        sample = responses[0]
                        st.json({
                            "response_id": sample.get('response_id'),
                            "subject": sample.get('subject'),
                            "question": sample.get('question'),
                            "start_timestamp": sample.get('start_timestamp'),
                            "end_timestamp": sample.get('end_timestamp'),
                            "verbatim_response": sample.get('verbatim_response')[:100] + "..."
                        })
            
        except Exception as e:
            st.error(f"❌ Error processing row {index + 1}: {e}")
            continue
    
    # Final results
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    st.markdown("#### 📊 Processing Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Interviews Processed", processed_count)
    
    with col2:
        st.metric("Total Responses", total_responses)
    
    with col3:
        st.metric("Responses with Timestamps", total_with_timestamps)
    
    if total_responses > 0:
        timestamp_percentage = (total_with_timestamps / total_responses) * 100
        st.metric("Timestamp Coverage", f"{timestamp_percentage:.1f}%")
    
    # Show detailed results
    if all_responses:
        st.markdown("#### 🎬 All Responses with Timestamps")
        
        # Create a dataframe for display
        display_data = []
        for response in all_responses:
            display_data.append({
                "Response ID": response.get('response_id'),
                "Company": response.get('company'),
                "Subject": response.get('subject'),
                "Start Time": response.get('start_timestamp', 'N/A'),
                "End Time": response.get('end_timestamp', 'N/A'),
                "Question": response.get('question', '')[:50] + "..." if len(response.get('question', '')) > 50 else response.get('question', ''),
                "Response": response.get('verbatim_response', '')[:100] + "..." if len(response.get('verbatim_response', '')) > 100 else response.get('verbatim_response', '')
            })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)
        
        # Show database status
        if not dry_run and db:
            st.success("✅ All responses saved to database with timestamps")
            st.info("💡 You can now view the quotes with timestamps in your main application")
        else:
            st.info("🔍 Dry run completed - no data saved to database")
            st.info("💡 Uncheck 'Dry run' to save data to database")

def process_single_transcript_with_timestamps(transcript, company, interviewee, deal_status, interview_date, client_id):
    """Process a single transcript and extract responses with timestamps"""
    
    try:
        # Parse transcript into segments
        parser = TimestampParser()
        segments = parser.parse_transcript_segments(transcript)
        
        if not segments:
            return []
        
        # Find Q&A pairs
        qa_pairs = parser.find_qa_segments(segments)
        
        # Create responses from Q&A pairs
        responses = []
        for i, (question_seg, answer_seg) in enumerate(qa_pairs):
            response_id = f"{client_id}_{company.lower().replace(' ', '_')}_{interviewee.lower().replace(' ', '_')}_{i+1}"
            
            response = {
                "response_id": response_id,
                "verbatim_response": answer_seg.text,
                "subject": "Interview Response",  # Could be enhanced with LLM classification
                "question": question_seg.text,
                "deal_status": deal_status,
                "company": company,
                "interviewee_name": interviewee,
                "interview_date": interview_date,
                "client_id": client_id,
                "start_timestamp": answer_seg.start_timestamp,
                "end_timestamp": answer_seg.end_timestamp
            }
            
            # Format timestamps for database
            response['start_timestamp'] = format_timestamp_for_database(response['start_timestamp'])
            response['end_timestamp'] = format_timestamp_for_database(response['end_timestamp'])
            
            responses.append(response)
        
        return responses
        
    except Exception as e:
        st.error(f"Error processing transcript: {e}")
        return []

def save_responses_to_database(db, responses):
    """Save responses to database"""
    for response in responses:
        try:
            db.save_core_response(response)
        except Exception as e:
            st.error(f"Error saving response {response.get('response_id')}: {e}")

if __name__ == "__main__":
    main()
