import streamlit as st
import pandas as pd
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
        st.warning("⚠️ **Client ID Required**")
        st.info("Please set a Client ID in the sidebar before proceeding.")
        st.info("💡 **How to set Client ID:**")
        st.info("1. Look in the sidebar under '🏢 Client Settings'")
        st.info("2. Enter a unique identifier for this client's data")
        st.info("3. Press Enter to save")
        st.stop()
    return client_id

def get_curator_name():
    """Get curator name from session state or input."""
    if 'curator_name' not in st.session_state:
        st.session_state.curator_name = ''
    
    if not st.session_state.curator_name:
        curator_name = st.text_input("👤 Enter your name (for curation tracking):")
        if curator_name:
            st.session_state.curator_name = curator_name
            st.success(f"✅ Curator: {curator_name}")
            st.rerun()  # Rerun to continue with the curation process
        return None
    
    return st.session_state.curator_name

def get_themes_for_curation(client_id):
    """Get themes that need curation."""
    return db.get_themes_for_curation(client_id)

def get_quotes_for_theme(theme_id):
    """Get quotes for a theme by looking up supporting findings and their selected_quotes from stage3_findings."""
    import json
    try:
        # 1. Get supporting finding IDs from the theme
        theme_row = db.supabase.table('stage4_themes').select('supporting_finding_ids').eq('id', theme_id).execute()
        if not theme_row.data or not theme_row.data[0].get('supporting_finding_ids'):
            return pd.DataFrame()
        finding_ids = theme_row.data[0]['supporting_finding_ids']
        if isinstance(finding_ids, str):
            finding_ids = json.loads(finding_ids)
        if not finding_ids:
            return pd.DataFrame()
        # 2. Fetch all findings from stage3_findings
        findings_resp = db.supabase.table('stage3_findings').select('*').in_('id', finding_ids).execute()
        findings = findings_resp.data
        quotes_list = []
        for finding in findings:
            selected_quotes = finding.get('selected_quotes')
            if not selected_quotes:
                continue
            # Parse JSON if needed
            if isinstance(selected_quotes, str):
                try:
                    selected_quotes = json.loads(selected_quotes)
                except Exception:
                    continue
            # 3. For each quote in selected_quotes, extract details
            for quote in selected_quotes:
                quotes_list.append({
                    'id': quote.get('response_id', ''),
                    'text': quote.get('text', ''),
                    'sentiment': quote.get('sentiment', ''),
                    'priority_level': quote.get('priority_level', ''),
                    # Add more fields as needed
                })
        return pd.DataFrame(quotes_list)
    except Exception as e:
        st.error(f"Error getting quotes for theme: {e}")
        return pd.DataFrame()

def save_quote_curation(quote_id, curation_label, curator_name, notes=""):
    """Save curation decision for a quote within the theme's quotes column."""
    try:
        # Extract theme_id from quote_id (format: "theme_id_quote_index")
        theme_id = quote_id.split('_quote_')[0]
        
        # Get current theme data
        response = db.supabase.table('stage4_themes').select('quotes').eq('id', theme_id).execute()
        if not response.data:
            return False
        
        current_quotes = response.data[0].get('quotes', [])
        quote_index = int(quote_id.split('_quote_')[1])
        
        # Update the specific quote in the quotes array
        if isinstance(current_quotes, list) and quote_index < len(current_quotes):
            if isinstance(current_quotes[quote_index], dict):
                current_quotes[quote_index]['curation_label'] = curation_label
                current_quotes[quote_index]['curated_by'] = curator_name
                current_quotes[quote_index]['curated_at'] = datetime.now().isoformat()
                current_quotes[quote_index]['curator_notes'] = notes
            else:
                # If quote is just a string, convert to dict
                current_quotes[quote_index] = {
                    'text': str(current_quotes[quote_index]),
                    'curation_label': curation_label,
                    'curated_by': curator_name,
                    'curated_at': datetime.now().isoformat(),
                    'curator_notes': notes
                }
            
            # Update the theme with modified quotes
            update_data = {'quotes': current_quotes}
            db.supabase.table('stage4_themes').update(update_data).eq('id', theme_id).execute()
            return True
        
        return False
    except Exception as e:
        st.error(f"Error saving quote curation: {e}")
        return False

def save_theme_curation(theme_id, curation_status, curator_name, notes=""):
    """Save curation decision for a theme."""
    return db.save_theme_curation(theme_id, curation_status, curator_name, notes)

def show_curation_dashboard():
    """Show curation dashboard with progress and navigation."""
    st.subheader("🎯 Human Curation Dashboard")
    
    client_id = get_client_id()
    curator_name = get_curator_name()
    
    if not curator_name:
        st.info("Please enter your name to start curation.")
        return
    
    # Display current curator and option to change
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"👤 **Current Curator:** {curator_name}")
    with col2:
        if st.button("🔄 Change Curator"):
            st.session_state.curator_name = ''
            st.rerun()
    
    # Get themes for curation
    themes_df = get_themes_for_curation(client_id)
    
    if themes_df.empty:
        st.info("No themes found for curation.")
        return
    
    # Check if curation columns exist, if not show setup message
    if 'curation_status' not in themes_df.columns:
        st.warning("⚠️ **Database Schema Update Required**")
        st.info("The curation system requires database schema updates. Please run the database migration first.")
        st.markdown("""
        **To fix this:**
        1. The database needs to be updated with curation fields
        2. Contact your database administrator to run the migration
        3. Or manually add the following columns to your tables:
           - `stage4_themes`: `curation_status`, `curated_by`, `curated_at`, `curator_notes`
        """)
        return
    
    # Calculate curation progress with safe column access
    total_themes = len(themes_df)
    pending_themes = len(themes_df[themes_df.get('curation_status', 'pending') == 'pending'])
    approved_themes = len(themes_df[themes_df.get('curation_status', 'pending') == 'approved'])
    denied_themes = len(themes_df[themes_df.get('curation_status', 'pending') == 'denied'])
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Themes", total_themes)
    with col2:
        st.metric("Pending", pending_themes)
    with col3:
        st.metric("Approved", approved_themes)
    with col4:
        st.metric("Denied", denied_themes)
    
    # Progress bar
    if total_themes > 0:
        progress = (approved_themes + denied_themes) / total_themes
        st.progress(progress)
        st.caption(f"Progress: {int(progress * 100)}% complete")
    
    # Theme navigation
    st.markdown("---")
    st.subheader("📋 Theme Navigation")
    
    # Filter options
    filter_option = st.selectbox(
        "Show themes by status:",
        ["All", "Pending", "Approved", "Denied"]
    )
    
    if filter_option == "Pending":
        filtered_themes = themes_df[themes_df.get('curation_status', 'pending') == 'pending']
    elif filter_option == "Approved":
        filtered_themes = themes_df[themes_df.get('curation_status', 'pending') == 'approved']
    elif filter_option == "Denied":
        filtered_themes = themes_df[themes_df.get('curation_status', 'pending') == 'denied']
    else:
        filtered_themes = themes_df
    
    if filtered_themes.empty:
        st.info(f"No {filter_option.lower()} themes found.")
        return
    
    # Theme selector - use theme_statement instead of description
    theme_options = [f"{i+1}. {row.get('theme_statement', 'No description')[:50]}..." for i, (_, row) in enumerate(filtered_themes.iterrows())]
    selected_theme_idx = st.selectbox("Select theme to curate:", range(len(theme_options)), format_func=lambda x: theme_options[x])
    
    if selected_theme_idx is not None:
        selected_theme = filtered_themes.iloc[selected_theme_idx]
        show_theme_curation(selected_theme, curator_name)

def show_theme_curation(theme, curator_name):
    """Show individual theme curation interface."""
    st.markdown("---")
    st.subheader(f"🎯 Curating Theme: {theme.get('theme_statement', 'No description')}")
    
    # Theme info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**Theme Statement:** {theme.get('theme_statement', 'N/A')}")
        st.write(f"**Strength:** {theme.get('theme_strength', 'N/A')}")
        st.write(f"**Competitive:** {'Yes' if theme.get('competitive_flag', False) else 'No'}")
    
    with col2:
        st.write(f"**Current Status:** {theme.get('curation_status', 'pending').title()}")
        if theme.get('curated_by'):
            st.write(f"**Curated by:** {theme['curated_by']}")
        if theme.get('curated_at'):
            st.write(f"**Curated at:** {theme['curated_at'][:19]}")
    
    # Get quotes for this theme
    quotes_df = get_quotes_for_theme(theme['id'])
    
    if quotes_df.empty:
        st.warning("No quotes found for this theme.")
        return
    
    st.markdown("### 📝 Quote Review")
    st.caption(f"Review each quote and select: **Approve** (good for theme), **Deny** (not relevant), or **Feature** (especially strong)")
    
    # Quote curation interface
    quote_curations = {}
    
    for idx, quote in quotes_df.iterrows():
        st.markdown(f"---")
        st.markdown(f"**Quote {idx + 1}:**")
        
        # Display quote text
        quote_text = quote.get('text', str(quote))
        st.write(f"*\"{quote_text}\"*")
        
        # Quote metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Sentiment: {quote.get('sentiment', 'N/A')}")
        with col2:
            st.caption(f"Priority: {quote.get('priority_level', 'N/A')}")
        with col3:
            st.caption(f"Current: {quote.get('curation_label', 'pending')}")
        
        # Curation controls
        col1, col2 = st.columns([3, 1])
        with col1:
            curation_label = st.radio(
                "Curation Decision:",
                ["approve", "deny", "feature"],
                index=["approve", "deny", "feature"].index(quote.get('curation_label', 'approve')),
                key=f"quote_{quote['id']}_label",
                horizontal=True
            )
        
        with col2:
            if st.button("💾 Save Quote", key=f"save_quote_{quote['id']}"):
                if save_quote_curation(quote['id'], curation_label, curator_name):
                    st.success("✅ Quote saved!")
                    st.rerun()
        
        # Notes field
        notes = st.text_area(
            "Notes (optional):",
            value=quote.get('curator_notes', ''),
            key=f"notes_{quote['id']}",
            height=80
        )
        
        quote_curations[quote['id']] = {
            'label': curation_label,
            'notes': notes
        }
    
    # Theme-level curation
    st.markdown("---")
    st.subheader("🎯 Theme Decision")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        theme_status = st.radio(
            "Theme Status:",
            ["pending", "approved", "denied"],
            index=["pending", "approved", "denied"].index(theme.get('curation_status', 'pending')),
            horizontal=True
        )
        
        notes = st.text_area(
            "Notes (optional):",
            value=theme.get('curator_notes', ''),
            key=f"theme_notes_{theme['id']}",
            height=80
        )
    
    with col2:
        if st.button("💾 Save Theme Decision", type="primary"):
            if save_theme_curation(theme['id'], theme_status, curator_name, notes):
                st.success("✅ Theme decision saved!")
                st.rerun()
    
    # Summary of quote decisions
    st.markdown("### 📊 Quote Summary")
    approved_quotes = sum(1 for q in quote_curations.values() if q['label'] == 'approve')
    denied_quotes = sum(1 for q in quote_curations.values() if q['label'] == 'deny')
    featured_quotes = sum(1 for q in quote_curations.values() if q['label'] == 'feature')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Approved Quotes", approved_quotes)
    with col2:
        st.metric("Denied Quotes", denied_quotes)
    with col3:
        st.metric("Featured Quotes", featured_quotes)

def show_curation_export():
    """Show export options for curated content."""
    st.subheader("📤 Export Curated Content")
    
    client_id = get_client_id()
    
    # Get approved themes
    try:
        approved_themes = db.supabase.table('stage4_themes').select('*').eq('client_id', client_id).eq('curation_status', 'approved').execute()
        approved_df = pd.DataFrame(approved_themes.data)
        
        if not approved_df.empty:
            st.success(f"✅ Found {len(approved_df)} approved themes")
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Export Approved Themes (CSV)"):
                    csv = approved_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"approved_themes_{client_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("📊 Export with Quotes"):
                    # Get approved quotes for approved themes
                    theme_ids = approved_df['id'].tolist()
                    approved_quotes = db.supabase.table('quote_analysis').select('*').in_('theme_id', theme_ids).eq('curation_label', 'approve').execute()
                    quotes_df = pd.DataFrame(approved_quotes.data)
                    
                    if not quotes_df.empty:
                        # Merge themes with quotes
                        merged_df = pd.merge(quotes_df, approved_df[['id', 'theme_statement']], left_on='theme_id', right_on='id', suffixes=('_quote', '_theme'))
                        csv = merged_df.to_csv(index=False)
                        st.download_button(
                            label="Download with Quotes",
                            data=csv,
                            file_name=f"approved_themes_with_quotes_{client_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
        else:
            st.info("No approved themes found for export.")
            
    except Exception as e:
        st.error(f"Error exporting curated content: {e}")

def show_curation_ui():
    """Main curation UI function."""
    st.title("🎯 Human Curation & QA")
    st.markdown("Review and approve/deny themes and quotes before client delivery.")
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📋 Curation Dashboard", "📤 Export Curated Content"])
    
    with tab1:
        show_curation_dashboard()
    
    with tab2:
        show_curation_export() 