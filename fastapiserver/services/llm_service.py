"""LLM service for workout plan generation using OpenAI-compatible APIs (LM Studio, OMLX, OLLAMA, OpenAI, etc.)."""
import os
import logging
import time
from typing import Dict, List, Optional

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError

from fastapiserver.models.user_profile import UserProfile
from fastapiserver.utils.json_parser import parse_llm_json_response

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLMs via OpenAI-compatible API.
    
    Supports:
    - Local servers (LM Studio, OMLX, OLLAMA)
    - Public APIs (OpenAI, Anthropic, Groq, etc.)
    """
    
    def __init__(self, base_url: str, model: str, api_key: str = "", temperature: float = 0.7, max_tokens: int = 2000):
        """Initialize the LLM service.
        
        Args:
            base_url: Server base URL
                - LM Studio: 'http://127.0.0.1:1234/v1'
                - OMLX: 'http://127.0.0.1:8000/v1'
                - OLLAMA: 'http://127.0.0.1:11434/v1'
                - OpenAI: 'https://api.openai.com/v1'
                - Anthropic: 'https://api.anthropic.com/v1'
                - Groq: 'https://api.groq.com/openai/v1'
            model: Model name
                - Local: 'local-model'
                - OpenAI: 'gpt-4o-mini', 'gpt-4o', etc.
                - Anthropic: 'claude-3-5-sonnet-20241022', etc.
                - Groq: 'llama-3.3-70b-versatile', etc.
            api_key: API key for public services (optional for local servers)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Determine if this is a local or public API
        is_local = base_url.startswith('http://127.0.0.1') or base_url.startswith('http://localhost')
        
        # Determine if this is OMLX (port 8000)
        is_omlx = ':8000' in base_url
        
        # Use provided API key, or fallback to environment variable, or default for local
        if api_key:
            # Use explicitly provided API key (highest priority)
            final_api_key = api_key
            logger.info("Using provided API key for authentication")
        elif not is_local:
            # For public APIs, try to get from environment
            final_api_key = os.getenv('LLM_API_KEY', '')
            if not final_api_key:
                logger.warning("No API key provided for public LLM service. This may cause authentication errors.")
        else:
            # For local servers
            if is_omlx:
                # OMLX: Don't send API key unless explicitly provided in environment
                # OMLX's verify_api_key() returns True when _server_state.api_key is None
                # Sending any key (like 'lm-studio') will cause rejection if OMLX has no key configured
                final_api_key = os.getenv('LLM_API_KEY') or os.getenv('OMLX_API_KEY')
                if final_api_key:
                    logger.info("Using API key from environment for OMLX authentication")
                else:
                    # Use None to skip Authorization header entirely
                    final_api_key = None
                    logger.info("No API key configured for OMLX - skipping authentication header")
            else:
                # LM Studio and other local servers: check environment first, then use default
                final_api_key = os.getenv('LLM_API_KEY') or os.getenv('LM_STUDIO_API_KEY', 'lm-studio')
                if final_api_key and final_api_key != 'lm-studio':
                    logger.info("Using API key from environment for local server authentication")
        
        self.client = OpenAI(base_url=base_url, api_key=final_api_key)
        
        # Log initialization
        service_type = "local server" if is_local else "public API"
        logger.info(f"LLM service initialized with {service_type} at {base_url}, model: {model}")
        if not is_local and api_key:
            logger.info("Using provided API key for authentication")
    
    def construct_prompt(
        self,
        user_profile: UserProfile,
        exercises: List[Dict],
        split_strategy: str
    ) -> str:
        """Construct the prompt for workout plan generation.
        
        Args:
            user_profile: User profile information
            exercises: List of retrieved exercises
            split_strategy: Workout split strategy description
            
        Returns:
            Formatted prompt string
        """
        # Format exercises for prompt
        exercises_text = ""
        for i, ex in enumerate(exercises[:30], 1):  # Limit to 30 exercises
            meta = ex.get('metadata', {})
            exercises_text += f"{i}. {meta.get('name', 'Unknown')} (ID: {meta.get('exercise_id', '')})\n"
            exercises_text += f"   Target: {meta.get('target_muscles', '')}\n"
            exercises_text += f"   Equipment: {meta.get('equipment', '')}\n\n"
        
        # Determine sets/reps based on fitness level
        if user_profile.fitness_level.value == "beginner":
            sets_reps_guide = "Beginner: 2-3 sets, 12-15 reps, 60-90s rest"
        elif user_profile.fitness_level.value == "intermediate":
            sets_reps_guide = "Intermediate: 3-4 sets, 8-12 reps, 60s rest"
        else:
            sets_reps_guide = "Advanced: 4-5 sets, 6-10 reps, 45-60s rest"
        
        prompt = f"""You are an expert personal trainer AI assistant. Generate a personalized workout plan based on the user profile and available exercises.

CRITICAL RULES - READ CAREFULLY:
1. Use ONLY exercises from the provided list below - DO NOT suggest any exercises not in the list
2. Your response MUST contain ONLY the JSON workout plan - NO explanations, NO markdown, NO additional text
3. Do NOT wrap the JSON in code blocks or markdown formatting
4. Output raw JSON only, starting with {{ and ending with }}
5. Do NOT invent or suggest exercises not in the provided list
6. Consider user's fitness level when assigning sets/reps
7. Balance muscle groups across the week
8. Include warm-up (5-10 min) and cool-down (5 min) exercises
9. Ensure total workout duration matches user's available time

USER PROFILE:
- Age: {user_profile.age}, Gender: {user_profile.gender}
- Height: {user_profile.height}cm, Weight: {user_profile.weight}kg
- Fitness Level: {user_profile.fitness_level.value}
- Goals: {', '.join([g.value for g in user_profile.goals])}
- Days per week: {user_profile.gym_days_per_week}
- Session duration: {user_profile.workout_duration_minutes} minutes
- Available equipment: {', '.join(user_profile.available_equipment)}
- Injuries/Limitations: {', '.join(user_profile.injuries_limitations or ['None'])}
- Preferred split: {user_profile.preferred_split.value}

WORKOUT SPLIT STRATEGY:
{split_strategy}

SETS & REPS GUIDELINES:
{sets_reps_guide}

For strength goals: Lower reps (4-6), higher weight
For hypertrophy: Medium reps (8-12), moderate weight
For endurance: Higher reps (15+), lower weight

AVAILABLE EXERCISES (USE ONLY THESE):
{exercises_text}

OUTPUT JSON SCHEMA:
{{
  "workout_days": [
    {{
      "day_number": 1,
      "day_name": "Day 1: Upper Body Push",
      "focus": "Chest, Shoulders, Triceps",
      "warm_up": [],
      "main_workout": [
        {{
          "exercise_id": "0001",
          "name": "barbell bench press",
          "target_muscles": ["pectorals"],
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "notes": "Keep shoulder blades retracted"
        }}
      ],
      "cool_down": [],
      "estimated_duration_minutes": 60
    }}
  ],
  "progression_notes": "Increase weight by 2.5-5% when you can complete all sets with good form",
  "nutrition_tips": "Aim for 1.6-2.2g protein per kg bodyweight"
}}

Generate the complete workout plan as valid JSON. Remember: ONLY use exercises from the provided list above."""
        
        return prompt
    
    async def generate_workout_plan(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> Dict:
        """Generate workout plan using LLM with retry logic.
        
        Args:
            prompt: Formatted prompt for the LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated workout plan as dictionary
            
        Raises:
            Exception: If generation fails after all retries
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s wait...")
                    time.sleep(wait_time)
                
                logger.info(f"Generating workout plan with {self.model}... (attempt {attempt + 1}/{max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert personal trainer AI assistant. You MUST respond with ONLY valid JSON, no additional text, explanations, or markdown formatting. DO NOT include reasoning or thinking process - output the JSON directly."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                message = response.choices[0].message
                generated_text = message.content
                
                # Check if model used reasoning tokens (Qwen models)
                if hasattr(message, 'reasoning_content') and message.reasoning_content:
                    logger.warning(f"Model used {len(message.reasoning_content)} chars for reasoning - this wastes tokens!")
                    logger.info(f"Reasoning content: {message.reasoning_content[:500]}...")
                
                if generated_text:
                    logger.info(f"Generated response length: {len(generated_text)} characters")
                    logger.info(f"Full generated response:\n{generated_text}")
                    
                    # Parse JSON from response
                    workout_plan = self.parse_json_response(generated_text)
                    
                    return workout_plan
                else:
                    logger.error("Model returned empty/null response (content field is empty)")
                    logger.error("This usually means the model spent all tokens on reasoning and didn't generate output")
                    raise ValueError("Empty response from model - try increasing max_tokens or check server configuration")
                    
            except (APIConnectionError, APITimeoutError, RateLimitError) as e:
                # Retryable errors
                last_exception = e
                logger.warning(f"Retryable error on attempt {attempt + 1}/{max_retries}: {type(e).__name__} - {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} retry attempts failed")
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}") from e
                continue
                
            except APIError as e:
                # Non-retryable API errors (e.g., invalid request)
                logger.error(f"Non-retryable API error: {e}")
                raise
                
            except Exception as e:
                # Other errors
                logger.error(f"Error generating workout plan: {e}")
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise Exception(f"Failed after {max_retries} attempts") from last_exception
        raise Exception("Unexpected error in retry logic")
    
    def parse_json_response(self, response: str) -> Dict:
        """Extract and parse JSON from LLM response using shared utility.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON parsing fails
        """
        return parse_llm_json_response(response, save_on_error=True)
    
    def test_connection(self) -> bool:
        """Test connection to LLM server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            models = self.client.models.list()
            logger.info(f"Successfully connected to LLM server. Available models: {len(models.data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to LLM server: {e}")
            return False
    
    def list_models(self) -> List[Dict]:
        """List available models from the LLM provider.
        
        Returns:
            List of model dictionaries with id, name, and metadata
            
        Raises:
            Exception: If listing models fails
        """
        try:
            response = self.client.models.list()
            models = []
            for model in response.data:
                models.append({
                    "id": model.id,
                    "object": model.object,
                    "created": getattr(model, 'created', None),
                    "owned_by": getattr(model, 'owned_by', 'unknown')
                })
            logger.info(f"Listed {len(models)} models from LLM provider")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise

# Made with Bob
