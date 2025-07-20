#!/usr/bin/env python3
"""
Analyst Data Explorer - Streamlit Interface
Enables analysts to search and explore raw data with interview IDs and findings references
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_scripts.database.supabase_database import SupabaseDatabase
from official_scripts.enhanced_quote_scoring import EnhancedQuoteScoring

def main():
    st.set_page_config(
        page_title="Analyst Data Explorer",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Analyst Data Explorer")
    st.markdown("Search and explore raw data with interview IDs and findings references")
    
    # Initialize database connection
    try:
        db = SupabaseDatabase()
        quote_scoring = EnhancedQuoteScoring()
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return
    
    # Sidebar for filters
    st.sidebar.header("🔧 Search Filters")
    
    # Client selection
    client_id = st.sidebar.selectbox(
        "Select Client",
        ["Rev", "Other Client"],  # Add more clients as needed
        index=0
    )
    
    # Search options
    search_type = st.sidebar.selectbox(
        "Search Type",
        ["Quotes", "Findings", "Themes", "All"],
        index=0
    )
    
    # Search input
    search_query = st.sidebar.text_input(
        "Search Query",
        placeholder="Enter keywords to search..."
    )
    
    # Priority score filter
    min_priority = st.sidebar.slider(
        "Minimum Priority Score",
        min_value=0,
        max_value=13,
        value=0,
        help="Filter quotes by minimum priority score"
    )
    
    # Company filter
    companies = st.sidebar.multiselect(
        "Filter by Company",
        options=get_company_options(db, client_id),
        default=[]
    )
    
    # Role filter
    roles = st.sidebar.multiselect(
        "Filter by Role",
        options=get_role_options(db, client_id),
        default=[]
    )
    
    # Main content area
    if st.sidebar.button("🔍 Search Data"):
        with st.spinner("Searching data..."):
            results = search_data(db, client_id, search_type, search_query, min_priority, companies, roles)
            display_results(results, search_type)
    
    # Quick access sections
    st.header("📊 Quick Access")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 View All Quotes"):
            with st.spinner("Loading quotes..."):
                quotes = get_all_quotes(db, client_id)
                display_quotes_table(quotes)
    
    with col2:
        if st.button("🔍 View All Findings"):
            with st.spinner("Loading findings..."):
                findings = get_all_findings(db, client_id)
                display_findings_table(findings)
    
    with col3:
        if st.button("🎯 View All Themes"):
            with st.spinner("Loading themes..."):
                themes = get_all_themes(db, client_id)
                display_themes_table(themes)
    
    # Data overview
    st.header("📈 Data Overview")
    overview = get_data_overview(db, client_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quotes", overview['total_quotes'])
    
    with col2:
        st.metric("Total Findings", overview['total_findings'])
    
    with col3:
        st.metric("Total Themes", overview['total_themes'])
    
    with col4:
        st.metric("Unique Clients", overview['unique_clients'])

def get_company_options(db, client_id):
    """Get list of companies for filter dropdown"""
    try:
        quotes = db.get_stage1_data_responses_by_client(client_id)
        companies = quotes['company'].dropna().unique().tolist()
        return sorted(companies)
    except:
        return []

def get_role_options(db, client_id):
    """Get list of roles for filter dropdown"""
    try:
        quotes = db.get_stage1_data_responses_by_client(client_id)
        roles = quotes['interviewee_role'].dropna().unique().tolist()
        return sorted(roles)
    except:
        return []

def search_data(db, client_id, search_type, search_query, min_priority, companies, roles):
    """Search data based on filters"""
    results = {
        'quotes': [],
        'findings': [],
        'themes': []
    }
    
    try:
        if search_type in ["Quotes", "All"]:
            quotes = db.get_stage1_data_responses_by_client(client_id)
            
            # Apply filters
            if search_query:
                quotes = quotes[quotes['verbatim_response'].str.contains(search_query, case=False, na=False)]
            
            if companies:
                quotes = quotes[quotes['company'].isin(companies)]
            
            if roles:
                quotes = quotes[quotes['interviewee_role'].isin(roles)]
            
            # Score quotes and filter by priority
            scored_quotes = []
            for _, quote in quotes.iterrows():
                quote_dict = {
                    'quote_id': quote['response_id'],
                    'quote': quote['verbatim_response'],
                    'interviewee_name': quote.get('interviewee_name', 'Unknown'),
                    'company': quote.get('company', 'Unknown'),
                    'interviewee_role': quote.get('interviewee_role', 'Unknown'),
                    'interview_id': quote.get('interview_id', 'Unknown')
                }
                
                priority_score = quote_scoring.calculate_quote_priority_score(quote_dict)
                if priority_score['total_score'] >= min_priority:
                    quote_dict['priority_score'] = priority_score
                    scored_quotes.append(quote_dict)
            
            results['quotes'] = scored_quotes
        
        if search_type in ["Findings", "All"]:
            findings = db.get_stage3_findings(client_id)
            
            if search_query:
                findings = findings[findings['finding_statement'].str.contains(search_query, case=False, na=False)]
            
            results['findings'] = findings.to_dict('records')
        
        if search_type in ["Themes", "All"]:
            themes = db.get_themes(client_id)
            
            if search_query:
                themes = themes[
                    themes['theme_title'].str.contains(search_query, case=False, na=False) |
                    themes['theme_statement'].str.contains(search_query, case=False, na=False)
                ]
            
            results['themes'] = themes.to_dict('records')
    
    except Exception as e:
        st.error(f"Search error: {str(e)}")
    
    return results

def display_results(results, search_type):
    """Display search results"""
    if search_type in ["Quotes", "All"] and results['quotes']:
        st.header("📝 Quotes Results")
        
        # Sort by priority score
        results['quotes'].sort(key=lambda x: x['priority_score']['total_score'], reverse=True)
        
        for i, quote in enumerate(results['quotes'][:20], 1):  # Show top 20
            with st.expander(f"Quote {i} - {quote['priority_score']['priority_level']} ({quote['priority_score']['total_score']}/13)"):
                st.write(f"**Quote:** {quote['quote']}")
                st.write(f"**Interviewee:** {quote['interviewee_name']}")
                st.write(f"**Role:** {quote['interviewee_role']}")
                st.write(f"**Company:** {quote['company']}")
                st.write(f"**Interview ID:** {quote['interview_id']}")
                st.write(f"**Priority Score:** {quote['priority_score']['total_score']}/13")
                st.write(f"**Reasoning:** {'; '.join(quote['priority_score']['reasoning'])}")
    
    if search_type in ["Findings", "All"] and results['findings']:
        st.header("🔍 Findings Results")
        
        for i, finding in enumerate(results['findings'][:20], 1):  # Show top 20
            with st.expander(f"Finding {i} - Confidence: {finding.get('enhanced_confidence', 'N/A')}"):
                st.write(f"**Statement:** {finding['finding_statement']}")
                st.write(f"**Interviewee:** {finding.get('interviewee_name', 'Unknown')}")
                st.write(f"**Company:** {finding.get('company', 'Unknown')}")
                st.write(f"**Interview ID:** {finding.get('interview_id', 'Unknown')}")
                st.write(f"**Confidence:** {finding.get('enhanced_confidence', 'N/A')}")
    
    if search_type in ["Themes", "All"] and results['themes']:
        st.header("🎯 Themes Results")
        
        for i, theme in enumerate(results['themes'][:10], 1):  # Show top 10
            with st.expander(f"Theme {i} - {theme['theme_title']}"):
                st.write(f"**Title:** {theme['theme_title']}")
                st.write(f"**Statement:** {theme['theme_statement']}")
                st.write(f"**Classification:** {theme.get('classification', 'Unknown')}")
                st.write(f"**Theme ID:** {theme['theme_id']}")

def get_all_quotes(db, client_id):
    """Get all quotes for client"""
    try:
        quotes = db.get_stage1_data_responses_by_client(client_id)
        return quotes
    except Exception as e:
        st.error(f"Error loading quotes: {str(e)}")
        return pd.DataFrame()

def get_all_findings(db, client_id):
    """Get all findings for client"""
    try:
        findings = db.get_stage3_findings(client_id)
        return findings
    except Exception as e:
        st.error(f"Error loading findings: {str(e)}")
        return pd.DataFrame()

def get_all_themes(db, client_id):
    """Get all themes for client"""
    try:
        themes = db.get_themes(client_id)
        return themes
    except Exception as e:
        st.error(f"Error loading themes: {str(e)}")
        return pd.DataFrame()

def display_quotes_table(quotes):
    """Display quotes in a table format"""
    if quotes.empty:
        st.warning("No quotes found")
        return
    
    # Select columns to display
    display_columns = ['interviewee_name', 'company', 'interviewee_role', 'verbatim_response', 'interview_id']
    available_columns = [col for col in display_columns if col in quotes.columns]
    
    if available_columns:
        st.dataframe(quotes[available_columns], use_container_width=True)
    else:
        st.dataframe(quotes, use_container_width=True)

def display_findings_table(findings):
    """Display findings in a table format"""
    if findings.empty:
        st.warning("No findings found")
        return
    
    # Select columns to display
    display_columns = ['interviewee_name', 'company', 'finding_statement', 'enhanced_confidence', 'interview_id']
    available_columns = [col for col in display_columns if col in findings.columns]
    
    if available_columns:
        st.dataframe(findings[available_columns], use_container_width=True)
    else:
        st.dataframe(findings, use_container_width=True)

def display_themes_table(themes):
    """Display themes in a table format"""
    if themes.empty:
        st.warning("No themes found")
        return
    
    # Select columns to display
    display_columns = ['theme_title', 'theme_statement', 'classification', 'theme_id']
    available_columns = [col for col in display_columns if col in themes.columns]
    
    if available_columns:
        st.dataframe(themes[available_columns], use_container_width=True)
    else:
        st.dataframe(themes, use_container_width=True)

def get_data_overview(db, client_id):
    """Get data overview statistics"""
    try:
        quotes = db.get_stage1_data_responses_by_client(client_id)
        findings = db.get_stage3_findings(client_id)
        themes = db.get_themes(client_id)
        
        return {
            'total_quotes': len(quotes),
            'total_findings': len(findings),
            'total_themes': len(themes),
            'unique_clients': quotes['company'].nunique() if not quotes.empty else 0
        }
    except Exception as e:
        st.error(f"Error getting overview: {str(e)}")
        return {
            'total_quotes': 0,
            'total_findings': 0,
            'total_themes': 0,
            'unique_clients': 0
        }

if __name__ == "__main__":
    main() 