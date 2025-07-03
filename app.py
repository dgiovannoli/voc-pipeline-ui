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
st.sidebar.header("2) Processing Details")

# Model details
st.sidebar.markdown("**Model:** OpenAI GPT-4o mini (via LangChain)")

# Estimate time and cost
if uploads:
    num_files = len(uploads)
    total_time = 2.5  # minutes for the whole batch
    avg_tokens_per_file = 2000  # adjust if you have a better estimate
    cost_per_1k = 0.0005  # GPT-4o mini pricing
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
    return pd.read_csv(path)

uploaded_paths = []

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
    for f in uploads:
        dest = UPLOAD_DIR / f.name
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        uploaded_paths.append(str(dest))
    st.sidebar.success(f"🗄️ Saved {len(uploaded_paths)} file(s)")

    if st.sidebar.button("▶️ Process"):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stage1_outputs = []
            total_files = len(uploaded_paths)
            status_text.text(f"Processing {total_files} files...")
            with ThreadPoolExecutor(max_workers=3) as ex:
                futures = [
                  ex.submit(
                    subprocess.run,
                    [sys.executable, "-m", "voc_pipeline", "process_transcript",
                     path,
                     company if company else "",  # client
                     company if company else "",  # company
                     interviewee if interviewee else "", "", ""],
                    check=True, capture_output=True, text=True
                  )
                  for path in uploaded_paths
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
                header = stage1_outputs[0].split('\n')[0]
                all_data = [header]
                for output in stage1_outputs:
                    lines = output.strip().split('\n')
                    if len(lines) > 1:
                        all_data.extend(lines[1:])
                with open(STAGE1_CSV, "w") as f:
                    f.write('\n'.join(all_data))
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
            st.experimental_rerun()
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"❌ Processing failed: {e}")
            st.sidebar.text(f"Error output: {e.stderr}")
        except Exception as e:
            st.sidebar.error(f"🔴 Unexpected error: {e}")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["Validated Quotes", "Response Data Table", "Prompt Template", "Processing Details"])

with tab1:
    st.header("Validated Quotes")
    st.caption("Main columns only. Metadata is auto-populated.")
    if os.path.exists(VALIDATED_CSV) and os.path.getsize(VALIDATED_CSV) > 0:
        try:
            df = load_csv(VALIDATED_CSV)
            if len(df) > 0:
                st.write(f"Showing {len(df)} validated quotes")
                main_cols = [
                    "Response ID", "Subject", "Key Insight", "Question", "Verbatim Response",
                    "Deal Status", "Company Name", "Interviewee Name", "Date of Interview"
                ]
                st.dataframe(df[main_cols])
                if len(df) > 200:
                    st.info(f"Showing first 200 of {len(df)} records")
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
CRITICAL:
- Capture **every question** and **follow-up**, including interviewer prompts or explanations.
- For each extracted segment, produce:
  1. **Key Insight**: a 1–2 sentence distilled takeaway.
  2. **Verbatim Response**: the full stakeholder text.
- Verbatim Response must be one complete, grammatical answer.
- Do NOT include any question text, interviewer prompts, speaker labels, timestamps, Q:/A: tags, or metadata.
- If answer is very short (<20 words), pad with any trailing context that completes the thought.
- You may remove filler words (‘um’, ‘uh’, ‘you know’, ‘so’, ‘like’, ‘well’, ‘er’) to improve readability, but preserve any key emphasis or nuance.
- If a single answer clearly expresses two separate analytical themes (e.g., ‘before vs. after’ *and* ‘pricing concerns’), split into two records, each with its own Response ID.

CONTENT TO SURFACE:
- Research methodology context (e.g. consent process, recording logistics).
- Concrete use-cases (e.g. specific scenarios or tasks mentioned by the interviewee).
- Ideas for integrating the product or service with other tools or workflows.
- Pricing, billing, or procurement preferences.
- Competitive evaluations and feature comparisons.

SEGMENTATION RULES:
- Default: one question → one record.
- Split only if a single answer clearly discusses two distinct analytical themes (e.g. "performance challenges" vs. "workflow suggestions").

Analyze the provided interview chunk and extract ONE meaningful insight. Return ONLY a valid JSON object with this structure:

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
- Extract ONE primary insight per chunk
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making
- Use "N/A" for fields that don't apply
- Ensure all fields are populated
- Return ONLY the JSON object, no other text
'''
    st.code(prompt_template_text, language="markdown")

with tab4:
    st.header("Processing Details")
    st.markdown("""
**How the pipeline processes your interviews (latest version):**

- **Batching & Parallel Processing:**
  - Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor` for speed and efficiency.
  - Each file is handled as a separate job, so you can upload and process many interviews at once.

- **Chunking & Segmentation:**
  - Each transcript is split into Q&A segments using regex patterns (e.g., `Q: ... A: ...`, speaker labels, etc.).
  - If Q&A patterns are not found, the transcript is chunked by speaker changes or by text length.
  - Uses a sliding window with increased chunk overlap (300) and respects sentence boundaries (splits on `.`, `?`, `\n\n`).
  - If a chunk ends without punctuation, it is merged with the next chunk to avoid mid-sentence truncation.

- **Filtering & Cleaning:**
  - Chunks are filtered to remove non-Q&A, low-value, or non-substantive content.
  - Verbatim responses are aggressively cleaned to remove interviewer prompts, Q:/A: tags, speaker labels, timestamps, and interview titles.
  - Common disfluencies ("um", "uh", "you know", etc.) are removed unless they carry meaning.

- **LLM Processing:**
  - Each chunk is sent to the LLM (OpenAI gpt-3.5-turbo-16k) with a detailed prompt.
  - The LLM returns a structured JSON object for each chunk, which is parsed and validated.

- **Post-processing & QA Logging:**
  - All results are combined, sorted, and written to CSV.
  - Additional validation ensures only high-quality, context-rich responses are kept.
  - After LLM output, the code checks if >80% of the original chunk was dropped after cleaning and flags low-quality verbatim responses.
  - A `verbatim_quality.csv` is exported with response_id, grade, and notes for manual review of low-grade items.

- **Performance:**
  - The pipeline is optimized for speed and cost, leveraging parallelism and efficient chunking.
  - Typical batch processing time is ~2.5 minutes for all interviews, with very low LLM costs (see sidebar).

---
This tab will be updated as the pipeline evolves. If you have questions or want to suggest improvements, let us know!
""")
