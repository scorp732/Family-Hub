import os
import asyncio
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime, timedelta

import streamlit as st
from pydantic import BaseModel

from family_hub.settings.config import get_ai_api_key

# Configure logging
logger = logging.getLogger('family_hub.ai')

class AIAssistantResponse(BaseModel):
    """Model for AI assistant responses"""
    text: str
    source: str = "ai_assistant"
    timestamp: datetime = datetime.now()


class AIModel:
    """AI model types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DUMMY = "dummy"  # Fallback rule-based model


def get_available_model() -> Tuple[str, str]:
    """
    Determine which AI model to use based on available credentials
    
    Returns:
        Tuple of (provider, model_name)
    """
    # Try OpenAI first
    if os.environ.get("OPENAI_API_KEY"):
        return (AIModel.OPENAI, "gpt-3.5-turbo")
    
    # Try Anthropic second
    if os.environ.get("ANTHROPIC_API_KEY"):
        return (AIModel.ANTHROPIC, "claude-instant-1")
    
    # Try Gemini third
    if os.environ.get("GOOGLE_API_KEY"):
        return (AIModel.GEMINI, "gemini-pro")
    
    # Check for API key in config
    api_key = get_ai_api_key()
    if api_key:
        # Determine which provider based on key format or settings
        if api_key.startswith("sk-"):
            return (AIModel.OPENAI, "gpt-3.5-turbo")
        elif api_key.startswith("sk-ant-"):
            return (AIModel.ANTHROPIC, "claude-instant-1")
        else:
            return (AIModel.OPENAI, "gpt-3.5-turbo")  # Default to OpenAI
    
    # Return dummy model as last resort
    return (AIModel.DUMMY, "rule-based")


async def process_user_query(user_id: str, family_id: str, query: str) -> str:
    """
    Process a user query with the AI assistant
    
    Args:
        user_id: ID of the user making the query
        family_id: ID of the user's family
        query: The user's query text
        
    Returns:
        The AI assistant's response
    """
    logger.info(f"Processing query from user {user_id}: {query}")
    
    # Get available AI model
    provider, model = get_available_model()
    
    # If we have a real AI model available, use it
    if provider != AIModel.DUMMY:
        try:
            # In a real implementation, this would call the appropriate AI model API
            # For now, we'll use the rule-based system as a placeholder
            logger.info(f"Using AI provider: {provider}, model: {model}")
            return await rule_based_response(query)
        except Exception as e:
            logger.error(f"Error calling AI model: {str(e)}")
            # Fall back to rule-based system on error
            return await rule_based_response(query, error=True)
    else:
        # Use rule-based system
        logger.info("Using rule-based fallback system")
        return await rule_based_response(query)


async def rule_based_response(query: str, error: bool = False) -> str:
    """
    Generate a response using a simple rule-based system
    
    Args:
        query: The user's query text
        error: Whether this is being called due to an API error
        
    Returns:
        A response string
    """
    # Add a small delay to simulate processing time
    await asyncio.sleep(0.5)
    
    # If this is being called due to an API error, add a note
    prefix = ""
    if error:
        prefix = "I'm having trouble connecting to my AI service. Using basic mode instead.\n\n"
    
    # Convert query to lowercase for easier matching
    query_lower = query.lower()
    
    # Get current time for time-based responses
    now = datetime.now()
    
    # Simple rule-based responses
    if any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
        return prefix + "Hello! How can I help you with your family management today?"
    
    elif "help" in query_lower:
        return prefix + """I can help you with:
1. Managing your calendar and events
2. Tracking tasks and assignments
3. Monitoring your budget and expenses
4. Managing shopping lists
5. Answering questions about your family's schedule

Just ask me what you need!"""
    
    elif any(word in query_lower for word in ["event", "calendar", "schedule"]):
        if "add" in query_lower or "create" in query_lower:
            return prefix + "To add an event, please go to the Calendar page and click the '+ Add Event' button."
        else:
            # In a real implementation, this would fetch actual events
            return prefix + f"Here are your upcoming events for the next few days:\n- Family dinner on {(now + timedelta(days=1)).strftime('%A')}\n- Doctor appointment on {(now + timedelta(days=3)).strftime('%A')}"
    
    elif any(word in query_lower for word in ["task", "todo", "to-do", "to do"]):
        if "add" in query_lower or "create" in query_lower:
            return prefix + "To add a task, please go to the Tasks page and click the '+ Add Task' button."
        else:
            # In a real implementation, this would fetch actual tasks
            return prefix + "Here are your pending tasks:\n- Buy groceries\n- Pay utility bills\n- Schedule car maintenance"
    
    elif any(word in query_lower for word in ["budget", "money", "expense", "spending"]):
        if "add" in query_lower:
            return prefix + "To add a transaction, please go to the Budget page and click the '+ Add Transaction' button."
        else:
            # In a real implementation, this would fetch actual budget data
            return prefix + "Your current month's budget summary:\n- Income: $3,500\n- Expenses: $2,800\n- Remaining: $700"
    
    elif any(word in query_lower for word in ["shopping", "grocery", "groceries", "buy"]):
        if "add" in query_lower:
            # Extract item to add (simple implementation)
            words = query_lower.split()
            if "add" in words and len(words) > words.index("add") + 1:
                item_index = words.index("add") + 1
                item = " ".join(words[item_index:])
                item = item.replace("to the shopping list", "").replace("to shopping list", "").strip()
                return prefix + f"I've added '{item}' to your shopping list."
            else:
                return prefix + "To add items to a shopping list, please go to the Shopping page."
        else:
            # In a real implementation, this would fetch actual shopping lists
            return prefix + "Here are your current shopping lists:\n- Groceries (10 items)\n- Household supplies (5 items)"
    
    elif "weather" in query_lower:
        return prefix + "I'm sorry, I don't have access to weather information at the moment."
    
    elif "time" in query_lower:
        return prefix + f"The current time is {now.strftime('%I:%M %p')}."
    
    elif "date" in query_lower:
        return prefix + f"Today is {now.strftime('%A, %B %d, %Y')}."
    
    elif any(word in query_lower for word in ["thank", "thanks"]):
        return prefix + "You're welcome! Is there anything else I can help you with?"
    
    else:
        return prefix + "I'm not sure how to help with that yet. You can ask me about your calendar, tasks, budget, or shopping lists."


def setup_assistant():
    """Initialize the AI assistant"""
    logger.info("Setting up AI assistant")
    
    # Check if AI is available
    provider, model = get_available_model()
    ai_available = provider != AIModel.DUMMY
    
    # Set AI availability in session state
    st.session_state.ai_available = ai_available
    
    # Initialize chat history
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []
        
        # Add welcome message
        welcome_message = """Welcome to Family Hub's AI Assistant! I'm here to help you manage your family's activities, events, and tasks."""
        
        if not ai_available:
            welcome_message += "\n\n⚠️ Note: AI features are running in basic mode. To enable full AI capabilities, please configure your API key in Settings."
        
        welcome_message += "\n\nHow can I help you today?"
        
        st.session_state.ai_chat_history.append({
            "content": welcome_message,
            "is_user": False
        })
    
    logger.info(f"AI assistant setup complete. Using provider: {provider}, model: {model}")