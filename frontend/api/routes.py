"""
API Routes for Gym Workout RAG
Handles workout generation requests
"""

import requests
from flask import request, jsonify
from . import api_bp

# Configuration
FASTAPI_URL = "http://localhost:8000"


@api_bp.route('/generate', methods=['POST'])
def generate_workout():
    """
    Generate workout plan by calling FastAPI backend.
    
    Expected JSON payload:
    {
        "model_config": {...},  # Optional, informational only
        "height": float,
        "weight": float,
        "age": int,
        "gender": str,
        "fitness_level": str,
        "days_per_week": int,
        "session_duration": int,
        "goals": list[str] or str,
        "equipment": list[str] or str,
        "injuries": str (optional),
        "preferred_split": str
    }
    
    Returns:
    {
        "success": bool,
        "workout_plan": {...} or "message": str
    }
    """
    try:
        data = request.json
        
        # Prepare user profile - match backend model field names
        user_profile = {
            "height": float(data['height']),
            "weight": float(data['weight']),
            "age": int(data['age']),
            "gender": data['gender'],
            "fitness_level": data['fitness_level'],
            "gym_days_per_week": int(data['days_per_week']),
            "workout_duration_minutes": int(data['session_duration']),
            "goals": _parse_list_field(data.get('goals', [])),
            "available_equipment": _parse_list_field(data.get('equipment', [])),
            "injuries_limitations": _parse_optional_list_field(data.get('injuries')),
            "preferred_split": data.get('preferred_split', 'full_body')
        }
        
        # Call FastAPI backend
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/generate",
            json=user_profile,
            timeout=600  # 10 minutes timeout for LLM generation
        )
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "workout_plan": response.json()
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Backend error: {response.text}"
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request timeout after 10 minutes. The model may be too slow. Try using a smaller model or LM Studio instead."
        }), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to backend server. Please ensure the FastAPI server is running."
        }), 503
        
    except KeyError as e:
        return jsonify({
            "success": False,
            "message": f"Missing required field: {str(e)}"
        }), 400
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid value: {str(e)}"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check health of both frontend and backend services.
    
    Returns:
    {
        "frontend": "healthy",
        "backend": {...}
    }
    """
    try:
        # Check backend health
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        backend_health = response.json()
        
        return jsonify({
            "frontend": "healthy",
            "backend": backend_health
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            "frontend": "healthy",
            "backend": {
                "status": "unhealthy",
                "error": str(e)
            }
        }), 503


# Helper functions
def _parse_list_field(value):
    """
    Parse a field that can be either a list or comma-separated string.
    
    Args:
        value: list[str] or str
        
    Returns:
        list[str]: Parsed and cleaned list
    """
    if isinstance(value, list):
        return [item.strip() for item in value if item.strip()]
    elif isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    else:
        return []


def _parse_optional_list_field(value):
    """
    Parse an optional field that can be either a list, comma-separated string, or None.
    
    Args:
        value: list[str], str, or None
        
    Returns:
        list[str] or None: Parsed list or None if empty
    """
    if not value:
        return None
    
    parsed = _parse_list_field(value)
    return parsed if parsed else None

# Made with Bob
