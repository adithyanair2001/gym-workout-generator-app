"""LLM service for workout plan generation using LM Studio (OpenAI-compatible API)."""
import os
import logging
from typing import Dict, List, Optional

from openai import OpenAI

from app.models.user_profile import UserProfile
from app.utils.json_parser import parse_llm_json_response

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LM Studio LLM via OpenAI-compatible API."""
    
    def __init__(self, base_url: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        """Initialize the LLM service.
        
        Args:
            base_url: LM Studio server base URL (e.g., 'http://127.0.0.1:1234/v1')
            model: Model name (use 'local-model' or the actual model name from LM Studio)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Use environment variable for API key, fallback to default for local LM Studio
        api_key = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        logger.info(f"LLM service initialized with LM Studio at {base_url}, model: {model}")
    
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
        prompt: str
    ) -> Dict:
        """Generate workout plan using LLM.
        
        Args:
            prompt: Formatted prompt for the LLM
            
        Returns:
            Generated workout plan as dictionary
            
        Raises:
            Exception: If generation fails
        """
        try:
            logger.info(f"Generating workout plan with {self.model}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert personal trainer AI assistant. You MUST respond with ONLY valid JSON, no additional text, explanations, or markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            generated_text = response.choices[0].message.content
            
            if generated_text:
                logger.info(f"Generated response length: {len(generated_text)} characters")
                logger.info(f"Full generated response:\n{generated_text}")
                
                # Parse JSON from response
                workout_plan = self.parse_json_response(generated_text)
                
                return workout_plan
            else:
                logger.error("Model returned empty/null response")
                raise ValueError("Empty response from model")
            
        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            raise
    
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
        """Test connection to LM Studio server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            models = self.client.models.list()
            logger.info(f"Successfully connected to LM Studio. Available models: {len(models.data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to LM Studio: {e}")
            return False

# Made with Bob
