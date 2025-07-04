import os
import sys
import subprocess
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import re
from database import VOCDatabase

load_dotenv()

# Helper functions
def extract_interviewee_and_company(filename):
    name = filename.rsplit('.', 1)[0]
    # Try to extract "Interview with [Interviewee], ... at [Company]"
    match = re.search(r'Interview with ([^,]+),.*? at ([^.,]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        company = match.group(2).strip()
        return interviewee, company
    # Try to extract "Interview with [Interviewee] at [Company]"
    match = re.search(r'Interview with ([^,]+) at ([^.,]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        company = match.group(2).strip()
        return interviewee, company
    # Try to extract "Interview with [Interviewee]"
    match = re.search(r'Interview with ([^.,-]+)', name, re.IGNORECASE)
    if match:
        interviewee = match.group(1).strip()
        return interviewee, ""
    # Fallback: use the whole name as interviewee
    return name.strip(), ""

@st.cache_data(ttl=1, show_spinner=False)
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading CSV from {path}: {e}")
        return pd.DataFrame()

def process_files_modular():
    """Process files using the original pipeline (compatible with existing workflow)"""
    if not st.session_state.uploaded_paths:
        raise Exception("No files uploaded")
    
    # Process using original pipeline
    for path in st.session_state.uploaded_paths:
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "process_transcript",
            path,
            company if company else "Unknown",  # client
            company if company else "Unknown",  # company
            interviewee if interviewee else "Unknown",  # interviewee
            "closed_won",  # deal_status
            "2024-01-01"  # date_of_interview
        ], check=True)

def run_modular_stage(stage):
    """Run a specific pipeline stage"""
    if stage == 'extract-core':
        # This stage is handled by process_files_modular() which processes individual files
        # and outputs to STAGE1_CSV
        st.info("Extract core stage is handled by the main processing pipeline")
    elif stage == 'validate':
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "validate",
            "--input", str(STAGE1_CSV),
            "--output", str(VALIDATED_CSV)
        ], check=True)
    elif stage == 'enrich-analysis':
        # This stage is handled by build-table which adds enrichment from database
        st.info("Enrichment is handled by the build-table stage")
    elif stage == 'build-table':
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "build-table",
            "--input", str(VALIDATED_CSV),
            "--output", str(RESPONSE_TABLE_CSV)
        ], check=True)

# Page configuration
st.set_page_config(
    page_title="VOC Pipeline - Modular Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UX
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stage-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

BASE = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = BASE / "validated_quotes.csv"
PASSTHROUGH_CSV = BASE / "passthrough_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"
STAGE1_CSV = BASE / "stage1_output.csv"

# Initialize database and session state
if 'db' not in st.session_state:
    st.session_state.db = VOCDatabase()

if 'uploaded_paths' not in st.session_state:
    st.session_state.uploaded_paths = []

if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 'upload'

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎯 VOC Pipeline - Modular Analysis</h1>
    <p>Transform customer interviews into actionable insights with our modular AI pipeline</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Modular Workflow
with st.sidebar:
    st.markdown("## 🚀 Modular Workflow")
    
    # Workflow stages
    stages = {
        'upload': {'icon': '📁', 'title': 'Upload Files', 'desc': 'Upload interview transcripts'},
        'extract': {'icon': '🔍', 'title': 'Extract Core', 'desc': 'Extract verbatim responses'},
        'enrich': {'icon': '🧠', 'title': 'Enrich Analysis', 'desc': 'Add AI insights'},
        'label': {'icon': '🏷️', 'title': 'Add Labels', 'desc': 'Categorize responses'},
        'export': {'icon': '📊', 'title': 'Export Data', 'desc': 'Download results'}
    }
    
    # Stage navigation
    for stage_key, stage_info in stages.items():
        is_active = st.session_state.current_stage == stage_key
        if is_active:
            st.markdown(f"""
            <div class="stage-card" style="border-left: 4px solid #667eea;">
                <h4>{stage_info['icon']} {stage_info['title']}</h4>
                <p>{stage_info['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{stage_info['icon']} {stage_info['title']}", key=f"nav_{stage_key}", use_container_width=True):
                st.session_state.current_stage = stage_key
                st.rerun()
    
    st.markdown("---")
    
    # Quick stats
    stats = st.session_state.db.get_stats()
    st.markdown("### 📈 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Responses", stats.get('total_responses', 0))
    with col2:
        st.metric("Analyses", stats.get('total_analyses', 0))

# Main content area
if st.session_state.current_stage == 'upload':
    st.markdown("## 📁 Upload Interview Files")
    st.markdown("Upload your customer interview transcripts to begin processing.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploads = st.file_uploader(
            "Select interview files",
            type=["txt", "docx"],
            accept_multiple_files=True,
            help="Upload .txt or .docx files containing customer interviews"
        )
        
        if uploads:
            st.success(f"✅ {len(uploads)} files uploaded successfully")
            
            # Show uploaded files
            with st.expander("📋 Uploaded Files", expanded=True):
                for i, f in enumerate(uploads):
                    filename = f.name
                    interviewee, company = extract_interviewee_and_company(filename)
                    st.write(f"**{i+1}. {filename}**")
                    if interviewee or company:
                        st.write(f"   👤 {interviewee} | 🏢 {company}")
            
            # Process button
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                # Save uploaded files to session state
                st.session_state.uploaded_paths = []
                for f in uploads:
                    dest = UPLOAD_DIR / f.name
                    with open(dest, "wb") as out:
                        out.write(f.getbuffer())
                    st.session_state.uploaded_paths.append(str(dest))
                
                st.session_state.current_stage = 'extract'
                st.rerun()
    
    with col2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        **File Naming:**
        - Use descriptive names like "Interview with John Smith at TechCorp.docx"
        - System will auto-extract interviewee and company names
        
        **Supported Formats:**
        - `.txt` - Plain text files
        - `.docx` - Word documents
        
        **Best Practices:**
        - Upload multiple files at once for efficiency
        - Ensure files contain complete interview transcripts
        - Use consistent naming conventions
        """)

elif st.session_state.current_stage == 'extract':
    st.markdown("## 🔍 Extract Core Responses")
    st.markdown("Extract verbatim responses and metadata from your interview files.")
    
    # Check if files are uploaded
    if not hasattr(st.session_state, 'uploaded_paths') or not st.session_state.uploaded_paths:
        st.warning("⚠️ No files uploaded. Please go back to the Upload stage.")
        if st.button("⬅️ Back to Upload"):
            st.session_state.current_stage = 'upload'
            st.rerun()
    else:
        # Show uploaded files
        st.markdown("### 📁 Files Ready for Processing")
        with st.expander("📋 Uploaded Files", expanded=True):
            for i, path in enumerate(st.session_state.uploaded_paths):
                filename = os.path.basename(path)
                interviewee, company = extract_interviewee_and_company(filename)
                st.write(f"**{i+1}. {filename}**")
                if interviewee or company:
                    st.write(f"   👤 {interviewee} | 🏢 {company}")
        
        st.markdown("---")
        # Processing status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files Ready", len(st.session_state.uploaded_paths))
        with col2:
            stage1_exists = os.path.exists(STAGE1_CSV) and os.path.getsize(STAGE1_CSV) > 0
            st.metric("Core Extracted", len(load_csv(STAGE1_CSV)) if stage1_exists else 0)
        with col3:
            db_count = st.session_state.db.get_stats().get('total_responses', 0)
            st.metric("In Database", db_count)
        
        # Processing options
        st.markdown("### 🔧 Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚀 Quick Process")
            st.markdown("Process all files using the original pipeline:")
            
            if st.button("▶️ Process All Files", type="primary", use_container_width=True):
                with st.spinner("Processing files..."):
                    # Process files using original pipeline
                    try:
                        process_files_modular()
                        st.success("✅ File processing complete!")
                        st.session_state.current_stage = 'enrich'
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Processing failed: {e}")
        
        with col2:
            st.markdown("#### 🔄 Manual Processing")
            st.markdown("Process files step by step:")
            
            if st.button("🔍 Stage 1: Extract", use_container_width=True):
                with st.spinner("Extracting core responses..."):
                    try:
                        run_modular_stage('extract-core')
                        st.success("✅ Stage 1 complete!")
                    except Exception as e:
                        st.error(f"❌ Stage 1 failed: {e}")
            
            if st.button("✅ Stage 2: Validate", use_container_width=True):
                with st.spinner("Validating responses..."):
                    try:
                        run_modular_stage('validate')
                        st.success("✅ Validation complete!")
                    except Exception as e:
                        st.error(f"❌ Validation failed: {e}")
        
        # Show results if available
        if os.path.exists(STAGE1_CSV) and os.path.getsize(STAGE1_CSV) > 0:
            st.markdown("### 📊 Extraction Results")
            df = load_csv(STAGE1_CSV)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Responses", len(df))
                st.metric("Companies", df['Company Name'].nunique() if 'Company Name' in df.columns else 0)
            with col2:
                st.metric("Subjects", df['Subject'].nunique() if 'Subject' in df.columns else 0)
                st.metric("Avg Response Length", f"{df['Verbatim Response'].str.len().mean():.0f} chars" if 'Verbatim Response' in df.columns else "N/A")
            
            # Sample data
            with st.expander("📋 Sample Extracted Data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Next stage button
            if st.button("➡️ Continue to Enrichment", type="primary", use_container_width=True):
                st.session_state.current_stage = 'enrich'
                st.rerun()

elif st.session_state.current_stage == 'enrich':
    st.markdown("## 🧠 Enrich with AI Analysis")
    st.markdown("Add AI-generated insights and analysis to your core responses.")
    
    # Check if core data exists
    if not os.path.exists(STAGE1_CSV) or os.path.getsize(STAGE1_CSV) == 0:
        st.warning("⚠️ No core data found. Please complete the extraction stage first.")
        if st.button("⬅️ Back to Extract"):
            st.session_state.current_stage = 'extract'
            st.rerun()
    else:
        # Enrichment status
        col1, col2, col3 = st.columns(3)
        with col1:
            core_count = len(load_csv(STAGE1_CSV))
            st.metric("Core Responses", core_count)
        with col2:
            enriched_count = len(load_csv(RESPONSE_TABLE_CSV)) if os.path.exists(RESPONSE_TABLE_CSV) else 0
            st.metric("Enriched Responses", enriched_count)
        with col3:
            db_analyses = st.session_state.db.get_stats().get('total_analyses', 0)
            st.metric("AI Analyses", db_analyses)
        
        # Enrichment options
        st.markdown("### 🤖 AI Enrichment Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚀 Quick Enrichment")
            st.markdown("Add AI analysis using the modular pipeline:")
            
            if st.button("🧠 Add AI Analysis", type="primary", use_container_width=True):
                with st.spinner("Adding AI analysis..."):
                    try:
                        run_modular_stage('enrich-analysis')
                        st.success("✅ AI enrichment complete!")
                        st.session_state.current_stage = 'label'
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Enrichment failed: {e}")
        
        with col2:
            st.markdown("#### 🔧 Manual Enrichment")
            st.markdown("Control the enrichment process:")
            
            if st.button("📊 Build Enriched Table", use_container_width=True):
                with st.spinner("Building enriched table..."):
                    try:
                        run_modular_stage('build-table')
                        st.success("✅ Enriched table built!")
                    except Exception as e:
                        st.error(f"❌ Table building failed: {e}")
            
            if st.button("💾 Save to Database", use_container_width=True):
                with st.spinner("Saving to database..."):
                    try:
                        count = st.session_state.db.migrate_csv_to_db(str(RESPONSE_TABLE_CSV))
                        st.success(f"✅ Saved {count} responses to database!")
                    except Exception as e:
                        st.error(f"❌ Database save failed: {e}")
        
        # Show enrichment results
        if os.path.exists(RESPONSE_TABLE_CSV) and os.path.getsize(RESPONSE_TABLE_CSV) > 0:
            st.markdown("### 📊 Enrichment Results")
            df = load_csv(RESPONSE_TABLE_CSV)
            
            # Show enrichment fields
            core_columns = ['Response ID', 'Verbatim Response', 'Subject', 'Question', 'Deal Status', 'Company Name', 'Interviewee Name', 'Date of Interview']
            enrichment_columns = [col for col in df.columns if col not in core_columns]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Responses", len(df))
                st.metric("Core Fields", len(core_columns))
            with col2:
                st.metric("Enrichment Fields", len(enrichment_columns))
                st.metric("AI Insights", len([col for col in enrichment_columns if col not in ['Key Insight']]))
            
            # Sample enriched data
            with st.expander("📋 Sample Enriched Data", expanded=True):
                st.dataframe(df.head(5), use_container_width=True)
            
            # Next stage button
            if st.button("➡️ Continue to Labeling", type="primary", use_container_width=True):
                st.session_state.current_stage = 'label'
                st.rerun()

elif st.session_state.current_stage == 'label':
    st.markdown("## 🏷️ Add Labels & Categories")
    st.markdown("Categorize and label your responses for better analysis.")
    
    # Check if data exists
    stats = st.session_state.db.get_stats()
    if stats.get('total_responses', 0) == 0:
        st.warning("⚠️ No data in database. Please complete the enrichment stage first.")
        if st.button("⬅️ Back to Enrich"):
            st.session_state.current_stage = 'enrich'
            st.rerun()
    else:
        # Labeling status
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Responses", stats.get('total_responses', 0))
        with col2:
            st.metric("Labeled Responses", stats.get('total_labels', 0))
        with col3:
            st.metric("Companies", len(stats.get('responses_by_company', {})))
        with col4:
            st.metric("Subjects", len(stats.get('responses_by_subject', {})))
        
        # Data exploration and labeling
        st.markdown("### 🔍 Explore & Label Data")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            companies = ["All"] + list(stats.get('responses_by_company', {}).keys())
            selected_company = st.selectbox("Filter by Company", companies)
        with col2:
            deal_statuses = ["All"] + list(stats.get('responses_by_status', {}).keys())
            selected_status = st.selectbox("Filter by Deal Status", deal_statuses)
        with col3:
            search_term = st.text_input("Search Responses", placeholder="Enter keywords...")
        
        # Apply filters
        if st.button("🔍 Apply Filters", use_container_width=True):
            filters = {}
            if selected_company != "All":
                filters['company'] = selected_company
            if selected_status != "All":
                filters['deal_status'] = selected_status
            
            df_filtered = st.session_state.db.get_responses(filters)
            
            if search_term:
                mask = df_filtered['verbatim_response'].str.contains(search_term, case=False, na=False) | \
                       df_filtered['subject'].str.contains(search_term, case=False, na=False)
                df_filtered = df_filtered[mask]
            
            st.session_state.filtered_data = df_filtered
            st.success(f"Found {len(df_filtered)} responses")
        
        # Display filtered data and labeling interface
        if hasattr(st.session_state, 'filtered_data') and len(st.session_state.filtered_data) > 0:
            st.markdown("### 📋 Response Labeling")
            
            df_filtered = st.session_state.filtered_data
            
            # Select response to label
            col1, col2 = st.columns([2, 1])
            
            with col1:
                response_ids = df_filtered['response_id'].tolist()
                selected_response = st.selectbox("Select Response to Label", response_ids)
                
                # Show selected response
                if selected_response:
                    response_data = df_filtered[df_filtered['response_id'] == selected_response].iloc[0]
                    
                    st.markdown("**Selected Response:**")
                    st.markdown(f"**Subject:** {response_data.get('subject', 'N/A')}")
                    st.markdown(f"**Company:** {response_data.get('company', 'N/A')}")
                    st.markdown(f"**Response:** {response_data.get('verbatim_response', 'N/A')[:200]}...")
            
            with col2:
                st.markdown("**Add Labels:**")
                
                label_types = ['sentiment', 'priority', 'actionable', 'topic', 'quality']
                selected_label_type = st.selectbox("Label Type", label_types)
                
                if selected_label_type == 'sentiment':
                    label_value = st.selectbox("Sentiment", ['positive', 'negative', 'neutral'])
                elif selected_label_type == 'priority':
                    label_value = st.selectbox("Priority", ['high', 'medium', 'low'])
                elif selected_label_type == 'actionable':
                    label_value = st.selectbox("Actionable", ['yes', 'no', 'maybe'])
                elif selected_label_type == 'topic':
                    label_value = st.selectbox("Topic", ['product', 'process', 'pricing', 'support', 'integration'])
                elif selected_label_type == 'quality':
                    label_value = st.selectbox("Quality", ['excellent', 'good', 'fair', 'poor'])
                else:
                    label_value = st.text_input("Custom Label Value")
                
                if st.button("➕ Add Label", use_container_width=True) and label_value:
                    if st.session_state.db.add_label(selected_response, selected_label_type, label_value):
                        st.success("✅ Label added!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add label")
            
            # Show current labels
            st.markdown("### 🏷️ Current Labels")
            response = st.session_state.db.get_response_by_id(selected_response)
            if response and response.get('labels'):
                labels_data = []
                for label_type, label_data in response['labels'].items():
                    labels_data.append({
                        'Label Type': label_type,
                        'Value': label_data['value'],
                        'Confidence': label_data.get('confidence', 'N/A')
                    })
                st.dataframe(pd.DataFrame(labels_data), use_container_width=True)
            else:
                st.info("No labels added yet")
        
        # Next stage button
        if st.button("➡️ Continue to Export", type="primary", use_container_width=True):
            st.session_state.current_stage = 'export'
            st.rerun()

elif st.session_state.current_stage == 'export':
    st.markdown("## 📊 Export & Analyze")
    st.markdown("Export your processed data for further analysis.")
    
    # Export status
    stats = st.session_state.db.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", stats.get('total_responses', 0))
    with col2:
        st.metric("AI Analyses", stats.get('total_analyses', 0))
    with col3:
        st.metric("Labels", stats.get('total_labels', 0))
    with col4:
        st.metric("Companies", len(stats.get('responses_by_company', {})))
    
    # Export options
    st.markdown("### 📤 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Complete Dataset")
        st.markdown("Export all data with core and enrichment fields:")
        
        if st.button("📥 Export Complete Data", type="primary", use_container_width=True):
            if stats.get('total_responses', 0) > 0:
                df_complete = st.session_state.db.get_responses()
                csv_data = df_complete.to_csv(index=False)
                st.download_button(
                    "Download Complete Dataset",
                    data=csv_data,
                    file_name=f"voc_complete_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
        
        st.markdown("#### 📋 Core Data Only")
        st.markdown("Export only core fields (verbatim responses and metadata):")
        
        if st.button("📥 Export Core Data", use_container_width=True):
            if stats.get('total_responses', 0) > 0:
                df_core = st.session_state.db.get_responses()
                core_cols = ['response_id', 'verbatim_response', 'subject', 'question', 'deal_status', 'company', 'interviewee_name', 'date_of_interview']
                df_core = df_core[core_cols]
                csv_data = df_core.to_csv(index=False)
                st.download_button(
                    "Download Core Data",
                    data=csv_data,
                    file_name=f"voc_core_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    with col2:
        st.markdown("#### 🔍 Filtered Export")
        st.markdown("Export filtered data based on criteria:")
        
        # Filter options
        export_company = st.selectbox("Company", ["All"] + list(stats.get('responses_by_company', {}).keys()), key="export_company")
        export_status = st.selectbox("Deal Status", ["All"] + list(stats.get('responses_by_status', {}).keys()), key="export_status")
        export_search = st.text_input("Search Term", key="export_search")
        
        if st.button("📥 Export Filtered Data", use_container_width=True):
            filters = {}
            if export_company != "All":
                filters['company'] = export_company
            if export_status != "All":
                filters['deal_status'] = export_status
            
            df_filtered = st.session_state.db.get_responses(filters)
            
            if export_search:
                mask = df_filtered['verbatim_response'].str.contains(export_search, case=False, na=False) | \
                       df_filtered['subject'].str.contains(export_search, case=False, na=False)
                df_filtered = df_filtered[mask]
            
            if len(df_filtered) > 0:
                csv_data = df_filtered.to_csv(index=False)
                st.download_button(
                    "Download Filtered Data",
                    data=csv_data,
                    file_name=f"voc_filtered_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data matches your filters")
    
    # Analytics dashboard
    st.markdown("### 📈 Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Response Distribution**")
        if stats.get('responses_by_company'):
            company_data = pd.DataFrame(list(stats['responses_by_company'].items()), columns=['Company', 'Count'])
            st.bar_chart(company_data.set_index('Company'))
        
        if stats.get('responses_by_status'):
            status_data = pd.DataFrame(list(stats['responses_by_status'].items()), columns=['Status', 'Count'])
            st.bar_chart(status_data.set_index('Status'))
    
    with col2:
        st.markdown("**🏷️ Label Summary**")
        if stats.get('total_labels', 0) > 0:
            # Get label statistics
            all_labels = []
            responses = st.session_state.db.get_responses()
            for _, row in responses.iterrows():
                response = st.session_state.db.get_response_by_id(row['response_id'])
                if response and response.get('labels'):
                    for label_type, label_data in response['labels'].items():
                        all_labels.append({
                            'Type': label_type,
                            'Value': label_data['value']
                        })
            
            if all_labels:
                labels_df = pd.DataFrame(all_labels)
                label_counts = labels_df.groupby(['Type', 'Value']).size().reset_index(name='Count')
                st.dataframe(label_counts, use_container_width=True)
        else:
            st.info("No labels added yet")
    
    # Restart workflow
    st.markdown("---")
    if st.button("🔄 Start New Workflow", type="primary", use_container_width=True):
        st.session_state.current_stage = 'upload'
        st.rerun()
