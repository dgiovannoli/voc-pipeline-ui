"""
Streamlit Test App for ShipBob CSV with Enhanced Timestamp Parser
Specifically designed for your ShipBob CSV format.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_timestamp_parser import EnhancedTimestampParser
from enhanced_database_save import create_timestamp_enhanced_response_data, format_timestamp_for_database
from supabase_database import SupabaseDatabase

def main():
    st.set_page_config(
        page_title="ShipBob Timestamp Test",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 ShipBob Timestamp Integration Test")
    st.markdown("**Test timestamp extraction with your ShipBob CSV data**")
    st.markdown("---")
    
    # Sidebar for client ID
    with st.sidebar:
        st.header("🏢 Client Settings")
        client_id = st.text_input("Client ID", value="shipbob", help="Enter your client identifier")
        
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("1. Upload your ShipBob CSV file")
        st.markdown("2. Configure processing options")
        st.markdown("3. Process transcripts to extract timestamps")
        st.markdown("4. View results and save to database")
        
        st.markdown("---")
        st.markdown("### ✅ Expected Results")
        st.markdown("- **100% timestamp coverage**")
        st.markdown("- **25+ responses per interview**")
        st.markdown("- **Precise timing** for each quote")
        st.markdown("- **Video-ready segments**")
    
    # Main content
    st.markdown("### 📁 Step 1: Upload ShipBob CSV")
    
    uploaded_file = st.file_uploader(
        "Choose your ShipBob CSV file",
        type=['csv'],
        help="Upload the CSV file with 'Raw Transcript' column containing interview transcripts"
    )
    
    if uploaded_file is not None:
        try:
            # Load the CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded CSV with {len(df)} interviews")
            
            # Check for required columns
            if 'Raw Transcript' not in df.columns:
                st.error("❌ CSV must contain 'Raw Transcript' column")
                st.info("Available columns:")
                st.write(df.columns.tolist())
                return
            
            # Show preview
            st.markdown("#### 📋 Data Preview")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Interviews", len(df))
                st.metric("Columns", len(df.columns))
            
            with col2:
                # Check for key columns
                key_columns = ['Interview Contact Company Name', 'Interview Contact Full Name', 'Deal Status']
                available_key_columns = [col for col in key_columns if col in df.columns]
                st.metric("Key Columns Available", len(available_key_columns))
            
            # Show sample data
            st.dataframe(df[['Interview ID', 'Interview Contact Company Name', 'Interview Contact Full Name', 'Deal Status']].head())
            
            # Store in session state
            st.session_state.df_uploaded = df
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")
            return
    
    # Step 2: Process transcripts
    if 'df_uploaded' in st.session_state:
        st.markdown("### 🚀 Step 2: Process Transcripts with Timestamps")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_interviews = st.number_input(
                "Max interviews to process",
                min_value=1,
                max_value=len(st.session_state.df_uploaded),
                value=min(3, len(st.session_state.df_uploaded)),
                help="Start with 2-3 interviews for testing"
            )
        
        with col2:
            dry_run = st.checkbox("Dry run (no database save)", value=True)
        
        with col3:
            show_details = st.checkbox("Show detailed results", value=True)
        
        if st.button("🔄 Process ShipBob Transcripts", type="primary"):
            process_shipbob_transcripts(
                st.session_state.df_uploaded,
                client_id,
                max_interviews,
                dry_run,
                show_details
            )

def process_shipbob_transcripts(df, client_id, max_interviews, dry_run, show_details):
    """Process ShipBob transcripts with enhanced timestamp extraction"""
    
    st.markdown("#### 🔄 Processing Status")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize enhanced parser
    parser = EnhancedTimestampParser()
    st.success("✅ Enhanced timestamp parser initialized for ShipBob format")
    
    # Initialize database if needed
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
            
            # Extract metadata from ShipBob CSV
            company = row.get('Interview Contact Company Name', f'Company_{index + 1}')
            interviewee = row.get('Interview Contact Full Name', f'Interviewee_{index + 1}')
            deal_status = row.get('Deal Status', 'closed_won')
            interview_date = row.get('Completion Date', datetime.now().strftime('%Y-%m-%d'))
            interview_id = row.get('Interview ID', f'IVW-{index + 1:05d}')
            
            # Process transcript with enhanced parser
            responses = process_shipbob_transcript_with_timestamps(
                transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser
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
                if show_details and len(responses) > 0:
                    with st.expander(f"📝 Sample Response from {company} (Interview {interview_id})"):
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Interviews Processed", processed_count)
    
    with col2:
        st.metric("Total Responses", total_responses)
    
    with col3:
        st.metric("Responses with Timestamps", total_with_timestamps)
    
    with col4:
        if total_responses > 0:
            timestamp_percentage = (total_with_timestamps / total_responses) * 100
            st.metric("Timestamp Coverage", f"{timestamp_percentage:.1f}%")
    
    # Show detailed results
    if all_responses and show_details:
        st.markdown("#### 🎬 All Responses with Timestamps")
        
        # Create a dataframe for display
        display_data = []
        for response in all_responses:
            display_data.append({
                "Response ID": response.get('response_id'),
                "Company": response.get('company'),
                "Interview ID": response.get('interview_id'),
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
    
    # Show summary statistics
    if all_responses:
        st.markdown("#### 📈 Summary Statistics")
        
        # Calculate average response duration
        durations = []
        for response in all_responses:
            if response.get('start_timestamp') and response.get('end_timestamp'):
                duration = calculate_duration(response['start_timestamp'], response['end_timestamp'])
                if duration > 0:
                    durations.append(duration)
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            st.metric("Average Response Duration", f"{avg_duration:.1f} seconds")
        
        # Show response count by company
        company_counts = {}
        for response in all_responses:
            company = response.get('company', 'Unknown')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        st.markdown("**Responses by Company:**")
        for company, count in company_counts.items():
            st.write(f"- {company}: {count} responses")

def process_shipbob_transcript_with_timestamps(transcript, company, interviewee, deal_status, interview_date, client_id, interview_id, parser):
    """Process a ShipBob transcript and extract responses with timestamps"""
    
    try:
        # Parse transcript into segments
        segments = parser.parse_transcript_segments(transcript)
        
        if not segments:
            return []
        
        # Find Q&A pairs
        qa_pairs = parser.find_qa_segments(segments)
        
        # Create responses from Q&A pairs
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

def calculate_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in seconds between two timestamps"""
    def time_to_seconds(time_str: str) -> int:
        if not time_str:
            return 0
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0
    
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    return max(0, end_seconds - start_seconds)

if __name__ == "__main__":
    main()
