import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase_database import SupabaseDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase database
try:
    db = SupabaseDatabase()
    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    st.error(f"❌ Failed to connect to Supabase: {e}")

def get_client_id():
    """Safely get client_id from session state."""
    client_id = st.session_state.get('client_id', '')
    if not client_id or client_id == 'default':
        st.error("❌ **Client ID Required**")
        st.info("Please set a client ID in the sidebar before proceeding.")
        st.stop()
    return client_id

def show_supabase_status():
    """Show database connection status and data summary"""
    st.subheader("🗄️ Database Status")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Database not connected")
        st.info("💡 Make sure your .env file contains database credentials")
        return
    
    try:
        # Get summary statistics with client_id filtering
        client_id = get_client_id()
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
            current_client = get_client_id()
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

def show_welcome_screen():
    """Show welcome screen with pipeline overview"""
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
        - Go to "Stage 1: Data Response Table" section
        - Select your interview transcripts
        - Click "Extract Quotes"
        """)
    
    with col2:
        st.markdown("""
        **2. Analyze & Insights**
        - Run "Stage 2: Response Labeling" to evaluate criteria
        - Identify findings and generate themes
        - Create executive summary
        """)
    
    # Database status with better labels
    st.subheader("🗄️ Database Status")
    if SUPABASE_AVAILABLE:
        st.success("✅ Database Connected - Ready to process quotes")
        
        # Show quick stats with better labels
        try:
            from stage2_ui import get_stage2_summary
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

def show_admin_utilities():
    """Admin / Utilities - Database management, status, and utility functions"""
    st.title("🔧 Admin / Utilities")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["Database Status", "Database Management", "Welcome"])
    
    with tab1:
        show_supabase_status()
    
    with tab2:
        show_database_management()
    
    with tab3:
        show_welcome_screen() 

def show_admin_panel():
    """Show admin panel with various management options."""
    st.title("🔧 Admin Panel")
    
    tabs = st.tabs([
        "Database Status",
        "Database Management",
        "Welcome",
        "Stage 3 Findings LLM Prompt & Process"
    ])
    
    with tabs[0]:
        st.header("User Management")
        st.info("Manage users, roles, and permissions.")
        # Placeholder for user management UI
        st.write("User management UI goes here.")
    
    with tabs[1]:
        st.header("Logs")
        st.info("View system logs and application events.")
        # Placeholder for logs UI
        st.write("Logs UI goes here.")
    
    with tabs[2]:
        st.header("Settings")
        st.info("Configure application settings.")
        # Placeholder for settings UI
        st.write("Settings UI goes here.")
    
    with tabs[3]:
        st.header("Stage 3 Findings LLM Prompt & Process")
        st.markdown("""
### Actual LLM Prompt Used for Findings Extraction

The following is the **exact LLM prompt** used for Stage 3 findings extraction. This prompt is designed to generate executive-ready findings from structured interview response data, using automated confidence scoring and strict criteria. The criteria and methodology are based on the Buried Wins framework, as detailed in `Context/Findings Criteria.docx`.

<details><summary>Click to expand full LLM prompt</summary>
""")
        try:
            # Try different encodings to handle the file
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            findings_prompt = None
            
            for encoding in encodings:
                try:
                    with open('Context/Findings Prompt.txt', 'r', encoding=encoding) as f:
                        findings_prompt = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if findings_prompt:
                st.code(findings_prompt, language="text")
            else:
                st.error("Could not read findings prompt file with any encoding. File may be corrupted.")
                st.info("The prompt file contains encoding issues. Please check the file manually.")
        except Exception as e:
            st.error(f"Could not load findings prompt: {e}")
            st.info("The prompt file may have encoding issues or be missing.")
        
        st.markdown("""
</details>

---

### Chunking/Tokenization & Processing Details
- **LLM Model:** gpt-4o-mini (via LangChain)
- **Max Tokens:** 4000 per call
- **Batch Size:** All responses processed in single LLM call
- **Chunking:** Full dataset sent to LLM with structured prompt
- **Criteria:** 8 Buried Wins criteria (see prompt above)
- **Confidence Scoring:** Automated using multipliers for stakeholder, impact, and evidence strength
- **Deduplication:** Semantic deduplication handled by LLM
- **Edge Case Gold:** Single-source findings allowed only for executive+high salience+deal tipping point

### Processing Flow
1. **Data Preparation:** Convert stage1_data_responses to CSV format
2. **Prompt Assembly:** Load prompt from Context/Findings Prompt.txt + append criteria
3. **LLM Call:** Send full dataset and prompt to GPT-4o-mini
4. **Output Parsing:** Extract JSON response with findings_csv and summary
5. **Database Save:** Parse findings and save to stage3_findings table
6. **Summary Generation:** Display processing metrics and results

### Quality Assurance
- **Multi-source requirement:** Minimum 2 interviews (except Edge Case Gold)
- **Criteria threshold:** At least 2 of 8 criteria must be met
- **Confidence scoring:** Automated calculation using stakeholder/impact/evidence multipliers
- **Quote attribution:** All quotes must include Response_ID for traceability
- **Executive focus:** Findings designed for executive decision-making

### Reference Documents
- **Primary Prompt:** `Context/Findings Prompt.txt` (LLM system message)
- **Criteria Definition:** `Context/Findings Criteria.docx` (evaluation framework)
- **Output Format:** JSON with findings_csv and response_table_csv
- **Quality Standards:** Buried Wins v4.0 framework
""") 