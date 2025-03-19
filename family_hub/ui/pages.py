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
        from family_hub.tasks.service import get_task_summary
        
        # Get user's tasks
        user_tasks = get_task_summary(user_data.get("family_id"), user_data.get("id"))
        
        if user_tasks:
            # Display up to 3 tasks
            display_tasks = user_tasks[:3]
            
            tasks_content = ""
            for task in display_tasks:
                # Format due date if exists
                due_date_display = ""
                if task.get("due_date"):
                    due_date = datetime.fromisoformat(task["due_date"].replace('Z', '+00:00')) if isinstance(task["due_date"], str) else task["due_date"]
                    due_date_display = f"<span style='color: {COLOR_PALETTE['accent3']}; font-size: 0.8em;'> • Due: {due_date.strftime('%b %d')}</span>"
                
                # Get priority color
                priority = task.get("priority", 1)
                priority_colors = {
                    0: COLOR_PALETTE["info"],         # Low priority
                    1: COLOR_PALETTE["accent4"],      # Medium priority
                    2: COLOR_PALETTE["warning"],      # High priority
                    3: COLOR_PALETTE["error"]         # Urgent priority
                }
                priority_color = priority_colors.get(priority, COLOR_PALETTE["accent4"])
                
                # Add task to content
                tasks_content += f"""
                <div style='margin-bottom: 10px; padding: 8px; border-left: 3px solid {priority_color}; background: linear-gradient(to right, {COLOR_PALETTE["bg_light"]}40, transparent);'>
                    <div style='font-weight: bold;'>{task.get("title")}</div>
                    <div style='font-size: 0.8em; color: {COLOR_PALETTE["text"]};'>
                        {task.get("status", "todo").replace("_", " ").title()}{due_date_display}
                    </div>
                </div>
                """
            
            # Add "View all" link
            tasks_content += f"""
            <div style='text-align: center; margin-top: 10px;'>
                <a href='#' onclick='none' style='color: {COLOR_PALETTE["primary"]}; text-decoration: none;'>View all tasks →</a>
            </div>
            """
        else:
            tasks_content = "<p>You don't have any tasks yet. Click to create one!</p>"
        
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
    
    # Get family ID
    family_id = user_data.get("family_id")
    user_id = user_data.get("id")
    
    # Create tabs for different task views
    tabs = ["My Tasks", "Family Tasks", "Create Task"]
    selected_tab = render_tabs(tabs)
    
    if selected_tab == "Create Task":
        render_create_task_form(user_data)
    else:
        # Determine which tasks to show
        if selected_tab == "My Tasks":
            show_user_tasks = True
        else:  # Family Tasks
            show_user_tasks = False
        
        # Render task list with filters
        render_task_list(family_id, user_id, show_user_tasks)


def render_create_task_form(user_data: Dict[str, Any]):
    """Render form for creating a new task"""
    from family_hub.tasks.service import create_task
    from family_hub.data.models import TaskPriority
    from family_hub.data.storage import DataManager
    
    st.markdown("### Create New Task")
    
    with st.form("create_task_form"):
        # Basic task info
        title = st.text_input("Title", placeholder="Enter task title")
        description = st.text_area("Description", placeholder="Enter task description (optional)")
        
        # Due date
        due_date = st.date_input("Due Date", value=None)
        
        # Priority selection
        priority_options = {
            "Low": 0,
            "Medium": 1,
            "High": 2,
            "Urgent": 3
        }
        priority_str = st.select_slider(
            "Priority",
            options=list(priority_options.keys()),
            value="Medium"
        )
        priority = priority_options[priority_str]
        
        # Assignees
        family_id = user_data.get("family_id")
        family_members = DataManager.get_users_by_family(family_id)
        
        # Create options for multiselect
        member_options = {f"{member.get('display_name')} ({member.get('username')})": member.get('id')
                          for member in family_members}
        
        selected_members = st.multiselect(
            "Assign To",
            options=list(member_options.keys()),
            default=[f"{user_data.get('display_name')} ({user_data.get('username')})"]
        )
        
        # Convert selected members to user IDs
        assigned_to = [member_options[member] for member in selected_members]
        
        # Submit button
        submitted = st.form_submit_button("Create Task")
        
        if submitted:
            if not title:
                st.error("Title is required")
            else:
                # Convert date to datetime if provided
                due_datetime = None
                if due_date:
                    due_datetime = datetime.combine(due_date, datetime.min.time())
                
                # Create the task
                try:
                    task = create_task(
                        title=title,
                        family_id=family_id,
                        created_by=user_data.get("id"),
                        description=description,
                        priority=TaskPriority(priority),
                        due_date=due_datetime,
                        assigned_to=assigned_to
                    )
                    
                    st.success("Task created successfully!")
                    
                    # Clear form by rerunning
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating task: {str(e)}")


def render_task_list(family_id: str, user_id: str, show_user_tasks: bool = True):
    """Render a list of tasks with filters and actions"""
    from family_hub.tasks.service import get_task_summary, update_task_status, delete_task
    from family_hub.data.models import TaskStatus
    
    # Add filters in an expander
    with st.expander("Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Status filter
            status_options = ["All", "To Do", "In Progress", "Done", "Cancelled"]
            selected_status = st.selectbox("Status", options=status_options, index=0)
            
            # Convert UI status to model status
            status_map = {
                "To Do": TaskStatus.TODO,
                "In Progress": TaskStatus.IN_PROGRESS,
                "Done": TaskStatus.DONE,
                "Cancelled": TaskStatus.CANCELLED
            }
            filter_status = status_map.get(selected_status) if selected_status != "All" else None
        
        with col2:
            # Priority filter
            priority_options = ["All", "Low", "Medium", "High", "Urgent"]
            selected_priority = st.selectbox("Priority", options=priority_options, index=0)
            
            # Convert UI priority to model priority
            priority_map = {
                "Low": 0,
                "Medium": 1,
                "High": 2,
                "Urgent": 3
            }
            filter_priority = priority_map.get(selected_priority) if selected_priority != "All" else None
    
    # Get tasks based on filters
    if show_user_tasks:
        # Get tasks assigned to the user
        tasks = get_task_summary(family_id, user_id)
    else:
        # Get all family tasks
        tasks = get_task_summary(family_id)
    
    # Apply filters
    if filter_status:
        tasks = [task for task in tasks if task.get("status") == filter_status.value]
    
    if filter_priority is not None:  # Check for None specifically since priority 0 is valid
        tasks = [task for task in tasks if task.get("priority") == filter_priority]
    
    # Display tasks
    if not tasks:
        render_empty_state(
            message="No tasks found matching your filters",
            icon="📝",
            action_label="Create Task",
            on_action=lambda: st.session_state.update(selected_tab="Create Task")
        )
    else:
        # Display each task with actions
        for task in tasks:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Render task using the component
                    render_task_item(task)
                
                with col2:
                    # Task actions
                    task_id = task.get("id")
                    
                    # Status update
                    current_status = TaskStatus(task.get("status", "todo"))
                    status_options = [s.value for s in TaskStatus]
                    
                    # Format status options for display
                    status_display = {
                        "todo": "To Do",
                        "in_progress": "In Progress",
                        "done": "Done",
                        "cancelled": "Cancelled"
                    }
                    
                    new_status = st.selectbox(
                        "Status",
                        options=status_options,
                        index=status_options.index(current_status.value),
                        format_func=lambda x: status_display.get(x, x.replace("_", " ").title()),
                        key=f"status_{task_id}"
                    )
                    
                    # Update status if changed
                    if new_status != current_status.value:
                        try:
                            update_task_status(task_id, TaskStatus(new_status), user_id)
                            st.success("Status updated!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating status: {str(e)}")
                    
                    # Delete button
                    if st.button("Delete", key=f"delete_{task_id}"):
                        # Confirm deletion
                        if st.session_state.get(f"confirm_delete_{task_id}", False):
                            try:
                                delete_task(task_id)
                                st.success("Task deleted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting task: {str(e)}")
                        else:
                            st.session_state[f"confirm_delete_{task_id}"] = True
                            st.warning("Click again to confirm deletion")
                
                # Separator
                st.markdown("<hr style='margin: 10px 0; opacity: 0.3;'/>", unsafe_allow_html=True)

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
