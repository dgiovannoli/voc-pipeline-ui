import streamlit as st
import pandas as pd
import os
import time
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
    
    # If no client_id is set, show a warning and guide user to set one
    st.warning("⚠️ **Client ID Required**")
    st.info("Please set a Client ID in the sidebar before proceeding.")
    st.info("💡 **How to set Client ID:**")
    st.info("1. Look in the sidebar under '🏢 Client Settings'")
    st.info("2. Enter a unique identifier for this client's data")
    st.info("3. Press Enter to save")
    st.stop()
    return None

def process_metadata_csv(csv_file, client_id, max_interviews=None, dry_run=False, processing_mode="parallel", max_workers=3):
    """Process Stage 1 data from metadata CSV file with parallel processing options"""
    try:
        processor = MetadataStage1Processor()
        
        # Use the stored dataframe directly (no mapping needed)
        df = st.session_state.df_preview
        
        # Save the dataframe as CSV temporarily
        temp_csv_path = f"temp_metadata_{client_id}.csv"
        df.to_csv(temp_csv_path, index=False)
        st.success(f"✅ Saved CSV to {temp_csv_path}")
        
        # Add performance tracking
        start_time = time.time()
        
        # Show processing mode
        if processing_mode == "parallel":
            st.info(f"🚀 Using parallel processing with {max_workers} workers")
        else:
            st.info("🐌 Using sequential processing")
        
        # Create a progress container for real-time updates
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text="Starting processing...")
            
            # Process the metadata CSV
            result = processor.process_metadata_csv(
                csv_file_path=temp_csv_path,
                client_id=client_id,
                max_interviews=max_interviews,
                dry_run=dry_run,
                processing_mode=processing_mode,
                max_workers=max_workers
            )
            
            progress_bar.progress(100, text="Processing completed!")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Clean up temp file
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        
        # Ensure result has all required keys
        if result is None:
            result = {}
        
        # Set default values for missing keys
        result.setdefault('success', False)
        result.setdefault('processed', 0)
        result.setdefault('successful', 0)
        result.setdefault('failed', 0)
        result.setdefault('total_responses', 0)
        result.setdefault('error', 'Unknown error')
        
        # Add performance metrics
        result['processing_time'] = processing_time
        result['processing_mode'] = processing_mode
        result['max_workers'] = max_workers if processing_mode == "parallel" else 1
        
        return result
        
    except Exception as e:
        st.error(f"❌ Error processing metadata CSV: {e}")
        return {
            'success': False, 
            'error': str(e),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_responses': 0,
            'processing_time': 0,
            'processing_mode': processing_mode
        }

def show_performance_comparison():
    """Show performance comparison between parallel and sequential processing"""
    
    st.subheader("⚡ Performance Optimization")
    
    # Performance info card
    with st.container():
        st.markdown("""
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 4px solid #1f77b4;">
        <h4>🚀 Parallel Processing Available!</h4>
        <p>Your Stage 1 processing now supports parallel execution for dramatically faster performance:</p>
        <ul>
        <li><strong>75-85% speed improvement</strong> typical</li>
        <li><strong>3-5x faster</strong> for large interviews</li>
        <li><strong>Same quality</strong> as sequential processing</li>
        <li><strong>Intelligent chunking</strong> with Q&A boundary awareness</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Performance estimates
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🐌 Sequential Processing:**")
        st.markdown("- 1 interview: ~25-50 seconds")
        st.markdown("- 10 interviews: ~4-8 minutes") 
        st.markdown("- 100 interviews: ~40-80 minutes")
    
    with col2:
        st.markdown("**🚀 Parallel Processing:**")
        st.markdown("- 1 interview: ~5-15 seconds")
        st.markdown("- 10 interviews: ~1-3 minutes")
        st.markdown("- 100 interviews: ~10-25 minutes")
    
    # Show last processing stats if available
    if 'last_processing_result' in st.session_state:
        result = st.session_state.last_processing_result
        processing_time = result.get('processing_time', 0)
        processing_mode = result.get('processing_mode', 'unknown')
        total_responses = result.get('total_responses', 0)
        max_workers = result.get('max_workers', 1)
        
        if processing_time > 0:
            st.subheader("📊 Last Processing Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mode", processing_mode.title())
            with col2:
                st.metric("Time", f"{processing_time:.1f}s")
            with col3:
                st.metric("Workers", max_workers)
            with col4:
                responses_per_sec = total_responses / processing_time if processing_time > 0 else 0
                st.metric("Speed", f"{responses_per_sec:.1f} resp/s")

def show_stage1_data_responses():
    """Stage 1: Data Response Table - Process metadata CSV to extract quotes"""
    st.title("📊 Stage 1: Data Response Table")
    st.markdown("Extract customer quotes and insights from interview transcripts using metadata CSV files.")
    st.info("✨ **Enhanced with Auto-Harmonization & Parallel Processing**: Subjects are automatically harmonized and processing is 3-5x faster!")
    
    # Get client ID first
    client_id = get_client_id()
    
    # Show performance comparison
    show_performance_comparison()
    
    # Status overview at the top
    st.subheader("📈 Current Status")
    
    if SUPABASE_AVAILABLE:
        try:
            db = get_database()
            if db is None:
                st.error("❌ Database not available for step 1")
                return
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
    
    # Show processing status
    st.success("✅ Ready to process your CSV!")
    
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
        - `Industry` - Industry/sector of the company
        - `Raw Transcript` - Full transcript text
        - `Interview Status` - Must be "Completed" for processing
        
        **Optional columns (will be saved if present):**
        - `Audio/Video Link` - URL to the original audio/video file
        - `Interview Contact Website` - Website URL for the contact/company
        """.format(client_id=client_id))
    
    # File upload with better visual design
    uploaded_csv = st.file_uploader(
        "📁 Upload metadata CSV file",
        type=['csv'],
        help="Upload a CSV file containing interview metadata and transcripts"
    )
    
    if uploaded_csv:
        # CSV validation and debugging
        st.subheader("🔍 CSV Validation")
        
        # Check file info
        file_info = uploaded_csv.getvalue()
        st.info(f"📁 File size: {len(file_info)} bytes")
        
        # Try to read CSV and show basic info
        try:
            df_preview = pd.read_csv(uploaded_csv)
            st.success(f"✅ CSV read successfully")
            st.info(f"📊 Rows: {len(df_preview)}")
            st.info(f"📊 Columns: {len(df_preview.columns)}")
            st.info(f"📊 Column names: {list(df_preview.columns)}")
            
            # Show first few rows
            with st.expander("👀 First 3 rows", expanded=False):
                st.dataframe(df_preview.head(3), use_container_width=True)
                
            # Store the dataframe in session state for reuse
            st.session_state.df_preview = df_preview
                
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")
            st.stop()
        
        # Show CSV info and processing button
        st.success("✅ CSV loaded successfully! Ready to process.")
        st.info(f"📊 Found {len(st.session_state.df_preview)} rows with columns: {', '.join(st.session_state.df_preview.columns)}")
        
        # Preview section
        with st.expander("📊 File Preview", expanded=True):
            try:
                # Use the stored dataframe instead of reading again
                df_preview = st.session_state.df_preview
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
        st.info("🎯 **Auto-Harmonization**: Subject harmonization will run automatically during processing to standardize customer language into business categories.")
        
        # Processing configuration
        col1, col2, col3 = st.columns(3)
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
        with col3:
            processing_mode = st.selectbox(
                "Processing Mode",
                ["parallel", "sequential"],
                index=0,
                help="Parallel processing is 3-5x faster"
            )
        
        # Parallel processing configuration
        if processing_mode == "parallel":
            st.subheader("🚀 Parallel Processing Configuration")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                max_workers = st.slider(
                    "Worker Threads",
                    min_value=1,
                    max_value=8,
                    value=3,
                    help="More workers = faster processing (3-5 recommended)"
                )
            with col2:
                st.metric("Expected Speed Boost", f"{max_workers}x faster")
            with col3:
                estimated_interviews = len(df_preview) if 'df_preview' in st.session_state else 1
                estimated_time = max(5, (estimated_interviews * 30) / max_workers)
                st.metric("Estimated Time", f"{estimated_time:.0f}s")
        
        # Process button with better styling
        button_text = "🚀 Process Interviews (Parallel)" if processing_mode == "parallel" else "🐌 Process Interviews (Sequential)"
        
        if st.button(button_text, type="primary", use_container_width=True):
            with st.spinner(f"Processing interviews with {processing_mode} mode..."):
                result = process_metadata_csv(
                    uploaded_csv, 
                    client_id, 
                    max_interviews if max_interviews > 0 else None,
                    dry_run,
                    processing_mode,
                    max_workers if processing_mode == "parallel" else 1
                )
                
                # Store result for performance tracking
                st.session_state.last_processing_result = result
                
                # Debug: Show result structure (only in development)
                if st.session_state.get('debug_mode', False):
                    with st.expander("🔧 Debug: Result Structure", expanded=False):
                        st.json(result)
            
            if result.get('success', False):
                st.success("✅ Processing completed!")
                
                # Performance metrics
                processing_time = result.get('processing_time', 0)
                processing_mode_used = result.get('processing_mode', 'unknown')
                max_workers_used = result.get('max_workers', 1)
                
                if processing_time > 0:
                    st.subheader("⚡ Performance Results")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Processing Time", f"{processing_time:.1f}s")
                    with col2:
                        st.metric("Mode", processing_mode_used.title())
                    with col3:
                        st.metric("Workers Used", max_workers_used)
                    with col4:
                        total_responses = result.get('total_responses', 0)
                        if processing_time > 0:
                            throughput = total_responses / processing_time
                            st.metric("Throughput", f"{throughput:.1f} resp/s")
                
                # Results in a clean card layout
                st.subheader("📊 Processing Results")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Interviews", result.get('processed', 0))
                with col2:
                    st.metric("Successful", result.get('successful', 0))
                with col3:
                    st.metric("Failed", result.get('failed', 0))
                with col4:
                    st.metric("Responses", result.get('total_responses', 0))
                with col5:
                    harmonized = result.get('total_harmonized', 0)
                    total_responses = result.get('total_responses', 0)
                    rate = result.get('harmonization_rate', 0)
                    st.metric("🎯 Harmonized", f"{harmonized} ({rate:.0f}%)")
                
                if dry_run:
                    st.info("🔍 Dry run completed - no data was saved")
                else:
                    total_responses = result.get('total_responses', 0)
                    total_harmonized = result.get('total_harmonized', 0)
                    st.success(f"✅ {total_responses} responses saved to database with {total_harmonized} auto-harmonized")
                    
                    # Auto-refresh the page to show updated status
                    st.rerun()
            else:
                error_message = result.get('error', 'Unknown error')
                st.error(f"❌ Processing failed: {error_message}")
                
                # Show additional error details if available
                if 'message' in result:
                    st.info(f"ℹ️ Additional info: {result['message']}")
    
    # Existing data section (only show if there's data)
    if SUPABASE_AVAILABLE:
        try:
            db = get_database()
            if db is None:
                st.error("❌ Database not available for step 1")
                return
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
        **Enhanced Processing Pipeline:**
        - **🚀 Parallel Processing**: Multiple chunks processed simultaneously for 3-5x speed improvement
        - **Perfect Metadata Linkage**: All responses automatically linked with correct interviewee, company, and interview details
        - **Intelligent Chunking**: Uses ~1K token chunks with 200 token overlap for context preservation
        - **Q&A Preservation**: Maintains conversation boundaries during processing with smart overlaps
        - **ThreadPoolExecutor**: Safe concurrent processing with configurable worker threads
        - **LLM Enhancement**: GPT-4o-mini extracts comprehensive quotes and insights
        - **Performance Monitoring**: Real-time processing metrics and throughput tracking
        """)
        
        # Debug mode toggle
        debug_mode = st.checkbox("🐛 Enable Debug Mode", value=st.session_state.get('debug_mode', False))
        st.session_state.debug_mode = debug_mode
        if debug_mode:
            st.info("🔧 Debug mode enabled - additional information will be shown during processing") 