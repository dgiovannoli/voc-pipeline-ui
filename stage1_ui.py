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
    st.markdown("Extract customer quotes and insights from interview transcripts using metadata CSV files.")
    
    # Get client ID first
    client_id = get_client_id()
    
    # Status overview at the top
    st.subheader("📈 Current Status")
    
    if SUPABASE_AVAILABLE:
        try:
            df = db.get_stage1_data_responses(client_id=client_id)
            if df.empty:
                st.info(f"📭 No Stage 1 data found for client: **{client_id}**")
                st.info("Upload a metadata CSV file below to get started.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Responses", len(df))
                with col2:
                    st.metric("Interviews", df['interview_id'].nunique())
                with col3:
                    st.metric("Companies", df['company'].nunique())
                with col4:
                    st.metric("Interviewees", df['interviewee_name'].nunique())
                st.success(f"✅ Stage 1 data ready for analysis")
        except Exception as e:
            st.error(f"❌ Error checking status: {e}")
    else:
        st.error("❌ Database not available")
        return
    
    # Main workflow section
    st.subheader("🚀 Process New Data")
    
    # Collapsible help section
    with st.expander("📋 Required CSV Format", expanded=False):
        st.markdown("""
        **Your CSV must contain these columns:**
        - `Interview ID` - Unique identifier for each interview
        - `Client Name` - Must match your current client ID: **{client_id}**
        - `Interview Contact Full Name` - Name of the interviewee
        - `Interview Contact Company Name` - Company name
        - `Deal Status` - Status of the deal (e.g., "Closed Won", "Closed Lost")
        - `Completion Date` - Date of the interview
        - `Raw Transcript` - Full transcript text
        - `Interview Status` - Must be "Completed" for processing
        """.format(client_id=client_id))
    
    # File upload with better visual design
    uploaded_csv = st.file_uploader(
        "📁 Upload metadata CSV file",
        type=['csv'],
        help="Upload a CSV file containing interview metadata and transcripts"
    )
    
    if uploaded_csv:
        # Preview section
        with st.expander("📊 File Preview", expanded=True):
            try:
                df_preview = pd.read_csv(uploaded_csv)
                st.info(f"📊 CSV contains {len(df_preview)} interviews")
                
                # Validate client match
                if 'Client Name' in df_preview.columns:
                    available_clients = df_preview['Client Name'].dropna().unique()
                    if client_id in available_clients:
                        st.success(f"✅ Client ID '{client_id}' found in CSV")
                    else:
                        st.warning(f"⚠️ Client ID '{client_id}' not found in CSV")
                        st.info(f"Available clients: {', '.join(available_clients)}")
                
                # Show first few rows
                st.dataframe(df_preview.head(3), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error reading CSV: {e}")
                return
        
        # Processing options in a cleaner layout
        st.subheader("⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            max_interviews = st.number_input(
                "Max interviews to process",
                min_value=0,
                value=0,
                help="0 = process all interviews"
            )
        with col2:
            dry_run = st.checkbox(
                "🔍 Dry run (test without saving)",
                help="Process without saving to database"
            )
        
        # Process button with better styling
        if st.button("🚀 Process Interviews", type="primary", use_container_width=True):
            with st.spinner("Processing interviews..."):
                result = process_metadata_csv(
                    uploaded_csv, 
                    client_id, 
                    max_interviews if max_interviews > 0 else None,
                    dry_run
                )
            
            if result['success']:
                st.success("✅ Processing completed!")
                
                # Results in a clean card layout
                st.subheader("📊 Processing Results")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Interviews", result['processed'])
                with col2:
                    st.metric("Successful", result['successful'])
                with col3:
                    st.metric("Failed", result['failed'])
                with col4:
                    st.metric("Responses", result['total_responses'])
                
                if dry_run:
                    st.info("🔍 Dry run completed - no data was saved")
                else:
                    st.success(f"💾 {result['total_responses']} responses saved to database")
                    
                    # Auto-refresh the page to show updated status
                    st.rerun()
            else:
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    # Existing data section (only show if there's data)
    if SUPABASE_AVAILABLE:
        try:
            df = db.get_stage1_data_responses(client_id=client_id)
            if not df.empty:
                st.subheader("📊 Current Data")
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Current Data",
                    data=csv,
                    file_name=f"stage1_data_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Show data in expandable section
                with st.expander("📋 View All Responses", expanded=False):
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error retrieving data: {e}")
    
    # Technical details in collapsible section
    with st.expander("🔧 Technical Details", expanded=False):
        st.markdown("""
        **Processing Pipeline:**
        - **Perfect Metadata Linkage**: All responses automatically linked with correct interviewee, company, and interview details
        - **Intelligent Chunking**: Uses ~2K token chunks with 200 token overlap for context preservation
        - **Q&A Preservation**: Maintains conversation boundaries during processing
        - **Parallel Processing**: Multiple interviews processed simultaneously for faster results
        - **LLM Enhancement**: GPT-3.5-turbo-16k extracts comprehensive quotes and insights
        """) 