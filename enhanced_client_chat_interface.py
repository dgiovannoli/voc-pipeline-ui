import streamlit as st
import pandas as pd
from supabase import create_client
import os
import json
from typing import List, Dict, Any
import openai
from datetime import datetime

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_client_data(client_id: str) -> Dict[str, Any]:
    """Fetch all relevant data for a specific client with enhanced context."""
    try:
        # Get themes with full context
        themes = supabase.table('stage4_themes').select('*').eq('client_id', client_id).execute()
        
        # Get findings with enhanced data
        findings = supabase.table('stage3_findings').select('*').eq('client_id', client_id).execute()
        
        # Get responses with metadata
        responses = supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).execute()
        
        # Get executive themes if available
        executive_themes = supabase.table('executive_themes').select('*').eq('client_id', client_id).execute()
        
        # Get criteria scorecard if available
        scorecard = supabase.table('criteria_scorecard').select('*').eq('client_id', client_id).execute()
        
        # Add debugging information
        if themes.data:
            st.sidebar.success(f"✅ Found {len(themes.data)} themes")
        if findings.data:
            st.sidebar.success(f"✅ Found {len(findings.data)} findings")
        if responses.data:
            st.sidebar.success(f"✅ Found {len(responses.data)} responses")
        if executive_themes.data:
            st.sidebar.success(f"✅ Found {len(executive_themes.data)} executive themes")
        if scorecard.data:
            st.sidebar.success(f"✅ Found {len(scorecard.data)} scorecard entries")
        
        return {
            'themes': themes.data,
            'findings': findings.data,
            'responses': responses.data,
            'executive_themes': executive_themes.data,
            'scorecard': scorecard.data
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return {}

def create_enhanced_system_prompt(client_data: Dict[str, Any]) -> str:
    """Create an enhanced system prompt with comprehensive data context."""
    
    # Build themes summary with strength and evidence
    themes_summary = ""
    for theme in client_data.get('themes', []):
        theme_statement = theme.get('theme_statement', 'N/A')
        theme_strength = theme.get('theme_strength', 'N/A')
        supporting_findings = theme.get('supporting_finding_ids', [])
        if isinstance(supporting_findings, str):
            supporting_findings = supporting_findings.split(',') if supporting_findings else []
        
        themes_summary += f"- {theme_statement}\n"
        themes_summary += f"  Strength: {theme_strength} | Supporting Findings: {len(supporting_findings)}\n\n"
    
    # Build findings summary with confidence and impact
    findings_summary = ""
    for finding in client_data.get('findings', []):
        finding_statement = finding.get('finding_statement', 'N/A')
        confidence = finding.get('enhanced_confidence', finding.get('confidence_score', 'N/A'))
        impact = finding.get('impact_score', 'N/A')
        companies = finding.get('companies_affected', 1)
        
        findings_summary += f"- {finding_statement}\n"
        findings_summary += f"  Confidence: {confidence} | Impact: {impact} | Companies: {companies}\n\n"
    
    # Build executive themes summary
    executive_summary = ""
    for theme in client_data.get('executive_themes', []):
        title = theme.get('theme_title', 'N/A')
        statement = theme.get('theme_statement', 'N/A')
        executive_summary += f"- {title}: {statement}\n"
    
    # Build scorecard summary
    scorecard_summary = ""
    for entry in client_data.get('scorecard', []):
        criterion = entry.get('criterion', 'N/A')
        performance = entry.get('performance_rating', 'N/A')
        priority = entry.get('executive_priority', 'N/A')
        scorecard_summary += f"- {criterion}: {performance} (Priority: {priority})\n"
    
    return f"""You are an expert AI assistant helping a client understand their comprehensive customer interview data. You have access to rich, structured insights that have been carefully analyzed and synthesized.

AVAILABLE DATA:
📊 Themes ({len(client_data.get('themes', []))}):
{themes_summary}

🔍 Key Findings ({len(client_data.get('findings', []))}):
{findings_summary}

💬 Customer Responses: {len(client_data.get('responses', []))} total responses

🎯 Executive Themes ({len(client_data.get('executive_themes', []))}):
{executive_summary}

📈 Performance Scorecard ({len(client_data.get('scorecard', []))}):
{scorecard_summary}

RESPONSE FRAMEWORK:
When answering questions, follow this comprehensive structure:

1. **Executive Summary (2-3 sentences):** High-level answer that directly addresses the question with key insights.

2. **Data-Driven Insights:** 
   - Reference specific themes and findings by name
   - Include confidence levels and impact scores where available
   - Mention the number of companies/respondents supporting each insight

3. **Direct Evidence:**
   - Provide 2-3 specific quotes from customer responses
   - Attribute each quote to the relevant company/interviewee
   - Include context about when/why the quote was given

4. **Strategic Context:**
   - Connect insights to broader business implications
   - Reference executive themes if relevant
   - Include performance scorecard data if applicable

5. **Actionable Recommendations:**
   - Suggest specific next steps based on the data
   - Prioritize recommendations by impact and feasibility
   - Reference supporting evidence for each recommendation

FORMATTING GUIDELINES:
- Use bold headers for each section
- Use bullet points for lists and evidence
- Include confidence scores and impact metrics where available
- Attribute all quotes to specific companies/interviewees
- Use professional, executive-level language
- Keep responses concise but comprehensive

EXAMPLE RESPONSE STRUCTURE:

**Executive Summary:**
[Clear, high-level answer with key metrics]

**Key Insights:**
• [Insight 1] - Supported by [X] companies, Confidence: [Y]
• [Insight 2] - Supported by [X] companies, Confidence: [Y]

**Direct Evidence:**
• "[Specific quote]" — [Company Name], [Context]
• "[Specific quote]" — [Company Name], [Context]

**Strategic Implications:**
[Connect to broader business impact and executive themes]

**Recommended Actions:**
1. [Action 1] - Priority: [High/Medium/Low], Impact: [High/Medium/Low]
2. [Action 2] - Priority: [High/Medium/Low], Impact: [High/Medium/Low]

Remember: This is their private customer interview data. Provide insights that are both strategic and actionable, always backed by specific evidence from their data."""

def chat_with_enhanced_data(user_message: str, client_data: Dict[str, Any]) -> str:
    """Send user message to OpenAI with enhanced client data context."""
    try:
        system_prompt = create_enhanced_system_prompt(client_data)
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"

def show_enhanced_data_summary(client_data: Dict[str, Any]):
    """Display an enhanced summary of the client's data."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Themes", len(client_data.get('themes', [])))
    
    with col2:
        st.metric("Findings", len(client_data.get('findings', [])))
    
    with col3:
        st.metric("Responses", len(client_data.get('responses', [])))
    
    with col4:
        st.metric("Executive Themes", len(client_data.get('executive_themes', [])))

def show_enhanced_themes_table(client_data: Dict[str, Any]):
    """Display themes in an enhanced table format."""
    if client_data.get('themes'):
        themes_df = pd.DataFrame(client_data['themes'])
        
        # Select relevant columns for display
        display_columns = []
        column_mapping = {
            'theme_title': 'Theme Title',
            'theme_statement': 'Theme Statement',
            'theme_strength': 'Strength',
            'supporting_finding_ids': 'Supporting Findings'
        }
        
        for col in column_mapping.keys():
            if col in themes_df.columns:
                display_columns.append(col)
        
        if display_columns:
            display_df = themes_df[display_columns].head(10)
            display_df = display_df.rename(columns=column_mapping)
            
            st.subheader("Key Themes")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No displayable theme columns found.")

def show_findings_insights(client_data: Dict[str, Any]):
    """Display findings with insights."""
    if client_data.get('findings'):
        findings_df = pd.DataFrame(client_data['findings'])
        
        # Show high-confidence findings
        high_confidence = findings_df[
            findings_df.get('enhanced_confidence', 0) >= 4.0
        ].head(5)
        
        if not high_confidence.empty:
            st.subheader("🔍 High-Confidence Insights")
            for _, finding in high_confidence.iterrows():
                with st.expander(f"Finding: {finding.get('finding_statement', 'N/A')[:100]}..."):
                    st.write(f"**Statement:** {finding.get('finding_statement', 'N/A')}")
                    st.write(f"**Confidence:** {finding.get('enhanced_confidence', 'N/A')}")
                    st.write(f"**Impact Score:** {finding.get('impact_score', 'N/A')}")
                    st.write(f"**Companies Affected:** {finding.get('companies_affected', 'N/A')}")

def show_executive_summary(client_data: Dict[str, Any]):
    """Display executive-level summary."""
    if client_data.get('executive_themes'):
        st.subheader("🎯 Executive Summary")
        
        for theme in client_data['executive_themes'][:3]:  # Show top 3
            with st.expander(f"Executive Theme: {theme.get('theme_title', 'N/A')}"):
                st.write(f"**Statement:** {theme.get('theme_statement', 'N/A')}")
                if theme.get('strategic_implications'):
                    st.write(f"**Strategic Implications:** {theme.get('strategic_implications')}")

def main():
    st.set_page_config(
        page_title="Customer Insights Chat - Enhanced",
        page_icon="💬",
        layout="wide"
    )
    
    st.title("💬 Customer Insights Chat - Enhanced")
    st.markdown("Ask questions about your customer interview data and get AI-powered insights with comprehensive context.")
    
    # Simple client ID input with validation
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Client Access")
    
    # Pre-populate with a default client ID for easy access
    default_client_id = "rev_winloss_2024"  # Change this to your client's ID
    
    client_id = st.sidebar.text_input(
        "Client ID",
        value=default_client_id,
        help="Enter your client identifier (e.g., rev_winloss_2024, acme_product_2024)",
        placeholder="company_project_year"
    )
    
    # Validate client ID format
    if client_id:
        if '_' in client_id and len(client_id.split('_')) >= 2:
            st.sidebar.success("✅ Valid Client ID Format")
        else:
            st.sidebar.warning("⚠️ Format: company_project_year")
    
    if st.sidebar.button("🚀 Load Data", type="primary"):
        with st.spinner("Loading your comprehensive data..."):
            client_data = get_client_data(client_id)
            if client_data and (client_data.get('themes') or client_data.get('findings') or client_data.get('responses')):
                st.session_state.client_data = client_data
                st.session_state.client_id = client_id
                st.success("✅ Data loaded successfully!")
                st.info(f"📊 Loaded data for client: {client_id}")
            else:
                st.error(f"❌ No data found for Client ID: {client_id}")
                st.info("💡 Try using a valid client ID or check your data.")
                st.session_state.client_data = None
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Show enhanced data summary if available
    if "client_data" in st.session_state and st.session_state.client_data:
        show_enhanced_data_summary(st.session_state.client_data)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Data Overview", "🔍 Insights", "🎯 Executive Summary"])
        
        with tab1:
            # Chat input at the top
            if prompt := st.chat_input("Ask about your customer insights..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Analyzing your data..."):
                    response = chat_with_enhanced_data(prompt, st.session_state.client_data)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        with tab2:
            show_enhanced_themes_table(st.session_state.client_data)
            
            # Show sample findings
            if st.session_state.client_data.get('findings'):
                st.subheader("Sample Findings")
                findings_df = pd.DataFrame(st.session_state.client_data['findings'])
                
                # Check which columns are available for findings
                findings_columns = []
                findings_mapping = {
                    'finding_statement': 'Finding Statement',
                    'enhanced_confidence': 'Confidence Score',
                    'impact_score': 'Impact Score',
                    'companies_affected': 'Companies Affected'
                }
                
                for col in findings_mapping.keys():
                    if col in findings_df.columns:
                        findings_columns.append(col)
                
                if findings_columns:
                    display_findings_df = findings_df[findings_columns].head(10)
                    display_findings_df = display_findings_df.rename(columns=findings_mapping)
                    
                    st.dataframe(display_findings_df, use_container_width=True)
                else:
                    st.warning("No displayable columns found in findings data.")
        
        with tab3:
            show_findings_insights(st.session_state.client_data)
        
        with tab4:
            show_executive_summary(st.session_state.client_data)
    
    else:
        st.info("👈 Enter your Client ID in the sidebar and click 'Load Data' to get started.")
        st.info("💡 Example Client ID: rev_winloss_2024")

if __name__ == "__main__":
    main() 