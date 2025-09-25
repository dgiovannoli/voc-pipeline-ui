"""
Universal Timestamp Processing UI
Future-proof Streamlit interface for any interview format.
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from universal_timestamp_processor import UniversalTimestampParser, process_universal_transcript_with_timestamps
from supabase_database import SupabaseDatabase

def main():
    st.set_page_config(
        page_title="Universal Timestamp Processor",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Universal Timestamp Processor")
    st.markdown("**Process any interview format with automatic timestamp detection**")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        client_id = st.text_input(
            "Client ID",
            value="default_client",
            help="Unique identifier for this client's data"
        )
        
        max_interviews = st.number_input(
            "Max interviews to process",
            min_value=1,
            max_value=1000,
            value=10,
            help="Limit processing to first N interviews"
        )
        
        dry_run = st.checkbox(
            "Dry run (no database save)",
            value=False,
            help="Process without saving to database"
        )
        
        st.markdown("---")
        st.markdown("### 📋 Supported Formats")
        st.markdown("""
        - **ShipBob**: `Speaker Name (00:00:38 - 00:00:39)`
        - **Rev**: `Speaker 1 (01:00:00):`
        - **Original**: `Speaker 1 (01:00):`
        - **Generic**: `Name (HH:MM:SS):`
        - **Inline**: `[00:01:00]` timestamps
        """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📁 Upload & Process", "🔍 Format Detection", "📊 Results"])
    
    with tab1:
        st.header("Upload Interview Data")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV with interview transcripts",
            type=['csv'],
            help="CSV should contain transcript data in any supported format"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} interviews")
                
                # Show available columns
                st.subheader("📋 Available Columns")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**All columns:**")
                    st.write(list(df.columns))
                
                with col2:
                    # Auto-detect transcript column
                    transcript_columns = ['Raw Transcript', 'Transcript', 'Full Transcript', 'Moderator Responses']
                    transcript_column = None
                    
                    for col in transcript_columns:
                        if col in df.columns:
                            transcript_column = col
                            break
                    
                    if transcript_column:
                        st.success(f"✅ Auto-detected transcript column: **{transcript_column}**")
                    else:
                        st.warning("⚠️ No standard transcript column found")
                        st.write("Available columns:", list(df.columns))
                
                # Show preview
                st.subheader("👀 Data Preview")
                preview_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in ['company', 'name', 'id', 'date', 'status'])]
                if preview_columns:
                    st.dataframe(df[preview_columns].head())
                else:
                    st.dataframe(df.head())
                
                # Process button
                if st.button("🔄 Process with Timestamps", type="primary", use_container_width=True):
                    process_interviews(df, client_id, max_interviews, dry_run, transcript_column)
                    
            except Exception as e:
                st.error(f"❌ Error loading CSV: {e}")
    
    with tab2:
        st.header("Format Detection")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Test format detection on first transcript
                transcript_columns = ['Raw Transcript', 'Transcript', 'Full Transcript', 'Moderator Responses']
                transcript_column = None
                
                for col in transcript_columns:
                    if col in df.columns:
                        transcript_column = col
                        break
                
                if transcript_column:
                    sample_transcript = df[transcript_column].iloc[0]
                    
                    if pd.notna(sample_transcript):
                        parser = UniversalTimestampParser()
                        detected_format = parser.detect_format(sample_transcript)
                        
                        st.success(f"✅ Detected format: **{detected_format}**")
                        
                        # Show sample parsing
                        segments = parser.parse_transcript_segments(sample_transcript)
                        
                        if segments:
                            st.subheader("📝 Parsed Segments (First 5)")
                            
                            for i, segment in enumerate(segments[:5]):
                                with st.expander(f"Segment {i+1} - {segment.speaker or 'Unknown'}"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Timestamps:**")
                                        st.write(f"Start: {segment.start_timestamp or 'N/A'}")
                                        st.write(f"End: {segment.end_timestamp or 'N/A'}")
                                    
                                    with col2:
                                        st.write("**Text Preview:**")
                                        st.write(segment.text[:200] + "..." if len(segment.text) > 200 else segment.text)
                        else:
                            st.warning("⚠️ No segments could be parsed from this transcript")
                    else:
                        st.warning("⚠️ No transcript data found in first row")
                else:
                    st.warning("⚠️ No transcript column found")
                    
            except Exception as e:
                st.error(f"❌ Error in format detection: {e}")
    
    with tab3:
        st.header("Processing Results")
        
        if 'processing_results' in st.session_state:
            results = st.session_state.processing_results
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Interviews", results.get('total_interviews', 0))
            
            with col2:
                st.metric("Processed", results.get('processed_interviews', 0))
            
            with col3:
                st.metric("Total Responses", results.get('total_responses', 0))
            
            with col4:
                st.metric("With Timestamps", results.get('total_with_timestamps', 0))
            
            # Timestamp coverage
            if results.get('total_responses', 0) > 0:
                coverage = (results.get('total_with_timestamps', 0) / results.get('total_responses', 0)) * 100
                st.metric("Timestamp Coverage", f"{coverage:.1f}%")
            
            # Show sample responses
            if 'sample_responses' in results and results['sample_responses']:
                st.subheader("📝 Sample Responses")
                
                for i, response in enumerate(results['sample_responses'][:3]):
                    with st.expander(f"Response {i+1} - {response.get('company', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Metadata:**")
                            st.write(f"Company: {response.get('company', 'N/A')}")
                            st.write(f"Interviewee: {response.get('interviewee_name', 'N/A')}")
                            st.write(f"Deal Status: {response.get('deal_status', 'N/A')}")
                        
                        with col2:
                            st.write("**Timestamps:**")
                            st.write(f"Start: {response.get('start_timestamp', 'N/A')}")
                            st.write(f"End: {response.get('end_timestamp', 'N/A')}")
                        
                        st.write("**Question:**")
                        st.write(response.get('question', 'N/A'))
                        
                        st.write("**Response:**")
                        st.write(response.get('verbatim_response', 'N/A')[:300] + "..." if len(response.get('verbatim_response', '')) > 300 else response.get('verbatim_response', 'N/A'))
        else:
            st.info("�� Upload a CSV and process interviews to see results here")

def process_interviews(df, client_id, max_interviews, dry_run, transcript_column):
    """Process interviews with progress tracking"""
    
    # Initialize parser
    parser = UniversalTimestampParser()
    
    # Initialize database
    db = None
    if not dry_run:
        try:
            db = SupabaseDatabase()
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            return
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_responses = 0
    total_with_timestamps = 0
    processed_interviews = 0
    sample_responses = []
    
    df_to_process = df.head(max_interviews)
    
    for index, row in df_to_process.iterrows():
        progress = (index + 1) / len(df_to_process)
        progress_bar.progress(progress)
        status_text.text(f"Processing interview {index + 1}/{len(df_to_process)}")
        
        try:
            # Get transcript
            transcript = row.get(transcript_column, '')
            if not transcript or pd.isna(transcript):
                continue
            
            # Extract metadata
            company = (row.get('Interview Contact Company Name') or 
                     row.get('Company') or 
                     row.get('Company Name') or 
                     f'Company_{index + 1}')
            
            interviewee = (row.get('Interview Contact Full Name') or 
                          row.get('Interviewee') or 
                          row.get('Contact Name') or 
                          f'Interviewee_{index + 1}')
            
            deal_status = (row.get('Deal Status') or 
                          row.get('Status') or 
                          'closed_won')
            
            interview_date = (row.get('Completion Date') or 
                            row.get('Interview Date') or 
                            row.get('Date') or 
                            datetime.now().strftime('%Y-%m-%d'))
            
            interview_id = (row.get('Interview ID') or 
                          row.get('ID') or 
                          f'IVW-{index + 1:05d}')
            
            # Process transcript
            responses = process_universal_transcript_with_timestamps(
                transcript, company, interviewee, deal_status, interview_date, client_id, interview_id
            )
            
            if responses:
                total_responses += len(responses)
                processed_interviews += 1
                
                # Count responses with timestamps
                timestamped_responses = [r for r in responses if r.get('start_timestamp') or r.get('end_timestamp')]
                total_with_timestamps += len(timestamped_responses)
                
                # Store sample responses
                if len(sample_responses) < 3:
                    sample_responses.extend(responses[:3-len(sample_responses)])
                
                # Save to database
                if not dry_run and db:
                    for response in responses:
                        try:
                            db.save_core_response(response)
                        except Exception as e:
                            st.error(f"Error saving response: {e}")
        
        except Exception as e:
            st.error(f"Error processing interview {index + 1}: {e}")
            continue
    
    # Store results in session state
    st.session_state.processing_results = {
        'total_interviews': len(df_to_process),
        'processed_interviews': processed_interviews,
        'total_responses': total_responses,
        'total_with_timestamps': total_with_timestamps,
        'sample_responses': sample_responses
    }
    
    # Show completion
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    st.success(f"✅ Processed {processed_interviews} interviews with {total_responses} responses")
    
    if not dry_run:
        st.success("💾 All data saved to database with timestamps")

if __name__ == "__main__":
    main()
