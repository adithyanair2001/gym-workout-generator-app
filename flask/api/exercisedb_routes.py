"""
ExerciseDB API Proxy Routes
Provides proxy endpoints to access ExerciseDB API through Flask server
"""

import os
import requests
from flask import request, jsonify, Blueprint

# Create blueprint for ExerciseDB routes
exercisedb_bp = Blueprint('exercisedb', __name__, url_prefix='/api/exercises')

# ExerciseDB API Configuration
EXERCISEDB_API_URL = os.getenv("EXERCISEDB_API_URL", "https://exercisedb.p.rapidapi.com/exercises")
EXERCISEDB_API_KEY = os.getenv("EXERCISEDB_API_KEY", "")
EXERCISEDB_API_HOST = "exercisedb.p.rapidapi.com"

# Request timeout
REQUEST_TIMEOUT = 30


def _get_headers():
    """Get headers for ExerciseDB API requests."""
    if not EXERCISEDB_API_KEY:
        raise ValueError("EXERCISEDB_API_KEY environment variable not set")
    
    return {
        "X-RapidAPI-Key": EXERCISEDB_API_KEY,
        "X-RapidAPI-Host": EXERCISEDB_API_HOST
    }


def _make_request(url, params=None):
    """
    Make a request to ExerciseDB API with error handling.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        
    Returns:
        tuple: (response_data, status_code)
    """
    try:
        headers = _get_headers()
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            return response.json(), 200
        elif response.status_code == 404:
            return {"success": False, "message": "Resource not found"}, 404
        elif response.status_code == 429:
            return {"success": False, "message": "Rate limit exceeded. Please try again later."}, 429
        else:
            return {
                "success": False,
                "message": f"ExerciseDB API error: {response.status_code}"
            }, response.status_code
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Request timeout. ExerciseDB API is slow or unavailable."
        }, 504
        
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Cannot connect to ExerciseDB API. Check your internet connection."
        }, 503
        
    except ValueError as e:
        return {
            "success": False,
            "message": str(e)
        }, 500
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }, 500


@exercisedb_bp.route('', methods=['GET'])
def list_exercises():
    """
    List all exercises with pagination.
    
    Query Parameters:
        limit (int): Number of exercises per page (1-200, default: 20)
        cursor (str): Pagination cursor from previous response
        
    Returns:
        JSON response with exercises and pagination metadata
    """
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            "success": False,
            "message": "Limit must be between 1 and 200"
        }), 400
    
    # Build URL with parameters
    params: dict[str, int | str] = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    
    # Make request to ExerciseDB API
    data, status = _make_request(EXERCISEDB_API_URL, params)
    
    # Format response
    if status == 200:
        return jsonify({
            "success": True,
            "meta": data.get('meta', {}),
            "data": data.get('data', [])
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/<exercise_id>', methods=['GET'])
def get_exercise(exercise_id):
    """
    Get a specific exercise by ID.
    
    Path Parameters:
        exercise_id (str): Exercise ID
        
    Returns:
        JSON response with exercise details
    """
    url = f"{EXERCISEDB_API_URL}/{exercise_id}"
    data, status = _make_request(url)
    
    if status == 200:
        return jsonify({
            "success": True,
            "data": data
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/search', methods=['GET'])
def search_exercises():
    """
    Search exercises by name using fuzzy matching.
    
    Query Parameters:
        query (str): Search query (required)
        limit (int): Number of results (1-200, default: 20)
        cursor (str): Pagination cursor
        
    Returns:
        JSON response with matching exercises
    """
    # Get query parameters
    query = request.args.get('query', None, type=str)
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    # Validate query
    if not query:
        return jsonify({
            "success": False,
            "message": "Query parameter is required"
        }), 400
    
    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            "success": False,
            "message": "Limit must be between 1 and 200"
        }), 400
    
    # Build URL
    url = f"{EXERCISEDB_API_URL}/name/{query}"
    params: dict[str, int | str] = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    
    # Make request
    data, status = _make_request(url, params)
    
    if status == 200:
        return jsonify({
            "success": True,
            "meta": data.get('meta', {}),
            "data": data.get('data', [])
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/target/<muscle>', methods=['GET'])
def filter_by_target_muscle(muscle):
    """
    Get exercises that target a specific muscle group.
    
    Path Parameters:
        muscle (str): Target muscle (e.g., 'pectorals', 'biceps')
        
    Query Parameters:
        limit (int): Number of results (1-200, default: 20)
        cursor (str): Pagination cursor
        
    Returns:
        JSON response with exercises targeting the specified muscle
    """
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            "success": False,
            "message": "Limit must be between 1 and 200"
        }), 400
    
    # Build URL
    url = f"{EXERCISEDB_API_URL}/target/{muscle}"
    params: dict[str, int | str] = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    
    # Make request
    data, status = _make_request(url, params)
    
    if status == 200:
        return jsonify({
            "success": True,
            "meta": data.get('meta', {}),
            "data": data.get('data', [])
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/bodypart/<part>', methods=['GET'])
def filter_by_body_part(part):
    """
    Get exercises for a specific body part.
    
    Path Parameters:
        part (str): Body part (e.g., 'chest', 'back', 'legs')
        
    Query Parameters:
        limit (int): Number of results (1-200, default: 20)
        cursor (str): Pagination cursor
        
    Returns:
        JSON response with exercises for the specified body part
    """
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            "success": False,
            "message": "Limit must be between 1 and 200"
        }), 400
    
    # Build URL
    url = f"{EXERCISEDB_API_URL}/bodyPart/{part}"
    params: dict[str, int | str] = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    
    # Make request
    data, status = _make_request(url, params)
    
    if status == 200:
        return jsonify({
            "success": True,
            "meta": data.get('meta', {}),
            "data": data.get('data', [])
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/equipment/<equipment>', methods=['GET'])
def filter_by_equipment(equipment):
    """
    Get exercises that use specific equipment.
    
    Path Parameters:
        equipment (str): Equipment type (e.g., 'barbell', 'dumbbell')
        
    Query Parameters:
        limit (int): Number of results (1-200, default: 20)
        cursor (str): Pagination cursor
        
    Returns:
        JSON response with exercises using the specified equipment
    """
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    # Validate limit
    if limit < 1 or limit > 200:
        return jsonify({
            "success": False,
            "message": "Limit must be between 1 and 200"
        }), 400
    
    # Build URL
    url = f"{EXERCISEDB_API_URL}/equipment/{equipment}"
    params: dict[str, int | str] = {'limit': limit}
    if cursor:
        params['cursor'] = cursor
    
    # Make request
    data, status = _make_request(url, params)
    
    if status == 200:
        return jsonify({
            "success": True,
            "meta": data.get('meta', {}),
            "data": data.get('data', [])
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/targets', methods=['GET'])
def list_target_muscles():
    """
    Get a list of all available target muscle groups.
    
    Returns:
        JSON response with list of target muscles
    """
    url = f"{EXERCISEDB_API_URL}/targetList"
    data, status = _make_request(url)
    
    if status == 200:
        return jsonify({
            "success": True,
            "data": data
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/bodyparts', methods=['GET'])
def list_body_parts():
    """
    Get a list of all available body parts.
    
    Returns:
        JSON response with list of body parts
    """
    url = f"{EXERCISEDB_API_URL}/bodyPartList"
    data, status = _make_request(url)
    
    if status == 200:
        return jsonify({
            "success": True,
            "data": data
        }), 200
    else:
        return jsonify(data), status


@exercisedb_bp.route('/equipments', methods=['GET'])
def list_equipment_types():
    """
    Get a list of all available equipment types.
    
    Returns:
        JSON response with list of equipment types
    """
    url = f"{EXERCISEDB_API_URL}/equipmentList"
    data, status = _make_request(url)
    
    if status == 200:
        return jsonify({
            "success": True,
            "data": data
        }), 200
    else:
        return jsonify(data), status


# Error handlers for this blueprint
@exercisedb_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "message": "Endpoint not found"
    }), 404


@exercisedb_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500


# Made with Bob