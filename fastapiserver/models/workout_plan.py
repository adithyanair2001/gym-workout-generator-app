"""Workout plan data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Exercise(BaseModel):
    """Individual exercise in a workout."""
    
    exercise_id: str = Field(..., description="Exercise ID from database")
    name: str = Field(..., description="Exercise name")
    target_muscles: List[str] = Field(..., description="Primary target muscles")
    sets: int = Field(..., ge=1, le=10, description="Number of sets")
    reps: str = Field(..., description="Reps (e.g., '8-12', '10', 'AMRAP')")
    rest_seconds: int = Field(..., ge=30, le=300, description="Rest time between sets")
    gif_url: str = Field(..., description="URL to exercise demonstration GIF")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    notes: Optional[str] = Field(None, description="Additional notes or tips")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exercise_id": "0001",
                "name": "Barbell Bench Press",
                "target_muscles": ["pectorals"],
                "sets": 4,
                "reps": "8-12",
                "rest_seconds": 90,
                "gif_url": "https://static.exercisedb.dev/media/example.gif",
                "instructions": [
                    "Lie flat on bench with feet on ground",
                    "Grip barbell slightly wider than shoulder width",
                    "Lower bar to chest with control",
                    "Press bar back up to starting position"
                ],
                "notes": "Keep shoulder blades retracted throughout movement"
            }
        }


class WorkoutDay(BaseModel):
    """Single day's workout plan."""
    
    day_number: int = Field(..., ge=1, le=7, description="Day number in the week")
    day_name: str = Field(..., description="Day name (e.g., 'Day 1: Push')")
    focus: str = Field(..., description="Focus of the day (e.g., 'Upper Body Push')")
    warm_up: List[Exercise] = Field(default=[], description="Warm-up exercises")
    main_workout: List[Exercise] = Field(..., description="Main workout exercises")
    cool_down: List[Exercise] = Field(default=[], description="Cool-down exercises")
    estimated_duration_minutes: int = Field(..., description="Estimated workout duration")
    total_exercises: int = Field(..., description="Total number of exercises")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "day_name": "Day 1: Upper Body Push",
                "focus": "Chest, Shoulders, Triceps",
                "warm_up": [],
                "main_workout": [],
                "cool_down": [],
                "estimated_duration_minutes": 60,
                "total_exercises": 6
            }
        }


class WorkoutPlan(BaseModel):
    """Complete workout plan for the user."""
    
    user_profile_summary: dict = Field(..., description="Summary of user profile")
    plan_duration_weeks: int = Field(default=4, ge=1, le=52, description="Plan duration in weeks")
    days_per_week: int = Field(..., ge=1, le=7, description="Training days per week")
    workout_days: List[WorkoutDay] = Field(..., description="Workout days")
    progression_notes: str = Field(..., description="Notes on progression and advancement")
    nutrition_tips: Optional[str] = Field(None, description="Optional nutrition recommendations")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp when plan was generated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_profile_summary": {
                    "age": 28,
                    "fitness_level": "intermediate",
                    "goals": ["muscle_gain", "strength"]
                },
                "plan_duration_weeks": 4,
                "days_per_week": 4,
                "workout_days": [],
                "progression_notes": "Increase weight by 2.5-5% when you can complete all sets with good form",
                "nutrition_tips": "Aim for 1.6-2.2g protein per kg bodyweight for muscle gain",
                "generated_at": "2026-05-10T14:00:00.000000"
            }
        }

# Made with Bob
