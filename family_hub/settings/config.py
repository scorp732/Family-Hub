import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger('family_hub.settings')

# Default configuration
DEFAULT_CONFIG = {
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

def load_configuration() -> Dict[str, Any]:
    """
    Load application configuration from config file or environment variables
    
    Returns:
        Configuration dictionary
    """
    logger.info("Loading configuration")
    
    try:
        # Check for config file
        config_path = Path(__file__).parents[2] / "config" / "config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Merge with defaults, file config takes precedence
                config = {**DEFAULT_CONFIG, **file_config}
        else:
            # Use default config if no file exists
            config = DEFAULT_CONFIG
            
            # Save default config for future use
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        
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
        return DEFAULT_CONFIG


def save_configuration(config: Dict[str, Any]) -> bool:
    """
    Save application configuration to config file
    
    Args:
        config: Configuration dictionary to save
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Saving configuration")
    
    try:
        # Create config directory if it doesn't exist
        config_path = Path(__file__).parents[2] / "config" / "config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        # Save config to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False


def get_ai_api_key() -> Optional[str]:
    """
    Get AI API key from environment variable or config file
    
    Returns:
        API key or None if not found
    """
    # First check environment variable
    api_key = os.environ.get("FAMILY_HUB_AI_API_KEY")
    if api_key:
        return api_key
    
    # Then check config file
    try:
        config = load_configuration()
        return config.get("ai_api_key")
    except:
        return None