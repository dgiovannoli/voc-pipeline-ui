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

st.title("Buried Wins Fantastical Interview Parser")

# Remove metadata input fields
# st.sidebar.header("Metadata")
# client = st.sidebar.text_input("Client")
# deal_status = st.sidebar.selectbox("Deal Status", ["closed_won", "closed_lost", "no_decision"])
# company = st.sidebar.text_input("Company")
# interviewee_name = st.sidebar.text_input("Interviewee Name")
# date_of_interview = st.sidebar.date_input("Date of Interview", value=date.today())

st.sidebar.info("ℹ️ Metadata is now auto-populated from the pipeline and transcript. No manual entry required.")

st.sidebar.header("1) Upload Interviews")
uploads = st.sidebar.file_uploader(
    "Select .txt or .docx files", type=["txt", "docx"], accept_multiple_files=True
)

# Live CSV loader with TTL
@st.cache_data(ttl=1, show_spinner=False)
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading CSV from {path}: {e}")
        return pd.DataFrame()

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

if uploads:
    # Clear previous uploads and add new ones
    st.session_state.uploaded_paths = []
    
    # Save files silently without showing details
    for f in uploads:
        dest = UPLOAD_DIR / f.name
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        st.session_state.uploaded_paths.append(str(dest))
    
    st.sidebar.success(f"📁 {len(uploads)} files uploaded successfully")
    
    # Move Process button right after upload section
    st.sidebar.markdown("### 2) Process Files")
    
    if st.sidebar.button("▶️ Process Files", use_container_width=True):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stage1_outputs = []
            total_files = len(st.session_state.uploaded_paths)
            
            status_text.text(f"Processing {total_files} files...")
            with ThreadPoolExecutor(max_workers=3) as ex:
                futures = [
                  ex.submit(
                    subprocess.run,
                    [sys.executable, "-m", "voc_pipeline", "process_transcript",
                     path,
                     company if company else "Unknown",  # client
                     company if company else "Unknown",  # company
                     interviewee if interviewee else "Unknown", 
                     "closed_won",  # deal_status
                     "2024-01-01"],  # date_of_interview
                    check=True, capture_output=True, text=True
                  )
                  for path in st.session_state.uploaded_paths
                  for interviewee, company in [extract_interviewee_and_company(os.path.basename(path))]
                ]
                completed = 0
                for f in as_completed(futures):
                    try:
                        result = f.result()
                        st.sidebar.write(f"🔍 Debug: Subprocess return code: {result.returncode}")
                        st.sidebar.write(f"🔍 Debug: Subprocess stdout length: {len(result.stdout)}")
                        st.sidebar.write(f"🔍 Debug: Subprocess stderr: {result.stderr}")
                        stage1_outputs.append(result.stdout)
                        completed += 1
                        progress = completed / total_files
                        progress_bar.progress(progress)
                        status_text.text(f"Processed {completed}/{total_files} files...")
                    except Exception as e:
                        st.warning(f"File failed: {e}")
                        st.sidebar.write(f"🔍 Debug: Exception details: {str(e)}")
                        completed += 1
                        progress = completed / total_files
                        progress_bar.progress(progress)
                        continue
            if stage1_outputs:
                st.sidebar.write(f"🔍 Debug: Got {len(stage1_outputs)} outputs from pipeline")
                for i, output in enumerate(stage1_outputs):
                    st.sidebar.write(f"🔍 Debug: Output {i+1} length: {len(output)} chars")
                    if len(output) > 0:
                        st.sidebar.write(f"🔍 Debug: Output {i+1} preview: {output[:200]}...")
                
                # Combine all outputs into a single CSV file
                if stage1_outputs:
                    st.sidebar.write(f"🔍 Debug: Combining {len(stage1_outputs)} outputs into {STAGE1_CSV}")
                    combined_csv = ""
                    header_written = False
                    
                    for i, output in enumerate(stage1_outputs):
                        if len(output.strip()) > 0:
                            lines = output.strip().split('\n')
                            if not header_written:
                                # Write header from first output
                                combined_csv += lines[0] + '\n'
                                header_written = True
                                # Add data rows from first output
                                for line in lines[1:]:
                                    if line.strip():  # Skip empty lines
                                        combined_csv += line + '\n'
                            else:
                                # Add only data rows (skip header) from subsequent outputs
                                for line in lines[1:]:
                                    if line.strip():  # Skip empty lines
                                        combined_csv += line + '\n'
                    
                    # Write combined output to file
                    with open(STAGE1_CSV, "w") as f:
                        f.write(combined_csv)
                    st.sidebar.write(f"🔍 Debug: Combined output written with {combined_csv.count(chr(10))} lines")
                    
                    # Log summary of processing
                    total_rows = combined_csv.count('\n') - 1  # Subtract header
                    st.sidebar.write(f"🔍 Debug: Total rows processed: {total_rows}")
                    st.sidebar.write(f"🔍 Debug: Files processed: {len([o for o in stage1_outputs if len(o.strip()) > 0])}")
                else:
                    st.sidebar.write("🔍 Debug: No valid output to write")
            else:
                st.warning("No data collected from processing")
                st.sidebar.write("🔍 Debug: stage1_outputs is empty")
            status_text.text("Validating data...")
            progress_bar.progress(0.8)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "validate",
                "--input", str(STAGE1_CSV),
                "--output", str(VALIDATED_CSV)
            ], check=True)
            status_text.text("Building final table...")
            progress_bar.progress(0.9)
            subprocess.run([
                sys.executable, "-m", "voc_pipeline", "build-table",
                "--input", str(VALIDATED_CSV),
                "--output", str(RESPONSE_TABLE_CSV)
            ], check=True)
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ All interviews processed, validated, and table built!")
            st.rerun()
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"❌ Processing failed: {e}")
            st.sidebar.text(f"Error output: {e.stderr}")
            st.sidebar.text(f"Command output: {e.stdout}")
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")
            st.sidebar.text(f"Error details: {str(e)}")
else:
    st.sidebar.write("⚠️ No files uploaded yet")

# Processing Details section (moved to after Process button)
st.sidebar.markdown("---")
st.sidebar.header("3) Processing Details")

# Model details
st.sidebar.markdown("**Model:** OpenAI gpt-3.5-turbo-16k (via LangChain)")

# Estimate time and cost
if uploads:
    num_files = len(uploads)
    total_time = 2.5  # minutes for the whole batch
    avg_tokens_per_file = 2000  # adjust if you have a better estimate
    cost_per_1k = 0.003  # gpt-3.5-turbo-16k pricing
    total_tokens = num_files * avg_tokens_per_file
    total_cost = (total_tokens / 1000) * cost_per_1k
    st.sidebar.markdown(f"**Expected time:** ~{total_time:.1f} min for {num_files} interview(s)")
    st.sidebar.markdown(f"**Expected cost:** ~${total_cost:.4f} for {num_files} interview(s)")
else:
    st.sidebar.markdown("**Expected time:** N/A")
    st.sidebar.markdown("**Expected cost:** N/A")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Database", "📋 Raw Data", "🔧 Processing", "📖 Documentation"])

with tab1:
    st.header("📊 Database Management")
    st.caption("Your centralized data hub - view, filter, label, and export responses.")
    
    # Database statistics
    stats = st.session_state.db.get_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", stats.get('total_responses', 0))
    with col2:
        st.metric("Analysis Results", stats.get('total_analyses', 0))
    with col3:
        st.metric("Labels", stats.get('total_labels', 0))
    with col4:
        st.metric("Companies", len(stats.get('responses_by_company', {})))
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Migrate CSV Data", use_container_width=True):
            if os.path.exists(RESPONSE_TABLE_CSV):
                with st.spinner("Migrating response data..."):
                    count = st.session_state.db.migrate_csv_to_db(str(RESPONSE_TABLE_CSV))
                    st.success(f"✅ Migrated {count} responses!")
                    st.rerun()
            elif os.path.exists(VALIDATED_CSV):
                with st.spinner("Migrating validated quotes..."):
                    count = st.session_state.db.migrate_csv_to_db(str(VALIDATED_CSV))
                    st.success(f"✅ Migrated {count} responses!")
                    st.rerun()
            else:
                st.warning("No CSV data found. Process files first.")
    
    with col2:
        if st.button("📥 Export All Data", use_container_width=True):
            if stats.get('total_responses', 0) > 0:
                csv_data = st.session_state.db.get_responses().to_csv(index=False)
                st.download_button(
                    "Download Complete Dataset",
                    data=csv_data,
                    file_name=f"voc_database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    with col3:
        if st.button("📊 View Statistics", use_container_width=True):
            st.session_state.show_stats = True
    
    # Show detailed statistics if requested
    if hasattr(st.session_state, 'show_stats') and st.session_state.show_stats:
        st.subheader("📈 Detailed Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            if stats.get('responses_by_company'):
                st.write("**Responses by Company:**")
                for company, count in stats['responses_by_company'].items():
                    st.write(f"• {company}: {count}")
        
        with col2:
            if stats.get('responses_by_status'):
                st.write("**Responses by Deal Status:**")
                for status, count in stats['responses_by_status'].items():
                    st.write(f"• {status}: {count}")
    
    # Data exploration section
    st.subheader("🔍 Explore Data")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        companies = ["All"] + list(stats.get('responses_by_company', {}).keys())
        selected_company = st.selectbox("Company", companies)
    with col2:
        deal_statuses = ["All"] + list(stats.get('responses_by_status', {}).keys())
        selected_status = st.selectbox("Deal Status", deal_statuses)
    with col3:
        search_term = st.text_input("Search Responses", placeholder="Enter keywords...")
    with col4:
        if st.button("🔍 Apply Filters", use_container_width=True):
            filters = {}
            if selected_company != "All":
                filters['company'] = selected_company
            if selected_status != "All":
                filters['deal_status'] = selected_status
            
            # Get filtered data
            df_db = st.session_state.db.get_responses(filters)
            
            # Apply text search if provided
            if search_term:
                mask = df_db['verbatim_response'].str.contains(search_term, case=False, na=False) | \
                       df_db['subject'].str.contains(search_term, case=False, na=False)
                df_db = df_db[mask]
            
            st.session_state.filtered_db_data = df_db
            st.success(f"Found {len(df_db)} responses")
    
    # Display filtered data
    if hasattr(st.session_state, 'filtered_db_data') and len(st.session_state.filtered_db_data) > 0:
        st.subheader("📋 Results")
        df_db = st.session_state.filtered_db_data
        
        # Show key columns
        display_cols = ['response_id', 'subject', 'verbatim_response', 'company', 'deal_status', 'created_at']
        available_cols = [col for col in display_cols if col in df_db.columns]
        
        if available_cols:
            # Truncate verbatim response for display
            display_df = df_db[available_cols].copy()
            if 'verbatim_response' in display_df.columns:
                display_df['verbatim_response'] = display_df['verbatim_response'].str[:100] + "..."
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export filtered results
            if st.button("📥 Export Filtered Results"):
                csv_data = df_db.to_csv(index=False)
                st.download_button(
                    "Download Filtered Data",
                    data=csv_data,
                    file_name=f"filtered_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Labeling section
    st.subheader("🏷️ Add Labels")
    
    if hasattr(st.session_state, 'filtered_db_data') and len(st.session_state.filtered_db_data) > 0:
        df_db = st.session_state.filtered_db_data
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            response_ids = df_db['response_id'].tolist()
            selected_response = st.selectbox("Select Response", response_ids)
        with col2:
            label_types = ['sentiment', 'priority', 'actionable', 'topic', 'quality', 'custom']
            selected_label_type = st.selectbox("Label Type", label_types)
        with col3:
            if selected_label_type == 'sentiment':
                label_values = st.selectbox("Label Value", ['positive', 'negative', 'neutral'])
            elif selected_label_type == 'priority':
                label_values = st.selectbox("Label Value", ['high', 'medium', 'low'])
            elif selected_label_type == 'actionable':
                label_values = st.selectbox("Label Value", ['yes', 'no', 'maybe'])
            else:
                label_values = st.text_input("Label Value")
        with col4:
            if st.button("➕ Add Label", use_container_width=True) and label_values:
                if st.session_state.db.add_label(selected_response, selected_label_type, label_values):
                    st.success("✅ Label added!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add label")
    else:
        st.info("Filter data first to add labels")
    
    # Show current labels
    if hasattr(st.session_state, 'filtered_db_data') and len(st.session_state.filtered_db_data) > 0:
        st.subheader("🏷️ Current Labels")
        
        # Get labels for displayed responses
        response_ids = st.session_state.filtered_db_data['response_id'].tolist()
        all_labels = []
        
        for response_id in response_ids[:10]:  # Limit to first 10 for performance
            response = st.session_state.db.get_response_by_id(response_id)
            if response and response.get('labels'):
                for label_type, label_data in response['labels'].items():
                    all_labels.append({
                        'response_id': response_id,
                        'label_type': label_type,
                        'label_value': label_data['value'],
                        'confidence': label_data['confidence']
                    })
        
        if all_labels:
            labels_df = pd.DataFrame(all_labels)
            st.dataframe(labels_df, use_container_width=True)
        else:
            st.info("No labels found for displayed responses")

with tab2:
    st.header("📋 Raw Data Files")
    st.caption("View and manage your raw CSV data files with the new normalized structure.")
    
    # File status overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        stage1_exists = os.path.exists(STAGE1_CSV) and os.path.getsize(STAGE1_CSV) > 0
        st.metric("Stage 1 Output", 
                 f"{len(load_csv(STAGE1_CSV)) if stage1_exists else 0} rows",
                 "✅ Core Fields" if stage1_exists else "❌ Empty")
    
    with col2:
        validated_exists = os.path.exists(VALIDATED_CSV) and os.path.getsize(VALIDATED_CSV) > 0
        st.metric("Validated Quotes", 
                 f"{len(load_csv(VALIDATED_CSV)) if validated_exists else 0} rows",
                 "✅ Core Fields" if validated_exists else "❌ Empty")
    
    with col3:
        response_exists = os.path.exists(RESPONSE_TABLE_CSV) and os.path.getsize(RESPONSE_TABLE_CSV) > 0
        st.metric("Response Table", 
                 f"{len(load_csv(RESPONSE_TABLE_CSV)) if response_exists else 0} rows",
                 "✅ Complete" if response_exists else "❌ Empty")
    
    with col4:
        db_count = st.session_state.db.get_stats().get('total_responses', 0)
        st.metric("Database", 
                 f"{db_count} responses",
                 "✅ Normalized" if db_count > 0 else "❌ Empty")
    
    # Core Data Files (Stage 1 and Validated)
    st.subheader("📄 Core Data Files")
    st.info("These files contain only the essential fields (Response ID, Verbatim Response, Subject, Question, Deal Status, Company Name, Interviewee Name, Date of Interview). Enrichment fields are stored separately in the database.")
    
    core_file_options = {
        "Stage 1 Output (Core Fields Only)": STAGE1_CSV,
        "Validated Quotes (Core Fields Only)": VALIDATED_CSV
    }
    
    selected_core_file = st.selectbox("Select core data file:", list(core_file_options.keys()))
    selected_core_path = core_file_options[selected_core_file]
    
    if os.path.exists(selected_core_path) and os.path.getsize(selected_core_path) > 0:
        try:
            df = load_csv(selected_core_path)
            if len(df) > 0:
                st.write(f"**{selected_core_file}** - {len(df)} rows, {len(df.columns)} columns")
                st.write("**Core Fields:** " + ", ".join(df.columns.tolist()))
                
                # Show sample data
                st.dataframe(df.head(50), use_container_width=True)
                
                # Download option
                csv_data = df.to_csv(index=False)
                st.download_button(
                    f"📥 Download {selected_core_file}",
                    data=csv_data,
                    file_name=f"{selected_core_file.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Column info
                with st.expander("📊 Column Information"):
                    col_info = []
                    for col in df.columns:
                        non_null = df[col].notna().sum()
                        null_pct = (len(df) - non_null) / len(df) * 100
                        col_info.append({
                            'Column': col,
                            'Non-Null Count': non_null,
                            'Null Percentage': f"{null_pct:.1f}%",
                            'Data Type': str(df[col].dtype)
                        })
                    st.dataframe(pd.DataFrame(col_info))
                
            else:
                st.warning(f"{selected_core_file} is empty")
        except Exception as e:
            st.error(f"Error reading {selected_core_file}: {e}")
    else:
        st.info(f"{selected_core_file} not found or empty")
    
    # Enriched Data Files (Complete with all fields)
    st.subheader("🔍 Enriched Data Files")
    st.info("These files contain the complete dataset with both core fields and enrichment fields (AI-generated insights, labels, quality metrics).")
    
    enriched_file_options = {
        "Response Data Table (Complete with Enrichment)": RESPONSE_TABLE_CSV
    }
    
    selected_enriched_file = st.selectbox("Select enriched data file:", list(enriched_file_options.keys()))
    selected_enriched_path = enriched_file_options[selected_enriched_file]
    
    if os.path.exists(selected_enriched_path) and os.path.getsize(selected_enriched_path) > 0:
        try:
            df = load_csv(selected_enriched_path)
            if len(df) > 0:
                st.write(f"**{selected_enriched_file}** - {len(df)} rows, {len(df.columns)} columns")
                
                # Separate core and enrichment columns
                core_columns = ['Response ID', 'Verbatim Response', 'Subject', 'Question', 'Deal Status', 'Company Name', 'Interviewee Name', 'Date of Interview']
                enrichment_columns = [col for col in df.columns if col not in core_columns]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Core Fields:** " + ", ".join(core_columns))
                with col2:
                    st.write("**Enrichment Fields:** " + ", ".join(enrichment_columns))
                
                # Show sample data
                st.dataframe(df.head(50), use_container_width=True)
                
                # Download option
                csv_data = df.to_csv(index=False)
                st.download_button(
                    f"📥 Download {selected_enriched_file}",
                    data=csv_data,
                    file_name=f"{selected_enriched_file.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Column info
                with st.expander("📊 Column Information"):
                    col_info = []
                    for col in df.columns:
                        non_null = df[col].notna().sum()
                        null_pct = (len(df) - non_null) / len(df) * 100
                        col_type = "Core" if col in core_columns else "Enrichment"
                        col_info.append({
                            'Column': col,
                            'Type': col_type,
                            'Non-Null Count': non_null,
                            'Null Percentage': f"{null_pct:.1f}%",
                            'Data Type': str(df[col].dtype)
                        })
                    st.dataframe(pd.DataFrame(col_info))
                
            else:
                st.warning(f"{selected_enriched_file} is empty")
        except Exception as e:
            st.error(f"Error reading {selected_enriched_file}: {e}")
    else:
        st.info(f"{selected_enriched_file} not found or empty")
    
    # Database Export (Normalized Structure)
    st.subheader("🗄️ Database Export")
    st.info("Export data from the normalized database structure with proper separation of core and enrichment fields.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Core Data Only", use_container_width=True):
            if st.session_state.db.get_stats().get('total_responses', 0) > 0:
                # Get only core fields from database
                df_core = st.session_state.db.get_responses()
                core_cols = ['response_id', 'verbatim_response', 'subject', 'question', 'deal_status', 'company', 'interviewee_name', 'date_of_interview']
                df_core = df_core[core_cols]
                
                csv_data = df_core.to_csv(index=False)
                st.download_button(
                    "Download Core Data",
                    data=csv_data,
                    file_name=f"core_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data in database")
    
    with col2:
        if st.button("📥 Export Complete Data", use_container_width=True):
            if st.session_state.db.get_stats().get('total_responses', 0) > 0:
                # Get complete data with enrichment fields
                df_complete = st.session_state.db.get_responses()
                
                csv_data = df_complete.to_csv(index=False)
                st.download_button(
                    "Download Complete Data",
                    data=csv_data,
                    file_name=f"complete_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data in database")
    
    # Manual processing controls
    st.subheader("🔧 Manual Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Validate Stage 1 Output", use_container_width=True):
            if os.path.exists(STAGE1_CSV):
                try:
                    with st.spinner("Validating data..."):
                        subprocess.run([
                            sys.executable, "-m", "voc_pipeline", "validate",
                            "--input", str(STAGE1_CSV),
                            "--output", str(VALIDATED_CSV)
                        ], check=True, capture_output=True, text=True)
                    st.success("✅ Validation complete!")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error(f"❌ Validation failed: {e}")
            else:
                st.warning("No Stage 1 output found")
    
    with col2:
        if st.button("🔧 Build Response Table", use_container_width=True):
            if os.path.exists(VALIDATED_CSV):
                try:
                    with st.spinner("Building response table..."):
                        subprocess.run([
                            sys.executable, "-m", "voc_pipeline", "build-table",
                            "--input", str(VALIDATED_CSV),
                            "--output", str(RESPONSE_TABLE_CSV)
                        ], check=True, capture_output=True, text=True)
                    st.success("✅ Response table built!")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error(f"❌ Build failed: {e}")
            else:
                st.warning("No validated quotes found")

with tab3:
    st.header("🔧 Processing Pipeline")
    st.caption("Process interview files and manage the AI pipeline.")
    
    # Processing status
    st.subheader("📊 Processing Status")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        upload_count = len(st.session_state.uploaded_paths) if hasattr(st.session_state, 'uploaded_paths') else 0
        st.metric("Files Uploaded", upload_count, "Ready to process" if upload_count > 0 else "No files")
    
    with col2:
        stage1_count = len(load_csv(STAGE1_CSV)) if os.path.exists(STAGE1_CSV) else 0
        st.metric("Stage 1 Output", stage1_count, "✅ Complete" if stage1_count > 0 else "❌ Pending")
    
    with col3:
        db_count = st.session_state.db.get_stats().get('total_responses', 0)
        st.metric("In Database", db_count, "✅ Migrated" if db_count > 0 else "❌ Not migrated")
    
    # File processing
    st.subheader("🔄 Process Files")
    
    if uploads:
        st.success(f"📁 {len(uploads)} files uploaded successfully")
        
        # Show uploaded files
        with st.expander("📋 Uploaded Files"):
            for i, path in enumerate(st.session_state.uploaded_paths):
                filename = os.path.basename(path)
                interviewee, company = extract_interviewee_and_company(filename)
                st.write(f"{i+1}. **{filename}**")
                st.write(f"   - Interviewee: {interviewee}")
                st.write(f"   - Company: {company}")
        
        # Process button
        if st.button("▶️ Process All Files", use_container_width=True, type="primary"):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                stage1_outputs = []
                total_files = len(st.session_state.uploaded_paths)
                
                status_text.text(f"Processing {total_files} files...")
                with ThreadPoolExecutor(max_workers=3) as ex:
                    futures = [
                      ex.submit(
                        subprocess.run,
                        [sys.executable, "-m", "voc_pipeline", "process_transcript",
                         path,
                         company if company else "Unknown",  # client
                         company if company else "Unknown",  # company
                         interviewee if interviewee else "Unknown", 
                         "closed_won",  # deal_status
                         "2024-01-01"],  # date_of_interview
                        check=True, capture_output=True, text=True
                      )
                      for path in st.session_state.uploaded_paths
                      for interviewee, company in [extract_interviewee_and_company(os.path.basename(path))]
                    ]
                    completed = 0
                    for f in as_completed(futures):
                        try:
                            result = f.result()
                            stage1_outputs.append(result.stdout)
                            completed += 1
                            progress = completed / total_files
                            progress_bar.progress(progress)
                            status_text.text(f"Processed {completed}/{total_files} files...")
                        except Exception as e:
                            st.warning(f"File failed: {e}")
                            completed += 1
                            progress = completed / total_files
                            progress_bar.progress(progress)
                            continue
                
                if stage1_outputs:
                    # Combine outputs
                    combined_csv = ""
                    header_written = False
                    
                    for output in stage1_outputs:
                        if len(output.strip()) > 0:
                            lines = output.strip().split('\n')
                            if not header_written:
                                combined_csv += lines[0] + '\n'
                                header_written = True
                                for line in lines[1:]:
                                    if line.strip():
                                        combined_csv += line + '\n'
                            else:
                                for line in lines[1:]:
                                    if line.strip():
                                        combined_csv += line + '\n'
                    
                    # Write combined output
                    with open(STAGE1_CSV, "w") as f:
                        f.write(combined_csv)
                    
                    # Run validation and table building
                    status_text.text("Validating data...")
                    progress_bar.progress(0.8)
                    subprocess.run([
                        sys.executable, "-m", "voc_pipeline", "validate",
                        "--input", str(STAGE1_CSV),
                        "--output", str(VALIDATED_CSV)
                    ], check=True)
                    
                    status_text.text("Building final table...")
                    progress_bar.progress(0.9)
                    subprocess.run([
                        sys.executable, "-m", "voc_pipeline", "build-table",
                        "--input", str(VALIDATED_CSV),
                        "--output", str(RESPONSE_TABLE_CSV)
                    ], check=True)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Complete!")
                    st.success("✅ All interviews processed successfully!")
                    st.rerun()
                else:
                    st.warning("No data collected from processing")
                    
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Processing failed: {e}")
                st.text(f"Error output: {e.stderr}")
            except Exception as e:
                st.error(f"🔴 Unexpected error: {e}")
    else:
        st.info("⚠️ No files uploaded yet. Use the sidebar to upload interview files.")
    
    # Pipeline configuration
    st.subheader("⚙️ Pipeline Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Model Details:**")
        st.write("• **Model:** OpenAI gpt-3.5-turbo-16k")
        st.write("• **Chunk Size:** ~7K tokens")
        st.write("• **Insights per chunk:** 1-2")
        st.write("• **Processing:** Parallel with ThreadPoolExecutor")
    
    with col2:
        if uploads:
            num_files = len(uploads)
            total_time = 2.5  # minutes for the whole batch
            avg_tokens_per_file = 2000
            cost_per_1k = 0.003
            total_tokens = num_files * avg_tokens_per_file
            total_cost = (total_tokens / 1000) * cost_per_1k
            
            st.markdown("**Estimated Processing:**")
            st.write(f"• **Time:** ~{total_time:.1f} min for {num_files} file(s)")
            st.write(f"• **Cost:** ~${total_cost:.4f}")
            st.write(f"• **Tokens:** ~{total_tokens:,}")
        else:
            st.markdown("**Estimated Processing:**")
            st.write("• **Time:** N/A")
            st.write("• **Cost:** N/A")
            st.write("• **Tokens:** N/A")

with tab4:
    st.header("📖 Documentation & Help")
    st.caption("Learn how to use the VOC pipeline and database.")
    
    # Documentation sections
    tab_docs, tab_prompt, tab_schema = st.tabs(["📚 User Guide", "🤖 AI Prompt", "🏗️ Database Schema"])
    
    with tab_docs:
        st.subheader("🚀 Quick Start Guide")
        
        st.markdown("""
        ### **Step 1: Upload Files**
        1. Use the sidebar to upload interview files (.txt or .docx)
        2. Files are automatically saved and ready for processing
        
        ### **Step 2: Process Files**
        1. Go to the **🔧 Processing Pipeline** tab
        2. Click **"▶️ Process All Files"** to run the AI pipeline
        3. Wait for processing to complete (usually 2-3 minutes)
        
        ### **Step 3: Migrate to Database**
        1. Go to the **📊 Database** tab
        2. Click **"🔄 Migrate CSV Data"** to import processed data
        3. Your data is now in the database and ready for analysis
        
        ### **Step 4: Explore & Label**
        1. Use filters to find specific responses
        2. Add labels to categorize responses
        3. Export filtered data for further analysis
        """)
        
        st.subheader("💡 Pro Tips")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **File Naming:**
            - Use descriptive names like "Interview with John Smith at TechCorp.docx"
            - The system will auto-extract interviewee and company names
            
            **Processing:**
            - Process multiple files at once for efficiency
            - Each file is processed independently
            - Results are combined automatically
            """)
        
        with col2:
            st.markdown("""
            **Database Usage:**
            - Start with simple labels like sentiment
            - Use filters to find specific responses quickly
            - Export data regularly for backup
            
            **Troubleshooting:**
            - Check the **📋 Raw Data Files** tab if processing fails
            - Use manual validation if needed
            - Database is persistent - your data is safe
            """)
    
    with tab_prompt:
        st.subheader("🤖 AI Prompt Template")
        st.markdown("Below is the exact prompt sent to the AI for each interview chunk. You can review and suggest improvements.")
        prompt_template_text = '''
CRITICAL INSTRUCTIONS FOR ENHANCED QUALITY ANALYSIS:
- You have access to focused context windows (~7K tokens) containing 6-8 Q&A exchanges.
- Extract the 1-2 RICHEST, MOST DETAILED insights from this chunk, prioritizing:
  1. **Comprehensive Customer Experiences**: Complete scenarios with full context, specific examples, detailed explanations, and quantitative details
  2. **Quantitative Feedback**: Specific metrics, timelines, ROI discussions, pricing details, accuracy percentages, workload distributions
  3. **Comparative Analysis**: Before/after comparisons, competitive evaluations with specific differentiators and performance metrics
  4. **Integration Requirements**: Workflow details, tool integration needs, process changes, technical specifications
  5. **Strategic Perspectives**: Decision factors, risk assessments, future planning, business impact

EXTRACTION STRATEGY:
- Identify the 1-2 richest, most comprehensive responses in this chunk
- Extract the COMPLETE verbatim response for each with full context and conversation flow
- Create comprehensive key insights that capture the main themes and specific details
- Focus on responses that provide complete context and detailed explanations
- Choose responses that cover different aspects or themes when possible
- If only one high-quality response exists, extract just that one
- Prioritize responses with specific examples, metrics, and actionable insights

VERBATIM RESPONSE RULES:
- Include the COMPLETE response text (300-800 words for optimal context and richness)
- Preserve ALL context, examples, specific details, and quantitative information
- Include relevant parts of the conversation flow for better understanding
- Include follow-up questions and clarifications that add context
- Remove only speaker labels, timestamps, and interviewer prompts
- Keep filler words if they add emphasis or meaning
- Maintain the natural flow and structure of the response
- Include specific examples, metrics, detailed explanations, and follow-up context
- Preserve comparative language and specific differentiators
- Include workflow details, process descriptions, and technical specifications

QUALITY-FOCUSED INSIGHTS:
- Extract the 1-2 most comprehensive insights from the richest responses
- Focus on responses that provide complete context and detailed explanations
- Ensure each verbatim response captures the full conversation context
- Choose responses that cover different topics or perspectives when possible
- Only extract if the response contains substantial, actionable content
- Prioritize responses with specific metrics, examples, and detailed workflows

DIFFERENTIATION STRATEGY:
- When multiple responses cover similar topics, extract the most detailed and specific one
- Focus on responses that provide unique perspectives or specific examples
- Include responses that show different aspects of the same topic (e.g., different use cases, workflows, or pain points)
- Prioritize responses with quantitative details, specific processes, or technical specifications
- Choose responses that provide the most complete picture of customer experiences

Analyze the provided interview chunk and extract the 1-2 RICHEST, MOST COMPREHENSIVE insights from the most detailed responses. Return ONLY a JSON array containing one or two objects:

[
  {
    "response_id": "{response_id}_1",
    "key_insight": "first_comprehensive_insight_summary_with_specific_details",
    "verbatim_response": "first_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_1",
    "question": "what_question_this_answers_1",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}",
    "findings": "key_finding_summary_with_specific_details_1",
    "value_realization": "value_or_roi_metrics_with_quantitative_details_1",
    "implementation_experience": "implementation_details_with_workflow_specifics_1",
    "risk_mitigation": "risk_mitigation_approaches_with_specific_strategies_1",
    "competitive_advantage": "competitive_positioning_with_specific_differentiators_1",
    "customer_success": "customer_success_factors_with_measurable_outcomes_1",
    "product_feedback": "product_feature_feedback_with_specific_examples_1",
    "service_quality": "service_quality_assessment_with_quantitative_metrics_1",
    "decision_factors": "decision_influencing_factors_with_specific_criteria_1",
    "pain_points": "challenges_or_pain_points_with_detailed_context_1",
    "success_metrics": "success_criteria_and_metrics_with_specific_measurements_1",
    "future_plans": "future_plans_or_expansion_with_specific_timelines_1"
  },
  {
    "response_id": "{response_id}_2",
    "key_insight": "second_comprehensive_insight_summary_with_specific_details",
    "verbatim_response": "second_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_2",
    "question": "what_question_this_answers_2",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}",
    "findings": "key_finding_summary_with_specific_details_2",
    "value_realization": "value_or_roi_metrics_with_quantitative_details_2",
    "implementation_experience": "implementation_details_with_workflow_specifics_2",
    "risk_mitigation": "risk_mitigation_approaches_with_specific_strategies_2",
    "competitive_advantage": "competitive_positioning_with_specific_differentiators_2",
    "customer_success": "customer_success_factors_with_measurable_outcomes_2",
    "product_feedback": "product_feature_feedback_with_specific_examples_2",
    "service_quality": "service_quality_assessment_with_quantitative_metrics_2",
    "decision_factors": "decision_influencing_factors_with_specific_criteria_2",
    "pain_points": "challenges_or_pain_points_with_detailed_context_2",
    "success_metrics": "success_criteria_and_metrics_with_specific_measurements_2",
    "future_plans": "future_plans_or_expansion_with_specific_timelines_2"
  }
]

Guidelines:
- Extract the 1-2 richest, most comprehensive insights per chunk
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making, Workflow Optimization
- Use "N/A" for fields that don't apply
- Ensure all fields are populated with specific, actionable content
- Return ONLY the JSON array, no other text
- Focus on responses with specific examples, metrics, detailed explanations, and full context
- Choose responses that provide the most complete picture and actionable insights
- If only one rich insight exists, return an array with just one object
- Skip chunks that only contain low-quality content (acknowledgments, thank yous, etc.)
- Prioritize responses that show different aspects of similar topics (e.g., different use cases, workflows, or specific pain points)
'''
        st.code(prompt_template_text, language="markdown")
        
        st.subheader("🔧 Pipeline Details")
        st.markdown("""
        **How the pipeline processes your interviews (16K-optimized version):**

        - **Batching & Parallel Processing:**
          - Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor` for speed and efficiency.
          - Each file is handled as a separate job, so you can upload and process many interviews at once.

        - **Advanced Chunking & Segmentation (16K Optimized):**
          - Uses token-based chunking with ~7K tokens per chunk
          - Q&A-aware segmentation that preserves conversation boundaries and context
          - Intelligent overlap of 800 tokens to maintain continuity between chunks
          - Preserves full Q&A exchanges and speaker turns within chunks

        - **Enhanced LLM Processing:**
          - Each large chunk is sent to GPT-3.5-turbo-16k with comprehensive context
          - Extracts 1-2 insights per chunk for optimal quality
          - Preserves longer verbatim responses (300-800 words)
          - Focuses on detailed customer experiences, quantitative feedback, and specific examples

        - **Quality Assurance:**
          - Enhanced validation for richer, more contextually complete responses
          - Quality logging tracks response length and content preservation
          - Flags responses that lose too much context during processing
        """)
    
    with tab_schema:
        st.subheader("🏗️ Database Schema")
        st.markdown("""
        The database uses a normalized design with 4 main tables:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📋 responses** (Source of Truth)
            - `response_id` (PRIMARY KEY)
            - `verbatim_response` (TEXT)
            - `subject`, `question`
            - `deal_status`, `company`, `interviewee_name`
            - `date_of_interview`, `created_at`, `updated_at`
            
            **🔍 analysis_results** (AI Insights)
            - `id` (PRIMARY KEY)
            - `response_id` (FOREIGN KEY)
            - `analysis_type` (findings, value_realization, etc.)
            - `analysis_text` (TEXT)
            - `model_version`, `confidence_score`
            """)
        
        with col2:
            st.markdown("""
            **🏷️ response_labels** (Manual/AI Labels)
            - `id` (PRIMARY KEY)
            - `response_id` (FOREIGN KEY)
            - `label_type`, `label_value`
            - `confidence_score`, `labeled_by`
            
            **📊 quality_metrics** (Quality Tracking)
            - `id` (PRIMARY KEY)
            - `response_id` (FOREIGN KEY)
            - `metric_type`, `metric_value`
            - `metric_details` (JSON)
            """)
        
        st.markdown("""
        **Key Benefits:**
        - **Data Integrity**: Raw responses never change
        - **Flexibility**: Add new labels and metrics without schema changes
        - **Performance**: Indexed for fast queries
        - **Audit Trail**: Track all changes and additions
        - **Scalability**: Easy to add new analysis types and labels
        """)
