from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from family_hub.data.storage import DataManager
from family_hub.data.models import Task, TaskStatus, TaskPriority

# Configure logging
logger = logging.getLogger('family_hub.tasks')

def get_task_summary(family_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a summary of tasks for a family or user
    
    Args:
        family_id: Family ID to get tasks for
        user_id: Optional user ID to filter tasks by
        
    Returns:
        List of task dictionaries
    """
    logger.info(f"Getting task summary for family {family_id}" + (f", user {user_id}" if user_id else ""))
    
    # Get tasks
    if user_id:
        tasks = DataManager.get_tasks_by_user(user_id, status=TaskStatus.TODO)
    else:
        tasks = DataManager.get_tasks_by_family(family_id, status=TaskStatus.TODO)
    
    # Sort by priority (high to low) and due date
    tasks.sort(key=lambda x: (
        -1 * x.get("priority", 1),  # Higher priority first
        x.get("due_date", "9999-12-31")  # Earlier due date first
    ))
    
    return tasks


def create_task(
    title: str,
    family_id: str,
    created_by: str,
    description: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    due_date: Optional[datetime] = None,
    assigned_to: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new task
    
    Args:
        title: Task title
        family_id: Family ID
        created_by: User ID of creator
        description: Optional task description
        priority: Task priority
        due_date: Optional due date
        assigned_to: Optional list of user IDs to assign to
        
    Returns:
        Created task dictionary
    """
    logger.info(f"Creating task '{title}' for family {family_id}")
    
    # Create task
    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        created_by=created_by,
        family_id=family_id,
        assigned_to=assigned_to or [created_by],
        status=TaskStatus.TODO
    )
    
    # Save task
    return DataManager.save_task(task)


def update_task(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing task
    
    Args:
        task_id: ID of task to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated task dictionary
    """
    logger.info(f"Updating task {task_id}")
    
    # Get existing task
    task_data = DataManager.get_task(task_id)
    if not task_data:
        logger.error(f"Task {task_id} not found")
        raise ValueError(f"Task {task_id} not found")
    
    # Update task
    task = Task(**task_data)
    
    # Apply updates
    for key, value in updates.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    # Save updated task
    return DataManager.save_task(task)


def update_task_status(task_id: str, new_status: TaskStatus, user_id: str) -> Dict[str, Any]:
    """
    Update a task's status
    
    Args:
        task_id: ID of task to update
        new_status: New status to set
        user_id: ID of user making the change
        
    Returns:
        Updated task dictionary
    """
    logger.info(f"Updating task {task_id} status to {new_status.value} by user {user_id}")
    
    # Get existing task
    task_data = DataManager.get_task(task_id)
    if not task_data:
        logger.error(f"Task {task_id} not found")
        raise ValueError(f"Task {task_id} not found")
    
    # Update task status
    task = Task(**task_data)
    task.status = new_status
    
    # Set completed_at if task is being marked as done
    if new_status == TaskStatus.DONE and task.status != TaskStatus.DONE:
        task.completed_at = datetime.now()
    elif new_status != TaskStatus.DONE:
        task.completed_at = None
    
    # Save updated task
    return DataManager.save_task(task)


def delete_task(task_id: str) -> bool:
    """
    Delete a task
    
    Args:
        task_id: ID of task to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting task {task_id}")
    
    return DataManager.delete_task(task_id)