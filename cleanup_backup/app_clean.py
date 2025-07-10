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
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        return False
    return True

def save_uploaded_files(uploaded_files, upload_dir="uploads"):
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


# Constants
BASE = pathlib.Path(__file__).parent
STAGE1_CSV = BASE / "stage1_output.csv"
VALIDATED_CSV = BASE / "validated_quotes.csv"
RESPONSE_TABLE_CSV = BASE / "response_data_table.csv"

def process_files_with_progress():
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
        **Purpose**: Extract key insights and verbatim responses from interview transcripts
        
        **Process**:
        - Token-based chunking with ~2K tokens per chunk
        - Q&A-aware segmentation preserving conversation boundaries
        - LLM processing with GPT-3.5-turbo-16k
        - Extracts 3-5 insights per chunk with detailed verbatim responses
        **Chunking Strategy**:
        - Token-based chunking (not character-based)
        - ~2K tokens per chunk for optimal context
        - 200 token overlap for continuity
        - Q&A-aware segmentation
        
        **Processing**:
        - Parallel processing with ThreadPoolExecutor
        - Quality-focused extraction targeting ~5 insights per chunk
        - Enhanced validation for richer responses
        **Purpose**: Score extracted quotes against 10 executive criteria using binary + intensity scoring
        
        **Scoring System**:
        - **0**: Not relevant/not mentioned
        - **1**: Slight mention/indirect relevance  
        - **2**: Clear mention/direct relevance
        - **3**: Strong emphasis/important feedback
        - **4**: Critical feedback/deal-breaking issue
        - **5**: Exceptional praise/deal-winning strength
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
        **Deal Weighting**:
        - Lost deals: 1.2x base multiplier
        - Won deals: 0.9x base multiplier
        - Critical feedback: 1.5x multiplier
        - Minor feedback: 0.7x multiplier
        
        **Processing**:
        - Incremental processing (only new quotes)
        - Parallel processing with configurable workers
        - Context-aware scoring based on question relevance
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
        st.markdown(evaluation_criteria)
        
        
        st.subheader("📋 Stage 5 Prompt Template")
    with tab5:
        st.subheader("🏆 Stage 5: Executive Synthesis")
        
        st.subheader("📊 Criteria Scorecard Integration")
        
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
        
        st.subheader("📋 Executive Readiness")
    
    with tab6:
        st.subheader("⚙️ Configuration & Settings")
        
        st.subheader("🔧 Environment Variables")
        st.code(env_vars, language='bash')
        
        st.subheader("📊 Quality Assurance")

def show_welcome_screen():
    st.title("🎤 Voice of Customer Pipeline")
    st.markdown("### AI-Powered Quote Analysis & Insights")
    
    
    # Quick start with better flow
    st.subheader("🚀 Quick Start")
    
    col1, col2 = st.columns(2)
    
    with col1:
    
    with col2:
    
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
