import streamlit as st
from typing import Dict, Any, List, Optional, Tuple, Callable
import datetime
import asyncio
from PIL import Image
import io
import base64

from family_hub.auth.authentication import logout_user, check_permission
from family_hub.data.models import RoleType
from family_hub.ai.assistant import process_user_query

# UI Constants
SIDEBAR_ICON_MAP = {
    "dashboard": "🏠",
    "calendar": "📅",
    "tasks": "✅",
    "budget": "💰",
    "shopping": "🛒",
    "settings": "⚙️",
    "profile": "👤",
    "logout": "🚪"
}

COLOR_PALETTE = {
    "primary": "#5B8AF0",       # Softer blue
    "secondary": "#E86C6C",     # Softer red
    "success": "#4CAF50",       # Softer green
    "warning": "#F9C74F",       # Softer amber
    "info": "#64B5F6",          # Softer light blue
    "light": "#F8F9FA",         # Lighter background
    "dark": "#343A40",          # Softer dark
    "background": "#F8F9FD",    # Softer background
    "text": "#495057"           # Softer text color
}

def render_header(user_data: Dict[str, Any]):
    """
    Render the application header with user information
    
    Args:
        user_data: Current user data
    """
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.image("https://via.placeholder.com/100x50?text=FamilyHub", width=100)
    
    with col2:
        st.markdown(f"<h1 style='text-align: center;'>Family Hub</h1>", unsafe_allow_html=True)
    
    with col3:
        # User info and notifications
        display_name = user_data.get("display_name", "User")
        st.markdown(f"""
        <div style='text-align: right; padding: 10px;'>
            <span>Welcome, {display_name}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Notifications indicator
        notifications = st.session_state.get("notifications", [])
        if notifications:
            st.markdown(f"""
            <div style='text-align: right; color: {COLOR_PALETTE["secondary"]};'>
                <span>🔔 {len(notifications)} notifications</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Horizontal line
    st.markdown("<hr/>", unsafe_allow_html=True)


def setup_sidebar(user_data: Dict[str, Any]) -> str:
    """
    Set up sidebar navigation based on user role
    
    Args:
        user_data: Current user data
        
    Returns:
        Selected page name
    """
    st.sidebar.markdown("## Navigation")
    
    # Determine available pages based on user role
    role = RoleType(user_data.get("role", "child"))
    
    # All users get these pages
    available_pages = ["dashboard", "calendar", "tasks", "shopping"]
    
    # Parents and admins get budget
    if check_permission(user_data, RoleType.PARENT):
        available_pages.append("budget")
    
    # Everyone gets settings and profile
    available_pages.extend(["settings", "profile"])
    
    # Create navigation buttons
    selected_page = st.session_state.get("current_page", "dashboard")
    
    for page in available_pages:
        icon = SIDEBAR_ICON_MAP.get(page, "📄")
        if st.sidebar.button(f"{icon} {page.capitalize()}", key=f"nav_{page}"):
            selected_page = page
            st.session_state.current_page = page
    
    # Logout button (always available)
    st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
    if st.sidebar.button(f"{SIDEBAR_ICON_MAP['logout']} Logout", key="nav_logout"):
        logout_user()
        st.rerun()
    
    # Display current family info
    st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
    family_id = user_data.get("family_id")
    from family_hub.data.storage import DataManager
    family_data = DataManager.get_family(family_id) if family_id else None
    
    if family_data:
        st.sidebar.markdown(f"### Family: {family_data.get('name', 'Unknown')}")
        
        # Show family members count with collapsible list
        members = DataManager.get_users_by_family(family_id)
        st.sidebar.markdown(f"**Members:** {len(members)}")
        
        with st.sidebar.expander("View Members"):
            for member in members:
                role_icon = "👑" if member.get("role") == "admin" else "👨‍👩‍👧‍👦" if member.get("role") == "parent" else "👶" if member.get("role") == "child" else "👤"
                st.markdown(f"{role_icon} {member.get('display_name', 'Unknown')}")
    
    # Version info at bottom
    st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
    st.sidebar.markdown("Family Hub v1.0", help="Version 1.0.0")
    
    return selected_page


def render_card(title: str, content: str, icon: str = None, color: str = None, is_clickable: bool = False, on_click: Callable = None) -> None:
    """
    Render a card component with title and content
    
    Args:
        title: Card title
        content: Card content (can include HTML)
        icon: Optional icon to display
        color: Optional accent color
        is_clickable: Whether the card is clickable
        on_click: Optional function to call when clicked
    """
    color = color or COLOR_PALETTE["primary"]
    icon_html = f"<span style='font-size: 1.5rem; margin-right: 10px;'>{icon}</span>" if icon else ""
    
    card_html = f"""
    <div style='
        border-radius: 5px;
        padding: 15px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 5px solid {color};
        {"cursor: pointer;" if is_clickable else ""}
    '>
        <h3 style='margin-top: 0; color: {color};'>
            {icon_html} {title}
        </h3>
        <div>
            {content}
        </div>
    </div>
    """
    
    # Use a button if clickable, otherwise just render
    if is_clickable and on_click:
        if st.markdown(card_html, unsafe_allow_html=True):
            on_click()
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def render_tabs(tabs: List[str], default_tab: str = None) -> str:
    """
    Render horizontal tabs and return the selected tab
    
    Args:
        tabs: List of tab names
        default_tab: Optional default selected tab
        
    Returns:
        Name of the selected tab
    """
    if "selected_tab" not in st.session_state or st.session_state.selected_tab not in tabs:
        st.session_state.selected_tab = default_tab or tabs[0]
    
    col_size = 12 // len(tabs)
    cols = st.columns(len(tabs))
    
    for i, tab in enumerate(tabs):
        with cols[i]:
            is_active = st.session_state.selected_tab == tab
            background = COLOR_PALETTE["primary"] if is_active else "transparent"
            text_color = "white" if is_active else COLOR_PALETTE["dark"]
            border = f"2px solid {COLOR_PALETTE['primary']}"
            
            tab_html = f"""
            <div style='
                text-align: center;
                padding: 10px;
                border-radius: 5px 5px 0 0;
                background-color: {background};
                color: {text_color};
                border-top: {border};
                border-left: {border};
                border-right: {border};
                cursor: pointer;
                font-weight: {"bold" if is_active else "normal"};
            '>
                {tab}
            </div>
            """
            
            if st.markdown(tab_html, unsafe_allow_html=True):
                st.session_state.selected_tab = tab
                st.rerun()
    
    st.markdown("<hr style='margin-top: 0;'/>", unsafe_allow_html=True)
    return st.session_state.selected_tab


def render_calendar_event(event: Dict[str, Any], is_clickable: bool = True) -> None:
    """
    Render a calendar event card
    
    Args:
        event: Event data dictionary
        is_clickable: Whether the event is clickable
    """
    title = event.get("title", "Untitled Event")
    event_type = event.get("event_type", "appointment")
    
    # Format date and time
    start_time = event.get("start_time")
    if isinstance(start_time, str):
        start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    
    end_time = event.get("end_time")
    if isinstance(end_time, str) and end_time:
        end_time = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    # Format time display
    if event.get("all_day", False):
        time_display = "All day"
    elif end_time:
        time_display = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
    else:
        time_display = f"{start_time.strftime('%I:%M %p')}"
    
    # Choose icon based on event type
    icon_map = {
        "appointment": "🗓️",
        "reminder": "⏰",
        "task": "✅",
        "birthday": "🎂",
        "holiday": "🎉",
        "school": "🏫",
        "work": "💼",
        "social": "👥",
        "other": "📌"
    }
    icon = icon_map.get(event_type, "📌")
    
    # Choose color based on event type
    color_map = {
        "appointment": COLOR_PALETTE["primary"],
        "reminder": COLOR_PALETTE["warning"],
        "task": COLOR_PALETTE["success"],
        "birthday": COLOR_PALETTE["secondary"],
        "holiday": COLOR_PALETTE["info"],
        "school": COLOR_PALETTE["primary"],
        "work": COLOR_PALETTE["dark"],
        "social": COLOR_PALETTE["secondary"],
        "other": COLOR_PALETTE["light"]
    }
    color = event.get("color") or color_map.get(event_type, COLOR_PALETTE["primary"])
    
    # Create content
    content = f"""
    <div>
        <p><strong>Date:</strong> {start_time.strftime('%A, %B %d, %Y')}</p>
        <p><strong>Time:</strong> {time_display}</p>
        {f"<p><strong>Location:</strong> {event.get('location')}</p>" if event.get('location') else ""}
        {f"<p>{event.get('description')}</p>" if event.get('description') else ""}
    </div>
    """
    
    def on_click():
        st.session_state.selected_event = event.get("id")
    
    render_card(
        title=title,
        content=content,
        icon=icon,
        color=color,
        is_clickable=is_clickable,
        on_click=on_click if is_clickable else None
    )


def render_task_item(task: Dict[str, Any], is_clickable: bool = True) -> None:
    """
    Render a task item card
    
    Args:
        task: Task data dictionary
        is_clickable: Whether the task is clickable
    """
    title = task.get("title", "Untitled Task")
    status = task.get("status", "todo")
    priority = task.get("priority", 1)
    
    # Format due date
    due_date = task.get("due_date")
    if isinstance(due_date, str) and due_date:
        due_date = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
    
    # Choose icon based on status
    icon_map = {
        "todo": "⭕",
        "in_progress": "🔄",
        "done": "✅",
        "cancelled": "❌"
    }
    icon = icon_map.get(status, "⭕")
    
    # Choose color based on priority and status
    if status == "done":
        color = COLOR_PALETTE["success"]
    elif status == "cancelled":
        color = COLOR_PALETTE["light"]
    else:
        color_map = {
            0: COLOR_PALETTE["info"],      # Low priority
            1: COLOR_PALETTE["primary"],   # Medium priority
            2: COLOR_PALETTE["warning"],   # High priority
            3: COLOR_PALETTE["secondary"]  # Urgent priority
        }
        color = color_map.get(priority, COLOR_PALETTE["primary"])
    
    # Format priority display
    priority_map = {
        0: "Low",
        1: "Medium",
        2: "High",
        3: "Urgent"
    }
    priority_display = priority_map.get(priority, "Medium")
    
    # Create content
    content = f"""
    <div>
        <p><strong>Status:</strong> {status.replace('_', ' ').title()}</p>
        <p><strong>Priority:</strong> {priority_display}</p>
        {f"<p><strong>Due:</strong> {due_date.strftime('%A, %B %d, %Y')}</p>" if due_date else ""}
        {f"<p>{task.get('description')}</p>" if task.get('description') else ""}
    </div>
    """
    
    def on_click():
        st.session_state.selected_task = task.get("id")
    
    render_card(
        title=title,
        content=content,
        icon=icon,
        color=color,
        is_clickable=is_clickable,
        on_click=on_click if is_clickable else None
    )


def render_shopping_item(item: Dict[str, Any], on_toggle: Callable = None) -> None:
    """
    Render a shopping item with checkbox
    
    Args:
        item: Shopping item data dictionary
        on_toggle: Function to call when item is toggled
    """
    col1, col2 = st.columns([1, 10])
    
    with col1:
        is_purchased = item.get("is_purchased", False)
        new_state = st.checkbox("", value=is_purchased, key=f"item_{item.get('id')}")
        
        if new_state != is_purchased and on_toggle:
            on_toggle(item.get("id"), new_state)
    
    with col2:
        name = item.get("name", "Untitled Item")
        quantity = item.get("quantity", 1)
        category = item.get("category", "")
        note = item.get("note", "")
        
        # Style based on purchased state
        style = "text-decoration: line-through; color: gray;" if new_state else ""
        
        st.markdown(f"""
        <div style='{style}'>
            <strong>{name}</strong> {f"({quantity})" if quantity > 1 else ""}
            {f"<span style='color: gray; margin-left: 10px;'>{category}</span>" if category else ""}
            {f"<div style='font-size: 0.9em; color: gray;'>{note}</div>" if note else ""}
        </div>
        """, unsafe_allow_html=True)


def render_budget_item(transaction: Dict[str, Any]) -> None:
    """
    Render a budget transaction item
    
    Args:
        transaction: Transaction data dictionary
    """
    amount = transaction.get("amount", 0)
    description = transaction.get("description", "")
    category = transaction.get("category", "other")
    transaction_type = transaction.get("transaction_type", "expense")
    
    # Format date
    date = transaction.get("date")
    if isinstance(date, str):
        date = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
    date_display = date.strftime("%b %d") if date else ""
    
    # Choose color based on transaction type
    color = COLOR_PALETTE["success"] if transaction_type == "income" else COLOR_PALETTE["secondary"]
    
    # Format amount with sign
    sign = "+" if transaction_type == "income" else "-"
    amount_display = f"{sign}${abs(amount):.2f}"
    
    col1, col2, col3 = st.columns([2, 7, 3])
    
    with col1:
        st.markdown(f"<div style='color: gray;'>{date_display}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div>
            <strong>{description}</strong>
            <div style='font-size: 0.9em; color: gray;'>{category.replace('_', ' ').title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='text-align: right; color: {color}; font-weight: bold;'>
            {amount_display}
        </div>
        """, unsafe_allow_html=True)


def render_ai_assistant_card(user_data: Dict[str, Any]):
    """Render card with AI assistant quick access"""
    # Check if AI is available
    ai_available = st.session_state.get("ai_available", False)
    
    if ai_available:
        content = """
        <p>Ask me anything about your family's schedule, tasks, or budget. I can help you manage your household efficiently.</p>
        <div style='font-style: italic; color: gray; margin-top: 10px;'>
            Try asking:
            <ul style='margin-top: 5px;'>
                <li>What events do we have this weekend?</li>
                <li>Add milk to the shopping list</li>
                <li>How much have we spent on groceries this month?</li>
            </ul>
        </div>
        """
        
        title = "AI Assistant"
        icon = "🤖"
    else:
        content = """
        <p>AI assistant features are running in basic mode with limited capabilities.</p>
        <p>To enable full AI features, please configure your API key in Settings.</p>
        """
        
        title = "AI Assistant (Basic Mode)"
        icon = "🤖"
    
    render_card(
        title=title,
        content=content,
        icon=icon,
        color=COLOR_PALETTE["secondary"],
        is_clickable=True,
        on_click=lambda: st.session_state.update(current_page="dashboard", show_ai_assistant=True)
    )
    
    # Show AI assistant dialog if requested
    if st.session_state.get("show_ai_assistant", False):
        with st.expander("AI Assistant", expanded=True):
            st.markdown(f"### How can I help you today?")
            
            if not ai_available:
                st.info("⚠️ AI assistant is running in basic mode with limited capabilities. To enable full AI features, please configure your API key in Settings.")
            
            # Chat history
            if "ai_chat_history" not in st.session_state:
                st.session_state.ai_chat_history = []
            
            # Display chat history
            for message in st.session_state.ai_chat_history:
                render_ai_chat_message(message["content"], message["is_user"])
            
            # Input for new message
            user_input = st.text_input("Ask a question or give a command", key="ai_input")
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                if st.button("Send", key="ai_send", use_container_width=True):
                    if user_input:
                        # Add user message to history
                        st.session_state.ai_chat_history.append({
                            "content": user_input,
                            "is_user": True
                        })
                        
                        # Process with AI assistant
                        try:
                            # Use asyncio to run the async function
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            response = loop.run_until_complete(
                                process_user_query(
                                    user_id=user_data.get("id"),
                                    family_id=user_data.get("family_id"),
                                    query=user_input
                                )
                            )
                            loop.close()
                            
                            # Add AI response to history
                            st.session_state.ai_chat_history.append({
                                "content": response,
                                "is_user": False
                            })
                        except Exception as e:
                            # Add error message to history
                            st.session_state.ai_chat_history.append({
                                "content": f"Sorry, I encountered an error: {str(e)}",
                                "is_user": False
                            })
                        
                        # Clear input
                        st.session_state.ai_input = ""
                        
                        # Rerun to update UI
                        st.rerun()
            
            with col2:
                # Close button
                if st.button("Close", key="ai_close", use_container_width=True):
                    st.session_state.show_ai_assistant = False
                    st.rerun()
            
            # Settings button
            if not ai_available:
                if st.button("Configure AI", key="ai_settings"):
                    st.session_state.current_page = "settings"
                    st.session_state.settings_tab = "ai"
                    st.rerun()


def render_ai_chat_message(message: str, is_user: bool = False) -> None:
    """
    Render a chat message in the AI assistant interface
    
    Args:
        message: Message content
        is_user: Whether the message is from the user
    """
    align = "right" if is_user else "left"
    color = COLOR_PALETTE["light"] if is_user else "white"
    border_color = COLOR_PALETTE["primary"] if is_user else COLOR_PALETTE["light"]
    text_color = COLOR_PALETTE["dark"] if is_user else COLOR_PALETTE["text"]
    
    st.markdown(f"""
    <div style='
        display: flex;
        justify-content: {align};
        margin-bottom: 10px;
    '>
        <div style='
            background-color: {color};
            border-radius: 10px;
            padding: 10px;
            max-width: 80%;
            border: 1px solid {border_color};
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            color: {text_color};
        '>
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_notification(message: str, type: str = "info", dismissible: bool = True) -> None:
    """
    Render a notification message
    
    Args:
        message: Notification message
        type: Type of notification (info, success, warning, error)
        dismissible: Whether the notification can be dismissed
    """
    color_map = {
        "info": COLOR_PALETTE["info"],
        "success": COLOR_PALETTE["success"],
        "warning": COLOR_PALETTE["warning"],
        "error": COLOR_PALETTE["secondary"]
    }
    color = color_map.get(type, COLOR_PALETTE["info"])
    
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    icon = icon_map.get(type, "ℹ️")
    
    notification_id = f"notification_{hash(message)}"
    
    if dismissible:
        col1, col2 = st.columns([10, 1])
        
        with col1:
            st.markdown(f"""
            <div style='
                background-color: {color}25;
                border-left: 5px solid {color};
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            '>
                <span style='font-weight: bold;'>{icon} {type.capitalize()}:</span> {message}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("✕", key=notification_id):
                return False
    else:
        st.markdown(f"""
        <div style='
            background-color: {color}25;
            border-left: 5px solid {color};
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        '>
            <span style='font-weight: bold;'>{icon} {type.capitalize()}:</span> {message}
        </div>
        """, unsafe_allow_html=True)
    
    return True


def render_empty_state(message: str, icon: str = "📭", action_label: str = None, on_action: Callable = None) -> None:
    """
    Render an empty state message with optional action button
    
    Args:
        message: Empty state message
        icon: Icon to display
        action_label: Optional label for action button
        on_action: Optional function to call when action button is clicked
    """
    st.markdown(f"""
    <div style='
        text-align: center;
        padding: 40px 20px;
        background-color: {COLOR_PALETTE["light"]};
        border-radius: 10px;
        margin: 20px 0;
    '>
        <div style='font-size: 3rem; margin-bottom: 20px;'>{icon}</div>
        <h3>{message}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and on_action:
        col1, col2, col3 = st.columns([3, 4, 3])
        with col2:
            if st.button(action_label, key="empty_state_action"):
                on_action()