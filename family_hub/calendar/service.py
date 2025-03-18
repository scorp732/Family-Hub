from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from family_hub.data.storage import DataManager
from family_hub.data.models import Event, EventType

# Configure logging
logger = logging.getLogger('family_hub.calendar')

def get_upcoming_events(family_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get upcoming events for a family
    
    Args:
        family_id: Family ID to get events for
        days: Number of days to look ahead (default: 7)
        
    Returns:
        List of event dictionaries
    """
    logger.info(f"Getting upcoming events for family {family_id} for next {days} days")
    
    # Calculate date range
    today = datetime.now()
    end_date = today + timedelta(days=days)
    
    # Get events in date range
    events = DataManager.get_events_by_family(family_id, start_date=today, end_date=end_date)
    
    # Sort by start time
    events.sort(key=lambda x: x.get("start_time", ""))
    
    return events


def create_event(
    title: str,
    start_time: datetime,
    family_id: str,
    created_by: str,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None,
    event_type: EventType = EventType.APPOINTMENT,
    location: Optional[str] = None,
    all_day: bool = False,
    assigned_to: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new event
    
    Args:
        title: Event title
        start_time: Event start time
        family_id: Family ID
        created_by: User ID of creator
        end_time: Optional event end time
        description: Optional event description
        event_type: Event type
        location: Optional event location
        all_day: Whether this is an all-day event
        assigned_to: Optional list of user IDs to assign to
        
    Returns:
        Created event dictionary
    """
    logger.info(f"Creating event '{title}' for family {family_id}")
    
    # Create event
    event = Event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        event_type=event_type,
        created_by=created_by,
        family_id=family_id,
        location=location,
        all_day=all_day,
        assigned_to=assigned_to or [created_by]
    )
    
    # Save event
    return DataManager.save_event(event)


def update_event(event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing event
    
    Args:
        event_id: ID of event to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated event dictionary
    """
    logger.info(f"Updating event {event_id}")
    
    # Get existing event
    event_data = DataManager.get_event(event_id)
    if not event_data:
        logger.error(f"Event {event_id} not found")
        raise ValueError(f"Event {event_id} not found")
    
    # Update event
    event = Event(**event_data)
    
    # Apply updates
    for key, value in updates.items():
        if hasattr(event, key):
            setattr(event, key, value)
    
    # Save updated event
    return DataManager.save_event(event)


def delete_event(event_id: str) -> bool:
    """
    Delete an event
    
    Args:
        event_id: ID of event to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting event {event_id}")
    
    return DataManager.delete_event(event_id)