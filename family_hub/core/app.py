import os
import json
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('family_hub.core')

def initialize_app():
    """
    Initialize the application components and state.
    This function:
    1. Sets up session state
    2. Initializes the database
    3. Loads configuration
    4. Sets up the AI assistant
    5. Initializes any other required components
    """
    logger.info("Initializing Family Hub application")
    
    # Only initialize once
    if "initialized" in st.session_state and st.session_state.initialized:
        logger.debug("App already initialized, skipping")
        return
    
    # Create essential session state variables
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.user_id = None
        st.session_state.current_page = "dashboard"
        st.session_state.notifications = []
        st.session_state.temp_data = {}
    
    try:
        # Initialize the database
        initialize_database()
        
        # Load configuration
        config = load_configuration()
        st.session_state.config = config
        
        # Set up AI assistant
        setup_assistant()
        
        # Initialize any other components
        initialize_components()
        
        # Mark as initialized
        st.session_state.initialized = True
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}")
        st.error(f"Failed to initialize application: {str(e)}")
        raise

def initialize_database():
    """Initialize database structure and connections"""
    from family_hub.data.models import initialize_database as init_db
    
    logger.info("Initializing database")
    try:
        # Create data directory if it doesn't exist
        data_dir = Path(__file__).parents[2] / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Initialize database structure
        init_db()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def load_configuration() -> Dict[str, Any]:
    """Load application configuration from config file or environment variables"""
    logger.info("Loading configuration")
    
    # Default configuration
    default_config = {
        "app_name": "Family Hub",
        "theme": "light",
        "timezone": "UTC",
        "features": {
            "ai_assistant": True,
            "calendar_sync": False,
            "budget_reminders": True,
            "task_notifications": True
        },
        "default_view": "dashboard",
        "retention_period_days": 365
    }
    
    try:
        # Check for config file
        config_path = Path(__file__).parents[2] / "config" / "config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Merge with defaults, file config takes precedence
                config = {**default_config, **file_config}
        else:
            # Use default config if no file exists
            config = default_config
            
            # Save default config for future use
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        # Override with environment variables if present
        if os.environ.get("FAMILY_HUB_THEME"):
            config["theme"] = os.environ.get("FAMILY_HUB_THEME")
        if os.environ.get("FAMILY_HUB_TIMEZONE"):
            config["timezone"] = os.environ.get("FAMILY_HUB_TIMEZONE")
        
        logger.info(f"Configuration loaded: {config}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        # Return default config in case of error
        return default_config

def setup_assistant():
    """Initialize the AI assistant with fallback options"""
    logger.info("Setting up AI assistant")
    try:
        # Check if API keys are configured
        from family_hub.settings.config import get_ai_api_key
        api_key = get_ai_api_key()
        
        # Initialize AI assistant
        from family_hub.ai.assistant import setup_assistant as setup_ai
        setup_ai()
        
        # Set AI availability in session state based on API key
        if api_key:
            logger.info("AI assistant initialized with API key")
        else:
            logger.info("AI assistant initialized in basic mode (no API key)")
            
        logger.info("AI assistant setup complete")
    except Exception as e:
        logger.error(f"Error setting up AI assistant: {str(e)}")
        # Don't raise, as AI is optional
        st.session_state.ai_available = False
        st.warning("AI assistant could not be initialized. Some features may be limited.")

def initialize_components():
    """Initialize any additional components"""
    logger.info("Initializing additional components")
    
    # Create necessary directories
    dirs = [
        Path(__file__).parents[2] / "data",
        Path(__file__).parents[2] / "config",
        Path(__file__).parents[2] / "logs",
        Path(__file__).parents[2] / "uploads"
    ]
    
    for directory in dirs:
        directory.mkdir(exist_ok=True)
    
    # Initialize any other services or components here
    
    logger.info("Component initialization complete")