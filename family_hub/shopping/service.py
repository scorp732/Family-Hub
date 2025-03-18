from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from family_hub.data.storage import DataManager
from family_hub.data.models import ShoppingList, ShoppingItem

# Configure logging
logger = logging.getLogger('family_hub.shopping')

def get_shopping_lists(family_id: str) -> List[Dict[str, Any]]:
    """
    Get all shopping lists for a family
    
    Args:
        family_id: Family ID to get shopping lists for
        
    Returns:
        List of shopping list dictionaries
    """
    logger.info(f"Getting shopping lists for family {family_id}")
    
    # Get shopping lists
    shopping_lists = DataManager.get_shopping_lists_by_family(family_id)
    
    # Sort by name
    shopping_lists.sort(key=lambda x: x.get("name", "").lower())
    
    return shopping_lists


def get_shopping_list_with_items(list_id: str) -> Dict[str, Any]:
    """
    Get a shopping list with all its items
    
    Args:
        list_id: Shopping list ID
        
    Returns:
        Shopping list dictionary with items
    """
    logger.info(f"Getting shopping list {list_id} with items")
    
    # Get shopping list
    shopping_list = DataManager.get_shopping_list(list_id)
    if not shopping_list:
        logger.error(f"Shopping list {list_id} not found")
        raise ValueError(f"Shopping list {list_id} not found")
    
    # Get items for this list
    items = DataManager.get_shopping_items_by_list(list_id)
    
    # Sort items by category, then by name
    items.sort(key=lambda x: (x.get("category", "").lower(), x.get("name", "").lower()))
    
    # Add items to shopping list
    shopping_list["items"] = items
    
    return shopping_list


def create_shopping_list(
    name: str,
    family_id: str,
    created_by: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new shopping list
    
    Args:
        name: Shopping list name
        family_id: Family ID
        created_by: User ID of creator
        description: Optional description
        
    Returns:
        Created shopping list dictionary
    """
    logger.info(f"Creating shopping list '{name}' for family {family_id}")
    
    # Create shopping list
    shopping_list = ShoppingList(
        name=name,
        description=description,
        created_by=created_by,
        family_id=family_id
    )
    
    # Save shopping list
    return DataManager.save_shopping_list(shopping_list)


def add_item_to_list(
    list_id: str,
    name: str,
    created_by: str,
    quantity: int = 1,
    category: Optional[str] = None,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add an item to a shopping list
    
    Args:
        list_id: Shopping list ID
        name: Item name
        created_by: User ID of creator
        quantity: Item quantity
        category: Optional item category
        note: Optional note
        
    Returns:
        Created shopping item dictionary
    """
    logger.info(f"Adding item '{name}' to shopping list {list_id}")
    
    # Create shopping item
    item = ShoppingItem(
        name=name,
        quantity=quantity,
        category=category,
        note=note,
        created_by=created_by,
        list_id=list_id,
        is_purchased=False
    )
    
    # Save shopping item
    return DataManager.save_shopping_item(item)


def update_item(item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a shopping item
    
    Args:
        item_id: ID of item to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated shopping item dictionary
    """
    logger.info(f"Updating shopping item {item_id}")
    
    # Get existing item
    item_data = DataManager.get_shopping_item(item_id)
    if not item_data:
        logger.error(f"Shopping item {item_id} not found")
        raise ValueError(f"Shopping item {item_id} not found")
    
    # Update item
    item = ShoppingItem(**item_data)
    
    # Apply updates
    for key, value in updates.items():
        if hasattr(item, key):
            setattr(item, key, value)
    
    # Save updated item
    return DataManager.save_shopping_item(item)


def toggle_item_purchased(item_id: str, is_purchased: bool) -> Dict[str, Any]:
    """
    Toggle a shopping item's purchased status
    
    Args:
        item_id: ID of item to update
        is_purchased: New purchased status
        
    Returns:
        Updated shopping item dictionary
    """
    logger.info(f"Toggling shopping item {item_id} purchased status to {is_purchased}")
    
    # Get existing item
    item_data = DataManager.get_shopping_item(item_id)
    if not item_data:
        logger.error(f"Shopping item {item_id} not found")
        raise ValueError(f"Shopping item {item_id} not found")
    
    # Update item
    item = ShoppingItem(**item_data)
    item.is_purchased = is_purchased
    
    # Set purchased_at if item is being marked as purchased
    if is_purchased and not item.is_purchased:
        item.purchased_at = datetime.now()
    elif not is_purchased:
        item.purchased_at = None
    
    # Save updated item
    return DataManager.save_shopping_item(item)


def delete_shopping_list(list_id: str) -> bool:
    """
    Delete a shopping list and all its items
    
    Args:
        list_id: ID of shopping list to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting shopping list {list_id}")
    
    # Delete all items in the list
    items = DataManager.get_shopping_items_by_list(list_id)
    for item in items:
        DataManager.delete_shopping_item(item.get("id"))
    
    # Delete the list
    return DataManager.delete_shopping_list(list_id)


def delete_shopping_item(item_id: str) -> bool:
    """
    Delete a shopping item
    
    Args:
        item_id: ID of shopping item to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting shopping item {item_id}")
    
    return DataManager.delete_shopping_item(item_id)