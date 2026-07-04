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

# Base URLs for online providers
_ONLINE_BASE_URLS = {
    "openai":    "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "groq":      "https://api.groq.com/openai/v1",
    "gemini":    "https://generativelanguage.googleapis.com/v1beta/openai",
}


# ---------------------------------------------------------------------------
# /api/validate-model  — only used for GGUF path validation now
# ---------------------------------------------------------------------------

@api_bp.route('/validate-model', methods=['POST'])
def validate_model():
    """Validate GGUF model file path."""
    try:
        data = request.json or {}
        model_type = data.get('model_type', '')

        if model_type == 'gguf':
            return _validate_gguf_model(data)

        # Anything else: respond success (local/online already verified via /fetch-models)
        return jsonify({"success": True, "message": "Configuration accepted."})

    except Exception as e:
        return jsonify({"success": False, "message": f"Validation error: {str(e)}"}), 500


def _validate_gguf_model(data):
    """Check that the GGUF file path exists and has the right extension."""
    model_path = (data.get('gguf_model_path') or '').strip()

    if not model_path:
        return jsonify({"success": False, "message": "GGUF model path is required"}), 400

    if not model_path.endswith('.gguf'):
        return jsonify({"success": False, "message": "File must have a .gguf extension"}), 400

    if not os.path.exists(model_path):
        return jsonify({
            "success": False,
            "message": f"GGUF model not found at: {model_path}",
            "details": {"path": model_path, "exists": False}
        }), 404

    return jsonify({
        "success": True,
        "message": f"GGUF model found: {os.path.basename(model_path)}",
        "details": {"path": model_path, "exists": True, "type": "gguf"}
    })


# ---------------------------------------------------------------------------
# /api/fetch-models  — connect to local or online provider, return model list
# ---------------------------------------------------------------------------

@api_bp.route('/fetch-models', methods=['POST'])
def fetch_models():
    """
    Connect to a local or online LLM provider and return available models.

    POST JSON payload:
    {
        "provider_type": "local" | "online",

        # For local:
        "base_url": str,          # e.g. "http://127.0.0.1:1234/v1"
        "api_key":  str | null,   # optional

        # For online:
        "provider": "openai" | "anthropic" | "groq" | "gemini",
        "api_key":  str
    }

    Returns:
    {
        "success": bool,
        "models": [{"id": str}, ...],
        "message": str   (on error)
    }
    """
    try:
        data = request.json or {}
        provider_type = data.get('provider_type', '')

        if provider_type == 'local':
            return _fetch_local_models(data)
        elif provider_type == 'online':
            return _fetch_online_models(data)
        else:
            return jsonify({"success": False, "message": f"Unknown provider_type: '{provider_type}'"}), 400

    except Exception as e:
        logger.exception("Unexpected error in /fetch-models")
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500


def _fetch_local_models(data):
    """Query an OpenAI-compatible /v1/models endpoint on a local server."""
    base_url = (data.get('base_url') or '').rstrip('/')
    api_key  = (data.get('api_key') or '').strip()

    if not base_url:
        return jsonify({"success": False, "message": "base_url is required"}), 400

    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    try:
        resp = requests.get(f"{base_url}/models", headers=headers, timeout=8)

        if resp.status_code == 200:
            models = resp.json().get('data', [])
            if not models:
                return jsonify({
                    "success": False,
                    "message": "Server is reachable but returned no models. Make sure a model is loaded."
                }), 200
            return jsonify({"success": True, "models": models, "count": len(models)})

        elif resp.status_code == 401:
            return jsonify({
                "success": False,
                "message": "Server requires authentication. Please provide an API key.",
                "details": {"hint": "Enter the server's API key in the 'API Key' field"}
            }), 401

        else:
            return jsonify({
                "success": False,
                "message": f"Server returned HTTP {resp.status_code}."
            }), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": f"Cannot connect to {base_url}. Is the server running?",
            "details": {"hint": "LM Studio: enable 'Serve on Local Network'. OLLAMA: run 'ollama serve'."}
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Connection timed out."}), 504
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


def _fetch_online_models(data):
    """Verify an API key and fetch available models from an online provider."""
    provider = (data.get('provider') or '').lower()
    api_key  = (data.get('api_key') or '').strip()

    if not provider:
        return jsonify({"success": False, "message": "provider is required"}), 400
    if not api_key:
        return jsonify({"success": False, "message": "api_key is required"}), 400
    if provider not in _ONLINE_BASE_URLS:
        return jsonify({"success": False, "message": f"Unknown provider: '{provider}'"}), 400

    base_url = _ONLINE_BASE_URLS[provider]

    # Build auth headers (Anthropic uses a different header)
    if provider == 'anthropic':
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
    else:
        headers = {'Authorization': f'Bearer {api_key}'}

    try:
        if provider == 'anthropic':
            # Anthropic doesn't have a /models list endpoint; use a minimal
            # messages call with max_tokens=1 to verify the key, then return
            # a curated static model list.
            verify_resp = requests.post(
                f"{base_url}/messages",
                headers={**headers, 'content-type': 'application/json'},
                json={"model": "claude-3-haiku-20240307", "max_tokens": 1,
                      "messages": [{"role": "user", "content": "hi"}]},
                timeout=10
            )
            if verify_resp.status_code in (200, 400):
                # 400 = bad request but key is valid (model may not exist);
                # treat both as "key accepted"
                models = [
                    {"id": "claude-3-5-sonnet-20241022"},
                    {"id": "claude-3-5-haiku-20241022"},
                    {"id": "claude-3-opus-20240229"},
                    {"id": "claude-3-haiku-20240307"},
                ]
                return jsonify({"success": True, "models": models, "count": len(models)})
            elif verify_resp.status_code == 401:
                return jsonify({"success": False, "message": "Invalid Anthropic API key."}), 401
            else:
                return jsonify({
                    "success": False,
                    "message": f"Anthropic API returned HTTP {verify_resp.status_code}."
                }), verify_resp.status_code

        elif provider == 'gemini':
            # Google's OpenAI-compatible endpoint supports /models
            resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                raw = resp.json().get('data', [])
                # Filter to text-generation models only
                models = [m for m in raw if 'gemini' in m.get('id', '').lower()]
                if not models:
                    models = raw  # fall back to full list if filter yields nothing
                return jsonify({"success": True, "models": models, "count": len(models)})
            elif resp.status_code == 401:
                return jsonify({"success": False, "message": "Invalid Google Gemini API key."}), 401
            else:
                return jsonify({
                    "success": False,
                    "message": f"Gemini API returned HTTP {resp.status_code}."
                }), resp.status_code

        else:
            # OpenAI / Groq — standard /v1/models endpoint
            resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                models = resp.json().get('data', [])
                return jsonify({"success": True, "models": models, "count": len(models)})
            elif resp.status_code == 401:
                return jsonify({"success": False, "message": f"Invalid {provider.title()} API key."}), 401
            else:
                return jsonify({
                    "success": False,
                    "message": f"{provider.title()} API returned HTTP {resp.status_code}."
                }), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": f"Cannot connect to {provider.title()} API. Check your internet connection."
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": f"{provider.title()} API timed out."}), 504
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# /api/generate
# ---------------------------------------------------------------------------

@api_bp.route('/generate', methods=['POST'])
def generate_workout():
    """
    Generate workout plan by calling FastAPI backend.

    POST JSON payload:
    {
        "model_config": {
            "model_type": str,
            ...provider-specific fields...
        },
        "height": float, "weight": float, "age": int,
        "gender": str, "fitness_level": str,
        "days_per_week": int, "session_duration": int,
        "goals": list[str], "equipment": list[str] or str,
        "injuries": str (optional), "preferred_split": str
    }
    """
    try:
        data = request.json

        # Validate input data
        is_valid, error_message = validate_user_profile(data)
        if not is_valid:
            return jsonify({"success": False, "message": f"Validation error: {error_message}"}), 400

        user_profile = {
            "height":                float(data['height']),
            "weight":                float(data['weight']),
            "age":                   int(data['age']),
            "gender":                data['gender'],
            "fitness_level":         data['fitness_level'],
            "gym_days_per_week":     int(data['days_per_week']),
            "workout_duration_minutes": int(data['session_duration']),
            "goals":                 _parse_list_field(data.get('goals', [])),
            "available_equipment":   _parse_list_field(data.get('equipment', [])),
            "injuries_limitations":  _parse_optional_list_field(data.get('injuries')),
            "preferred_split":       data.get('preferred_split', 'full_body')
        }

        request_payload = {"user_profile": user_profile}

        model_config = data.get('model_config')
        if model_config:
            cleaned = {k: v for k, v in model_config.items() if v is not None and v != ''}
            if cleaned:
                request_payload["llm_config"] = cleaned
                logger.info(f"Using model configuration: {cleaned.get('model_type', 'unknown')}")
        else:
            logger.info("No model configuration provided, using .env defaults")

        response = requests.post(
            f"{FASTAPI_URL}/api/v1/generate",
            json=request_payload,
            timeout=600
        )

        if response.status_code == 200:
            return jsonify({"success": True, "workout_plan": response.json()})
        else:
            return jsonify({"success": False, "message": f"Backend error: {response.text}"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Request timed out after 10 minutes. Try a smaller or faster model."
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to the backend server. Is the FastAPI server running?"
        }), 503
    except KeyError as e:
        return jsonify({"success": False, "message": f"Missing required field: {e}"}), 400
    except ValueError as e:
        return jsonify({"success": False, "message": f"Invalid value: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {e}"}), 500


# ---------------------------------------------------------------------------
# /api/config  — exposes runtime LLM host for Docker vs local
# ---------------------------------------------------------------------------

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Return the runtime LLM host so the frontend can build provider URLs."""
    try:
        response = requests.get(f"{FASTAPI_URL}/api/v1/config", timeout=5)
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({"llm_host": "127.0.0.1"})


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Check health of both frontend and backend services."""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        return jsonify({"frontend": "healthy", "backend": response.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({
            "frontend": "healthy",
            "backend": {"status": "unhealthy", "error": str(e)}
        }), 503


# ---------------------------------------------------------------------------
# /api/models  — legacy endpoint (kept for compatibility)
# ---------------------------------------------------------------------------

@api_bp.route('/models', methods=['GET', 'POST'])
def list_models():
    """
    List available models from the LLM provider.

    GET: proxies to FastAPI backend default config.
    POST: { "base_url": str, "api_key": str (optional) }
    """
    try:
        if request.method == 'POST':
            data = request.json or {}
            base_url = data.get('base_url')
            api_key  = data.get('api_key')

            if not base_url:
                return jsonify({"success": False, "message": "base_url is required"}), 400

            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            try:
                resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
                if resp.status_code == 200:
                    models = resp.json().get('data', [])
                    return jsonify({"success": True, "provider": "local", "models": models})
                elif resp.status_code == 401:
                    return jsonify({"success": False, "message": "Authentication failed."}), 401
                else:
                    return jsonify({"success": False, "message": f"Server returned {resp.status_code}"}), resp.status_code
            except requests.exceptions.ConnectionError:
                return jsonify({"success": False, "message": "Cannot connect to server."}), 503
            except requests.exceptions.Timeout:
                return jsonify({"success": False, "message": "Connection timeout."}), 504
        else:
            response = requests.get(f"{FASTAPI_URL}/api/v1/models", timeout=10)
            if response.status_code == 200:
                return jsonify({"success": True, **response.json()})
            else:
                return jsonify({"success": False, "message": f"Backend error: {response.text}"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Request timeout."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Cannot connect to backend server."}), 503
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_list_field(value):
    if isinstance(value, list):
        return [item.strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return []


def _parse_optional_list_field(value):
    if not value:
        return None
    parsed = _parse_list_field(value)
    return parsed if parsed else None

# Made with Bob
