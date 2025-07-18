import streamlit as st
import pandas as pd
import os
import sys
import subprocess
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Tuple, Dict, List
from supabase_database import SupabaseDatabase

# Constants
BASE = Path("temp")
BASE.mkdir(exist_ok=True)
STAGE1_CSV = BASE / "stage1_data_responses.csv"
SUPABASE_AVAILABLE = True

try:
    db = SupabaseDatabase()
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    SUPABASE_AVAILABLE = False

def extract_interview_id_from_file(file_path: str) -> str:
    """Extract interview ID from the top of a transcript file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to find interview ID
            first_lines = []
            for i in range(10):  # Check first 10 lines
                line = f.readline().strip()
                if line:
                    first_lines.append(line)
            
            # Look for interview ID patterns
            for line in first_lines:
                # Pattern: IVW-XXXXX (Rev format)
                match = re.search(r'IVW-\d+', line)
                if match:
                    return match.group(0)
                
                # Pattern: Interview ID: XXXXX
                match = re.search(r'Interview ID:\s*([A-Z0-9-]+)', line, re.IGNORECASE)
                if match:
                    return match.group(1)
                
                # Pattern: ID: XXXXX
                match = re.search(r'ID:\s*([A-Z0-9-]+)', line, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return ""
    except Exception as e:
        st.warning(f"Could not extract interview ID from {file_path}: {e}")
        return ""

def get_metadata_for_interview_id(interview_id: str, client_id: str) -> Dict:
    """Get metadata for a given interview ID from the database"""
    if not SUPABASE_AVAILABLE or not interview_id:
        return {}
    
    try:
        # Query the metadata table for this interview ID
        response = db.supabase.table('interview_metadata').select('*').eq('interview_id', interview_id).eq('client_id', client_id).execute()
        
        if response.data:
            metadata = response.data[0]
            return {
                'interviewee_name': metadata.get('interviewee_name', ''),
                'company': metadata.get('company', ''),
                'deal_status': metadata.get('deal_status', ''),
                'date_of_interview': metadata.get('date_of_interview', ''),
                'interview_id': metadata.get('interview_id', '')
            }
        else:
            st.warning(f"No metadata found for interview ID: {interview_id}")
            return {}
    except Exception as e:
        st.error(f"Error getting metadata for interview ID {interview_id}: {e}")
        return {}

def extract_interviewee_and_company(filename):
    """Extract interviewee and company from filename"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Split by common separators
    parts = re.split(r'[_\-\s]+', name)
    
    if len(parts) >= 2:
        # Assume first part is interviewee, second is company
        interviewee = parts[0]
        company = parts[1]
        
        # Handle cases with more parts
        if len(parts) > 2:
            # If there are numbers or additional parts, include them in company
            company_parts = []
            for part in parts[1:]:
                if not part.isdigit() or len(part) <= 2:  # Include short numbers
                    company_parts.append(part)
            company = ' '.join(company_parts)
    else:
        interviewee = name
        company = "Unknown"
    
    return interviewee, company

def save_uploaded_files(uploaded_files, upload_dir="uploads"):
    """Save uploaded files and return their paths"""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    saved_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(file_path)
    
    return saved_paths

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

def process_single_file(file_info: Tuple[int, str]) -> Dict:
    """Process a single file and return results"""
    file_index, file_path = file_info
    result = {
        'success': False,
        'filename': os.path.basename(file_path),
        'data': None,
        'quotes_count': 0,
        'error': None
    }
    
    try:
        # Extract interview ID from file
        interview_id = extract_interview_id_from_file(file_path)
        client_id = get_client_id()
        
        # Get metadata if interview ID found
        metadata = {}
        if interview_id:
            metadata = get_metadata_for_interview_id(interview_id, client_id)
            st.info(f"📋 Found interview ID: {interview_id} for {os.path.basename(file_path)}")
        
        # Use metadata if available, otherwise extract from filename
        if metadata:
            interviewee = metadata.get('interviewee_name', '')
            company = metadata.get('company', '')
            deal_status = metadata.get('deal_status', 'closed_won')
            date_of_interview = metadata.get('date_of_interview', '2024-01-01')
            st.success(f"✅ Using metadata for {os.path.basename(file_path)}: {interviewee} at {company}")
        else:
            interviewee, company = extract_interviewee_and_company(os.path.basename(file_path))
            deal_status = "closed_won"
            date_of_interview = "2024-01-01"
            st.info(f"📝 Using filename extraction for {os.path.basename(file_path)}: {interviewee} at {company}")
        
        # Create temporary output file
        temp_output = BASE / f"temp_output_{file_index}.csv"
        
        # Run the modular CLI
        cmd = [
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            file_path, company, interviewee, deal_status, date_of_interview, "-o", str(temp_output)
        ]
        
        process_result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if process_result.returncode == 0 and temp_output.exists():
            try:
                df_temp = pd.read_csv(temp_output)
                
                # Add metadata fields if available
                if metadata:
                    df_temp['interview_id'] = metadata.get('interview_id', '')
                    df_temp['interviewee_name'] = metadata.get('interviewee_name', '')
                    df_temp['company'] = metadata.get('company', '')
                    df_temp['deal_status'] = metadata.get('deal_status', '')
                    df_temp['date_of_interview'] = metadata.get('date_of_interview', '')
                    df_temp['client_id'] = client_id
                else:
                    # Use extracted values
                    df_temp['interviewee_name'] = interviewee
                    df_temp['company'] = company
                    df_temp['deal_status'] = deal_status
                    df_temp['date_of_interview'] = date_of_interview
                    df_temp['client_id'] = client_id
                
                result['data'] = df_temp
                result['quotes_count'] = len(df_temp)
                result['success'] = True
                
            except Exception as e:
                result['error'] = f"Failed to read CSV: {e}"
        else:
            result['error'] = f"Process failed: {process_result.stderr}"
        
        # Clean up temp file
        if temp_output.exists():
            temp_output.unlink()
            
    except subprocess.TimeoutExpired:
        result['error'] = "Process timed out"
    except Exception as e:
        result['error'] = str(e)
    
    return result

def process_files_with_progress_parallel():
    """Process uploaded files with parallel processing and progress tracking"""
    if not st.session_state.uploaded_paths:
        st.error("No files uploaded")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(st.session_state.uploaded_paths)
    completed = 0
    successful_results = []
    error_count = 0
    
    # Determine number of workers (conservative approach)
    max_workers = min(3, total_files)  # Max 3 concurrent processes
    
    # Prepare file info for processing
    file_infos = [(i, path) for i, path in enumerate(st.session_state.uploaded_paths)]
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_single_file, file_info): file_info for file_info in file_infos}
        
        # Process completed tasks
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                completed += 1
                progress_bar.progress(completed / total_files)
                status_text.text(f"Processing {completed}/{total_files} files...")
                
                if result['success'] and result['data'] is not None:
                    successful_results.append(result['data'])
                    st.success(f"✅ {result['filename']}: {result['quotes_count']} quotes extracted")
                else:
                    st.warning(f"⚠️ {result['filename']}: {result['error']}")
                    error_count += 1
                    
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                completed += 1
                error_count += 1
    
    # Final progress update
    progress_bar.progress(1.0)
    status_text.text("Processing complete!")
    
    # Combine successful results
    if successful_results:
        combined_df = pd.concat(successful_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Processed {len(successful_results)} files successfully with {len(combined_df)} total quotes")
        if error_count > 0:
            st.warning(f"⚠️ {error_count} files had errors")
        st.session_state.current_step = 2
    else:
        st.error("No quotes extracted from any files")

def process_files_with_progress():
    """Legacy sequential processing - kept for fallback"""
    if not st.session_state.uploaded_paths:
        st.error("No files uploaded")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(st.session_state.uploaded_paths)
    all_results = []
    
    for i, path in enumerate(st.session_state.uploaded_paths):
        status_text.text(f"Processing {os.path.basename(path)}...")
        
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        temp_output = BASE / f"temp_output_{i}.csv"
        
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path, company, interviewee, "closed_won", "2024-01-01", "-o", str(temp_output)
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and temp_output.exists():
            try:
                df_temp = pd.read_csv(temp_output)
                all_results.append(df_temp)
                st.success(f"✅ {os.path.basename(path)}: {len(df_temp)} quotes extracted")
            except Exception as e:
                st.warning(f"⚠️ {os.path.basename(path)}: {e}")
        
        if temp_output.exists():
            temp_output.unlink()
        
        progress_bar.progress((i + 1) / total_files)
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Processed {len(all_results)} files with {len(combined_df)} total quotes")
        st.session_state.current_step = 2
    else:
        st.error("No quotes extracted")

def save_stage1_to_supabase(csv_path):
    """Save Stage 1 results to Supabase with metadata linking"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return False
    
    try:
        df = pd.read_csv(csv_path)
        saved_count = 0
        client_id = get_client_id()
        
        for _, row in df.iterrows():
            response_data = {
                'response_id': row.get('response_id', '') or row.get('Response ID', ''),
                'verbatim_response': row.get('verbatim_response', '') or row.get('Verbatim Response', ''),
                'subject': row.get('subject', '') or row.get('Subject', ''),
                'question': row.get('question', '') or row.get('Question', ''),
                'deal_status': row.get('deal_status', '') or row.get('Deal Status', 'closed_won'),
                'company': row.get('company', '') or row.get('Company Name', ''),
                'interviewee_name': row.get('interviewee_name', '') or row.get('Interviewee Name', ''),
                'interview_date': row.get('date_of_interview', '') or row.get('Date of Interview', '2024-01-01'),
                'interview_id': row.get('interview_id', ''),  # New field for metadata linking
                'file_source': 'stage1_processing',
                'client_id': client_id
            }
            
            if not response_data['response_id']:
                st.warning(f"Blank response_id for row: {row}")
            
            if db.save_core_response(response_data):
                saved_count += 1
        
        st.success(f"✅ Saved {saved_count} quotes to database for client: {client_id}")
        if any(row.get('interview_id') for _, row in df.iterrows()):
            st.success(f"🔗 {sum(1 for _, row in df.iterrows() if row.get('interview_id'))} quotes linked to metadata")
        return True
    except Exception as e:
        st.error(f"❌ Failed to save to database: {e}")
        return False

def show_stage1_data_responses():
    """Stage 1: Data Response Table - Upload and extract quotes from interview files"""
    st.title("📊 Stage 1: Data Response Table")
    st.markdown("Upload interview transcripts and extract customer quotes and insights.")
    
    # File upload section
    st.subheader("📤 Upload Interview Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['txt', 'docx'],
        accept_multiple_files=True,
        help="Select one or more interview transcript files"
    )
    
    if uploaded_files:
        st.session_state.uploaded_paths = save_uploaded_files(uploaded_files)
        st.success(f"✅ Uploaded {len(uploaded_files)} files")
        
        # Show uploaded files
        st.subheader("📁 Uploaded Files")
        for i, path in enumerate(st.session_state.uploaded_paths):
            st.write(f"{i+1}. {os.path.basename(path)}")
        
        # Process button
        if st.button("🚀 Extract Quotes", type="primary", help="Process files to extract customer quotes"):
            with st.spinner("Extracting quotes from interviews..."):
                # Add processing mode selection
                processing_mode = st.radio(
                    "Processing Mode",
                    ["Parallel (Faster)", "Sequential (More Stable)"],
                    horizontal=True,
                    help="Parallel processing is faster but may use more resources"
                )
                
                if processing_mode == "Parallel (Faster)":
                    process_files_with_progress_parallel()
                else:
                    process_files_with_progress()
                    
                if SUPABASE_AVAILABLE and os.path.exists(STAGE1_CSV):
                    if save_stage1_to_supabase(STAGE1_CSV):
                        st.success("✅ Quotes extracted and saved to database")
                        st.session_state.current_step = 1
                        st.rerun()
                    else:
                        st.error("❌ Failed to save to database")
    
    # Show existing results
    if os.path.exists(STAGE1_CSV):
        st.subheader("📋 Extracted Quotes")
        df = pd.read_csv(STAGE1_CSV)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Quotes", len(df))
            with col2:
                if 'Subject' in df.columns:
                    st.metric("Topics Covered", df['Subject'].nunique())
                else:
                    st.metric("Topics Covered", "N/A")
            with col3:
                if 'Company Name' in df.columns:
                    st.metric("Companies", df['Company Name'].nunique())
                else:
                    st.metric("Companies", "N/A")
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Quotes",
                data=csv,
                file_name="extracted_quotes.csv",
                mime="text/csv",
                key="download_extracted_quotes"
            )
            
            # Proceed to Stage 2
            if st.button("🎯 Proceed to Stage 2: Label Quotes", type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        else:
            st.info("📤 Please upload and process files first")
    
    # Processing details
    st.subheader("🔧 Processing Details")
    st.markdown("""
    **How the pipeline extracts quotes from your interviews (16K-optimized version):**
    
    **Batching & Parallel Processing:**
    - Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor`
    - Each file is handled as a separate job for speed and efficiency
    
    **Advanced Chunking & Segmentation:**
    - Uses token-based chunking with ~2K tokens per chunk
    - Q&A-aware segmentation that preserves conversation boundaries
    - Intelligent overlap of 200 tokens to maintain continuity
    
    **Enhanced LLM Processing:**
    - Each chunk is sent to GPT-3.5-turbo-16k with comprehensive context
    - Extracts 3-5 quotes per chunk with detailed verbatim responses
    - Focuses on detailed customer experiences and specific examples
    """) 