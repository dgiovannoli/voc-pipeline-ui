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

try:
    db = SupabaseDatabase()
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    SUPABASE_AVAILABLE = False



def get_client_id():
    """Get client ID from session state or sidebar"""
    if 'client_id' in st.session_state and st.session_state.client_id:
        return st.session_state.client_id
    
    # If no client_id is set, show a warning and guide user to set one
    st.warning("⚠️ **Client ID Required**")
    st.info("Please set a Client ID in the sidebar before proceeding.")
    st.info("💡 **How to set Client ID:**")
    st.info("1. Look in the sidebar under '🏢 Client Settings'")
    st.info("2. Enter a unique identifier for this client's data")
    st.info("3. Press Enter to save")
    st.stop()
    return None



def process_metadata_csv(csv_file, client_id, max_interviews=None, dry_run=False):
    """Process Stage 1 data from metadata CSV file"""
    try:
        processor = MetadataStage1Processor()
        
        # Save uploaded file temporarily
        temp_csv_path = f"temp_metadata_{client_id}.csv"
        with open(temp_csv_path, "wb") as f:
            f.write(csv_file.getbuffer())
        
        # Process the metadata CSV
        result = processor.process_metadata_csv(
            csv_file_path=temp_csv_path,
            client_id=client_id,
            max_interviews=max_interviews,
            dry_run=dry_run
        )
        
        # Clean up temp file
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        
        return result
    except Exception as e:
        st.error(f"❌ Error processing metadata CSV: {e}")
        return {'success': False, 'error': str(e)}

def show_stage1_data_responses():
    """Stage 1: Data Response Table - Process metadata CSV to extract quotes"""
    st.title("📊 Stage 1: Data Response Table")
    st.markdown("Upload metadata CSV files and extract customer quotes and insights from interview transcripts.")
    
    st.subheader("📊 Metadata CSV Processing")
    
    st.info("""
    **Metadata CSV Processing** processes Stage 1 data directly from a metadata CSV file 
    that contains interview transcripts. This approach ensures perfect metadata linkage and eliminates 
    filename parsing issues.
    
    **Required CSV Columns:**
    - `Interview ID` - Unique identifier for each interview
    - `Client Name` - Client identifier (must match your current client ID)
    - `Interview Contact Full Name` - Name of the interviewee
    - `Interview Contact Company Name` - Company name
    - `Deal Status` - Status of the deal (e.g., "Closed Won", "Closed Lost")
    - `Completion Date` - Date of the interview
    - `Raw Transcript` - Full transcript text
    - `Interview Status` - Must be "Completed" for processing
    """)
    
    # File upload
    uploaded_csv = st.file_uploader(
        "Upload metadata CSV file",
        type=['csv'],
        help="Upload a CSV file containing interview metadata and transcripts"
    )
    
    if uploaded_csv:
        st.success(f"✅ CSV file uploaded: {uploaded_csv.name}")
        
        # Show CSV preview
        try:
            df_preview = pd.read_csv(uploaded_csv)
            st.info(f"📊 CSV contains {len(df_preview)} rows")
            
            # Show available clients
            if 'Client Name' in df_preview.columns:
                available_clients = df_preview['Client Name'].dropna().unique()
                st.info(f"👥 Available clients: {', '.join(available_clients)}")
            
            # Show column info
            st.write("**CSV Columns:**")
            st.write(list(df_preview.columns))
            
            # Show first few rows
            st.write("**Preview (first 3 rows):**")
            st.dataframe(df_preview.head(3), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")
            return
        
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            max_interviews = st.number_input(
                "Max interviews to process (0 = all)",
                min_value=0,
                value=0,
                help="Limit the number of interviews to process (0 means process all)"
            )
        with col2:
            dry_run = st.checkbox(
                "Dry run (don't save to database)",
                help="Process without saving to database to test the results"
            )
        
        # Process button
        if st.button("🚀 Process Metadata CSV", type="primary"):
            client_id = get_client_id()
            
            with st.spinner("Processing metadata CSV..."):
                result = process_metadata_csv(
                    uploaded_csv, 
                    client_id, 
                    max_interviews if max_interviews > 0 else None,
                    dry_run
                )
            
            if result['success']:
                st.success(f"✅ Processing completed successfully!")
                
                # Show results
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Interviews Processed", result['processed'])
                with col2:
                    st.metric("Successful", result['successful'])
                with col3:
                    st.metric("Failed", result['failed'])
                with col4:
                    st.metric("Total Responses", result['total_responses'])
                
                # Show detailed results
                if result['results']:
                    st.write("**Detailed Results:**")
                    results_df = pd.DataFrame(result['results'])
                    st.dataframe(results_df, use_container_width=True)
                
                if dry_run:
                    st.info("🔍 This was a dry run - no data was saved to the database")
                else:
                    st.success(f"💾 {result['total_responses']} responses saved to database")
            else:
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    # Show existing Stage 1 data from database
    st.subheader("📊 Existing Stage 1 Data")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return
    
    try:
        client_id = get_client_id()
        df = db.get_stage1_data_responses(client_id=client_id)
        
        if df.empty:
            st.info("📭 No Stage 1 data responses found for this client")
        else:
            st.success(f"✅ Found {len(df)} Stage 1 data responses for client: {client_id}")
            
            # Display summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Responses", len(df))
            with col2:
                st.metric("Unique Interviews", df['interview_id'].nunique())
            with col3:
                st.metric("Unique Companies", df['company'].nunique())
            with col4:
                st.metric("Unique Interviewees", df['interviewee_name'].nunique())
            
            # Show data
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Stage 1 Data as CSV",
                data=csv,
                file_name=f"stage1_data_responses_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"❌ Error retrieving Stage 1 data: {e}")
    
    # Processing details
    st.subheader("🔧 Processing Details")
    st.markdown("""
    **How the metadata-driven pipeline extracts quotes from your interviews:**
    
    **Perfect Metadata Linkage:**
    - All responses are automatically linked with correct interviewee, company, deal status, and interview_id
    - No filename parsing required - metadata comes directly from the CSV
    - Ensures data consistency and eliminates manual errors
    
    **Batch Processing:**
    - Multiple interviews are processed from a single CSV file
    - Each interview transcript is processed through the same Stage 1 extraction pipeline
    - Supports parallel processing for faster results
    
    **Advanced LLM Processing:**
    - Uses token-based chunking with ~2K tokens per chunk
    - Q&A-aware segmentation that preserves conversation boundaries
    - Intelligent overlap of 200 tokens to maintain continuity
    - Each chunk is processed by GPT-3.5-turbo-16k for comprehensive quote extraction
    """) 