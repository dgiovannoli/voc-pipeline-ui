import streamlit as st
import pandas as pd
from supabase import create_client
import os
import json
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables from .env file (fallback)
load_dotenv()

# Configuration - Use Streamlit secrets if available, otherwise fall back to environment variables
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv('SUPABASE_URL'))
SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv('SUPABASE_ANON_KEY'))
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_client_data(client_id: str) -> Dict[str, Any]:
    """Fetch all relevant data for a specific client with enhanced context."""
    try:
        # Get themes with full context
        themes = supabase.table('stage4_themes').select('*').eq('client_id', client_id).execute()
        
        # Get findings with enhanced data - order by earliest date first
        findings = supabase.table('stage3_findings').select('*').eq('client_id', client_id).order('date', desc=False).execute()
        
        # Get responses with metadata - order by earliest date first
        responses = supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).order('interview_date', desc=False).execute()
        
        # Add debugging information
        if themes.data:
            st.sidebar.success(f"✅ Found {len(themes.data)} themes")
        if findings.data:
            st.sidebar.success(f"✅ Found {len(findings.data)} findings")
        if responses.data:
            st.sidebar.success(f"✅ Found {len(responses.data)} responses")
        
        return {
            'themes': themes.data,
            'findings': findings.data,
            'responses': responses.data
        }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return {}

def select_diversified_responses(responses: List[Dict], max_samples: int = 5) -> List[Dict]:
    """Select diversified sample responses prioritizing different companies and earliest dates."""
    if not responses:
        return []
    
    # Sort responses by date (earliest first)
    sorted_responses = sorted(responses, key=lambda x: x.get('interview_date', x.get('date_of_interview', '9999-12-31')))
    
    # Group responses by company
    company_groups = {}
    for response in sorted_responses:
        company = response.get('company', response.get('company_name', 'Unknown'))
        if company not in company_groups:
            company_groups[company] = []
        company_groups[company].append(response)
    
    # Select diversified sample
    selected_responses = []
    companies_selected = set()
    
    # First pass: select earliest response from each company
    for company, company_responses in company_groups.items():
        if len(selected_responses) >= max_samples:
            break
        if company not in companies_selected:
            # Take the earliest response from this company
            earliest_response = min(company_responses, key=lambda x: x.get('interview_date', x.get('date_of_interview', '9999-12-31')))
            selected_responses.append(earliest_response)
            companies_selected.add(company)
    
    # Second pass: if we have room, add more responses from different companies
    remaining_slots = max_samples - len(selected_responses)
    if remaining_slots > 0:
        for company, company_responses in company_groups.items():
            if len(selected_responses) >= max_samples:
                break
            # Skip companies we already selected from
            if company in companies_selected:
                continue
            # Take the earliest response from this company
            earliest_response = min(company_responses, key=lambda x: x.get('interview_date', x.get('date_of_interview', '9999-12-31')))
            selected_responses.append(earliest_response)
            companies_selected.add(company)
    
    # If we still have room, add more responses from companies we haven't selected from yet
    if len(selected_responses) < max_samples:
        for company, company_responses in company_groups.items():
            if len(selected_responses) >= max_samples:
                break
            # Get responses we haven't selected yet from this company
            selected_company_responses = [r for r in selected_responses if r.get('company', r.get('company_name', '')) == company]
            available_responses = [r for r in company_responses if r not in selected_company_responses]
            if available_responses:
                # Take the next earliest response
                next_earliest = min(available_responses, key=lambda x: x.get('interview_date', x.get('date_of_interview', '9999-12-31')))
                selected_responses.append(next_earliest)
    
    # Sort final selection by date (earliest first)
    selected_responses.sort(key=lambda x: x.get('interview_date', x.get('date_of_interview', '9999-12-31')))
    
    return selected_responses

def select_diversified_findings(findings: List[Dict], max_samples: int = 5) -> List[Dict]:
    """Select diversified sample findings prioritizing different companies and earliest dates."""
    if not findings:
        return []
    
    # Sort findings by date (earliest first)
    sorted_findings = sorted(findings, key=lambda x: x.get('date', '9999-12-31'))
    
    # Group findings by company
    company_groups = {}
    for finding in sorted_findings:
        company = finding.get('interview_company', 'Unknown')
        if company not in company_groups:
            company_groups[company] = []
        company_groups[company].append(finding)
    
    # Select diversified sample
    selected_findings = []
    companies_selected = set()
    
    # First pass: select earliest finding from each company
    for company, company_findings in company_groups.items():
        if len(selected_findings) >= max_samples:
            break
        if company not in companies_selected:
            # Take the earliest finding from this company
            earliest_finding = min(company_findings, key=lambda x: x.get('date', '9999-12-31'))
            selected_findings.append(earliest_finding)
            companies_selected.add(company)
    
    # Second pass: if we have room, add more findings from different companies
    remaining_slots = max_samples - len(selected_findings)
    if remaining_slots > 0:
        for company, company_findings in company_groups.items():
            if len(selected_findings) >= max_samples:
                break
            # Skip companies we already selected from
            if company in companies_selected:
                continue
            # Take the earliest finding from this company
            earliest_finding = min(company_findings, key=lambda x: x.get('date', '9999-12-31'))
            selected_findings.append(earliest_finding)
            companies_selected.add(company)
    
    # If we still have room, add more findings from companies we haven't selected from yet
    if len(selected_findings) < max_samples:
        for company, company_findings in company_groups.items():
            if len(selected_findings) >= max_samples:
                break
            # Get findings we haven't selected yet from this company
            selected_company_findings = [f for f in selected_findings if f.get('interview_company', '') == company]
            available_findings = [f for f in company_findings if f not in selected_company_findings]
            if available_findings:
                # Take the next earliest finding
                next_earliest = min(available_findings, key=lambda x: x.get('date', '9999-12-31'))
                selected_findings.append(next_earliest)
    
    # Sort final selection by date (earliest first)
    selected_findings.sort(key=lambda x: x.get('date', '9999-12-31'))
    
    return selected_findings

def create_best_in_class_system_prompt(client_data: Dict[str, Any]) -> str:
    """Create a best-in-class system prompt with comprehensive data context and citation requirements."""
    
    # Build comprehensive themes summary
    themes_summary = ""
    for theme in client_data.get('themes', []):
        theme_statement = theme.get('theme_statement', theme.get('theme_name', 'N/A'))
        theme_strength = theme.get('theme_strength', theme.get('theme_confidence', 'N/A'))
        supporting_findings = theme.get('supporting_finding_ids', theme.get('theme_findings', []))
        companies_affected = theme.get('companies_affected', theme.get('theme_companies_affected', 1))
        
        themes_summary += f"**Theme: {theme_statement}**\n"
        themes_summary += f"  - Strength: {theme_strength}\n"
        themes_summary += f"  - Companies Affected: {companies_affected}\n"
        themes_summary += f"  - Supporting Findings: {len(supporting_findings) if isinstance(supporting_findings, list) else 'N/A'}\n\n"
    
    # Build comprehensive findings summary with diversification
    findings_summary = ""
    all_findings = client_data.get('findings', [])
    
    # Select diversified findings (prioritize different companies and earliest dates)
    sample_findings = select_diversified_findings(all_findings, max_samples=5)
    
    for finding in sample_findings:
        finding_statement = finding.get('finding_statement', 'N/A')
        confidence = finding.get('enhanced_confidence', finding.get('confidence_score', 'N/A'))
        impact = finding.get('impact_score', 'N/A')
        companies = finding.get('companies_affected', 1)
        primary_quote = finding.get('primary_quote', 'N/A')
        secondary_quote = finding.get('secondary_quote', 'N/A')
        interview_company = finding.get('interview_company', 'N/A')
        priority_level = finding.get('priority_level', 'Standard Finding')
        deal_status = finding.get('deal_status', 'N/A')
        interviewee_name = finding.get('interviewee_name', 'N/A')
        interview_date = finding.get('date', 'N/A')
        finding_category = finding.get('finding_category', 'N/A')
        credibility_tier = finding.get('credibility_tier', 'N/A')
        evidence_strength = finding.get('evidence_strength', 'N/A')
        
        findings_summary += f"**Finding: {finding_statement}**\n"
        findings_summary += f"  - Confidence: {confidence}/10\n"
        findings_summary += f"  - Impact Score: {impact}/5\n"
        findings_summary += f"  - Priority: {priority_level}\n"
        findings_summary += f"  - Category: {finding_category}\n"
        findings_summary += f"  - Credibility Tier: {credibility_tier}\n"
        findings_summary += f"  - Evidence Strength: {evidence_strength}\n"
        findings_summary += f"  - Companies Affected: {companies}\n"
        findings_summary += f"  - Source Company: {interview_company}\n"
        findings_summary += f"  - Interviewee: {interviewee_name}\n"
        findings_summary += f"  - Deal Status: {deal_status}\n"
        findings_summary += f"  - Interview Date: {interview_date}\n"
        if primary_quote and primary_quote != 'N/A':
            findings_summary += f"  - Primary Quote: \"{primary_quote[:100]}...\"\n"
        if secondary_quote and secondary_quote != 'N/A':
            findings_summary += f"  - Secondary Quote: \"{secondary_quote[:100]}...\"\n"
        findings_summary += "\n"
    
    # Build sample responses summary with diversification
    responses_summary = ""
    all_responses = client_data.get('responses', [])
    
    # Select diversified sample responses (prioritize different companies and earliest dates)
    sample_responses = select_diversified_responses(all_responses, max_samples=5)
    
    for response in sample_responses:
        verbatim = response.get('verbatim_response', 'N/A')
        company = response.get('company', response.get('company_name', 'N/A'))
        interviewee = response.get('interviewee_name', 'N/A')
        subject = response.get('subject', 'N/A')
        deal_status = response.get('deal_status', 'N/A')
        interview_date = response.get('interview_date', response.get('date_of_interview', 'N/A'))
        industry = response.get('industry', 'N/A')
        segment = response.get('segment', 'N/A')
        
        responses_summary += f"**Response from {company} ({interviewee}):**\n"
        responses_summary += f"Subject: {subject}\n"
        responses_summary += f"Deal Status: {deal_status}\n"
        responses_summary += f"Interview Date: {interview_date}\n"
        responses_summary += f"Industry: {industry}\n"
        responses_summary += f"Segment: {segment}\n"
        responses_summary += f"\"{verbatim[:150]}...\"\n\n"
    
    return f"""You are an expert B2B SaaS research analyst providing strategic insights from customer interview data. Your responses must be evidence-driven, precisely cited, and executive-ready.

## AVAILABLE DATA SOURCES

### 📊 Synthesized Themes ({len(client_data.get('themes', []))}):
{themes_summary}

### 🔍 Key Findings ({len(client_data.get('findings', []))}):
{findings_summary}

### 💬 Customer Responses ({len(client_data.get('responses', []))}):
{responses_summary}

## RESPONSE FRAMEWORK REQUIREMENTS

### 1. **Executive Summary (2-3 sentences)**
- High-level answer with key metrics and confidence levels
- Reference specific themes and findings by name
- Include impact scores and company coverage

### 2. **Evidence-Based Insights**
- **MUST** reference specific themes and findings by ID/name
- Include confidence scores and impact metrics
- Mention number of companies/respondents supporting each insight
- Connect insights to broader business implications

### 3. **Direct Evidence with Full Attribution**
- Provide 2-3 specific verbatim quotes from customer responses
- **REQUIRED ATTRIBUTION**: Company name, interviewee name, context
- Include confidence scores and impact metrics for each quote
- Reference the specific finding or theme that supports each quote

### 4. **Strategic Context and Business Impact**
- Connect insights to executive themes when relevant
- Include performance metrics and competitive implications
- Reference specific business outcomes and strategic implications

### 5. **Actionable Recommendations with Evidence**
- Suggest specific next steps based on the data
- Prioritize by impact score and confidence level
- Reference supporting evidence for each recommendation
- Include expected business impact and timeline

## CITATION REQUIREMENTS

### For Every Claim:
- **Theme Reference**: "Supported by Theme: [Theme Name] (Strength: X/10)"
- **Finding Reference**: "Based on Finding: [Finding Statement] (Confidence: X/10)"
- **Quote Attribution**: "Quote from [Company Name] - [Interviewee Name]"
- **Impact Metrics**: "Impact Score: X/5, Companies Affected: Y"

### For Every Quote:
- **Full Attribution**: Company name, interviewee name, context
- **Confidence Level**: Based on finding confidence score
- **Business Context**: What this quote reveals about the business

## FORMATTING STANDARDS

### Headers:
- Use bold headers for each section
- Include metrics and confidence scores in headers

### Evidence Presentation:
- Use bullet points for lists and evidence
- Include confidence scores and impact metrics
- Attribute all quotes to specific companies/interviewees
- Reference specific themes and findings by name

### Professional Language:
- Executive-appropriate, neutral tone
- Specific, actionable insights
- Clear traceability to source data
- Strategic business implications

## EXAMPLE RESPONSE STRUCTURE:

**Executive Summary:**
[Clear, high-level answer with key metrics and confidence levels]

**Key Insights:**
• [Insight 1] - Supported by Theme: [Theme Name] (Strength: X/10), Confidence: Y/10
• [Insight 2] - Based on Finding: [Finding Statement] (Confidence: X/10), Impact: Y/5

**Direct Evidence:**
• "[Specific quote]" — [Company Name], [Interviewee Name] (Confidence: X/10)
• "[Specific quote]" — [Company Name], [Interviewee Name] (Confidence: X/10)

**Strategic Implications:**
[Connect to broader business impact and executive themes]

**Recommended Actions:**
1. [Action 1] - Priority: [High/Medium/Low], Impact: [High/Medium/Low], Evidence: [Theme/Finding Reference]
2. [Action 2] - Priority: [High/Medium/Low], Impact: [High/Medium/Low], Evidence: [Theme/Finding Reference]

## CRITICAL REQUIREMENTS:

1. **EVERY** claim must be supported by specific data
2. **EVERY** quote must have full attribution
3. **EVERY** insight must reference confidence scores
4. **EVERY** recommendation must cite supporting evidence
5. **NO** generic statements without data backing
6. **NO** unsourced quotes or claims
7. **MUST** use exact theme and finding names from the data
8. **MUST** include impact scores and confidence levels

Remember: This is their private customer interview data. Provide insights that are both strategic and actionable, always backed by specific evidence from their data with full traceability to source materials."""

def process_research_query(user_message: str, client_data: Dict[str, Any]) -> str:
    """Process research queries with best-in-class evidence and citation requirements."""
    
    # Create comprehensive system prompt
    system_prompt = create_best_in_class_system_prompt(client_data)
    
    # Enhanced user message with citation requirements
    enhanced_user_message = f"""
RESEARCH QUERY: {user_message}

REQUIRED RESPONSE ELEMENTS:
1. Executive summary with key metrics
2. Evidence-based insights with specific theme/finding references
3. Direct quotes with full attribution (company, interviewee, confidence)
4. Strategic implications with business impact
5. Actionable recommendations with supporting evidence

CITATION REQUIREMENTS:
- Reference specific themes and findings by name
- Include confidence scores and impact metrics
- Provide full attribution for all quotes
- Connect insights to broader business implications
"""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_user_message}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"

def show_data_summary(client_data: Dict[str, Any]):
    """Display a comprehensive summary of the client's data."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Themes", len(client_data.get('themes', [])))
    
    with col2:
        st.metric("Findings", len(client_data.get('findings', [])))
    
    with col3:
        st.metric("Responses", len(client_data.get('responses', [])))
    
    with col4:
        # Calculate average confidence
        findings = client_data.get('findings', [])
        if findings:
            confidences = [f.get('enhanced_confidence', f.get('confidence_score', 0)) for f in findings if f.get('enhanced_confidence') or f.get('confidence_score')]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            st.metric("Avg Confidence", f"{avg_confidence:.1f}/10")

def show_themes_table(client_data: Dict[str, Any]):
    """Display themes in a comprehensive table format."""
    if client_data.get('themes'):
        themes_df = pd.DataFrame(client_data['themes'])
        st.subheader("📊 Key Themes")
        
        # Check which columns are available and use them
        available_columns = []
        column_mapping = {
            'theme_statement': 'Theme Statement',
            'theme_name': 'Theme Name',
            'theme_strength': 'Strength', 
            'theme_confidence': 'Confidence',
            'competitive_flag': 'Competitive',
            'companies_affected': 'Companies Affected'
        }
        
        for col in column_mapping.keys():
            if col in themes_df.columns:
                available_columns.append(col)
        
        if available_columns:
            display_df = themes_df[available_columns].head(10)
            # Rename columns for display
            display_df = display_df.rename(columns=column_mapping)
            
            # Format boolean values
            if 'Competitive' in display_df.columns:
                display_df['Competitive'] = display_df['Competitive'].map({True: 'Yes', False: 'No'})
            
            st.dataframe(
                display_df,
                use_container_width=True
            )
        else:
            st.warning("No displayable columns found in themes data.")

def show_findings_table(client_data: Dict[str, Any]):
    """Display findings in a comprehensive table format."""
    if client_data.get('findings'):
        findings_df = pd.DataFrame(client_data['findings'])
        st.subheader("🔍 Key Findings")
        
        # Check which columns are available and use them
        available_columns = []
        column_mapping = {
            'finding_statement': 'Finding Statement',
            'confidence_score': 'Confidence Score',
            'enhanced_confidence': 'Enhanced Confidence',
            'impact_score': 'Impact Score',
            'priority_level': 'Priority Level',
            'interview_company': 'Company',
            'companies_affected': 'Companies Affected'
        }
        
        for col in column_mapping.keys():
            if col in findings_df.columns:
                available_columns.append(col)
        
        if available_columns:
            display_df = findings_df[available_columns].head(10)
            # Rename columns for display
            display_df = display_df.rename(columns=column_mapping)
            
            st.dataframe(
                display_df,
                use_container_width=True
            )
        else:
            st.warning("No displayable columns found in findings data.")

def main():
    st.set_page_config(
        page_title="Research-Grade Customer Insights",
        page_icon="🔬",
        layout="wide"
    )
    
    st.title("🔬 Research-Grade Customer Insights")
    st.markdown("Ask questions about your customer interview data and get evidence-driven, executive-ready insights with full citations.")
    
    # Client ID input (in production, this would be authenticated)
    client_id = st.sidebar.text_input("Client ID", value="demo_client")
    
    if st.sidebar.button("Load Data"):
        with st.spinner("Loading your research data..."):
            client_data = get_client_data(client_id)
            if client_data and (client_data.get('themes') or client_data.get('findings') or client_data.get('responses')):
                st.session_state.client_data = client_data
                st.success("Research data loaded successfully!")
            else:
                st.error(f"No research data found for Client ID: {client_id}")
                st.info("💡 Try using 'demo_client' or check your Client ID.")
                st.session_state.client_data = None
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Show data summary if available
    if "client_data" in st.session_state and st.session_state.client_data:
        show_data_summary(st.session_state.client_data)
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["🔬 Research Chat", "📊 Data Overview", "📈 Insights Dashboard"])
        
        with tab1:
            # Chat input at the top
            if prompt := st.chat_input("Ask a research question about your customer insights..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Analyzing research data..."):
                    response = process_research_query(prompt, st.session_state.client_data)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display chat messages in chronological order (oldest at the top)
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                show_themes_table(st.session_state.client_data)
            
            with col2:
                show_findings_table(st.session_state.client_data)
        
        with tab3:
            st.subheader("📈 Research Insights Dashboard")
            
            # Show high-confidence findings
            findings = st.session_state.client_data.get('findings', [])
            if findings:
                high_confidence_findings = [f for f in findings if f.get('enhanced_confidence', f.get('confidence_score', 0)) >= 7.0]
                if high_confidence_findings:
                    st.success(f"🎯 {len(high_confidence_findings)} High-Confidence Findings (≥7.0/10)")
                    for finding in high_confidence_findings[:3]:
                        with st.expander(f"Confidence: {finding.get('enhanced_confidence', finding.get('confidence_score', 'N/A'))}/10 - {finding.get('finding_statement', 'N/A')[:100]}..."):
                            st.write(f"**Statement:** {finding.get('finding_statement', 'N/A')}")
                            st.write(f"**Company:** {finding.get('interview_company', 'N/A')}")
                            st.write(f"**Impact Score:** {finding.get('impact_score', 'N/A')}/5")
                            if finding.get('primary_quote'):
                                st.write(f"**Key Quote:** \"{finding.get('primary_quote', 'N/A')}\"")
                else:
                    st.info("No high-confidence findings available.")
            
            # Show competitive themes
            themes = st.session_state.client_data.get('themes', [])
            if themes:
                competitive_themes = [t for t in themes if t.get('competitive_flag', False)]
                if competitive_themes:
                    st.warning(f"⚔️ {len(competitive_themes)} Competitive Themes")
                    for theme in competitive_themes[:3]:
                        with st.expander(f"Competitive Theme: {theme.get('theme_statement', theme.get('theme_name', 'N/A'))[:100]}..."):
                            st.write(f"**Statement:** {theme.get('theme_statement', theme.get('theme_name', 'N/A'))}")
                            st.write(f"**Strength:** {theme.get('theme_strength', theme.get('theme_confidence', 'N/A'))}")
                            st.write(f"**Companies Affected:** {theme.get('companies_affected', 'N/A')}")
                else:
                    st.info("No competitive themes identified.")
    
    else:
        st.info("👈 Enter your Client ID in the sidebar and click 'Load Data' to start your research analysis.")

if __name__ == "__main__":
    main() 