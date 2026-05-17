"""User profile data models for workout generation."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class FitnessLevel(str, Enum):
    """User fitness level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Goal(str, Enum):
    """Workout goals."""
    MUSCLE_GAIN = "muscle_gain"
    WEIGHT_LOSS = "weight_loss"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_FITNESS = "general_fitness"


class WorkoutSplit(str, Enum):
    """Workout split types."""
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    AUTO = "auto"


class UserProfile(BaseModel):
    """User profile for workout plan generation."""
    
    height: float = Field(..., ge=100, le=250, description="Height in cm")
    weight: float = Field(..., ge=30, le=300, description="Weight in kg")
    age: int = Field(..., ge=13, le=100, description="Age in years")
    gender: str = Field(..., pattern="^(male|female|other)$", description="Gender")
    fitness_level: FitnessLevel = Field(..., description="Current fitness level")
    gym_days_per_week: int = Field(..., ge=1, le=7, description="Days per week for gym")
    workout_duration_minutes: int = Field(..., ge=30, le=120, description="Workout duration in minutes")
    goals: List[Goal] = Field(..., description="Fitness goals")
    available_equipment: List[str] = Field(
        default=["barbell", "dumbbell", "bodyweight"],
        description="Available equipment at gym"
    )
    injuries_limitations: Optional[List[str]] = Field(
        default=None,
        description="Body parts with injuries or limitations"
    )
    preferred_split: WorkoutSplit = Field(
        default=WorkoutSplit.AUTO,
        description="Preferred workout split"
    )
    
    @validator('goals')
    def validate_goals(cls, v):
        """Ensure at least one goal is specified."""
        if not v:
            raise ValueError("At least one goal must be specified")
        return v
    
    @validator('available_equipment')
    def validate_equipment(cls, v):
        """Ensure at least one equipment type is available."""
        if not v:
            raise ValueError("At least one equipment type must be specified")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
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
            }
        }

# Made with Bob
