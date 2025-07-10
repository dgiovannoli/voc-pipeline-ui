import os
import sys
import subprocess
from datetime import date, datetime
import pathlib
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import re
from supabase_database import SupabaseDatabase
from prompts.core_extraction import CORE_EXTRACTION_PROMPT
from stage3_findings_analyzer import Stage3FindingsAnalyzer
import yaml
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from stage5_executive_analyzer import run_stage5_analysis

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase database
try:
    db = SupabaseDatabase()
    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    st.error(f"❌ Failed to connect to Supabase: {e}")

# Debug information (commented out for production)
# st.write("Current working directory:", os.getcwd())

# Helper functions
def extract_interviewee_and_company(filename):
    """
    Extract interviewee and company from filename.
    Example: 'Interview with Ben Evenstad, Owner at Evenstad Law.docx' -> ('Ben Evenstad', 'Evenstad Law')
    """
    base = os.path.basename(filename).replace('.docx', '').replace('.txt', '')
    
    # Handle simple filenames without interview format
    if not base.lower().startswith("interview with "):
        return ("Unknown", "Unknown")
    
    base = base[len("interview with "):]
    parts = [p.strip() for p in base.split(",")]
    interviewee = parts[0] if parts else "Unknown"
    company = "Unknown"
    for part in parts[1:]:
        match = re.search(r'at (.+)', part, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break
    return interviewee, company

def get_client_id():
    """Safely get client_id from session state, ensuring it's properly set"""
    client_id = st.session_state.get('client_id', '')
    
    # If client_id is not set or is default, show error and return None
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        st.stop()
    
    return client_id

def validate_client_id():
    """Validate that client_id is properly set, show error if not"""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        return False
    return True

def save_uploaded_files(uploaded_files, upload_dir="uploads"):
    """
    Save uploaded Streamlit files to disk and return a list of file paths.
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    saved_paths = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(file_path)
    return saved_paths

@st.cache_data(ttl=1, show_spinner=False)
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading CSV from {path}: {e}")
        return pd.DataFrame()

def process_files():
    """Process uploaded files using the modular pipeline CLI"""
    if not st.session_state.uploaded_paths:
        raise Exception("No files uploaded")
    
    all_results = []
    processed_count = 0
    
    for i, path in enumerate(st.session_state.uploaded_paths):
        interviewee, company = extract_interviewee_and_company(os.path.basename(path))
        
        # Create temporary output file for this file
        temp_output = BASE / f"temp_output_{i}.csv"
        
        result = subprocess.run([
            sys.executable, "-m", "voc_pipeline.modular_cli", "extract-core",
            path,
            company if company else "Unknown",
            interviewee if interviewee else "Unknown",
            "closed_won",
            "2024-01-01",
            "-o", str(temp_output)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"Processing failed for {os.path.basename(path)}!\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            # Clean up temp files
            for temp_file in [BASE / f"temp_output_{j}.csv" for j in range(len(st.session_state.uploaded_paths))]:
                if temp_file.exists():
                    temp_file.unlink()
            return
        
        # Load and combine results
        if temp_output.exists() and temp_output.stat().st_size > 0:
            try:
                df_temp = pd.read_csv(temp_output)
                all_results.append(df_temp)
                processed_count += 1
                st.success(f"✅ Processed {os.path.basename(path)}: {len(df_temp)} responses")
            except Exception as e:
                st.warning(f"⚠️ Could not read results from {os.path.basename(path)}: {e}")
        
        # Clean up temp file
        if temp_output.exists():
            temp_output.unlink()
    
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        combined_df.to_csv(STAGE1_CSV, index=False)
        st.success(f"🎉 Successfully processed {processed_count} files with {len(combined_df)} total responses")
    else:
        st.error("Processing failed: No output was generated from any files. Please check your input files and try again.")
    
    st.session_state.current_step = 2

def validate_and_build():
    """Run validation and build final table"""
    if os.path.exists(STAGE1_CSV):
        # Validate
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "validate",
            "--input", str(STAGE1_CSV),
            "--output", str(VALIDATED_CSV)
        ], check=True)
        
        # Build table
        subprocess.run([
            sys.executable, "-m", "voc_pipeline", "build-table",
            "--input", str(VALIDATED_CSV),
            "--output", str(RESPONSE_TABLE_CSV)
        ], check=True)

def load_prompt_template():
    prompt_path = os.path.join("prompts", "core_extraction.py")
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Could not load prompt template: {e}"

PROCESSING_DETAILS = """
### Processing Details

How the pipeline extracts quotes from your interviews (16K-optimized version):

**Batching & Parallel Processing:**
- Multiple interviews are processed in parallel using Python's `ThreadPoolExecutor` for speed and efficiency.
- Each file is handled as a separate job, so you can upload and process many interviews at once.

**Advanced Chunking & Segmentation (16K Optimized):**
- Uses token-based chunking with ~2K tokens per chunk (vs previous 2K character chunks)
- Q&A-aware segmentation that preserves conversation boundaries and context
- Intelligent overlap of 200 tokens to maintain continuity between chunks
- Preserves full Q&A exchanges and speaker turns within chunks
- Adaptive chunking that respects token limits while maximizing context

**Enhanced LLM Processing:**
- Each chunk is sent to GPT-3.5-turbo-16k with comprehensive context
- Extracts 3-5 quotes per chunk (vs previous 1 quote per chunk)
- Preserves much longer verbatim quotes (200-800 words vs previous 20-50 words)
- Focuses on detailed customer experiences, quantitative feedback, and specific examples

**Improved Quote Extraction:**
- Prioritizes detailed customer experiences with specific scenarios and examples
- Captures quantitative feedback (metrics, timelines, ROI discussions)
- Preserves comparative analysis and competitive evaluations
- Maintains integration requirements and workflow details

**Quality Assurance:**
- Enhanced validation for richer, more contextually complete quotes
- Quality logging tracks quote length and content preservation
- Flags quotes that lose too much context during processing

**Performance:**
- Fewer API calls due to larger chunks (more efficient token usage)
- Higher quality quotes due to better context preservation
- Richer verbatim quotes with full context and examples

---
This pipeline is optimized for the 16K token context window to deliver significantly richer quotes and more complete customer insights.
"""

# Constants
BASE = pathlib.Path(__file__).parent
STAGE1_CSV = BASE / "stage1_output.csv"
VALIDATED_CSV = BASE / "validated_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"

def process_files_with_progress():
    """Process uploaded files with progress tracking"""
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
    """Save Stage 1 results to Supabase"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return False
    
    try:
        df = pd.read_csv(csv_path)
        saved_count = 0
        client_id = get_client_id()  # Use helper function
        
        for _, row in df.iterrows():
            # Log row keys for debugging
            if saved_count == 0:
                st.info(f"Row keys: {list(row.keys())}")
            response_data = {
                'response_id': row.get('response_id', '') or row.get('Response ID', ''),
                'verbatim_response': row.get('verbatim_response', '') or row.get('Verbatim Response', ''),
                'subject': row.get('subject', '') or row.get('Subject', ''),
                'question': row.get('question', '') or row.get('Question', ''),
                'deal_status': row.get('deal_status', '') or row.get('Deal Status', 'closed_won'),
                'company': row.get('company', '') or row.get('Company Name', ''),
                'interviewee_name': row.get('interviewee_name', '') or row.get('Interviewee Name', ''),
                'interview_date': row.get('interview_date', '') or row.get('Date of Interview', '2024-01-01'),
                'file_source': 'stage1_processing',
                'client_id': client_id  # Use session state client_id
            }
            if not response_data['response_id']:
                st.warning(f"Blank response_id for row: {row}")
            if db.save_core_response(response_data):
                saved_count += 1
        st.success(f"✅ Saved {saved_count} quotes to database for client: {client_id}")
        return True
    except Exception as e:
        st.error(f"❌ Failed to save to database: {e}")
        return False

def run_stage2_analysis():
    """Run Stage 2 analysis using database"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        from enhanced_stage2_analyzer import SupabaseStage2Analyzer
        client_id = get_client_id()  # Use helper function
        analyzer = SupabaseStage2Analyzer()
        result = analyzer.process_incremental(client_id=client_id)
        return result
    except Exception as e:
        st.error(f"❌ Stage 2 analysis failed: {e}")
        return None

def get_stage2_summary():
    """Get Stage 2 summary from database"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        client_id = get_client_id()  # Use helper function
        summary = db.get_summary_statistics(client_id=client_id)
        return summary
    except Exception as e:
        st.error(f"❌ Failed to get summary: {e}")
        return None

def run_stage3_analysis():
    """Run Stage 3 findings analysis using database"""
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return None
    
    try:
        client_id = get_client_id()  # Use helper function
        analyzer = Stage3FindingsAnalyzer()
        result = analyzer.process_stage3_findings(client_id=client_id)
        return result
    except Exception as e:
        st.error(f"❌ Stage 3 analysis failed: {e}")
        return None

def get_stage3_summary():
    """Get Stage 3 enhanced findings summary from database"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        client_id = get_client_id()  # Use helper function
        summary = db.get_stage3_findings_summary(client_id=client_id)
        return summary
    except Exception as e:
        st.error(f"❌ Failed to get enhanced findings summary: {e}")
        return None

def show_supabase_status():
    """Show database connection status and data summary"""
    st.subheader("🗄️ Database Status")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not connected")
        st.info("💡 Make sure your .env file contains database credentials")
        return
    
    try:
        # Get summary statistics with client_id filtering
        client_id = get_client_id()  # Use helper function
        summary = db.get_summary_statistics(client_id=client_id)
        
        if "error" in summary:
            st.error(f"❌ Database error: {summary['error']}")
            return
        
        # Display client context
        st.info(f"📊 Showing data for client: **{client_id}**")
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Quotes", summary['total_quotes'])
        
        with col2:
            st.metric("Labeled Quotes", summary['quotes_with_scores'])
        
        with col3:
            st.metric("Analysis Coverage", f"{summary['coverage_percentage']}%")
        
        # Deal outcome distribution
        if summary['deal_outcome_distribution']:
            st.subheader("🏢 Deal Outcome Distribution")
            deal_df = pd.DataFrame(list(summary['deal_outcome_distribution'].items()), 
                                 columns=['Status', 'Count'])
            
            fig = px.pie(deal_df, values='Count', names='Status', 
                        title="Deal Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        # Company distribution
        if summary['company_distribution']:
            st.subheader("🏢 Company Distribution")
            company_df = pd.DataFrame(list(summary['company_distribution'].items()), 
                                    columns=['Company', 'Count'])
            company_df = company_df.sort_values('Count', ascending=False).head(10)
            
            fig = px.bar(company_df, x='Company', y='Count', 
                        title="Top 10 Companies")
            st.plotly_chart(fig, use_container_width=True)
        
        # Criteria performance
        if summary['criteria_performance']:
            st.subheader("📊 Criteria Performance")
            criteria_data = []
            for criterion, perf in summary['criteria_performance'].items():
                criteria_data.append({
                    'Criterion': criterion,
                    'Average Score': perf['average_score'],
                    'Mentions': perf['mention_count'],
                    'Coverage %': perf['coverage_percentage']
                })
            
            criteria_df = pd.DataFrame(criteria_data)
            criteria_df = criteria_df.sort_values('Average Score', ascending=False)
            
            fig = px.bar(criteria_df, x='Criterion', y='Average Score',
                        title="Average Scores by Criterion",
                        hover_data=['Mentions', 'Coverage %'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed table
            st.dataframe(criteria_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error getting database status: {e}")

def run_stage4_analysis():
    """Run Stage 4 theme analysis"""
    try:
        from stage4_theme_analyzer import Stage4ThemeAnalyzer
        client_id = get_client_id()  # Use helper function
        analyzer = Stage4ThemeAnalyzer()
        result = analyzer.process_themes(client_id=client_id)
        return result
    except Exception as e:
        st.error(f"Stage 4 analysis failed: {e}")
        return {"status": "error", "message": str(e)}

def get_stage4_summary():
    """Get Stage 4 themes summary"""
    try:
        client_id = get_client_id()  # Use helper function
        db = SupabaseDatabase()
        return db.get_themes_summary(client_id=client_id)
    except Exception as e:
        st.error(f"Failed to get Stage 4 summary: {e}")
        return {}

def show_stage4_themes():
    """Display Stage 4 themes analysis"""
    st.subheader("🎯 Stage 4: Theme Generation")
    
    # Get summary
    summary = get_stage4_summary()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Themes", summary.get('total_themes', 0))
    
    with col2:
        st.metric("High Strength", summary.get('high_strength', 0))
    
    with col3:
        st.metric("Competitive", summary.get('competitive_themes', 0))
    
    with col4:
        st.metric("Companies", summary.get('companies_covered', 0))
    
    # Run analysis button
    if st.button("🚀 Generate Themes", type="primary"):
        with st.spinner("Generating themes from findings..."):
            result = run_stage4_analysis()
            
            if result.get("status") == "success":
                st.success(f"✅ Generated {result.get('themes_generated', 0)} themes!")
                st.rerun()
            else:
                st.error(f"❌ Theme generation failed: {result.get('message', 'Unknown error')}")
    
    # Display themes
    client_id = get_client_id()  # Use helper function
    db = SupabaseDatabase()
    themes_df = db.get_themes(client_id=client_id)
    
    if not themes_df.empty:
        st.subheader("📊 Generated Themes")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strength_filter = st.selectbox(
                "Filter by Strength",
                ["All"] + list(themes_df['theme_strength'].unique())
            )
        
        with col2:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + list(themes_df['theme_category'].unique())
            )
        
        with col3:
            competitive_filter = st.selectbox(
                "Competitive Themes",
                ["All", "Yes", "No"]
            )
        
        # Apply filters
        filtered_df = themes_df.copy()
        
        if strength_filter != "All":
            filtered_df = filtered_df[filtered_df['theme_strength'] == strength_filter]
        
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['theme_category'] == category_filter]
        
        if competitive_filter != "All":
            competitive_flag = competitive_filter == "Yes"
            filtered_df = filtered_df[filtered_df['competitive_flag'] == competitive_flag]
        
        # Display themes
        for _, theme in filtered_df.iterrows():
            with st.expander(f"🎯 {theme['theme_statement'][:100]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Statement:** {theme['theme_statement']}")
                    st.markdown(f"**Category:** {theme['theme_category']}")
                    st.markdown(f"**Strength:** {theme['theme_strength']}")
                    st.markdown(f"**Companies:** {', '.join(theme['interview_companies']) if theme['interview_companies'] else 'N/A'}")
                    
                    if theme['business_implications']:
                        st.markdown(f"**Business Implications:** {theme['business_implications']}")
                    
                    # Show all contributing quotes
                    st.markdown("**All Contributing Quotes:**")
                    quotes = theme.get('quotes', [])
                    if quotes:
                        for quote in quotes:
                            quote_text = quote.get('text', '')
                            impact = quote.get('impact_score', None)
                            confidence = quote.get('confidence_score', None)
                            attribution = quote.get('attribution', '')
                            st.markdown(f"- {quote_text}")
                            if impact is not None or confidence is not None:
                                score_str = []
                                if impact is not None:
                                    score_str.append(f"Impact: {impact:.1f}/5")
                                if confidence is not None:
                                    score_str.append(f"Confidence: {confidence:.1f}/10")
                                st.caption(' | '.join(score_str))
                            if attribution:
                                st.caption(attribution)
                    else:
                        st.warning("No detailed quote information available for this theme.")
        # Export themes
        if st.button("📥 Export Themes"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Themes CSV",
                data=csv,
                file_name=f"themes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_themes"
            )
    
    else:
        st.info("No themes generated yet. Run Stage 4 analysis to generate themes from findings.")

def get_stage5_summary():
    """Get Stage 5 executive synthesis summary"""
    try:
        client_id = get_client_id()  # Use helper function
        db = SupabaseDatabase()
        return db.get_executive_synthesis_summary(client_id=client_id)
    except Exception as e:
        st.error(f"Failed to get Stage 5 summary: {e}")
        return {}

def show_stage5_synthesis():
    """Display Stage 5 executive synthesis"""
    st.subheader("🎯 Stage 5: Executive Synthesis")
    
    # Get summary
    summary = get_stage5_summary()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Executive Themes", summary.get('total_executive_themes', 0))
    
    with col2:
        st.metric("High Impact", summary.get('high_impact_themes', 0))
    
    with col3:
        st.metric("Presentation Ready", summary.get('presentation_ready', 0))
    
    with col4:
        st.metric("Competitive", summary.get('competitive_themes', 0))
    
    # Generate synthesis button
    if st.button("🚀 Generate Executive Synthesis", type="primary"):
        with st.spinner("Generating executive synthesis with criteria scorecard..."):
            client_id = get_client_id()  # Use helper function
            result = run_stage5_analysis(client_id=client_id)
            
            if result.get("status") == "success":
                st.success(f"✅ Generated {result.get('executive_themes_generated', 0)} executive themes!")
                st.rerun()
            else:
                st.error(f"❌ Synthesis failed: {result.get('message', 'Unknown error')}")
    
    # Display executive themes
    client_id = get_client_id()  # Use helper function
    db = SupabaseDatabase()
    themes_df = db.get_executive_themes(client_id=client_id)
    
    if not themes_df.empty:
        st.subheader("📊 Executive Themes")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            impact_filter = st.selectbox(
                "Filter by Impact",
                ["All"] + list(themes_df['business_impact_level'].unique())
            )
        
        with col2:
            readiness_filter = st.selectbox(
                "Filter by Readiness",
                ["All"] + list(themes_df['executive_readiness'].unique())
            )
        
        with col3:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + list(themes_df['theme_category'].unique())
            )
        
        # Apply filters
        filtered_df = themes_df.copy()
        
        if impact_filter != "All":
            filtered_df = filtered_df[filtered_df['business_impact_level'] == impact_filter]
        
        if readiness_filter != "All":
            filtered_df = filtered_df[filtered_df['executive_readiness'] == readiness_filter]
        
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['theme_category'] == category_filter]
        
        # Display themes
        for _, theme in filtered_df.iterrows():
            with st.expander(f"🎯 {theme['theme_headline'][:100]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Headline:** {theme['theme_headline']}")
                    st.markdown(f"**Narrative:** {theme['narrative_explanation']}")
                    st.markdown(f"**Category:** {theme['theme_category']}")
                    st.markdown(f"**Impact Level:** {theme['business_impact_level']}")
                    st.markdown(f"**Readiness:** {theme['executive_readiness']}")
                    
                    if theme['strategic_recommendations']:
                        st.markdown(f"**Strategic Recommendations:** {theme['strategic_recommendations']}")
                    
                    if theme['competitive_context']:
                        st.markdown(f"**Competitive Context:** {theme['competitive_context']}")
                    
                    if theme['primary_executive_quote']:
                        st.markdown(f"**Primary Quote:** {theme['primary_executive_quote'][:200]}...")
                
                with col2:
                    st.metric("Priority Rank", theme['priority_rank'])
                    st.metric("Priority Score", f"{theme['priority_score']:.1f}")
                    st.metric("Evidence Summary", theme['supporting_evidence_summary'])
                    
                    if theme['business_impact_level'] == 'High':
                        st.success("🏆 High Impact")
                    
                    if theme['executive_readiness'] == 'Presentation':
                        st.info("📋 Presentation Ready")
        
        # Export themes
        if st.button("📥 Export Executive Themes"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Executive Themes CSV",
                data=csv,
                file_name=f"executive_themes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_executive_themes"
            )
    
    else:
        st.info("No executive themes generated yet. Run Stage 5 analysis to generate executive synthesis.")

def show_stage5_criteria_scorecard():
    """Display Stage 5 criteria scorecard"""
    st.subheader("📊 Executive Criteria Scorecard")
    
    # Generate scorecard button
    if st.button("📊 Generate Criteria Scorecard", type="primary"):
        with st.spinner("Generating criteria scorecard..."):
            client_id = get_client_id()  # Use helper function
            db = SupabaseDatabase()
            scorecard = db.generate_criteria_scorecard(client_id=client_id)
            
            if scorecard:
                st.success("✅ Criteria scorecard generated successfully!")
                st.session_state['scorecard_data'] = scorecard
                st.rerun()
            else:
                st.error("❌ Failed to generate criteria scorecard")
    
    # Display scorecard if available
    if 'scorecard_data' in st.session_state:
        scorecard = st.session_state['scorecard_data']
        
        # Overall performance summary
        overall = scorecard.get('overall_performance', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Performance Rating", overall.get('average_performance_rating', 'N/A'))
        with col2:
            st.metric("Criteria Analyzed", overall.get('total_criteria_analyzed', 0))
        with col3:
            st.metric("Top Performers", len(overall.get('top_performing_criteria', [])))
        with col4:
            st.metric("Critical Issues", len(overall.get('critical_attention_needed', [])))
        
        # Criteria performance table
        st.subheader("🎯 Criteria Performance Details")
        
        criteria_details = scorecard.get('criteria_details', [])
        if criteria_details:
            # Create DataFrame for display
            df = pd.DataFrame(criteria_details)
            
            # Color-code performance ratings
            def color_performance(val):
                if val == "EXCEPTIONAL":
                    return "background-color: #d4edda; color: #155724"
                elif val == "STRONG":
                    return "background-color: #d1ecf1; color: #0c5460"
                elif val == "GOOD":
                    return "background-color: #fff3cd; color: #856404"
                elif val == "NEEDS ATTENTION":
                    return "background-color: #f8d7da; color: #721c24"
                else:
                    return "background-color: #f5c6cb; color: #721c24"
            
            # Display styled table
            st.dataframe(
                df[['criterion', 'performance_rating', 'avg_score', 'total_mentions', 
                    'companies_affected', 'executive_priority', 'action_urgency']].style
                .applymap(color_performance, subset=['performance_rating'])
            )
            
            # Detailed view for each criterion
            st.subheader("📋 Detailed Criteria Analysis")
            
            for criterion in criteria_details:
                with st.expander(f"🎯 {criterion['criterion'].replace('_', ' ').title()} - {criterion['performance_rating']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Key Insights:** {criterion['key_insights']}")
                        st.markdown(f"**Trend Direction:** {criterion['trend_direction']}")
                        st.markdown(f"**Executive Priority:** {criterion['executive_priority']}")
                        st.markdown(f"**Action Urgency:** {criterion['action_urgency']}")
                        
                        if criterion['sample_quotes']:
                            st.markdown("**Sample Quotes:**")
                            for i, quote in enumerate(criterion['sample_quotes'][:3], 1):
                                st.write(f"{i}. {quote}")
                    
                    with col2:
                        st.metric("Avg Score", f"{criterion['avg_score']:.2f}")
                        st.metric("Mentions", criterion['total_mentions'])
                        st.metric("Companies", criterion['companies_affected'])
                        st.metric("Critical", criterion['critical_mentions'])
            
            # Deal impact analysis
            deal_impact = scorecard.get('deal_impact_analysis', {})
            if deal_impact:
                st.subheader("💼 Deal Impact Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Criteria Affecting Lost Deals:**")
                    for criterion in deal_impact.get('criteria_affecting_lost_deals', []):
                        st.write(f"• {criterion.replace('_', ' ').title()}")
                
                with col2:
                    st.markdown("**Criteria Winning Deals:**")
                    for criterion in deal_impact.get('criteria_winning_deals', []):
                        st.write(f"• {criterion.replace('_', ' ').title()}")
        else:
            st.info("No criteria details available in scorecard.")
    
    else:
        st.info("No criteria scorecard available. Generate one to view detailed analysis.")

def show_prompts_details():
    st.title("📝 Prompts & Processing Details")
    
    # Create tabs for each stage
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Stage 1: Extraction", "Stage 2: Scoring", "Stage 3: Findings", "Stage 4: Themes", "Stage 5: Executive Synthesis", "Configuration"])
    
    with tab1:
        st.subheader("🎯 Stage 1: Core Response Extraction")
        st.markdown("""
        **Purpose**: Extract key insights and verbatim responses from interview transcripts
        
        **Process**:
        - Token-based chunking with ~2K tokens per chunk
        - Q&A-aware segmentation preserving conversation boundaries
        - LLM processing with GPT-3.5-turbo-16k
        - Extracts 3-5 insights per chunk with detailed verbatim responses
        """)
        
        st.subheader("📋 Stage 1 Prompt Template")
        prompt_content = load_prompt_template()
        st.code(prompt_content, language='python')
        
        st.subheader("🔧 Stage 1 Configuration")
        st.markdown("""
        **Chunking Strategy**:
        - Token-based chunking (not character-based)
        - ~2K tokens per chunk for optimal context
        - 200 token overlap for continuity
        - Q&A-aware segmentation
        
        **Processing**:
        - Parallel processing with ThreadPoolExecutor
        - Quality-focused extraction targeting ~5 insights per chunk
        - Enhanced validation for richer responses
        """)
    
    with tab2:
        st.subheader("🎯 Stage 2: Quote Labeling & Analysis")
        st.markdown("""
        **Purpose**: Score extracted quotes against 10 executive criteria using binary + intensity scoring
        
        **Scoring System**:
        - **0**: Not relevant/not mentioned
        - **1**: Slight mention/indirect relevance  
        - **2**: Clear mention/direct relevance
        - **3**: Strong emphasis/important feedback
        - **4**: Critical feedback/deal-breaking issue
        - **5**: Exceptional praise/deal-winning strength
        """)
        
        st.subheader("📊 10 Executive Criteria")
        criteria_info = """
        1. **Product Capability**: Functionality, features, performance, core solution fit
        2. **Implementation Onboarding**: Deployment ease, time-to-value, setup complexity
        3. **Integration Technical Fit**: APIs, data compatibility, technical architecture
        4. **Support Service Quality**: Post-sale support, responsiveness, expertise, SLAs
        5. **Security Compliance**: Data protection, certifications, governance, risk management
        6. **Market Position Reputation**: Brand trust, references, analyst recognition
        7. **Vendor Stability**: Financial health, roadmap clarity, long-term viability
        8. **Sales Experience Partnership**: Buying process quality, relationship building
        9. **Commercial Terms**: Price, contract flexibility, ROI, total cost of ownership
        10. **Speed Responsiveness**: Implementation timeline, decision-making speed, agility
        """
        st.markdown(criteria_info)
        
        st.subheader("📋 Stage 2 Prompt Template")
        stage2_prompt = '''
ANALYZE THIS QUOTE against the 10-criteria executive framework using BINARY + INTENSITY scoring.

DEAL CONTEXT: {deal_status} deal

QUOTE TO ANALYZE:
Subject: {subject}
Question: {question}
Response: {verbatim_response}

EVALUATION CRITERIA:
{criteria}

BINARY + INTENSITY SCORING SYSTEM:
- 0 = Not relevant/not mentioned (omit from scores)
- 1 = Slight mention/indirect relevance
- 2 = Clear mention/direct relevance
- 3 = Strong emphasis/important feedback
- 4 = Critical feedback/deal-breaking issue
- 5 = Exceptional praise/deal-winning strength

TASK: Score this quote against ANY criteria that are even loosely relevant. Use the binary + intensity approach:
1. First decide: Is this criterion relevant to the quote or question? (Binary: 0 or 1+)
2. If relevant, then assess intensity: How important/impactful is this feedback? (1-5)
3. Final score = Binary × Intensity (0 or 1-5)

CONTEXT ANALYSIS:
- Consider the QUESTION being asked - it provides crucial context
- A question about "pricing" makes commercial_terms highly relevant
- A question about "implementation" makes implementation_onboarding highly relevant
- A question about "security" makes security_compliance highly relevant
- If unsure about relevance, err on the side of inclusion and score it

SCORING EXAMPLES:
- Question: "How do you evaluate pricing?" + Response: "pricing is reasonable" → commercial_terms: 2 (clear mention)
- Question: "What about security?" + Response: "we're concerned about data privacy" → security_compliance: 4 (critical concern)
- Question: "How was setup?" + Response: "setup was easy" → implementation_onboarding: 3 (strong positive)
- Question: "What about pricing?" + Response: "the product works well" → commercial_terms: 1 (slight mention)
- Question: "How do you use Rev?" + Response: "We use it for depositions and hearings, and it saves us time." → product_capability: 3 (strong positive)
- Question: "What frustrates you?" + Response: "Sometimes the transcript isn't accurate." → product_capability: 4 (critical issue)
- Question: "What integrations would help?" + Response: "We use Dropbox and Clio." → integration_technical_fit: 2 (clear mention)
- Question: "How do you rank criteria?" + Response: "Speed and cost are most important, then security." → speed_responsiveness: 4, commercial_terms: 4, security_compliance: 3
- Question: "What about support?" + Response: "Support is fine, but not a big factor." → support_service_quality: 1 (minor mention)

OUTPUT FORMAT (JSON only):
{
    "scores": {
        "criterion_name": score_number
    },
    "priorities": {
        "criterion_name": "critical|high|medium|low"
    },
    "confidence": {
        "criterion_name": "high|medium|low"
    },
    "relevance_explanation": {
        "criterion_name": "Brief explanation of how this quote relates to the criterion"
    },
    "context_assessment": {
        "criterion_name": "deal_breaking|minor|neutral"
    },
    "question_relevance": {
        "criterion_name": "direct|indirect|unrelated"
    }
}

IMPORTANT: Only include criteria in "scores" that are relevant (score > 0). If a criterion is not mentioned or relevant, omit it entirely.
        '''
        st.code(stage2_prompt, language='python')
        
        st.subheader("🔧 Stage 2 Configuration")
        st.markdown("""
        **Deal Weighting**:
        - Lost deals: 1.2x base multiplier
        - Won deals: 0.9x base multiplier
        - Critical feedback: 1.5x multiplier
        - Minor feedback: 0.7x multiplier
        
        **Processing**:
        - Incremental processing (only new quotes)
        - Parallel processing with configurable workers
        - Context-aware scoring based on question relevance
        """)
    
    with tab3:
        st.subheader("🎯 Stage 3: Findings Identification")
        st.markdown("""
        **Purpose**: Transform scored quotes into executive-ready findings using the Buried Wins Findings Criteria v4.0 framework

       **Scoring System**:
        - **Relevance/Intensity (0–5):**
        - 0 = Not relevant/not mentioned
        - 1 = Slight mention
        - 2 = Clear mention
        - 3 = Strong mention
        - 4 = Very strong mention
        - 5 = Highest possible relevance/intensity
    - **Sentiment:**
        - positive
        - negative
        - neutral
        - mixed

                **How Scores and Findings Work**
        | Relevance | Sentiment | Example Use                |
        |-----------|-----------|---------------------------|
        | 5         | Negative  | “Deal-breaker, must fix”  |
        | 5         | Positive  | “Major strength”          |
        | 3         | Neutral   | “Important, not polarizing” |
        | 1         | Negative  | “Minor complaint”         |
        | 0         | —         | Not mentioned             |

        - **Relevance (0–5):** How important or salient the quote is for the criterion.
        - **Sentiment:** Whether the feedback is positive, negative, neutral, or mixed.
        - **Findings:**
            - **Strengths:** High relevance (>= 3.5) + positive sentiment
            - **Risks/Areas for Improvement:** High relevance (>= 3.5) + negative sentiment
            - **Monitor:** Moderate relevance, any sentiment
            - **Ignore:** Low relevance

        **Note:**
        The system now separates relevance and sentiment for clarity and better analytics.
        
        st.subheader("🔍 Buried Wins v4.0 Evaluation Criteria")
        evaluation_criteria = """
        **8 Core Evaluation Criteria**:
        1. **Novelty**: The observation is new/unexpected, challenging assumptions
        2. **Actionability**: Suggests clear steps, fixes, or actions to improve outcomes
        3. **Specificity**: Precise, detailed, not generic - references particular features or processes
        4. **Materiality**: Meaningful business impact affecting revenue, satisfaction, or positioning
        5. **Recurrence**: Same observation across multiple interviews or sources
        6. **Stakeholder Weight**: Comes from high-influence decision makers or critical personas
        7. **Tension/Contrast**: Exposes tensions, tradeoffs, or significant contrasts
        8. **Metric/Quantification**: Supported by tangible metrics, timeframes, or outcomes
        """
        st.markdown(evaluation_criteria)
        
        
        st.subheader("📋 Stage 5 Prompt Template")
    with tab5:
        st.subheader("🏆 Stage 5: Executive Synthesis")
        st.markdown("""
        **Purpose**: Transform themes into C-suite ready narratives with criteria scorecard integration
        
        **Executive Framework**:
        - **Punch Then Explain**: Bold headline + concise business narrative
        - **Data-Anchored**: Include specific metrics from themes and criteria scorecard
        - **Business Tension**: Highlight strategic implications and performance gaps
        - **Executive Relevance**: Focus on decision-making impact and priority actions
        - **Criteria Integration**: Reference specific criteria performance where relevant
        """)
        
        st.subheader("📊 Criteria Scorecard Integration")
        st.markdown("""
        **Performance Ratings**:
        - **EXCEPTIONAL**: Avg score >= 3.5, critical ratio >= 30%
        - **STRONG**: Avg score >= 3.0, critical ratio >= 20%
        - **GOOD**: Avg score >= 2.5
        - **NEEDS ATTENTION**: Avg score >= 2.0
        - **CRITICAL ISSUE**: Avg score < 2.0
        
        **Executive Priorities**:
        - **IMMEDIATE ACTION**: High scores affecting multiple companies
        - **HIGH PRIORITY**: Critical mentions requiring attention
        - **MEDIUM PRIORITY**: Moderate scores with company impact
        - **MONITOR**: Lower scores requiring observation
        """)
        
        st.subheader("📋 Stage 5 Prompt Template")
        stage5_prompt = '''
You are a senior research consultant for Buried Wins, specializing in executive communication for C-suite B2B SaaS clients.

THEME DATA:
{theme_data}

CRITERIA SCORECARD CONTEXT:
{scorecard_context}

TASK: Create an executive-ready synthesis that incorporates both theme insights AND criteria performance data.

REQUIREMENTS:
1. **Punch Then Explain**: Bold headline + concise business narrative
2. **Data-Anchored**: Include specific metrics from both themes and criteria scorecard
3. **Business Tension**: Highlight strategic implications and performance gaps
4. **Executive Relevance**: Focus on decision-making impact and priority actions
5. **Criteria Integration**: Reference specific criteria performance where relevant

OUTPUT FORMAT (JSON only):
{
    "theme_headline": "Executive-ready headline following punch-then-explain principle",
    "narrative_explanation": "2-3 sentence business narrative incorporating criteria performance",
    "business_impact_level": "High|Medium|Emerging",
    "strategic_recommendations": "High-level strategic implications with criteria-specific actions",
    "executive_readiness": "Presentation|Report|Follow-up",
    "criteria_connections": ["List of criteria this theme connects to"],
    "performance_insights": "How this theme relates to criteria performance data"
}

IMPORTANT: 
- Use exact quotes with response_id prefixes
- Reference specific criteria performance ratings (EXCEPTIONAL, STRONG, GOOD, NEEDS ATTENTION, CRITICAL ISSUE)
- Connect themes to criteria scorecard insights
- Focus on business impact, not technical details
- Use Buried Wins editorial style: conversational authority, clarity over cleverness, punch then explain
        '''
        st.code(stage5_prompt, language='python')
        
        st.subheader("🎯 Priority Scoring")
        st.markdown("""
        **Priority Score Calculation**:
        - Competitive flag: 3.0x weight
        - Theme strength: 2.0x weight
        - Company count: 1.5x weight
        - Average confidence: 1.0x weight
        - Additional weight for high-impact criteria connections
        
        **Business Impact Levels**:
        - **High**: Significant strategic implications
        - **Medium**: Moderate business impact
        - **Emerging**: Early indicators requiring attention
        """)
        
        st.subheader("📋 Executive Readiness")
        st.markdown("""
        **Readiness Categories**:
        - **Presentation**: Ready for C-suite presentation
        - **Report**: Suitable for executive reports
        - **Follow-up**: Requires additional analysis or context
        
        **Deal Impact Analysis**:
        - Criteria affecting lost deals
        - Criteria winning deals
        - Performance breakdown by deal status
        """)
    
    with tab6:
        st.subheader("⚙️ Configuration & Settings")
        st.markdown("""
        **Database Configuration**:
        - Supabase integration for all data storage
        - Real-time synchronization
        - Automatic schema management
        - Row-level security policies
        
        **Processing Configuration**:
        - Parallel processing with configurable workers
        - Incremental processing for efficiency
        - Quality metrics tracking
        - Error handling and retry logic
        """)
        
        st.subheader("🔧 Environment Variables")
        env_vars = """
Required Environment Variables:
- OPENAI_API_KEY: Your OpenAI API key
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_ANON_KEY: Your Supabase anonymous key

Optional:
- LOG_LEVEL: Logging level (INFO, DEBUG, WARNING, ERROR)
        """
        st.code(env_vars, language='bash')
        
        st.subheader("📊 Quality Assurance")
        st.markdown("""
        **Quality Metrics**:
        - Quote coverage percentage
        - Criteria performance tracking
        - Processing error rates
        - Data validation checks
        
        **Performance Monitoring**:
        - Processing duration tracking
        - Memory usage optimization
        - API rate limiting
        - Error recovery mechanisms
        """)

def show_welcome_screen():
    st.title("🎤 Voice of Customer Pipeline")
    st.markdown("### AI-Powered Quote Analysis & Insights")
    
    st.markdown("""
    Welcome to the VOC Pipeline! This tool helps you extract and analyze customer quotes from interviews to uncover actionable insights.
    
    **Pipeline Overview:**
    1. **📤 Upload** interview transcripts (.txt or .docx files)
    2. **📊 Extract** customer quotes and responses
    3. **🎯 Label** quotes against 10 evaluation criteria
    4. **🔍 Identify** key findings and insights
    5. **🎨 Generate** themes and patterns
    6. **📈 Create** executive synthesis and recommendations
    
    **Key Features:**
    - 🚀 **16K Token Optimization**: Processes longer, richer quotes
    - 🎯 **10-Criteria Analysis**: Comprehensive executive framework
    - 📊 **Real-time Analytics**: Live dashboards and visualizations
    - ☁️ **Cloud Storage**: All data stored securely in database
    - 🔄 **Incremental Processing**: Only analyze new quotes
    """)
    
    # Quick start with better flow
    st.subheader("🚀 Quick Start")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. Upload & Extract**
        - Go to "Upload Files" section
        - Select your interview transcripts
        - Click "Extract Quotes"
        """)
    
    with col2:
        st.markdown("""
        **2. Analyze & Insights**
        - Run "Label Quotes" to evaluate criteria
        - Identify findings and generate themes
        - Create executive summary
        """)
    
    # Database status with better labels
    st.subheader("🗄️ Database Status")
    if SUPABASE_AVAILABLE:
        st.success("✅ Database Connected - Ready to process quotes")
        
        # Show quick stats with better labels
        try:
            summary = get_stage2_summary()
            if summary and 'total_quotes' in summary:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Quotes", summary['total_quotes'])
                with col2:
                    st.metric("Labeled Quotes", summary['quotes_with_scores'])
                with col3:
                    st.metric("Analysis Coverage", f"{summary['coverage_percentage']}%")
        except:
            st.info("No quotes in database yet. Start by uploading and processing files.")
    else:
        st.error("❌ Database Not Connected")
        st.info("Please configure your .env file with database credentials")

def show_database_management():
    """Show database management interface for debugging client data issues"""
    st.subheader("🗄️ Database Management")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not available")
        return
    
    try:
        # Get client summary
        client_summary = db.get_client_summary()
        
        if not client_summary:
            st.info("📊 No data found in database")
            return
        
        st.subheader("📊 Data by Client")
        
        # Display client data summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Clients", len(client_summary))
            st.metric("Total Records", sum(client_summary.values()))
        
        with col2:
            # Show current client context
            current_client = get_client_id()  # Use helper function
            current_count = client_summary.get(current_client, 0)
            st.metric("Current Client Records", current_count)
        
        # Display client breakdown
        st.subheader("🏢 Client Data Breakdown")
        client_df = pd.DataFrame(list(client_summary.items()), columns=['Client ID', 'Record Count'])
        client_df = client_df.sort_values('Record Count', ascending=False)
        
        # Create a bar chart
        fig = px.bar(client_df, x='Client ID', y='Record Count', 
                    title="Records by Client ID",
                    color='Record Count')
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed table
        st.dataframe(client_df, use_container_width=True)
        
        # Data management section
        st.subheader("🔧 Data Management")
        
        # Merge data section
        st.markdown("**Merge Data Between Clients**")
        st.info("💡 Use this to consolidate data from different client IDs into one")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            from_client = st.selectbox(
                "From Client ID",
                list(client_summary.keys()),
                help="Select the source client ID"
            )
        
        with col2:
            to_client = st.selectbox(
                "To Client ID",
                list(client_summary.keys()) + ['new_client'],
                help="Select the target client ID"
            )
        
        with col3:
            if to_client == 'new_client':
                new_client_id = st.text_input(
                    "New Client ID",
                    placeholder="Enter new client ID"
                )
            else:
                new_client_id = to_client
        
        if st.button("🔄 Merge Data", type="primary", disabled=from_client == to_client):
            if from_client == to_client:
                st.warning("⚠️ Cannot merge to the same client ID")
            elif to_client == 'new_client' and not new_client_id.strip():
                st.warning("⚠️ Please enter a new client ID")
            else:
                target_client = new_client_id if to_client == 'new_client' else to_client
                
                with st.spinner(f"Merging data from {from_client} to {target_client}..."):
                    success = db.merge_client_data(from_client, target_client)
                    
                    if success:
                        st.success(f"✅ Successfully merged data from {from_client} to {target_client}")
                        st.info("🔄 Refreshing data...")
                        st.rerun()
                    else:
                        st.error("❌ Failed to merge data")
        
        # Set current client section
        st.subheader("🎯 Set Current Client")
        st.info("💡 Change which client's data you want to work with")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_current_client = st.selectbox(
                "Select Client ID",
                list(client_summary.keys()),
                index=list(client_summary.keys()).index(get_client_id()) if get_client_id() in client_summary else 0
            )
        
        with col2:
            if st.button("✅ Set as Current Client"):
                st.session_state.client_id = new_current_client
                st.success(f"✅ Current client set to: {new_current_client}")
                st.info("🔄 Refreshing interface...")
                st.rerun()
        
        # Show current client data
        if st.session_state.get('client_id') in client_summary:
            st.subheader(f"📊 Current Client Data: {st.session_state.client_id}")
            
            # Get current client data
            current_df = db.get_stage1_data_responses(client_id=st.session_state.client_id)
            
            if not current_df.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Quotes", len(current_df))
                
                with col2:
                    if 'company' in current_df.columns:
                        st.metric("Companies", current_df['company'].nunique())
                    else:
                        st.metric("Companies", "N/A")
                
                with col3:
                    if 'interviewee_name' in current_df.columns:
                        st.metric("Interviewees", current_df['interviewee_name'].nunique())
                    else:
                        st.metric("Interviewees", "N/A")
                
                # Show sample data
                st.dataframe(current_df.head(10), use_container_width=True)
            else:
                st.info("📭 No data found for current client")
    
    except Exception as e:
        st.error(f"❌ Error in database management: {e}")
        st.exception(e)

# --- Add helper to show labeled quotes ---
def show_labeled_quotes():
    st.subheader("📋 Labeled Quotes (Stage 2 Results)")
    client_id = get_client_id()  # Use helper function
    df = db.get_stage2_response_labeling(client_id=client_id)
    if df.empty:
        st.info("No labeled quotes found. Run Stage 2 analysis.")
        return
    # Show a summary table
    display_cols = [
        'quote_id', 'criterion', 'score', 'priority', 'confidence',
        'relevance_explanation', 'deal_weighted_score', 'context_keywords', 'question_relevance'
    ]
    display_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)
    # Export option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Labeled Quotes CSV",
        data=csv,
        file_name="labeled_quotes.csv",
        mime="text/csv",
        key="download_labeled_quotes"
    )

# --- Add helper to show findings ---
def show_findings():
    st.subheader("🔍 Findings (Stage 3 Results)")
    client_id = get_client_id()  # Use helper function
    df = db.get_stage3_findings(client_id=client_id)
    if df.empty:
        st.info("No findings found. Run Stage 3 analysis.")
        return
    display_cols = [
        'criterion', 'finding_type', 'priority_level', 'enhanced_confidence',
        'criteria_met', 'summary', 'selected_quotes', 'themes', 'deal_impacts'
    ]
    display_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Findings CSV",
        data=csv,
        file_name="findings.csv",
        mime="text/csv",
        key="download_findings"
    )

# Main Streamlit App Interface
def main():
    st.set_page_config(
        page_title="VOC Pipeline UI",
        page_icon="🎤",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'uploaded_paths' not in st.session_state:
        st.session_state.uploaded_paths = []
    if 'client_id' not in st.session_state:
        st.session_state.client_id = ''  # Start with empty client_id to force input
    
    # Sidebar navigation
    st.sidebar.title("🎤 VOC Pipeline")
    
    # Client ID selector with persistence and validation
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Client Settings")
    
    # Check if client_id is properly set (not default or empty)
    current_client_id = st.session_state.get('client_id', '')
    is_client_set = current_client_id and current_client_id != 'default'
    
    if not is_client_set:
        # Force client ID input if not properly set
        st.sidebar.warning("⚠️ **Client ID Required**")
        st.sidebar.info("Please enter a client ID to continue. This ensures your data is properly organized.")
        
        # Client ID input with strict validation
        new_client_id = st.sidebar.text_input(
            "🔑 Client ID *",
            value="",
            help="Enter a unique identifier for this client's data. This ensures data isolation between different clients.",
            placeholder="e.g., Rev, AcmeCorp, ProjectAlpha",
            key="client_id_input"
        )
        
        # Validate client ID
        if new_client_id:
            # Clean the client ID (alphanumeric, underscores, and periods only)
            clean_client_id = re.sub(r'[^a-zA-Z0-9_.]', '', new_client_id.strip())
            
            if clean_client_id != new_client_id.strip():
                st.sidebar.warning(f"⚠️ Client ID cleaned to: {clean_client_id}")
            
            if len(clean_client_id) < 2:
                st.sidebar.error("❌ Client ID must be at least 2 characters long")
            elif clean_client_id.lower() in ['default', 'test', 'demo', 'example']:
                st.sidebar.error("❌ Please use a meaningful client ID, not a placeholder")
            else:
                st.session_state.client_id = clean_client_id
                st.sidebar.success(f"✅ Client ID set to: {clean_client_id}")
                st.sidebar.info("🔄 Refreshing interface...")
                st.rerun()
        else:
            st.sidebar.error("❌ Client ID is required to continue")
            
        # Show helpful examples
        st.sidebar.markdown("**💡 Examples:**")
        st.sidebar.markdown("- `Rev` (for Rev company)")
        st.sidebar.markdown("- `AcmeCorp` (for Acme Corporation)")
        st.sidebar.markdown("- `ProjectAlpha` (for specific project)")
        st.sidebar.markdown("- `Client_2024` (for time-based organization)")
        
    else:
        # Client ID is properly set - show current status and allow changes
        st.sidebar.success(f"✅ **Current Client:** `{current_client_id}`")
        
        # Show client data summary if available
        if SUPABASE_AVAILABLE:
            try:
                client_summary = db.get_client_summary()
                current_count = client_summary.get(current_client_id, 0)
                total_records = sum(client_summary.values())
                
                if current_count > 0:
                    st.sidebar.metric("📊 Your Records", current_count)
                else:
                    st.sidebar.info("📭 No data yet for this client")
                    
                if total_records > current_count:
                    st.sidebar.info(f"📈 {total_records - current_count} records for other clients")
                    
            except Exception as e:
                st.sidebar.warning("⚠️ Could not load client data")
        
        # Option to change client ID
        if st.sidebar.button("🔄 Change Client ID", help="Switch to a different client"):
            st.session_state.client_id = ''
            st.sidebar.info("🔄 Please enter a new client ID above")
            st.rerun()
        
        # Option to see all clients (if database available)
        if SUPABASE_AVAILABLE:
            try:
                client_summary = db.get_client_summary()
                if len(client_summary) > 1:
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("**🔍 Other Clients:**")
                    for client, count in sorted(client_summary.items()):
                        if client != current_client_id:
                            if st.sidebar.button(f"📊 {client} ({count} records)", key=f"switch_{client}"):
                                st.session_state.client_id = client
                                st.sidebar.success(f"✅ Switched to: {client}")
                                st.rerun()
            except:
                pass
    
    # Navigation options with cleaner labels
    nav_options = {
        "🏠 Welcome": "welcome",
        "📤 Upload Files": "upload",
        "📊 Stage 1: Extract Quotes": "stage1",
        "🎯 Stage 2: Label Quotes": "stage2",
        "🔍 Stage 3: Findings": "stage3",
        "🎨 Stage 4: Generate Themes": "stage4",
        "📈 Stage 5: Executive Summary": "stage5",
        "📝 Prompts & Details": "prompts",
        "🗄️ Database Status": "database",
        "🗄️ Database Management": "database_management"
    }
    
    # Determine default page based on current step
    default_index = 0  # Welcome
    if st.session_state.current_step == 1:
        default_index = 2  # Stage 1: Extract Quotes
    elif st.session_state.current_step == 2:
        default_index = 3  # Stage 2: Label Quotes
    elif st.session_state.current_step == 3:
        default_index = 4  # Stage 3: Findings
    elif st.session_state.current_step == 4:
        default_index = 5  # Stage 4: Generate Themes
    elif st.session_state.current_step == 5:
        default_index = 6  # Stage 5: Executive Summary
    
    selected = st.sidebar.selectbox(
        "Navigation",
        list(nav_options.keys()),
        index=default_index
    )
    
    # Route to appropriate page
    page = nav_options[selected]
    
    if page == "welcome":
        show_welcome_screen()
    elif page == "upload":
        st.title("📤 Upload Interview Files")
        st.markdown("Upload your interview transcripts to extract customer quotes and insights.")
        
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
            
            # Process button with better UX
            if st.button("🚀 Extract Quotes", type="primary", help="Process files to extract customer quotes"):
                with st.spinner("Extracting quotes from interviews..."):
                    process_files_with_progress()
                    if SUPABASE_AVAILABLE and os.path.exists(STAGE1_CSV):
                        if save_stage1_to_supabase(STAGE1_CSV):
                            st.success("✅ Quotes extracted and saved to database")
                            # Do NOT auto-progress. Stay on Stage 1 for review.
                            st.session_state.current_step = 1
                            st.rerun()
                        else:
                            st.error("❌ Failed to save to database")
    
    elif page == "stage1":
        st.title("📊 Stage 1: Quote Extraction")
        if os.path.exists(STAGE1_CSV):
            st.success("✅ Quotes extracted successfully")
            df = load_csv(STAGE1_CSV)
            if not df.empty:
                st.subheader("📋 Extracted Quotes")
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
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Quotes",
                    data=csv,
                    file_name="extracted_quotes.csv",
                    mime="text/csv",
                    key="download_extracted_quotes"
                )
                # CTA button to proceed to Stage 2
                if st.button("🎯 Proceed to Stage 2: Label Quotes", type="primary"):
                    st.session_state.current_step = 2
                    st.rerun()
                st.info("💡 Review your extracted quotes above. When ready, proceed to Stage 2 to label them.")
        else:
            st.info("📤 Please upload and process files first")
            st.markdown(PROCESSING_DETAILS)
    
    elif page == "stage2":
        st.title("🎯 Stage 2: Quote Labeling & Analysis")
        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
            st.info("Please configure your .env file with database credentials")
        else:
            client_summary = db.get_client_summary()
            current_client = get_client_id()  # Use helper function
            current_count = client_summary.get(current_client, 0)
            total_records = sum(client_summary.values())
            if total_records > 0 and current_count == 0:
                st.warning("⚠️ **Data Found But Not for Current Client**")
                st.info(f"📊 Found {total_records} total records across {len(client_summary)} clients, but 0 for current client '{current_client}'")
                st.info("💡 **Solution**: Go to 'Database Management' to see all data and set the correct client ID")
                if len(client_summary) > 1:
                    st.subheader("🔧 Quick Fix: Switch Client")
                    col1, col2 = st.columns(2)
                    with col1:
                        available_clients = list(client_summary.keys())
                        new_client = st.selectbox(
                            "Select Client with Data",
                            available_clients,
                            index=0
                        )
                    with col2:
                        if st.button("✅ Switch to This Client"):
                            st.session_state.client_id = new_client
                            st.success(f"✅ Switched to client: {new_client}")
                            st.info("🔄 Refreshing...")
                            st.rerun()
            summary = get_stage2_summary()
            if summary and summary.get('total_quotes', 0) > 0:
                st.success(f"✅ Found {summary['total_quotes']} quotes ready for labeling")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Quotes", summary['total_quotes'])
                with col2:
                    st.metric("Labeled Quotes", summary['quotes_with_scores'])
                with col3:
                    st.metric("Analysis Coverage", f"{summary['coverage_percentage']}%")
                if st.button("🔄 Label Quotes", type="primary", help="Label quotes against 10 evaluation criteria"):
                    with st.spinner("Labeling quotes against criteria..."):
                        result = run_stage2_analysis()
                        if result:
                            st.success("✅ Quote labeling complete!")
                            st.rerun()
                        else:
                            st.error("❌ Quote labeling failed")
                # Show labeled quotes if available
                show_labeled_quotes()
                if summary['quotes_with_scores'] > 0:
                    if st.button("🔍 Proceed to Stage 3: Identify Findings", type="primary"):
                        st.session_state.current_step = 3
                        st.rerun()
            else:
                st.info("📤 Please upload and process files first, then extract quotes")
    
    elif page == "stage3":
        st.title("🔍 Stage 3: Findings Identification")
        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
        else:
            stage2_summary = get_stage2_summary()
            if not stage2_summary or stage2_summary.get('quotes_with_scores', 0) == 0:
                st.info("📊 Please run Stage 2 quote scoring first")
            else:
                findings_summary = get_stage3_summary()
                if findings_summary:
                    st.success(f"✅ Found {findings_summary.get('total_findings', 0)} findings")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Findings", findings_summary.get('total_findings', 0))
                    with col2:
                        st.metric("Priority Findings", findings_summary.get('priority_findings', 0))
                    with col3:
                        st.metric("High Confidence", findings_summary.get('high_confidence_findings', findings_summary.get('priority_findings', 0)))
                    if st.button("🔍 Identify Findings", type="primary", help="Identify key findings and insights from labeled quotes"):
                        with st.spinner("Identifying findings and insights..."):
                            result = run_stage3_analysis()
                            if result:
                                st.success("✅ Findings identification complete!")
                                # Only show findings once, after analysis or on page load
                                show_findings()
                                if st.button("🎨 Proceed to Stage 4: Generate Themes", type="primary"):
                                    st.session_state.current_step = 4
                                    st.rerun()
                            else:
                                st.error("❌ Findings identification failed")
                    else:
                        # Only show findings once, not duplicated
                        show_findings()
                        if findings_summary.get('total_findings', 0) > 0:
                            if st.button("🎨 Proceed to Stage 4: Generate Themes", type="primary"):
                                st.session_state.current_step = 4
                                st.rerun()
                else:
                    st.info("📊 No findings available yet. Run the analysis to identify findings.")
    
    elif page == "stage4":
        st.title("🎨 Stage 4: Theme Generation")
        
        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
        else:
            # Check if we have Stage 3 data
            findings_summary = get_stage3_summary()
            if not findings_summary or findings_summary.get('total_findings', 0) == 0:
                st.info("📊 Please run Stage 3 findings analysis first")
            else:
                # Show current themes status
                themes_summary = get_stage4_summary()
                if themes_summary:
                    st.success(f"✅ Generated {themes_summary.get('total_themes', 0)} themes")
                    # Only keep the main theme display section
                    show_stage4_themes()
                    # CTA button to go to Stage 5
                    if st.button("📈 Continue to Stage 5: Executive Summary", type="primary", help="Move to the final stage to create executive synthesis"):
                        st.session_state.current_step = 5
                        st.rerun()
                else:
                    st.info("📊 No themes available yet. Run the analysis to generate themes.")
    
    elif page == "stage5":
        st.title("📈 Stage 5: Executive Synthesis")
        
        if not SUPABASE_AVAILABLE:
            st.error("❌ Database not available")
        else:
            # Check if we have Stage 4 data
            themes_summary = get_stage4_summary()
            if not themes_summary or themes_summary.get('total_themes', 0) == 0:
                st.info("📊 Please run Stage 4 theme generation first")
            else:
                # Show current synthesis status
                synthesis_summary = get_stage5_summary()
                if synthesis_summary:
                    st.success(f"✅ Executive synthesis available")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Executive Themes", synthesis_summary.get('executive_themes', 0))
                    with col2:
                        st.metric("Priority Areas", synthesis_summary.get('priority_areas', 0))
                    with col3:
                        st.metric("Quality Score", f"{synthesis_summary.get('quality_score', 0):.1f}")
                    
                    # Run analysis button
                    if st.button("🔄 Create Synthesis", type="primary", help="Generate executive synthesis and recommendations"):
                        with st.spinner("Creating executive synthesis..."):
                            result = run_stage5_analysis()
                            if result:
                                st.success("✅ Executive synthesis complete!")
                                st.json(result)
                            else:
                                st.error("❌ Executive synthesis failed")
                    
                    # Show synthesis if available
                    if synthesis_summary.get('executive_themes', 0) > 0:
                        st.subheader("📈 Executive Summary")
                        show_stage5_synthesis()
                        
                        st.subheader("📊 Criteria Scorecard")
                        show_stage5_criteria_scorecard()
                        
                        # Completion message
                        st.success("🎉 **Pipeline Complete!** Your VOC analysis is ready for executive review.")
                        st.info("💡 You can now export your findings or run additional analysis as needed.")
                else:
                    st.info("📊 No synthesis available yet. Run the analysis to create executive summary.")
    
    elif page == "prompts":
        show_prompts_details()
    
    elif page == "database":
        show_supabase_status()
    elif page == "database_management":
        show_database_management()

# Streamlit app runs automatically when this file is executed
if __name__ == "__main__":
    main()


