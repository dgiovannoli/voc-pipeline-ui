import streamlit as st
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from official_scripts.ui_components.stage1_ui import show_stage1_data_responses
from official_scripts.ui_components.stage2_ui import show_stage2_response_labeling
from official_scripts.ui_components.stage3_ui import show_stage3_findings
from official_scripts.ui_components.stage4_ui import show_stage4_themes
from official_scripts.ui_components.admin_ui import show_admin_utilities, show_admin_panel

def main():
    st.set_page_config(page_title="VOC Pipeline", layout="wide")
    
    # Initialize session state
    if 'client_id' not in st.session_state:
        st.session_state.client_id = ''
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Sidebar navigation
    st.sidebar.title("VOC Pipeline Navigation")
    
    # Production status indicator
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Production Status")
    
    # Check production readiness
    try:
        from official_scripts.utilities.test_production_setup import test_environment_variables, test_database_connection
        env_ok = test_environment_variables()
        db_ok = test_database_connection()
        
        if env_ok and db_ok:
            st.sidebar.success("✅ Production Ready")
        else:
            st.sidebar.warning("⚠️ Production Issues")
    except:
        st.sidebar.info("ℹ️ Production status unknown")
    
    # Client ID management
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Client Settings")
    
    # Check if client_id is properly set
    current_client_id = st.session_state.get('client_id', '')
    if not current_client_id or current_client_id == 'default':
        st.sidebar.warning("⚠️ Please set a Client ID")
        st.sidebar.info("💡 Enter a unique identifier for this client's data")
        st.sidebar.info("📝 Examples: 'Rev', 'Client_A', 'Project_Alpha'")
    
    # Client ID input with validation
    new_client_id = st.sidebar.text_input(
        "Client ID:",
        value=current_client_id,
        help="Enter a unique identifier for this client's data"
    )
    
    # Validate client ID format
    if new_client_id:
        if re.match(r'^[a-zA-Z0-9_-]+$', new_client_id):
            if new_client_id != current_client_id:
                st.session_state.client_id = new_client_id
                st.sidebar.success(f"✅ Client ID set to: {new_client_id}")
                st.rerun()
        else:
            st.sidebar.error("❌ Client ID can only contain letters, numbers, underscores, and hyphens")
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 VOC Pipeline Flow")
    
    page = st.sidebar.radio(
        "Go to:",
        [
            "Stage 1: Data Response Table",
            "Stage 2: Response Labeling",
            "Stage 2: Findings",
            "Stage 3: Themes",
            "📋 Create Report Outline",
            "Admin / Utilities",
            "🚀 Production Dashboard"
        ]
    )

    if page == "Stage 1: Data Response Table":
        show_stage1_data_responses()
    elif page == "Stage 2: Response Labeling":
        show_stage2_response_labeling()
    elif page == "Stage 2: Findings":
        show_stage3_findings()
    elif page == "Stage 3: Themes":
        show_stage4_themes()
    elif page == "📋 Create Report Outline":
        from official_scripts.ui_components.theme_story_ui import show_theme_story_scorecard
        show_theme_story_scorecard()
    elif page == "Admin / Utilities":
        show_admin_panel()
    elif page == "🚀 Production Dashboard":
        from official_scripts.ui_components.production_dashboard import show_production_dashboard
        show_production_dashboard()

if __name__ == "__main__":
    main()


