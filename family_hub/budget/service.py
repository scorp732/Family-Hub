from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from family_hub.data.storage import DataManager
from family_hub.data.models import Transaction, TransactionType, Budget, BudgetCategory, BudgetPeriod

# Configure logging
logger = logging.getLogger('family_hub.budget')

def get_budget_summary(family_id: str) -> Dict[str, Any]:
    """
    Get a summary of the family's budget for the current month
    
    Args:
        family_id: Family ID to get budget for
        
    Returns:
        Dictionary with budget summary
    """
    logger.info(f"Getting budget summary for family {family_id}")
    
    # Get current month's date range
    today = datetime.now()
    start_of_month = datetime(today.year, today.month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get transactions for the current month
    transactions = DataManager.get_transactions_by_family(
        family_id, 
        start_date=start_of_month,
        end_date=end_of_month
    )
    
    # Calculate income and expenses
    income = sum(t.get("amount", 0) for t in transactions if t.get("transaction_type") == "income")
    expenses = sum(t.get("amount", 0) for t in transactions if t.get("transaction_type") == "expense")
    balance = income - expenses
    
    # Get budgets
    budgets = DataManager.get_budgets_by_family(family_id)
    total_budget = sum(b.get("amount", 0) for b in budgets if b.get("period") == "monthly")
    
    # Group expenses by category
    expenses_by_category = {}
    for transaction in transactions:
        if transaction.get("transaction_type") == "expense":
            category = transaction.get("category", "other")
            if category not in expenses_by_category:
                expenses_by_category[category] = 0
            expenses_by_category[category] += transaction.get("amount", 0)
    
    # Calculate budget vs actual
    budget_vs_actual = []
    for budget in budgets:
        if budget.get("period") == "monthly":
            category = budget.get("category")
            budget_amount = budget.get("amount", 0)
            actual_amount = expenses_by_category.get(category, 0)
            remaining = budget_amount - actual_amount
            percent_used = (actual_amount / budget_amount * 100) if budget_amount > 0 else 100
            
            budget_vs_actual.append({
                "category": category,
                "budget": budget_amount,
                "actual": actual_amount,
                "remaining": remaining,
                "percent_used": percent_used
            })
    
    return {
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "total_budget": total_budget,
        "budget_remaining": total_budget - expenses,
        "budget_percent_used": (expenses / total_budget * 100) if total_budget > 0 else 100,
        "expenses_by_category": expenses_by_category,
        "budget_vs_actual": budget_vs_actual
    }


def get_transactions(
    family_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Get transactions for a family within a date range
    
    Args:
        family_id: Family ID to get transactions for
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        List of transaction dictionaries
    """
    logger.info(f"Getting transactions for family {family_id}")
    
    # Set default date range if not provided
    if not start_date:
        # Default to current month
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
    
    if not end_date:
        # Default to end of current month
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    # Get transactions
    transactions = DataManager.get_transactions_by_family(
        family_id, 
        start_date=start_date,
        end_date=end_date
    )
    
    # Sort by date (newest first)
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return transactions


def create_transaction(
    amount: float,
    description: str,
    transaction_type: TransactionType,
    family_id: str,
    created_by: str,
    category: Optional[str] = None,
    date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create a new transaction
    
    Args:
        amount: Transaction amount
        description: Transaction description
        transaction_type: Transaction type (income or expense)
        family_id: Family ID
        created_by: User ID of creator
        category: Optional transaction category
        date: Optional transaction date (defaults to today)
        
    Returns:
        Created transaction dictionary
    """
    logger.info(f"Creating {transaction_type.value} transaction for family {family_id}")
    
    # Create transaction
    transaction = Transaction(
        amount=amount,
        description=description,
        transaction_type=transaction_type,
        category=category or "other",
        date=date or datetime.now(),
        created_by=created_by,
        family_id=family_id
    )
    
    # Save transaction
    return DataManager.save_transaction(transaction)


def create_budget(
    amount: float,
    category: BudgetCategory,
    period: BudgetPeriod,
    family_id: str,
    created_by: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new budget
    
    Args:
        amount: Budget amount
        category: Budget category
        period: Budget period (monthly, yearly)
        family_id: Family ID
        created_by: User ID of creator
        description: Optional budget description
        
    Returns:
        Created budget dictionary
    """
    logger.info(f"Creating {period.value} budget for category {category.value} for family {family_id}")
    
    # Create budget
    budget = Budget(
        amount=amount,
        category=category,
        period=period,
        description=description,
        created_by=created_by,
        family_id=family_id
    )
    
    # Save budget
    return DataManager.save_budget(budget)


def update_transaction(transaction_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing transaction
    
    Args:
        transaction_id: ID of transaction to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated transaction dictionary
    """
    logger.info(f"Updating transaction {transaction_id}")
    
    # Get existing transaction
    transaction_data = DataManager.get_transaction(transaction_id)
    if not transaction_data:
        logger.error(f"Transaction {transaction_id} not found")
        raise ValueError(f"Transaction {transaction_id} not found")
    
    # Update transaction
    transaction = Transaction(**transaction_data)
    
    # Apply updates
    for key, value in updates.items():
        if hasattr(transaction, key):
            setattr(transaction, key, value)
    
    # Save updated transaction
    return DataManager.save_transaction(transaction)


def update_budget(budget_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing budget
    
    Args:
        budget_id: ID of budget to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated budget dictionary
    """
    logger.info(f"Updating budget {budget_id}")
    
    # Get existing budget
    budget_data = DataManager.get_budget(budget_id)
    if not budget_data:
        logger.error(f"Budget {budget_id} not found")
        raise ValueError(f"Budget {budget_id} not found")
    
    # Update budget
    budget = Budget(**budget_data)
    
    # Apply updates
    for key, value in updates.items():
        if hasattr(budget, key):
            setattr(budget, key, value)
    
    # Save updated budget
    return DataManager.save_budget(budget)


def delete_transaction(transaction_id: str) -> bool:
    """
    Delete a transaction
    
    Args:
        transaction_id: ID of transaction to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting transaction {transaction_id}")
    
    return DataManager.delete_transaction(transaction_id)


def delete_budget(budget_id: str) -> bool:
    """
    Delete a budget
    
    Args:
        budget_id: ID of budget to delete
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Deleting budget {budget_id}")
    
    return DataManager.delete_budget(budget_id)


def get_spending_trends(
    family_id: str,
    months: int = 3
) -> Dict[str, Any]:
    """
    Get spending trends for a family
    
    Args:
        family_id: Family ID to get trends for
        months: Number of months to analyze
        
    Returns:
        Dictionary with spending trends
    """
    logger.info(f"Getting spending trends for family {family_id} for past {months} months")
    
    # Calculate date range
    today = datetime.now()
    end_date = today
    start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    for _ in range(months - 1):
        start_date = (start_date - timedelta(days=1)).replace(day=1)
    
    # Get transactions
    transactions = DataManager.get_transactions_by_family(
        family_id, 
        start_date=start_date,
        end_date=end_date
    )
    
    # Group by month and category
    monthly_data = {}
    for transaction in transactions:
        if transaction.get("transaction_type") != "expense":
            continue
        
        date = datetime.fromisoformat(transaction["date"].replace('Z', '+00:00')) if isinstance(transaction["date"], str) else transaction["date"]
        month_key = date.strftime("%Y-%m")
        category = transaction.get("category", "other")
        amount = transaction.get("amount", 0)
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {"total": 0, "categories": {}}
        
        monthly_data[month_key]["total"] += amount
        
        if category not in monthly_data[month_key]["categories"]:
            monthly_data[month_key]["categories"][category] = 0
        
        monthly_data[month_key]["categories"][category] += amount
    
    # Format data for charts
    months_labels = []
    total_spending = []
    categories_data = {}
    
    # Sort months chronologically
    for month_key in sorted(monthly_data.keys()):
        month_data = monthly_data[month_key]
        month_label = datetime.strptime(month_key, "%Y-%m").strftime("%b %Y")
        
        months_labels.append(month_label)
        total_spending.append(month_data["total"])
        
        for category, amount in month_data["categories"].items():
            if category not in categories_data:
                categories_data[category] = [0] * len(months_labels)
            
            categories_data[category][-1] = amount
    
    return {
        "months": months_labels,
        "total_spending": total_spending,
        "categories_data": categories_data
    }