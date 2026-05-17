#!/usr/bin/env python3
"""
Test COMPLETE RAG pipeline with LM Studio.

This demonstrates how:
1. Vector DB (ChromaDB) finds relevant exercises
2. LM Studio model generates workout plan using those exercises
"""

import json
import logging
from openai import OpenAI

from app.models.user_profile import UserProfile, FitnessLevel, Goal, WorkoutSplit
from app.services.vector_store import VectorStoreService
from app.services.exercisedb_client import ExerciseDBClient
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_vector_db():
    """Test vector database is working."""
    print("\n" + "="*60)
    print("STEP 1: Testing Vector Database (ChromaDB)")
    print("="*60)
    
    try:
        # Initialize vector store
        print("\n1. Initializing ChromaDB...")
        vector_store = VectorStoreService(
            db_path="./data/chroma_db",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vector_store.initialize_collection()
        
        # Check if populated
        stats = vector_store.get_collection_stats()
        print(f"✅ Vector DB Status: {stats['status']}")
        print(f"✅ Total Exercises: {stats['count']}")
        
        if stats['count'] == 0:
            print("\n⚠️  Vector DB is empty! Populating with exercises...")
            print("This will take 2-3 minutes on first run...")
            
            # Fetch exercises from ExerciseDB
            settings = get_settings()
            client = ExerciseDBClient(settings.exercisedb_api_url)
            
            # Fetch and add exercises (handle async properly)
            import asyncio
            async def populate_db():
                exercises = await client.fetch_all_exercises()
                await vector_store.add_exercises(exercises)
            
            asyncio.run(populate_db())
            
            stats = vector_store.get_collection_stats()
            print(f"✅ Populated! Total Exercises: {stats['count']}")
        
        # Test search
        print("\n2. Testing semantic search...")
        query = "beginner chest exercises with barbell"
        results = vector_store.search_exercises(query, n_results=10)
        
        print(f"✅ Found {len(results)} exercises for: '{query}'")
        print("\nTop 3 Results:")
        for i, ex in enumerate(results[:3], 1):
            meta = ex.get('metadata', {})
            print(f"  {i}. {meta.get('name', 'Unknown')}")
            print(f"     Target: {meta.get('target_muscles', 'N/A')}")
            print(f"     Equipment: {meta.get('equipment', 'N/A')}")
        
        return vector_store, results
        
    except Exception as e:
        print(f"❌ Vector DB test failed: {e}")
        return None, None


def test_lm_studio_connection():
    """Test LM Studio server connection."""
    print("\n" + "="*60)
    print("STEP 2: Testing LM Studio Connection")
    print("="*60)
    
    try:
        client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )
        
        print("\n1. Checking LM Studio server...")
        models = client.models.list()
        
        if models.data:
            model_name = models.data[0].id
            print(f"✅ Connected! Using model: {model_name}")
            return client, model_name
        else:
            print("❌ No models loaded in LM Studio")
            return None, None
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure LM Studio is running with server started!")
        return None, None


def test_full_rag_pipeline(vector_store, client, model_name):
    """Test complete RAG pipeline: Vector DB → LM Studio."""
    print("\n" + "="*60)
    print("STEP 3: Testing COMPLETE RAG Pipeline")
    print("="*60)
    
    try:
        # 1. Create user profile
        print("\n1. Creating user profile...")
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
        print(f"✅ User: {user_profile.fitness_level.value}, {user_profile.gym_days_per_week} days/week")
        
        # 2. Search vector DB for relevant exercises
        print("\n2. Searching vector DB for relevant exercises...")
        query = f"""beginner level exercises for muscle gain.
Target muscle groups: chest, back, shoulders, legs, arms.
Available equipment: barbell, dumbbell.
Suitable for 3 days per week training."""
        
        exercises = vector_store.search_exercises(query, n_results=30)
        print(f"✅ Found {len(exercises)} relevant exercises from vector DB")
        
        # Format exercises for LLM
        exercises_text = ""
        for i, ex in enumerate(exercises[:20], 1):  # Limit to 20 for prompt
            meta = ex.get('metadata', {})
            exercises_text += f"{i}. {meta.get('name', 'Unknown')} (ID: {meta.get('exercise_id', '')})\n"
            exercises_text += f"   Target: {meta.get('target_muscles', '')}\n"
            exercises_text += f"   Equipment: {meta.get('equipment', '')}\n\n"
        
        # 3. Send to LM Studio for workout plan generation
        print("\n3. Sending to LM Studio to generate workout plan...")
        print("   (This may take 10-30 seconds...)")
        
        prompt = f"""You are an expert personal trainer. Generate a 3-day full body workout plan.

CRITICAL RULES:
1. Use ONLY exercises from the list below
2. Respond with ONLY valid JSON, no markdown, no explanations
3. Each day should have 4-6 exercises
4. Include sets, reps, and rest times

USER PROFILE:
- Fitness Level: Beginner
- Goal: Muscle gain
- Days per week: 3
- Session duration: 45 minutes
- Equipment: Barbell, Dumbbell

AVAILABLE EXERCISES (USE ONLY THESE):
{exercises_text}

OUTPUT JSON SCHEMA:
{{
  "workout_days": [
    {{
      "day_number": 1,
      "day_name": "Day 1: Full Body",
      "focus": "Full Body",
      "main_workout": [
        {{
          "exercise_id": "0001",
          "name": "barbell bench press",
          "target_muscles": ["pectorals"],
          "sets": 3,
          "reps": "10-12",
          "rest_seconds": 90
        }}
      ],
      "estimated_duration_minutes": 45
    }}
  ],
  "progression_notes": "Increase weight by 5% when you can complete all sets"
}}

Generate the workout plan as valid JSON only:"""

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert personal trainer. You MUST respond with ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        
        # 4. Parse and display result
        print("\n4. Parsing workout plan...")
        
        # Extract JSON
        if "```json" in result:
            start = result.find("```json") + 7
            end = result.find("```", start)
            json_str = result[start:end].strip()
        elif "```" in result:
            start = result.find("```") + 3
            end = result.find("```", start)
            json_str = result[start:end].strip()
        else:
            start = result.find("{")
            end = result.rfind("}") + 1
            json_str = result[start:end]
        
        plan = json.loads(json_str)
        
        print("\n" + "="*60)
        print("✅ WORKOUT PLAN GENERATED!")
        print("="*60)
        
        for day in plan.get('workout_days', []):
            print(f"\n{day.get('day_name', 'Day ' + str(day.get('day_number')))}")
            print(f"Focus: {day.get('focus', 'N/A')}")
            print(f"Duration: {day.get('estimated_duration_minutes', 45)} minutes")
            
            exercises = day.get('main_workout', [])
            print(f"\nExercises ({len(exercises)}):")
            for ex in exercises:
                print(f"  • {ex.get('name')}")
                print(f"    {ex.get('sets')} sets × {ex.get('reps')} reps, {ex.get('rest_seconds')}s rest")
        
        if 'progression_notes' in plan:
            print(f"\nProgression: {plan['progression_notes']}")
        
        # Save to file
        with open("full_rag_output.json", "w") as f:
            json.dump(plan, f, indent=2)
        print("\n✅ Saved to full_rag_output.json")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG pipeline failed: {e}")
        logger.error("Full error:", exc_info=True)
        return False


def main():
    """Run complete RAG test."""
    print("\n" + "="*60)
    print("COMPLETE RAG PIPELINE TEST")
    print("Vector DB (ChromaDB) + LM Studio")
    print("="*60)
    
    print("\nThis test demonstrates:")
    print("1. Vector DB finds relevant exercises (embedding model)")
    print("2. LM Studio generates workout plan (LLM model)")
    print("3. Both models work together for RAG")
    
    # Step 1: Test Vector DB
    vector_store, sample_results = test_vector_db()
    if not vector_store:
        print("\n❌ Cannot proceed without vector DB")
        return
    
    # Step 2: Test LM Studio
    client, model_name = test_lm_studio_connection()
    if not client:
        print("\n❌ Cannot proceed without LM Studio")
        return
    
    # Step 3: Test Full Pipeline
    success = test_full_rag_pipeline(vector_store, client, model_name)
    
    print("\n" + "="*60)
    if success:
        print("✅ COMPLETE RAG PIPELINE WORKING!")
    else:
        print("❌ RAG PIPELINE FAILED")
    print("="*60)
    
    print("\nHow it works:")
    print("┌─────────────────────────────────────────┐")
    print("│  1. User Profile                        │")
    print("│     ↓                                   │")
    print("│  2. Vector DB (ChromaDB)                │")
    print("│     - Embedding model finds exercises   │")
    print("│     - Returns top 30 relevant exercises │")
    print("│     ↓                                   │")
    print("│  3. LM Studio (Qwen/Llama/etc)         │")
    print("│     - Receives exercises from vector DB │")
    print("│     - Generates structured workout plan │")
    print("│     ↓                                   │")
    print("│  4. Final Workout Plan (JSON)           │")
    print("└─────────────────────────────────────────┘")
    
    print("\nKey Points:")
    print("• LM Studio CANNOT directly access vector DB")
    print("• Vector DB searches first, then passes results to LM Studio")
    print("• This is the RAG (Retrieval-Augmented Generation) pattern")
    print("• Your FastAPI app orchestrates this flow automatically")


if __name__ == "__main__":
    main()

# Made with Bob