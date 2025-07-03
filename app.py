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

load_dotenv()

BASE = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
VALIDATED_CSV = BASE / "validated_quotes.csv"
PASSTHROUGH_CSV = BASE / "passthrough_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"
STAGE1_CSV = BASE / "stage1_output.csv"

# Initialize uploaded_paths list in session state
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

# Model and cost info
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
    st.sidebar.write(f"📁 Uploads detected: {len(uploads)} files")
    for f in uploads:
        st.sidebar.write(f"  📄 {f.name} (size: {len(f.getbuffer())} bytes)")
        dest = UPLOAD_DIR / f.name
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        st.session_state.uploaded_paths.append(str(dest))
        st.sidebar.write(f"  💾 Saved to: {dest}")
    st.sidebar.success(f"🗄️ Saved {len(st.session_state.uploaded_paths)} file(s)")
    
    st.sidebar.markdown("---")
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
                
                # Write the first output directly to file (it's already a complete CSV)
                if stage1_outputs and len(stage1_outputs[0]) > 0:
                    st.sidebar.write(f"🔍 Debug: Writing pipeline output directly to {STAGE1_CSV}")
                    with open(STAGE1_CSV, "w") as f:
                        f.write(stage1_outputs[0])
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

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["Validated Quotes", "Response Data Table", "Prompt Template", "Processing Details"])

with tab1:
    st.header("Validated Quotes")
    st.caption("Main columns only. Metadata is auto-populated.")
    
    # Check if file exists and has content
    file_exists = os.path.exists(VALIDATED_CSV)
    file_size = os.path.getsize(VALIDATED_CSV) if file_exists else 0
    
    if file_exists and file_size > 0:
        try:
            df = load_csv(VALIDATED_CSV)
            
            if len(df) > 0:
                st.write(f"Showing {len(df)} validated quotes")
                
                # Define the columns we want to show, with fallbacks
                display_cols = []
                col_mapping = {
                    "Response ID": ["Response ID"],
                    "Subject": ["Subject"],
                    "Key Insight": ["Key Insight", "Findings"],  # Fallback to Findings if Key Insight missing
                    "Question": ["Question"],
                    "Verbatim Response": ["Verbatim Response"],
                    "Deal Status": ["Deal Status"],
                    "Company Name": ["Company Name"],
                    "Interviewee Name": ["Interviewee Name"],
                    "Date of Interview": ["Date of Interview"]
                }
                
                # Find available columns for each desired column
                for desired_col, possible_names in col_mapping.items():
                    found = False
                    for possible_name in possible_names:
                        if possible_name in df.columns:
                            display_cols.append(possible_name)
                            found = True
                            break
                    if not found:
                        st.warning(f"Column '{desired_col}' not found in data")
                
                if display_cols:
                    st.dataframe(df[display_cols])
                    if len(df) > 200:
                        st.info(f"Showing first 200 of {len(df)} records")
                else:
                    st.error("No displayable columns found")
                    st.write("Available columns:", list(df.columns))
            else:
                st.warning("Validated quotes file is empty")
                if os.path.exists(STAGE1_CSV):
                    df = load_csv(STAGE1_CSV)
                    st.write(f"Showing {len(df)} raw quotes (fallback)")
                    st.dataframe(df.head(200))
                else:
                    st.info("No data available. Upload & Process to get started.")
        except Exception as e:
            st.error(f"Error reading validated quotes: {e}")
            if os.path.exists(STAGE1_CSV):
                df = load_csv(STAGE1_CSV)
                st.write(f"Showing {len(df)} raw quotes (fallback)")
                st.dataframe(df.head(200))
            else:
                st.info("No data available. Upload & Process to get started.")
    else:
        if os.path.exists(STAGE1_CSV):
            df = load_csv(STAGE1_CSV)
            st.write(f"Showing {len(df)} raw quotes")
            st.dataframe(df.head(200))
            
            # Add manual validation button
            if st.button("🔧 Manual Validate"):
                try:
                    st.write("Running manual validation...")
                    subprocess.run([
                        sys.executable, "-m", "voc_pipeline", "validate",
                        "--input", str(STAGE1_CSV),
                        "--output", str(VALIDATED_CSV)
                    ], check=True, capture_output=True, text=True)
                    st.success("Manual validation complete!")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error(f"Manual validation failed: {e}")
                    st.write(f"Error output: {e.stderr}")
        else:
            st.info("No data available. Upload & Process to get started.")

with tab2:
    st.header("Response Data Table")
    st.caption("Full table with all columns.")
    if os.path.exists(RESPONSE_TABLE_CSV) and os.path.getsize(RESPONSE_TABLE_CSV) > 0:
        try:
            df2 = load_csv(RESPONSE_TABLE_CSV)
            if len(df2) > 0:
                st.write(f"Showing {len(df2)} response records")
                st.dataframe(df2)
                st.download_button(
                    "Download Response Table",
                    data=df2.to_csv(index=False),
                    file_name="response_data_table.csv"
                )
            else:
                st.warning("Response data table is empty")
        except Exception as e:
            st.error(f"Error reading response data table: {e}")
            st.info("The CSV file may be malformed. Try regenerating it.")
    else:
        st.info("Run the pipeline to generate the response data table.")

with tab3:
    st.header("Prompt Template")
    st.markdown("Below is the exact prompt sent to the AI for each interview chunk. You can review and suggest improvements.")
    prompt_template_text = '''
CRITICAL INSTRUCTIONS FOR 16K CONTEXT ANALYSIS:
- You now have access to much larger context windows (~12K tokens) containing multiple Q&A exchanges.
- Extract the 2-3 MOST SIGNIFICANT insights from this chunk, prioritizing:
  1. **Detailed Customer Experiences**: Specific scenarios, use cases, implementation stories with concrete examples
  2. **Quantitative Feedback**: Specific metrics, timelines, ROI discussions, pricing details, accuracy percentages
  3. **Comparative Analysis**: Before/after comparisons, competitive evaluations with specific differentiators
  4. **Integration Requirements**: Workflow details, tool integration needs, process changes
  5. **Strategic Perspectives**: Decision factors, risk assessments, future planning

EXTRACTION STRATEGY:
- Identify the 2-3 richest, most detailed responses in this chunk
- Extract the COMPLETE verbatim response for each (preserve full context)
- Create comprehensive key insights that capture the main themes and specific details
- If multiple responses are equally rich, choose those with the most actionable insights

VERBATIM RESPONSE RULES:
- Include the COMPLETE response text (much longer than before - 200-500 words)
- Preserve ALL context, examples, specific details, and quantitative information
- Remove only speaker labels, timestamps, and interviewer prompts
- Keep filler words if they add emphasis or meaning
- Maintain the natural flow and structure of the response
- Include specific examples, metrics, and detailed explanations

MULTIPLE INSIGHTS PER CHUNK:
- Extract 2-3 separate insights if the chunk contains multiple rich responses
- Each insight should focus on a different aspect or theme
- Ensure each verbatim response is complete and contextually rich

Analyze the provided interview chunk and extract the 2-3 MOST SIGNIFICANT insights from the richest responses. Return ONLY a valid JSON object with this structure:

{
  "response_id": "{response_id}",
  "key_insight": "{key_insight}",
  "verbatim_response": "{chunk_text}",
  "subject": "brief_subject_description",
  "question": "what_question_this_answers",
  "deal_status": "{deal_status}",
  "company": "{company}",
  "interviewee_name": "{interviewee_name}",
  "date_of_interview": "{date_of_interview}",
  "findings": "key_finding_summary",
  "value_realization": "value_or_roi_metrics",
  "implementation_experience": "implementation_details",
  "risk_mitigation": "risk_mitigation_approaches",
  "competitive_advantage": "competitive_positioning",
  "customer_success": "customer_success_factors",
  "product_feedback": "product_feature_feedback",
  "service_quality": "service_quality_assessment",
  "decision_factors": "decision_influencing_factors",
  "pain_points": "challenges_or_pain_points",
  "success_metrics": "success_criteria_and_metrics",
  "future_plans": "future_plans_or_expansion"
}

Guidelines:
- Extract 2-3 primary insights per chunk when multiple rich responses exist
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making
- Use "N/A" for fields that don't apply
- Ensure all fields are populated
- Return ONLY the JSON object, no other text
- Focus on responses with specific examples, metrics, and detailed explanations
'''
    st.code(prompt_template_text, language="markdown")

with tab4:
    st.header("Processing Details")
    st.markdown("""
**How the pipeline processes your interviews (16K-optimized version):**

- **Batching & Parallel Processing:**
  - Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor` for speed and efficiency.
  - Each file is handled as a separate job, so you can upload and process many interviews at once.

- **Advanced Chunking & Segmentation (16K Optimized):**
  - Uses token-based chunking with ~12K tokens per chunk (vs previous 2K character chunks)
  - Q&A-aware segmentation that preserves conversation boundaries and context
  - Intelligent overlap of 800 tokens to maintain continuity between chunks
  - Preserves full Q&A exchanges and speaker turns within chunks
  - Adaptive chunking that respects token limits while maximizing context

- **Enhanced LLM Processing:**
  - Each large chunk is sent to GPT-3.5-turbo-16k with comprehensive context
  - Extracts 2-3 insights per chunk (vs previous 1 insight per chunk)
  - Preserves much longer verbatim responses (200-500 words vs previous 20-50 words)
  - Focuses on detailed customer experiences, quantitative feedback, and specific examples

- **Improved Content Extraction:**
  - Prioritizes detailed customer experiences with specific scenarios and examples
  - Captures quantitative feedback (metrics, timelines, ROI discussions)
  - Preserves comparative analysis and competitive evaluations
  - Maintains integration requirements and workflow details

- **Quality Assurance:**
  - Enhanced validation for richer, more contextually complete responses
  - Quality logging tracks response length and content preservation
  - Flags responses that lose too much context during processing

- **Performance:**
  - Fewer API calls due to larger chunks (more efficient token usage)
  - Higher quality insights due to better context preservation
  - Richer verbatim responses with full context and examples

---
This pipeline is optimized for the 16K token context window to deliver significantly richer insights and more complete verbatim responses.
""")
