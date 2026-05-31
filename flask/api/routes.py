"""
API Routes for Gym Workout RAG
Handles workout generation requests and model validation
"""

import os
import logging
import requests
from flask import request, jsonify
from . import api_bp
from utils.validators import validate_user_profile, sanitize_string, sanitize_list_field

logger = logging.getLogger(__name__)

# Configuration - Use environment variable with fallback
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:7501")


@api_bp.route('/validate-model', methods=['POST'])
def validate_model():
    """
    Validate model configuration and test connection.
    
    Expected JSON payload:
    {
        "model_type": str,
        "llm_base_url": str (optional),
        "llm_model": str (optional),
        "llm_api_key": str (optional),
        "mlx_model_path": str (optional),
        "gguf_model_path": str (optional)
    }
    
    Returns:
    {
        "success": bool,
        "message": str,
        "details": {...}
    }
    """
    try:
        data = request.json
        model_type = data.get('model_type')
        
        if model_type == 'mlx':
            return _validate_mlx_model(data)
        elif model_type == 'omlx':
            return _validate_omlx_server(data)
        elif model_type == 'gguf':
            return _validate_gguf_model(data)
        elif model_type == 'local_server':
            return _validate_local_server(data)
        elif model_type in ['openai', 'anthropic', 'groq']:
            return _validate_public_api(data, model_type)
        else:
            return jsonify({
                "success": False,
                "message": f"Unknown model type: {model_type}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Validation error: {str(e)}"
        }), 500


def _validate_mlx_model(data):
    """Validate MLX model path exists."""
    import os
    
    model_path = data.get('mlx_model_path', '')
    
    if not model_path:
        return jsonify({
            "success": False,
            "message": "MLX model path is required"
        }), 400
    
    # Check if path exists
    if not os.path.exists(model_path):
        return jsonify({
            "success": False,
            "message": f"MLX model not found at: {model_path}",
            "details": {
                "path": model_path,
                "exists": False
            }
        }), 404
    
    # Check if it's a directory with required files
    if not os.path.isdir(model_path):
        return jsonify({
            "success": False,
            "message": "MLX model path must be a directory"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "MLX model found and accessible",
        "details": {
            "path": model_path,
            "exists": True,
            "type": "mlx"
        }
    })


def _validate_omlx_server(data):
    """Validate OMLX server connection."""
    server_url = data.get('llm_base_url', '')
    model_name = data.get('llm_model', '')
    api_key = data.get('llm_api_key', '')
    
    if not server_url:
        return jsonify({
            "success": False,
            "message": "OMLX server URL is required"
        }), 400
    
    try:
        # Prepare headers with API key if provided
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Test connection to OMLX server
        response = requests.get(f"{server_url}/models", headers=headers, timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            return jsonify({
                "success": True,
                "message": "OMLX server is accessible and authenticated" if api_key else "OMLX server is accessible",
                "details": {
                    "server_url": server_url,
                    "model": model_name,
                    "authenticated": bool(api_key),
                    "available_models": models.get('data', [])
                }
            })
        elif response.status_code == 401:
            return jsonify({
                "success": False,
                "message": "OMLX server requires authentication. Please provide an API key.",
                "details": {
                    "hint": "Enter your OMLX API key in the 'API Key (optional)' field"
                }
            }), 401
        else:
            return jsonify({
                "success": False,
                "message": f"OMLX server returned status {response.status_code}"
            }), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to OMLX server. Make sure it's running.",
            "details": {
                "server_url": server_url,
                "hint": "Run: omlx serve --model <model-name> --port 8000"
            }
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Connection to OMLX server timed out"
        }), 504
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error connecting to OMLX server: {str(e)}"
        }), 500


def _validate_gguf_model(data):
    """Validate GGUF model path exists."""
    import os
    
    model_path = data.get('gguf_model_path', '')
    
    if not model_path:
        return jsonify({
            "success": False,
            "message": "GGUF model path is required"
        }), 400
    
    if not os.path.exists(model_path):
        return jsonify({
            "success": False,
            "message": f"GGUF model not found at: {model_path}",
            "details": {
                "path": model_path,
                "exists": False
            }
        }), 404
    
    if not model_path.endswith('.gguf'):
        return jsonify({
            "success": False,
            "message": "File must have .gguf extension"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "GGUF model found and accessible",
        "details": {
            "path": model_path,
            "exists": True,
            "type": "gguf"
        }
    })


def _validate_local_server(data):
    """Validate local server (LM Studio/OLLAMA) connection."""
    server_url = data.get('llm_base_url', '')
    
    if not server_url:
        return jsonify({
            "success": False,
            "message": "Server URL is required"
        }), 400
    
    try:
        # Test connection to local server
        response = requests.get(f"{server_url}/models", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            return jsonify({
                "success": True,
                "message": "Local server is accessible",
                "details": {
                    "server_url": server_url,
                    "available_models": models.get('data', [])
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Server returned status {response.status_code}"
            }), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to local server. Make sure LM Studio or OLLAMA is running.",
            "details": {
                "server_url": server_url,
                "hint": "Start LM Studio or run: ollama serve"
            }
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Connection to server timed out"
        }), 504
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error connecting to server: {str(e)}"
        }), 500


def _validate_public_api(data, model_type):
    """Validate public API (OpenAI/Anthropic/Groq) credentials."""
    api_key = data.get('llm_api_key', '')
    model_name = data.get('llm_model', '')
    
    if not api_key:
        return jsonify({
            "success": False,
            "message": f"{model_type.title()} API key is required"
        }), 400
    
    # API endpoint mapping
    endpoints = {
        'openai': 'https://api.openai.com/v1/models',
        'anthropic': 'https://api.anthropic.com/v1/messages',
        'groq': 'https://api.groq.com/openai/v1/models'
    }
    
    headers = {}
    if model_type == 'openai' or model_type == 'groq':
        headers['Authorization'] = f'Bearer {api_key}'
    elif model_type == 'anthropic':
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
    
    try:
        # Test API key with a simple request
        response = requests.get(
            endpoints[model_type],
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": f"{model_type.title()} API key is valid",
                "details": {
                    "model": model_name,
                    "provider": model_type
                }
            })
        elif response.status_code == 401:
            return jsonify({
                "success": False,
                "message": f"Invalid {model_type.title()} API key"
            }), 401
        else:
            return jsonify({
                "success": False,
                "message": f"API returned status {response.status_code}: {response.text}"
            }), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": f"Cannot connect to {model_type.title()} API. Check your internet connection."
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": f"Connection to {model_type.title()} API timed out"
        }), 504
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error validating API key: {str(e)}"
        }), 500


@api_bp.route('/generate', methods=['POST'])
def generate_workout():
    """
    Generate workout plan by calling FastAPI backend.
    
    Expected JSON payload:
    {
        "model_config": {...},  # Now actually used!
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
        
        # Validate input data
        is_valid, error_message = validate_user_profile(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": f"Validation error: {error_message}"
            }), 400
        
        # Sanitize and prepare user profile - match backend model field names
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
        
        # Prepare request payload with optional model configuration
        request_payload = {
            "user_profile": user_profile
        }
        
        # Add model configuration if provided
        model_config = data.get('model_config')
        if model_config:
            # Clean up the model config - remove empty/None values
            cleaned_config = {k: v for k, v in model_config.items() if v is not None and v != ''}
            if cleaned_config:
                request_payload["llm_config"] = cleaned_config
                logger.info(f"Using model configuration: {cleaned_config.get('model_type', 'unknown')}")
        else:
            logger.info("No model configuration provided, using .env defaults")
        
        # Call FastAPI backend with new request format
        response = requests.post(
            f"{FASTAPI_URL}/api/v1/generate",
            json=request_payload,
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


@api_bp.route('/models', methods=['GET', 'POST'])
def list_models():
    """
    List available models from the LLM provider.
    
    GET: Uses backend's default configuration from .env
    POST: Accepts custom base_url and api_key to fetch models dynamically
    
    POST JSON payload:
    {
        "base_url": str,
        "api_key": str (optional)
    }
    
    Returns:
    {
        "success": bool,
        "provider": str,
        "models": [...] or "message": str
    }
    """
    try:
        if request.method == 'POST':
            # POST request with custom configuration
            data = request.json
            base_url = data.get('base_url')
            api_key = data.get('api_key')
            
            if not base_url:
                return jsonify({
                    "success": False,
                    "message": "base_url is required"
                }), 400
            
            # Prepare headers with API key if provided
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Fetch models directly from the provided URL
            try:
                response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    models_data = response.json()
                    models = models_data.get('data', [])
                    
                    return jsonify({
                        "success": True,
                        "provider": "omlx",
                        "models": models
                    })
                elif response.status_code == 401:
                    return jsonify({
                        "success": False,
                        "message": "Authentication failed. Please check your API key."
                    }), 401
                else:
                    return jsonify({
                        "success": False,
                        "message": f"Server returned status {response.status_code}"
                    }), response.status_code
                    
            except requests.exceptions.ConnectionError:
                return jsonify({
                    "success": False,
                    "message": "Cannot connect to OMLX server. Make sure it's running."
                }), 503
            except requests.exceptions.Timeout:
                return jsonify({
                    "success": False,
                    "message": "Connection timeout. Server may be slow or unavailable."
                }), 504
        else:
            # GET request - use backend's default configuration
            response = requests.get(f"{FASTAPI_URL}/api/v1/models", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    "success": True,
                    **data
                })
            else:
                return jsonify({
                    "success": False,
                    "message": f"Backend error: {response.text}"
                }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request timeout. The LLM server may be slow or unavailable."
        }), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to backend server. Please ensure the FastAPI server is running."
        }), 503
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500


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
