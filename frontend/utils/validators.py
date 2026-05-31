"""
Input validation utilities for frontend
"""
from typing import Dict, List, Optional, Tuple


def validate_user_profile(data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate user profile data before sending to backend.
    
    Args:
        data: User profile dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields
    required_fields = [
        'height', 'weight', 'age', 'gender', 'fitness_level',
        'days_per_week', 'session_duration', 'goals', 'equipment'
    ]
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            return False, f"Missing required field: {field}"
    
    # Validate numeric ranges
    try:
        height = float(data['height'])
        if not (100 <= height <= 250):
            return False, "Height must be between 100 and 250 cm"
    except (ValueError, TypeError):
        return False, "Height must be a valid number"
    
    try:
        weight = float(data['weight'])
        if not (30 <= weight <= 300):
            return False, "Weight must be between 30 and 300 kg"
    except (ValueError, TypeError):
        return False, "Weight must be a valid number"
    
    try:
        age = int(data['age'])
        if not (13 <= age <= 100):
            return False, "Age must be between 13 and 100 years"
    except (ValueError, TypeError):
        return False, "Age must be a valid integer"
    
    try:
        days = int(data['days_per_week'])
        if not (1 <= days <= 7):
            return False, "Days per week must be between 1 and 7"
    except (ValueError, TypeError):
        return False, "Days per week must be a valid integer"
    
    try:
        duration = int(data['session_duration'])
        if not (30 <= duration <= 120):
            return False, "Session duration must be between 30 and 120 minutes"
    except (ValueError, TypeError):
        return False, "Session duration must be a valid integer"
    
    # Validate gender
    if data['gender'] not in ['male', 'female', 'other']:
        return False, "Gender must be 'male', 'female', or 'other'"
    
    # Validate fitness level
    if data['fitness_level'] not in ['beginner', 'intermediate', 'advanced']:
        return False, "Fitness level must be 'beginner', 'intermediate', or 'advanced'"
    
    # Validate goals (must be list or comma-separated string)
    goals = data.get('goals', [])
    if isinstance(goals, str):
        goals = [g.strip() for g in goals.split(',') if g.strip()]
    if not goals or len(goals) == 0:
        return False, "At least one fitness goal must be specified"
    
    valid_goals = ['muscle_gain', 'weight_loss', 'strength', 'endurance', 'general_fitness']
    for goal in goals:
        if goal not in valid_goals:
            return False, f"Invalid goal: {goal}. Must be one of: {', '.join(valid_goals)}"
    
    # Validate equipment (must be list or comma-separated string)
    equipment = data.get('equipment', [])
    if isinstance(equipment, str):
        equipment = [e.strip() for e in equipment.split(',') if e.strip()]
    if not equipment or len(equipment) == 0:
        return False, "At least one equipment type must be specified"
    
    # Validate preferred split
    preferred_split = data.get('preferred_split', 'auto')
    if preferred_split not in ['full_body', 'upper_lower', 'push_pull_legs', 'auto']:
        return False, "Invalid workout split. Must be 'full_body', 'upper_lower', 'push_pull_legs', or 'auto'"
    
    return True, None


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by trimming and limiting length.
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_list_field(value, allowed_values: Optional[List[str]] = None) -> List[str]:
    """
    Sanitize list field (can be list or comma-separated string).
    
    Args:
        value: Input value (list or string)
        allowed_values: Optional list of allowed values
        
    Returns:
        Sanitized list of strings
    """
    if isinstance(value, list):
        result = [sanitize_string(item) for item in value if item]
    elif isinstance(value, str):
        result = [sanitize_string(item) for item in value.split(',') if item.strip()]
    else:
        result = []
    
    # Filter by allowed values if provided
    if allowed_values:
        result = [item for item in result if item in allowed_values]
    
    return result

# Made with Bob