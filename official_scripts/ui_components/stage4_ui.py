import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from datetime import datetime
from official_scripts.database.supabase_database import SupabaseDatabase
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
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    """Display Stage 4 themes and strategic alerts"""
    try:
        client_id = get_client_id()
        db = SupabaseDatabase()
        
        # Get themes and strategic alerts
        themes_data = db.get_themes(client_id=client_id)
        
        if themes_data.empty:
            st.info("📊 No themes or strategic alerts found for this client.")
            return
        
        # Separate themes and strategic alerts
        themes = themes_data[themes_data['theme_type'] == 'theme']
        strategic_alerts = themes_data[themes_data['theme_type'] == 'strategic_alert']
        
        # Display themes
        if not themes.empty:
            st.subheader("🎯 Strategic Themes")
            for _, theme in themes.iterrows():
                with st.expander(f"**{theme['theme_statement']}**"):
                    st.write(f"**Theme Statement:** {theme['theme_statement']}")
                    st.write(f"**Strategic Impact:** {theme['strategic_impact']}")
                    st.write(f"**Evidence Count:** {theme['evidence_count']}")
                    st.write(f"**Competitive Flag:** {'Yes' if theme['competitive_flag'] else 'No'}")
                    if theme['company_ids']:
                        st.write(f"**Companies:** {theme['company_ids']}")
                    if theme['verbatim_quotes']:
                        st.write(f"**Key Quotes:** {theme['verbatim_quotes']}")
        
        # Display strategic alerts
        if not strategic_alerts.empty:
            st.subheader("🚨 Strategic Alerts")
            for _, alert in strategic_alerts.iterrows():
                with st.expander(f"**{alert['theme_statement']}**"):
                    st.write(f"**Alert Statement:** {alert['theme_statement']}")
                    st.write(f"**Strategic Impact:** {alert['strategic_impact']}")
                    st.write(f"**Evidence Count:** {alert['evidence_count']}")
                    st.write(f"**Competitive Flag:** {'Yes' if alert['competitive_flag'] else 'No'}")
                    if alert['company_ids']:
                        st.write(f"**Companies:** {alert['company_ids']}")
                    if alert['verbatim_quotes']:
                        st.write(f"**Key Quotes:** {alert['verbatim_quotes']}")
        
        # Display summary statistics
        summary = get_stage4_summary()
        st.subheader("📊 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Themes", summary['total_themes'])
        with col2:
            st.metric("Strategic Alerts", summary['total_strategic_alerts'])
        with col3:
            st.metric("Competitive Themes", summary['competitive_themes'])
        with col4:
            st.metric("Companies Covered", summary['companies_covered'])
            
    except Exception as e:
        st.error(f"Failed to display Stage 4 themes: {e}")

def main():
    """Main Stage 4 UI"""
    st.header("🎯 Stage 4: Strategic Theme Generation")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Cannot connect to database. Please check your configuration.")
        return
    
    # Client ID validation
    client_id = get_client_id()
    
    # Stage 4 Analysis Section
    st.subheader("🔄 Run Stage 4 Analysis")
    st.write("Generate strategic themes and alerts from Stage 3 findings.")
    
    if st.button("🚀 Run Stage 4 Analysis", type="primary"):
        result = run_stage4_analysis()
        if result:
            st.success("✅ Stage 4 analysis completed!")
        else:
            st.error("❌ Stage 4 analysis failed. Check the logs for details.")
    
    # Display existing themes
    st.subheader("📊 Current Themes & Alerts")
    show_stage4_themes()

if __name__ == "__main__":
    main() 