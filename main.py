import streamlit as st
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('family_hub')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import application components
from family_hub.core.app import initialize_app
from family_hub.auth.authentication import is_authenticated, get_current_user
from family_hub.ui.components import render_header, setup_sidebar
from family_hub.ui.pages import (
    render_login_page, render_register_page, render_dashboard,
    render_calendar_page, render_tasks_page, render_budget_page,
    render_shopping_page, render_settings_page
)

# Set page config
st.set_page_config(
    page_title="Family Hub",
    page_icon="👪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with muted, soothing colors
st.markdown("""
<style>
    /* Main app background - muted, easy on the eyes */
    .stApp {
        background-color: #D8DCE3;
        color: #2E3440;
    }
    
    /* Sidebar styling */
    .stSidebar {
        background-color: #E5E9F0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #5E81AC !important;
    }
    
    /* Text inputs and form elements - softer background */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        border-radius: 5px;
        border-color: #B8C2CC;
        color: #2E3440;
        background-color: #ECEFF4 !important;
    }
    
    /* Form field containers */
    .stTextInput>div,
    .stSelectbox>div,
    .stTextArea>div,
    .stNumberInput>div {
        background-color: transparent;
    }
    
    /* All buttons - ensure none are black */
    button {
        background-color: #81A1C1 !important;
        color: #ECEFF4 !important;
        border-color: #81A1C1 !important;
        border-radius: 5px;
    }
    
    /* Primary buttons */
    .stButton>button {
        background-color: #81A1C1 !important;
        color: #ECEFF4 !important;
    }
    
    /* Secondary buttons */
    .stButton.secondary>button {
        background-color: #B48EAD !important;
        color: #ECEFF4 !important;
    }
    
    /* Form submit buttons */
    button[kind="primaryFormSubmit"] {
        background-color: #81A1C1 !important;
        color: #ECEFF4 !important;
    }
    
    /* Success buttons/elements */
    .success, button.success {
        background-color: #A3BE8C !important;
        color: #ECEFF4 !important;
    }
    
    /* Warning elements */
    .warning, button.warning {
        background-color: #EBCB8B !important;
        color: #2E3440 !important;
    }
    
    /* Info elements */
    .info, button.info {
        background-color: #88C0D0 !important;
        color: #2E3440 !important;
    }
    
    /* Improve contrast for text */
    p, span, div {
        color: #2E3440;
    }
    
    /* Make form labels more visible */
    label {
        color: #4C566A !important;
        font-weight: 500;
    }
    
    /* Improve expander styling */
    .streamlit-expanderHeader {
        background-color: #E5E9F0;
        color: #2E3440;
    }
    
    /* Improve card styling */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #E5E9F0;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Radio buttons and checkboxes */
    .stRadio > div, .stCheckbox > div {
        background-color: transparent;
    }
    
    /* Dataframes and tables */
    .stDataFrame {
        background-color: #E5E9F0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E5E9F0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #E5E9F0;
        color: #2E3440;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #81A1C1;
        color: #ECEFF4;
    }
    
    /* Widget labels */
    .stWidgetLabel {
        color: #4C566A !important;
    }
    
    /* Horizontal rule */
    hr {
        border-color: #D8DEE9;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    # Initialize the application
    initialize_app()
    
    # Check if user is authenticated
    if not is_authenticated():
        # Show login or register page
        page = st.session_state.get("page", "login")
        
        if page == "login":
            render_login_page()
        else:
            render_register_page()
        return
    
    # Get current user data
    user_data = get_current_user()
    if not user_data:
        logger.error("User is authenticated but data could not be retrieved")
        st.error("An error occurred. Please try logging in again.")
        return
    
    # Render header
    render_header(user_data)
    
    # Setup sidebar and get selected page
    selected_page = setup_sidebar(user_data)
    
    # Render selected page
    if selected_page == "dashboard":
        render_dashboard(user_data)
    elif selected_page == "calendar":
        render_calendar_page(user_data)
    elif selected_page == "tasks":
        render_tasks_page(user_data)
    elif selected_page == "budget":
        render_budget_page(user_data)
    elif selected_page == "shopping":
        render_shopping_page(user_data)
    elif selected_page == "settings":
        render_settings_page(user_data)
    elif selected_page == "profile":
        # Profile page is part of settings
        st.session_state.current_page = "settings"
        render_settings_page(user_data)
    else:
        st.error(f"Unknown page: {selected_page}")

if __name__ == "__main__":
    main()