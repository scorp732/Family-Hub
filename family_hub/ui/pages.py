import streamlit as st
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import asyncio

from family_hub.auth.authentication import login_user, register_user, check_permission
from family_hub.data.storage import DataManager
from family_hub.data.models import (
    User, Family, Event, Task, TaskStatus, TaskPriority,
    Transaction, TransactionType, Budget, BudgetCategory, BudgetPeriod,
    ShoppingItem, ShoppingList, AISettings, AIModel, RoleType, EventType
)
from family_hub.ui.components import (
    render_card, render_tabs, render_calendar_event, render_task_item,
    render_shopping_item, render_budget_item, render_ai_chat_message,
    render_notification, render_empty_state, COLOR_PALETTE
)
from family_hub.ai.assistant import process_user_query

# Authentication Pages
def render_login_page():
    """Render the login page"""
    st.markdown("<h1 style='text-align: center;'>Welcome to Family Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Your family's central command center</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login to Your Account")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, user_data = login_user(username, password)
                    if success:
                        st.session_state.user_id = user_data["id"]
                        st.session_state.current_page = "dashboard"
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        # Link to register page
        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Register"):
            st.session_state.page = "register"
            st.rerun()

def render_register_page():
    """Render the registration page"""
    st.markdown("<h1 style='text-align: center;'>Join Family Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Create a new account</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Create Your Account")
        
        # Registration form
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email")
            display_name = st.text_input("Display Name")
            
            # Family options
            family_option = st.radio(
                "Family",
                options=["Create a new family", "Join an existing family"]
            )
            
            if family_option == "Create a new family":
                family_name = st.text_input("Family Name")
                family_id = None
            else:
                family_id = st.text_input("Family ID")
                family_name = None
            
            # Role selection
            default_role = RoleType.PARENT if family_option == "Create a new family" else RoleType.CHILD
            role_options = [r.value for r in RoleType]
            role = st.selectbox("Role", options=role_options, index=role_options.index(default_role.value))
            
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                # Validate inputs
                if not username or not password or not email or not display_name:
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif family_option == "Create a new family" and not family_name:
                    st.error("Please enter a family name")
                elif family_option == "Join an existing family" and not family_id:
                    st.error("Please enter a family ID")
                else:
                    # Register the user
                    success, message = register_user(
                        username=username,
                        password=password,
                        email=email,
                        display_name=display_name,
                        family_id=family_id,
                        family_name=family_name,
                        role=RoleType(role)
                    )
                    
                    if success:
                        st.success("Registration successful! You can now log in.")
                        st.session_state.user_id = message
                        st.session_state.current_page = "dashboard"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {message}")
        
        # Link to login page
        st.markdown("---")
        st.markdown("Already have an account?")
        if st.button("Log In"):
            st.session_state.page = "login"
            st.rerun()

# Dashboard Page
def render_dashboard(user_data: Dict[str, Any]):
    """Render the dashboard page"""
    st.markdown("# Dashboard")
    st.markdown(f"Welcome to your Family Hub, {user_data.get('display_name')}!")
    
    # Layout in 3 columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Upcoming events card
        events_content = "<p>Your upcoming events will appear here.</p>"
        render_card(
            title="Upcoming Events",
            content=events_content,
            icon="📅",
            color=COLOR_PALETTE["primary"],
            is_clickable=True,
            on_click=lambda: st.session_state.update(current_page="calendar")
        )
        
        # Budget summary card (for parents only)
        if check_permission(user_data, RoleType.PARENT):
            budget_content = "<p>Your budget summary will appear here.</p>"
            render_card(
                title="Budget Summary",
                content=budget_content,
                icon="💰",
                color=COLOR_PALETTE["primary"],
                is_clickable=True,
                on_click=lambda: st.session_state.update(current_page="budget")
            )
    
    with col2:
        # Tasks card
        tasks_content = "<p>Your tasks will appear here.</p>"
        render_card(
            title="My Tasks",
            content=tasks_content,
            icon="✅",
            color=COLOR_PALETTE["success"],
            is_clickable=True,
            on_click=lambda: st.session_state.update(current_page="tasks")
        )
        
        # Shopping lists card
        shopping_content = "<p>Your shopping lists will appear here.</p>"
        render_card(
            title="Shopping Lists",
            content=shopping_content,
            icon="🛒",
            color=COLOR_PALETTE["info"],
            is_clickable=True,
            on_click=lambda: st.session_state.update(current_page="shopping")
        )
    
    with col3:
        # AI assistant card - use the component that handles AI availability
        from family_hub.ui.components import render_ai_assistant_card
        render_ai_assistant_card(user_data)
        
        # Family card
        family_id = user_data.get("family_id")
        family_data = DataManager.get_family(family_id) if family_id else None
        
        if family_data:
            family_name = family_data.get("name", "My Family")
            family_content = f"""
            <div style='margin-bottom: 15px;'>
                <div style='font-weight: bold; font-size: 1.2em;'>{family_name}</div>
                <div style='color: gray;'>Family members will appear here.</div>
            </div>
            """
            render_card(
                title="Family",
                content=family_content,
                icon="👪",
                color=COLOR_PALETTE["warning"],
                is_clickable=True,
                on_click=lambda: st.session_state.update(current_page="settings")
            )

# Calendar Page
def render_calendar_page(user_data: Dict[str, Any]):
    """Render the calendar page"""
    st.markdown("# Calendar")
    st.markdown("Your family calendar will be displayed here.")
    
    # Add event button
    if st.button("➕ Add Event"):
        st.info("Event creation functionality will be implemented here.")

# Tasks Page
def render_tasks_page(user_data: Dict[str, Any]):
    """Render the tasks page"""
    st.markdown("# Tasks")
    st.markdown("Your family tasks will be displayed here.")
    
    # Add task button
    if st.button("➕ Add Task"):
        st.info("Task creation functionality will be implemented here.")

# Budget Page
def render_budget_page(user_data: Dict[str, Any]):
    """Render the budget page"""
    # Check permissions
    if not check_permission(user_data, RoleType.PARENT):
        st.warning("You don't have permission to view the budget page.")
        return
    
    st.markdown("# Budget")
    st.markdown("Your family budget will be displayed here.")
    
    # Add transaction button
    if st.button("➕ Add Transaction"):
        st.info("Transaction creation functionality will be implemented here.")

# Shopping Page
def render_shopping_page(user_data: Dict[str, Any]):
    """Render the shopping page"""
    st.markdown("# Shopping Lists")
    st.markdown("Your family shopping lists will be displayed here.")
    
    # Add shopping list button
    if st.button("➕ Add Shopping List"):
        st.info("Shopping list creation functionality will be implemented here.")

# Settings Page
def render_settings_page(user_data: Dict[str, Any]):
    """Render the settings page"""
    st.markdown("# Settings")
    
    # Settings tabs
    tabs = ["Profile", "Family", "AI Assistant", "Appearance"]
    selected_tab = render_tabs(tabs)
    
    if selected_tab == "Profile":
        st.markdown("### Profile Settings")
        st.markdown("User profile settings will be displayed here.")
    
    elif selected_tab == "Family":
        st.markdown("### Family Settings")
        st.markdown("Family settings will be displayed here.")
    elif selected_tab == "AI Assistant":
        st.markdown("### AI Assistant Settings")
        
        # Store settings tab in session state for navigation
        if "settings_tab" not in st.session_state or st.session_state.settings_tab != "ai":
            st.session_state.settings_tab = "ai"
        
        # Get current AI settings
        family_id = user_data.get("family_id")
        ai_settings = DataManager.get_ai_settings_by_family(family_id)
        
        # Default settings if none exist
        if not ai_settings:
            ai_settings = {
                "model": AIModel.GPT_3_5_TURBO.value,
                "api_key": "",
                "temperature": 0.7,
                "max_tokens": 800,
                "enabled": True
            }
        
        # Enable/disable AI features
        ai_enabled = st.toggle("Enable AI Assistant", value=ai_settings.get("enabled", True))
        
        if ai_enabled:
            st.markdown("#### API Configuration")
            
            # Select AI Provider
            ai_provider_options = ["OpenAI", "Anthropic", "Google (Gemini)"]
            
            # Determine current provider from model
            current_model = ai_settings.get("model", AIModel.GPT_3_5_TURBO.value)
            current_provider_index = 0  # Default to OpenAI
            if "claude" in current_model:
                current_provider_index = 1
            elif "gemini" in current_model:
                current_provider_index = 2
                
            ai_provider = st.selectbox(
                "AI Provider",
                options=ai_provider_options,
                index=current_provider_index
            )
            
            # API Key input
            api_key = st.text_input(
                f"{ai_provider} API Key",
                value=ai_settings.get("api_key", ""),
                type="password",
                help="Your API key will be stored securely and used only for this application."
            )
            
            # Model selection based on provider
            if ai_provider == "OpenAI":
                model_options = [AIModel.GPT_4.value, AIModel.GPT_4O.value, AIModel.GPT_3_5_TURBO.value]
                model_index = 2  # Default to GPT-3.5 Turbo
                if current_model in model_options:
                    model_index = model_options.index(current_model)
                    
                model = st.selectbox(
                    "Model",
                    options=model_options,
                    index=model_index,
                    format_func=lambda x: x.replace("gpt-", "GPT ").replace("-turbo", " Turbo")
                )
            elif ai_provider == "Anthropic":
                model_options = [AIModel.CLAUDE.value, AIModel.CLAUDE_SONNET.value, AIModel.CLAUDE_HAIKU.value]
                model_index = 0
                if current_model in model_options:
                    model_index = model_options.index(current_model)
                    
                model = st.selectbox(
                    "Model",
                    options=model_options,
                    index=model_index,
                    format_func=lambda x: x.replace("claude-", "Claude ").replace("-", " ")
                )
            else:  # Google
                model = AIModel.GEMINI_PRO.value
            
            st.markdown("#### Model Parameters")
            
            # Temperature slider
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=ai_settings.get("temperature", 0.7),
                step=0.1,
                help="Higher values make output more random, lower values make it more deterministic."
            )
            
            # Max tokens slider
            max_tokens = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=ai_settings.get("max_tokens", 800),
                step=100,
                help="Maximum number of tokens in the AI response."
            )
            
            # Custom instructions
            custom_instructions = st.text_area(
                "Custom Instructions",
                value=ai_settings.get("custom_instructions", ""),
                help="Additional instructions to guide the AI assistant's behavior."
            )
            
            # Save button
            if st.button("Save AI Settings"):
                # Create or update AI settings
                ai_settings_obj = AISettings(
                    id=ai_settings.get("id", None),
                    family_id=family_id,
                    model=model,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    enabled=ai_enabled,
                    custom_instructions=custom_instructions
                )
                
                # Save to database
                DataManager.save_ai_settings(ai_settings_obj)
                
                # Update session state
                st.session_state.ai_available = bool(api_key)
                
                st.success("AI settings saved successfully!")
                st.rerun()
        else:
            st.info("AI Assistant is currently disabled. Enable it to configure settings.")
            
            # Save disabled state if needed
            if ai_settings.get("enabled", True):  # If it was previously enabled
                ai_settings_obj = AISettings(
                    id=ai_settings.get("id", None),
                    family_id=family_id,
                    model=ai_settings.get("model", AIModel.GPT_3_5_TURBO.value),
                    api_key=ai_settings.get("api_key", ""),
                    temperature=ai_settings.get("temperature", 0.7),
                    max_tokens=ai_settings.get("max_tokens", 800),
                    enabled=False,
                    custom_instructions=ai_settings.get("custom_instructions", "")
                )
                
                # Save to database
                DataManager.save_ai_settings(ai_settings_obj)
                
                # Update session state
                st.session_state.ai_available = False
        st.markdown("AI assistant settings will be displayed here.")
    
    else:  # Appearance
        st.markdown("### Appearance Settings")
        st.markdown("Appearance settings will be displayed here.")
