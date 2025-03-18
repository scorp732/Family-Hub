import hashlib
import uuid
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import logging

from family_hub.data.models import User, RoleType, Family
from family_hub.data.storage import DataManager

# Configure logging
logger = logging.getLogger('family_hub.auth')

def hash_password(password: str) -> str:
    """
    Hash a password for storage using SHA-256 with salt
    
    Args:
        password: Plain text password
        
    Returns:
        String in format {hash}:{salt}
    """
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{hashed}:{salt}"


def check_password(hashed_password: str, user_password: str) -> bool:
    """
    Verify a stored password against one provided by user
    
    Args:
        hashed_password: Stored password hash in format {hash}:{salt}
        user_password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    if not hashed_password or ':' not in hashed_password:
        return False
        
    stored_hash, salt = hashed_password.split(':')
    user_hash = hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()
    return stored_hash == user_hash


def register_user(
    username: str, 
    password: str, 
    email: str, 
    display_name: str, 
    family_id: Optional[str] = None, 
    family_name: Optional[str] = None,
    role: RoleType = RoleType.PARENT
) -> Tuple[bool, str]:
    """
    Register a new user with optional family creation
    
    Args:
        username: Unique username
        password: Password (will be hashed)
        email: Email address
        display_name: User's display name
        family_id: Optional ID of existing family to join
        family_name: Optional name for new family (if family_id not provided)
        role: User role (default: PARENT)
        
    Returns:
        Tuple of (success, message/user_id)
    """
    # Check if username exists
    existing_user = DataManager.get_user_by_username(username)
    if existing_user:
        logger.warning(f"Registration failed: Username {username} already exists")
        return False, "Username already exists"
    
    # Create or get family
    if not family_id and not family_name:
        return False, "Either family_id or family_name must be provided"
    
    if not family_id:
        # Create new family
        family = Family(
            name=family_name,
            created_by=username  # Will be updated with user ID after user creation
        )
        family_data = DataManager.save_family(family)
        family_id = family_data["id"]
        logger.info(f"Created new family: {family_name} (ID: {family_id})")
    
    # Create new user
    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        display_name=display_name,
        role=role,
        family_id=family_id,
        last_login=datetime.now()
    )
    
    # Save user
    user_data = DataManager.save_user(user)
    user_id = user_data["id"]
    logger.info(f"Created new user: {username} (ID: {user_id})")
    
    # Update family members and created_by if this was a new family
    family = DataManager.get_family(family_id)
    if family:
        family_obj = Family(**family)
        # Add user to family members if not already there
        if user_id not in family_obj.members:
            family_obj.members.append(user_id)
        
        # If this is a new family and created_by is still the username, update it to the user_id
        if family_obj.created_by == username:
            family_obj.created_by = user_id
            
        DataManager.save_family(family_obj)
        logger.debug(f"Updated family {family_id} with new member {user_id}")
    
    return True, user_id


def login_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """
    Authenticate a user and return user data if successful
    
    Args:
        username: Username to authenticate
        password: Plain text password to verify
        
    Returns:
        Tuple of (success, user_data or None)
    """
    user_data = DataManager.get_user_by_username(username)
    
    if not user_data:
        logger.warning(f"Login failed: Username {username} not found")
        return False, None
    
    if check_password(user_data["password_hash"], password):
        # Update last login time
        user = User(**user_data)
        user.last_login = datetime.now()
        updated_user = DataManager.save_user(user)
        
        logger.info(f"User {username} logged in successfully")
        return True, updated_user
    
    logger.warning(f"Login failed: Invalid password for user {username}")
    return False, None


def is_authenticated() -> bool:
    """
    Check if user is authenticated in the current session
    
    Returns:
        True if user is authenticated, False otherwise
    """
    if "user_id" in st.session_state and st.session_state.user_id:
        user_data = DataManager.get_user(st.session_state.user_id)
        if user_data and user_data.get("is_active", True):
            return True
    
    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user's data
    
    Returns:
        User data dictionary or None if not authenticated
    """
    if "user_id" in st.session_state and st.session_state.user_id:
        user_data = DataManager.get_user(st.session_state.user_id)
        if user_data and user_data.get("is_active", True):
            return user_data
    
    return None


def check_authentication() -> Tuple[bool, Optional[Dict]]:
    """
    Check if user is authenticated in the current session
    
    Returns:
        Tuple of (is_authenticated, user_data or None)
    """
    if "user_id" in st.session_state and st.session_state.user_id:
        user_data = DataManager.get_user(st.session_state.user_id)
        if user_data:
            # Check if user is still active
            if user_data.get("is_active", True):
                return True, user_data
            else:
                # User has been deactivated
                logout_user()
                logger.warning(f"Access denied: User account {st.session_state.user_id} is inactive")
                
    return False, None


def logout_user():
    """Log out the current user by clearing session state"""
    if "user_id" in st.session_state:
        user_id = st.session_state.user_id
        logger.info(f"User {user_id} logged out")
        del st.session_state.user_id
    
    # Clear other session state keys except for certain ones
    keys_to_keep = ["page", "initialized", "config"]
    keys_to_clear = [key for key in st.session_state.keys() if key not in keys_to_keep]
    
    for key in keys_to_clear:
        del st.session_state[key]
    
    # Set page to login
    st.session_state.page = "login"


def check_permission(user_data: Dict, required_role: RoleType) -> bool:
    """
    Check if user has the required role or higher permission level
    
    Args:
        user_data: User data dictionary
        required_role: Role required for the operation
        
    Returns:
        True if user has sufficient permissions, False otherwise
    """
    if not user_data:
        return False
        
    # Get user's role
    user_role = RoleType(user_data["role"])
    
    # Role hierarchy - higher number = more permissions
    role_hierarchy = {
        RoleType.ADMIN: 3,
        RoleType.PARENT: 2,
        RoleType.CHILD: 1,
        RoleType.GUEST: 0
    }
    
    # Check if user's role has sufficient permissions
    return role_hierarchy[user_role] >= role_hierarchy[required_role]


def get_family_members(family_id: str) -> List[Dict]:
    """
    Get all members of a family
    
    Args:
        family_id: Family ID to get members for
        
    Returns:
        List of user data dictionaries
    """
    return DataManager.get_users_by_family(family_id)


def update_user_role(user_id: str, new_role: RoleType, admin_user_id: str) -> bool:
    """
    Update a user's role (requires admin privileges)
    
    Args:
        user_id: ID of user to update
        new_role: New role to assign
        admin_user_id: ID of user making the change (must be admin)
        
    Returns:
        True if successful, False otherwise
    """
    # Check if admin user has permission
    admin_data = DataManager.get_user(admin_user_id)
    if not check_permission(admin_data, RoleType.ADMIN):
        logger.warning(f"Role update failed: User {admin_user_id} lacks admin privileges")
        return False
    
    # Get user to update
    user_data = DataManager.get_user(user_id)
    if not user_data:
        logger.warning(f"Role update failed: User {user_id} not found")
        return False
    
    # Update role
    user = User(**user_data)
    user.role = new_role
    DataManager.save_user(user)
    
    logger.info(f"User {user_id} role updated to {new_role} by admin {admin_user_id}")
    return True


def invite_to_family(email: str, family_id: str, inviter_id: str) -> Tuple[bool, str]:
    """
    Generate an invitation for someone to join a family
    
    Args:
        email: Email address to invite
        family_id: Family ID to invite to
        inviter_id: User ID of person sending invitation
        
    Returns:
        Tuple of (success, message/invitation_code)
    """
    # This is a placeholder for a more complex invitation system
    # In a real implementation, this would generate an invitation code
    # and send an email with a registration link
    
    # For now, just return a success message
    logger.info(f"Invitation sent to {email} for family {family_id} by user {inviter_id}")
    return True, f"Invitation sent to {email}"