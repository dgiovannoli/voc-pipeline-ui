import streamlit as st
import pandas as pd
from supabase import create_client
import os
import json
from typing import List, Dict, Any
import openai

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')  # Use anon key for client access
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_client_data(client_id: str) -> Dict[str, Any]:
    """Fetch all relevant data for a specific client."""
    try:
        # Get themes
        themes = supabase.table('stage4_themes').select('*').eq('client_id', client_id).execute()
        
        # Get findings
        findings = supabase.table('stage3_findings').select('*').eq('client_id', client_id).execute()
        
        # Get responses
        responses = supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).execute()
        
        return {
            'themes': themes.data,
            'findings': findings.data,
            'responses': responses.data
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return {}

def create_system_prompt(client_data: Dict[str, Any]) -> str:
    """Create a system prompt with the client's data context."""
    themes_summary = "\n".join([
        f"- {theme.get('theme_statement', 'N/A')} (Strength: {theme.get('strength', 'N/A')})"
        for theme in client_data.get('themes', [])
    ])
    
    findings_summary = "\n".join([
        f"- {finding.get('finding_statement', 'N/A')}"
        for finding in client_data.get('findings', [])
    ])
    
    return f"""You are an AI assistant helping a client understand their customer interview data.

AVAILABLE DATA:
Themes ({len(client_data.get('themes', []))}):
{themes_summary}

Key Findings ({len(client_data.get('findings', []))}):
{findings_summary}

Customer Responses: {len(client_data.get('responses', []))} total responses

INSTRUCTIONS:
- Answer questions about their customer interview insights
- Reference specific themes and findings when relevant
- Provide actionable insights based on the data
- Be conversational but professional
- If asked about specific topics, search through the themes and findings for relevant information
- Always cite the source (theme or finding) when making claims

Remember: This is their private customer interview data. Be helpful and insightful.""" 

def chat_with_data(user_message: str, client_data: Dict[str, Any]) -> str:
    """Send user message to OpenAI with client data context."""
    try:
        system_prompt = create_system_prompt(client_data)
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"

def show_data_summary(client_data: Dict[str, Any]):
    """Display a summary of the client's data."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Themes", len(client_data.get('themes', [])))
    
    with col2:
        st.metric("Findings", len(client_data.get('findings', [])))
    
    with col3:
        st.metric("Responses", len(client_data.get('responses', [])))

def show_themes_table(client_data: Dict[str, Any]):
    """Display themes in a table format."""
    if client_data.get('themes'):
        themes_df = pd.DataFrame(client_data['themes'])
        st.subheader("Key Themes")
        st.dataframe(
            themes_df[['theme_statement', 'strength', 'competitive_flag']].head(10),
            use_container_width=True
        )

def main():
    st.set_page_config(
        page_title="Customer Insights Chat",
        page_icon="💬",
        layout="wide"
    )
    
    st.title("💬 Customer Insights Chat")
    st.markdown("Ask questions about your customer interview data and get AI-powered insights.")
    
    # Client ID input (in production, this would be authenticated)
    client_id = st.sidebar.text_input("Client ID", value="demo_client")
    
    if st.sidebar.button("Load Data"):
        with st.spinner("Loading your data..."):
            client_data = get_client_data(client_id)
            if client_data:
                st.session_state.client_data = client_data
                st.success("Data loaded successfully!")
            else:
                st.error("Failed to load data. Please check your Client ID.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Show data summary if available
    if "client_data" in st.session_state:
        show_data_summary(st.session_state.client_data)
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["💬 Chat", "📊 Data Overview"])
        
        with tab1:
            # Chat interface
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input
            if prompt := st.chat_input("Ask about your customer insights..."):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = chat_with_data(prompt, st.session_state.client_data)
                        st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        with tab2:
            show_themes_table(st.session_state.client_data)
            
            # Show sample findings
            if st.session_state.client_data.get('findings'):
                st.subheader("Sample Findings")
                findings_df = pd.DataFrame(st.session_state.client_data['findings'])
                st.dataframe(
                    findings_df[['finding_statement', 'confidence_score']].head(10),
                    use_container_width=True
                )
    
    else:
        st.info("👈 Enter your Client ID in the sidebar and click 'Load Data' to get started.")

if __name__ == "__main__":
    main() 