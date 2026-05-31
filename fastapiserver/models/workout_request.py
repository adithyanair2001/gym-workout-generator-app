"""Request model for workout generation with optional model configuration."""
from pydantic import BaseModel, Field
from typing import Optional

from fastapiserver.models.user_profile import UserProfile
from fastapiserver.models.model_config import ModelConfig


class WorkoutGenerationRequest(BaseModel):
    """Request model for workout generation endpoint.
    
    Combines user profile with optional model configuration.
    If llm_config is not provided, uses .env defaults.
    """
    
    user_profile: UserProfile
    llm_config: Optional[ModelConfig] = Field(None, description="Optional LLM configuration. If not provided, uses .env defaults.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_profile": {
                    "height": 175,
                    "weight": 75,
                    "age": 28,
                    "gender": "male",
                    "fitness_level": "intermediate",
                    "gym_days_per_week": 4,
                    "workout_duration_minutes": 60,
                    "goals": ["muscle_gain", "strength"],
                    "available_equipment": ["barbell", "dumbbell", "cable"],
                    "injuries_limitations": [],
                    "preferred_split": "upper_lower"
                },
                "llm_config": {
                    "model_type": "omlx",
                    "llm_base_url": "http://127.0.0.1:8000/v1",
                    "llm_model": "mlx-community/Qwen3.5-4B-MLX-4bit",
                    "llm_api_key": "your-api-key",
                    "temperature": 0.7,
                    "max_tokens": 32000
                }
            }
        }


# Made with Bob