import streamlit as st
import re
from stage1_ui import show_stage1_data_responses
from stage2_ui import show_stage2_response_labeling
from stage3_ui import show_stage3_findings
from stage4_ui import show_stage4_themes
from admin_ui import show_admin_utilities
from curation_ui import show_curation_ui

def main():
    st.set_page_config(page_title="VOC Pipeline", layout="wide")
    
    # Initialize session state
    if 'client_id' not in st.session_state:
        st.session_state.client_id = ''
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    # Sidebar navigation
    st.sidebar.title("VOC Pipeline Navigation")
    
    # Client ID management
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 Client Settings")
    
    # Check if client_id is properly set
    current_client_id = st.session_state.get('client_id', '')
    if not current_client_id or current_client_id == 'default':
        st.sidebar.warning("⚠️ Please set a Client ID")
    
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
    st.sidebar.subheader("📊 Pipeline Stages")
    
    page = st.sidebar.radio(
        "Go to:",
        [
            "Stage 1: Data Response Table",
            "Stage 2: Response Labeling", 
            "Stage 3: Findings",
            "Stage 4: Themes",
            "Stage 5: Human Curation",
            "Admin / Utilities"
        ]
    )

    if page == "Stage 1: Data Response Table":
        show_stage1_data_responses()
    elif page == "Stage 2: Response Labeling":
        show_stage2_response_labeling()
    elif page == "Stage 3: Findings":
        show_stage3_findings()
    elif page == "Stage 4: Themes":
        show_stage4_themes()
    elif page == "Stage 5: Human Curation":
        show_curation_ui()
    elif page == "Admin / Utilities":
        show_admin_utilities()

if __name__ == "__main__":
    main()


