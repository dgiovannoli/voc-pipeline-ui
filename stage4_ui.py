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

def run_stage4_analysis():
    """Run Stage 4 theme analysis with JSON-based process"""
    try:
        from stage4_theme_analyzer import Stage4ThemeAnalyzer
        client_id = get_client_id()
        
        with st.spinner("🔄 Running Stage 4 Analysis..."):
            analyzer = Stage4ThemeAnalyzer(client_id=client_id)
            result = analyzer.process_themes(client_id=client_id)
            
            if result:
                st.success("✅ Stage 4 analysis completed successfully!")
                st.rerun()
            else:
                st.error("❌ Stage 4 analysis failed")
                
        return result
    except Exception as e:
        st.error(f"Stage 4 analysis failed: {e}")
        return {"status": "error", "message": str(e)}

def get_stage4_summary():
    """Get Stage 4 themes and strategic alerts summary"""
    try:
        client_id = get_client_id()
        db = SupabaseDatabase()
        
        # Get themes and strategic alerts from the new schema
        themes_data = db.get_themes(client_id=client_id)
        
        if themes_data.empty:
            return {
                'total_themes': 0,
                'total_strategic_alerts': 0,
                'competitive_themes': 0,
                'companies_covered': 0
            }
        
        # Separate themes and strategic alerts
        themes = themes_data[themes_data['theme_type'] == 'theme']
        strategic_alerts = themes_data[themes_data['theme_type'] == 'strategic_alert']
        
        # Calculate competitive themes
        competitive_themes = len(themes[themes['competitive_flag'] == True])
        
        # Count unique companies
        all_companies = []
        for companies in themes_data['company_ids']:
            if companies and isinstance(companies, str):
                company_list = [c.strip() for c in companies.split(',') if c.strip()]
                all_companies.extend(company_list)
        
        companies_covered = len(set(all_companies))
        
        return {
            'total_themes': len(themes),
            'total_strategic_alerts': len(strategic_alerts),
            'competitive_themes': competitive_themes,
            'companies_covered': companies_covered
        }
        
    except Exception as e:
        st.error(f"Failed to get Stage 4 summary: {e}")
        return {
            'total_themes': 0,
            'total_strategic_alerts': 0,
            'competitive_themes': 0,
            'companies_covered': 0
        }

def show_stage4_themes():
    """Display Stage 4 themes and strategic alerts analysis"""
    st.subheader("🎯 Stage 4 — Consolidated Themes & Strategic Alerts")
    
    # Get summary
    summary = get_stage4_summary()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Themes", summary.get('total_themes', 0))
    
    with col2:
        st.metric("Strategic Alerts", summary.get('total_strategic_alerts', 0))
    
    with col3:
        st.metric("Competitive", summary.get('competitive_themes', 0))
    
    with col4:
        st.metric("Companies", summary.get('companies_covered', 0))
    
    # Run analysis button
    if st.button("🔄 Run Stage 4 Analysis", type="primary"):
        run_stage4_analysis()
    
    # Show current themes status
    themes_summary = get_stage4_summary()
    total_items = themes_summary.get('total_themes', 0) + themes_summary.get('total_strategic_alerts', 0)
    
    if total_items > 0:
        st.success(f"✅ Generated {themes_summary.get('total_themes', 0)} themes and {themes_summary.get('total_strategic_alerts', 0)} strategic alerts")
        # CTA button to go to Stage 5
        if st.button("📈 Continue to Stage 5: Executive Summary", type="primary"):
            st.session_state.current_step = 5
            st.rerun()
    else:
        st.info("📊 No themes or strategic alerts available yet. Run the analysis to generate them.")
    
    # Deduplication control (post-generation)
    with st.expander("🧹 Deduplicate & Merge Themes (post-generation)", expanded=False):
        st.info("Detects near-duplicate themes across research/discovered, merges evidence, and marks merged children.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔍 Dry Run (no changes)"):
                with st.spinner("Analyzing duplicates..."):
                    try:
                        from scripts.deduplicate_themes import dedup_client
                        result = dedup_client(db, client_id, dry_run=True)
                        st.success(f"Groups: {result.get('groups')} | Canonicals: {result.get('canonicals')} | Merged pairs (simulated): {result.get('merged_pairs')}")
                    except Exception as e:
                        st.error(f"Dedup dry run failed: {e}")
        with col_b:
            if st.button("✅ Apply Merge (write)"):
                with st.spinner("Merging duplicates..."):
                    try:
                        from scripts.deduplicate_themes import dedup_client
                        result = dedup_client(db, client_id, dry_run=False)
                        st.success(f"Merged pairs applied: {result.get('merged_pairs')} across {result.get('groups')} groups")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Dedup write failed: {e}")

    # Get themes data
    client_id = get_client_id()
    themes_df = db.get_themes(client_id=client_id)
    
    # Display themes and alerts in a table
    if not themes_df.empty:
        # Create display dataframe with proper field mapping
        display_data = []
        for _, row in themes_df.iterrows():
            if row['theme_type'] == 'strategic_alert':
                # Use alert fields for strategic alerts
                display_data.append({
                    'Type': 'Strategic Alert',
                    'Title': row.get('alert_title', 'No title'),
                    'Statement': row.get('alert_statement', 'No description'),
                    'Classification': row.get('alert_classification', 'No classification'),
                    'Deal Context': 'N/A',  # Alerts don't have deal context
                    'Competitive': 'No',  # Alerts are not competitive
                    'Primary Quote': row.get('primary_alert_quote', 'No quote'),
                    'Strategic Implications': row.get('strategic_implications', 'No implications'),
                    'Supporting Findings': row.get('supporting_alert_finding_ids', 'No findings'),
                    'Companies': row.get('alert_company_ids', 'No companies'),
                    'Created': row.get('created_at', 'Unknown')
                })
            else:
                # Use theme fields for themes
                display_data.append({
                    'Type': 'Theme',
                    'Title': row.get('theme_title', 'No title'),
                    'Statement': row.get('theme_statement', 'No description'),
                    'Classification': row.get('classification', 'No classification'),
                    'Deal Context': row.get('deal_context', 'No context'),
                    'Competitive': 'Yes' if row.get('competitive_flag') else 'No',
                    'Primary Quote': row.get('primary_quote', 'No quote'),
                    'Strategic Implications': row.get('metadata_insights', 'No insights'),
                    'Supporting Findings': row.get('supporting_finding_ids', 'No findings'),
                    'Companies': row.get('company_ids', 'No companies'),
                    'Created': row.get('created_at', 'Unknown')
                })
        
        display_df = pd.DataFrame(display_data)
        
        # Display the table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    
    # Show detailed theme and strategic alert information in expandable sections
    if not themes_df.empty:
        st.markdown("---")
        st.subheader("🔍 Detailed Theme & Strategic Alert Information")
        
        for idx, item in themes_df.iterrows():
            item_type = item.get('theme_type', 'theme')
            
            # Handle None values safely
            if item_type == 'strategic_alert':
                title = item.get('alert_title', 'No title')
                statement = item.get('alert_statement', 'No description')
                classification = item.get('alert_classification', 'No classification')
                implications = item.get('strategic_implications', 'No implications')
                primary_quote = item.get('primary_alert_quote', 'No quote')
                secondary_quote = item.get('secondary_alert_quote', 'No quote')
                supporting_findings = item.get('supporting_alert_finding_ids', 'No findings')
                companies = item.get('alert_company_ids', 'No companies')
            else:
                title = item.get('theme_title', 'No title')
                statement = item.get('theme_statement', 'No description')
                classification = item.get('classification', 'No classification')
                implications = item.get('metadata_insights', 'No insights')
                primary_quote = item.get('primary_quote', 'No quote')
                secondary_quote = item.get('secondary_quote', 'No quote')
                supporting_findings = item.get('supporting_finding_ids', 'No findings')
                companies = item.get('company_ids', 'No companies')
            
            if title is None:
                title = 'No title'
            if statement is None:
                statement = 'No description'
            
            # Create safe display title
            display_title = title[:50] + "..." if len(str(title)) > 50 else str(title)
            
            with st.expander(f"{item_type.title()} {idx + 1}: {display_title}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {item_type.title()}")
                    st.write(f"**Title:** {title}")
                    st.write(f"**Statement:** {statement}")
                    st.write(f"**Classification:** {classification}")
                    if item_type == 'theme':
                        st.write(f"**Deal Context:** {item.get('deal_context', 'No context')}")
                        st.write(f"**Competitive:** {'Yes' if item.get('competitive_flag') else 'No'}")
                    else:
                        st.write(f"**Strategic Implications:** {implications}")
                
                with col2:
                    st.write(f"**Companies:** {companies}")
                    st.write(f"**Supporting Findings:** {supporting_findings}")
                    st.write(f"**Primary Quote:** {primary_quote}")
                    st.write(f"**Secondary Quote:** {secondary_quote}")
                    st.write(f"**Created:** {item.get('created_at', 'Unknown')}")
                
                # Show quotes if available
                if primary_quote or secondary_quote:
                    st.markdown("---")
                    st.subheader("📝 Supporting Quotes")
                    
                    if primary_quote:
                        st.write("**Primary Quote:**")
                        st.write(f"*{primary_quote}*")
                    
                    if secondary_quote:
                        st.write("**Secondary Quote:**")
                        st.write(f"*{secondary_quote}*")
                
                # Show strategic implications for strategic alerts
                if item_type == 'strategic_alert':
                    if implications and implications != 'No implications':
                        st.markdown("---")
                        st.subheader("⚠️ Strategic Implications")
                        st.write(implications) 

# (moved deduplication UI into show_stage4_themes)

# Main entry point for Streamlit
if __name__ == "__main__":
    st.set_page_config(
        page_title="Stage 4: Theme & Strategic Alert Generation",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Stage 4: Theme & Strategic Alert Generation")
    st.markdown("---")
    
    # Add client ID input in sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        client_id = st.text_input(
            "Client ID",
            value=st.session_state.get('client_id', ''),
            help="Enter your client ID to filter data"
        )
        if client_id:
            st.session_state.client_id = client_id
            st.success(f"✅ Client ID set to: {client_id}")
        else:
            st.warning("⚠️ Please enter a Client ID")
    
    # Show the main content
    show_stage4_themes() 