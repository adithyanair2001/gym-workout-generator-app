"""Input validation and sanitization utilities."""
import re
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def validate_n_results(n_results: Any, min_val: int = 1, max_val: int = 100) -> int:
    """Validate and sanitize n_results parameter.
    
    Args:
        n_results: Value to validate (can be string or int)
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated integer value
        
    Raises:
        ValueError: If value is invalid or out of bounds
    """
    try:
        n = int(n_results)
        if n < min_val or n > max_val:
            raise ValueError(f"n_results must be between {min_val} and {max_val}, got {n}")
        return n
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid n_results value: {n_results}. Must be an integer between {min_val} and {max_val}") from e


def validate_exercise_id(exercise_id: str) -> str:
    """Validate and sanitize exercise ID.
    
    Exercise IDs should be alphanumeric with optional hyphens/underscores.
    
    Args:
        exercise_id: Exercise ID to validate
        
    Returns:
        Sanitized exercise ID
        
    Raises:
        ValueError: If ID format is invalid
    """
    if not exercise_id or not isinstance(exercise_id, str):
        raise ValueError("Exercise ID must be a non-empty string")
    
    # Remove any whitespace
    exercise_id = exercise_id.strip()
    
    # Check format: alphanumeric with optional hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', exercise_id):
        raise ValueError(f"Invalid exercise ID format: {exercise_id}. Must contain only alphanumeric characters, hyphens, or underscores")
    
    # Limit length to prevent abuse
    if len(exercise_id) > 50:
        raise ValueError(f"Exercise ID too long: {len(exercise_id)} characters (max 50)")
    
    return exercise_id


def sanitize_query_string(query: str, max_length: int = 500) -> str:
    """Sanitize search query string.
    
    Args:
        query: Query string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized query string
        
    Raises:
        ValueError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    # Remove leading/trailing whitespace
    query = query.strip()
    
    if not query:
        raise ValueError("Query cannot be empty after trimming whitespace")
    
    # Limit length to prevent abuse
    if len(query) > max_length:
        logger.warning(f"Query truncated from {len(query)} to {max_length} characters")
        query = query[:max_length]
    
    # Remove any null bytes or control characters
    query = ''.join(char for char in query if ord(char) >= 32 or char in '\n\r\t')
    
    return query


def validate_equipment_list(equipment: Any) -> List[str]:
    """Validate and sanitize equipment list.
    
    Args:
        equipment: Equipment list (can be string, list, or comma-separated)
        
    Returns:
        Validated list of equipment names
        
    Raises:
        ValueError: If equipment list is invalid
    """
    if not equipment:
        raise ValueError("Equipment list cannot be empty")
    
    # Convert to list if string
    if isinstance(equipment, str):
        equipment_list = [e.strip() for e in equipment.split(',')]
    elif isinstance(equipment, list):
        equipment_list = [str(e).strip() for e in equipment]
    else:
        raise ValueError(f"Equipment must be a string or list, got {type(equipment)}")
    
    # Remove empty strings
    equipment_list = [e for e in equipment_list if e]
    
    if not equipment_list:
        raise ValueError("Equipment list cannot be empty after processing")
    
    # Validate each equipment name
    validated = []
    for equip in equipment_list:
        # Check format: alphanumeric with spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', equip):
            logger.warning(f"Skipping invalid equipment name: {equip}")
            continue
        
        # Limit length
        if len(equip) > 50:
            logger.warning(f"Equipment name too long, truncating: {equip}")
            equip = equip[:50]
        
        validated.append(equip.lower())  # Normalize to lowercase
    
    if not validated:
        raise ValueError("No valid equipment names found in list")
    
    return validated


def sanitize_user_data_for_logging(data: dict) -> dict:
    """Sanitize user profile data for safe logging (remove PII).
    
    Args:
        data: User profile dictionary
        
    Returns:
        Sanitized dictionary safe for logging
    """
    sensitive_fields = ['age', 'weight', 'height', 'gender', 'name', 'email']
    sanitized = {}
    
    for key, value in data.items():
        if key in sensitive_fields:
            sanitized[key] = '[REDACTED]'
        else:
            sanitized[key] = value
    
    return sanitized


# Made with Bob