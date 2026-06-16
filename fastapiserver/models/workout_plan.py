"""Workout plan data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Exercise(BaseModel):
    """Individual exercise in a workout - Custom format."""
    
    exerciseDbId: str = Field(..., description="Exercise ID from ExerciseDB")
    exerciseName: str = Field(..., description="Exercise name")
    bodyPart: str = Field(..., description="Primary body part (e.g., 'Chest', 'Back', 'Legs')")
    equipments: str = Field(..., description="Required equipment (e.g., 'Barbell', 'Dumbbell')")
    targetMuscles: str = Field(..., description="Primary target muscles")
    secondaryMuscles: str = Field(default="", description="Secondary muscles (comma-separated)")
    mediaUrl: str = Field(..., description="URL to exercise demonstration GIF")
    description: str = Field(..., description="Exercise instructions (steps separated by $$)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exerciseDbId": "EIeI8Vf",
                "exerciseName": "barbell bench press",
                "bodyPart": "Chest",
                "equipments": "Barbell",
                "targetMuscles": "pectorals",
                "secondaryMuscles": "shoulders,Triceps",
                "mediaUrl": "https://static.exercisedb.dev/media/EIeI8Vf.gif",
                "description": "Lie flat on a bench with your feet flat on the ground. $$ Grip the barbell slightly wider than shoulder-width apart. $$ Lower bar to chest with control. $$ Press bar back up to starting position."
            }
        }


class WorkoutDay(BaseModel):
    """Single day's workout plan - Custom format."""
    
    groupName: str = Field(..., description="Name of the workout group/day")
    isAiGenerated: bool = Field(default=True, description="Whether this workout was AI-generated")
    selectedExercises: List[Exercise] = Field(..., description="List of exercises in this group")
    
    class Config:
        json_schema_extra = {
            "example": {
                "groupName": "Day 1: Upper Body Push",
                "isAiGenerated": True,
                "selectedExercises": []
            }
        }


class WorkoutPlan(BaseModel):
    """Complete workout plan for the user - Custom format."""
    
    workoutGroups: List[WorkoutDay] = Field(..., description="List of workout groups/days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workoutGroups": [
                    {
                        "groupName": "Day 1: Upper Body",
                        "isAiGenerated": True,
                        "selectedExercises": []
                    }
                ]
            }
        }

# Made with Bob
