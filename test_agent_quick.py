#!/usr/bin/env python3
"""Quick test of MLX agent to verify it produces output."""

import json
import logging

from app.models.user_profile import (FitnessLevel, Goal, UserProfile,
                                     WorkoutSplit)
from app.services.database_tools import DatabaseTools
from app.services.mlx_agent_service import MLXAgentService
from app.services.vector_store import VectorStoreService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        print("\n" + "="*60)
        print("Quick MLX Agent Test")
        print("="*60)
        
        # 1. Initialize vector store
        print("\n1. Initializing vector store...")
        vector_store = VectorStoreService(
            db_path="./data/chroma_db",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vector_store.initialize_collection()  # Initialize the collection
        
        # 2. Initialize database tools
        print("\n2. Initializing database tools...")
        db_tools = DatabaseTools(vector_store)
        
        # 3. Initialize MLX agent
        print("\n3. Initializing MLX agent...")
        model_path = "/Users/adithyanair/.lmstudio/models/mlx-community/Llama-3.2-3B-Instruct-4bit"
        print(f"Loading model: {model_path}")
        agent = MLXAgentService(
            model_path=model_path,
            database_tools=db_tools,
            max_tokens=8000  # Increased from 3000 - enough for complete JSON without excessive wait
        )
        print("✅ Llama 3.2 3B model loaded successfully!")
        
        # 4. Create simple user profile
        print("\n4. Creating user profile...")
        user_profile = UserProfile(
            age=25,
            gender="male",
            height=175,
            weight=70,
            fitness_level=FitnessLevel.BEGINNER,
            goals=[Goal.MUSCLE_GAIN],
            gym_days_per_week=3,
            workout_duration_minutes=45,
            available_equipment=["barbell", "dumbbell"],
            injuries_limitations=[],
            preferred_split=WorkoutSplit.FULL_BODY
        )
        
        print(f"User: {user_profile.fitness_level.value}, {user_profile.gym_days_per_week} days/week")
        
        # 5. Generate workout plan
        print("\n5. Generating workout plan (this may take 2-3 minutes)...")
        print("Agent will query database and create plan...\n")
        
        workout_plan = agent.generate_workout_plan(user_profile)
        
        # 6. Display results
        print("\n" + "="*60)
        print("WORKOUT PLAN GENERATED!")
        print("="*60)
        
        # Print raw output
        print("\n" + workout_plan)
        
        # Save to file
        with open("agent_output.log", "w") as f:
            f.write(workout_plan)
        print("\n✅ Output saved to agent_output.log")
        
        # Try to parse as JSON for structured display
        try:
            # Extract JSON from response
            start = workout_plan.find("{")
            end = workout_plan.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = workout_plan[start:end]
                plan_dict = json.loads(json_str)
                
                if "workout_days" in plan_dict:
                    print(f"\n📊 Total Days: {len(plan_dict['workout_days'])}")
                    
                    for day in plan_dict['workout_days']:
                        print(f"\n--- {day.get('day_name', 'Day ' + str(day.get('day_number')))} ---")
                        exercises = day.get('main_workout', day.get('exercises', []))
                        print(f"Exercises: {len(exercises)}")
                        
                        for i, ex in enumerate(exercises[:3], 1):  # Show first 3
                            print(f"  {i}. {ex.get('name', 'Unknown')}")
                            print(f"     Sets: {ex.get('sets')}, Reps: {ex.get('reps')}")
                        
                        if len(exercises) > 3:
                            print(f"  ... and {len(exercises) - 3} more exercises")
        except json.JSONDecodeError:
            print("\n⚠️  Could not parse as JSON, but output was generated")
        
        print("\n" + "="*60)
        print("Test Complete!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()

# Made with Bob
