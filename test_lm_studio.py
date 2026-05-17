#!/usr/bin/env python3
"""Test LM Studio server connection and workout plan generation."""

import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test basic connection to LM Studio server."""
    print("\n" + "="*60)
    print("Testing LM Studio Connection")
    print("="*60)
    
    try:
        # Initialize OpenAI client pointing to LM Studio
        client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"  # LM Studio doesn't require real API key
        )
        
        # Test connection by listing models
        print("\n1. Checking available models...")
        models = client.models.list()
        
        if models.data:
            print(f"✅ Connected! Found {len(models.data)} model(s):")
            for model in models.data:
                print(f"   - {model.id}")
            return client, models.data[0].id
        else:
            print("❌ No models loaded in LM Studio")
            print("\nPlease:")
            print("1. Open LM Studio")
            print("2. Load a model (e.g., Qwen3.5-9B)")
            print("3. Click 'Start Server'")
            return None, None
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure:")
        print("1. LM Studio is running")
        print("2. Server is started (default: http://127.0.0.1:1234)")
        print("3. A model is loaded")
        return None, None


def test_simple_generation(client, model_name):
    """Test simple text generation."""
    print("\n" + "="*60)
    print("Testing Simple Generation")
    print("="*60)
    
    try:
        print("\n2. Sending test prompt...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! I am working correctly.' in one sentence."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"\n✅ Model Response:\n{result}")
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False


def test_workout_generation(client, model_name):
    """Test workout plan generation with structured JSON output."""
    print("\n" + "="*60)
    print("Testing Workout Plan Generation")
    print("="*60)
    
    prompt = """You are an expert personal trainer. Generate a simple 3-day workout plan for a beginner.

CRITICAL: Respond with ONLY valid JSON, no markdown, no explanations.

User Profile:
- Fitness Level: Beginner
- Days per week: 3
- Goal: Muscle gain
- Equipment: Barbell, Dumbbell

Output this exact JSON structure:
{
  "workout_days": [
    {
      "day_number": 1,
      "day_name": "Day 1: Full Body",
      "focus": "Full Body",
      "main_workout": [
        {
          "exercise_id": "0001",
          "name": "Barbell Squat",
          "target_muscles": ["quadriceps"],
          "sets": 3,
          "reps": "10-12",
          "rest_seconds": 90
        }
      ],
      "estimated_duration_minutes": 45
    }
  ],
  "progression_notes": "Increase weight by 5% when you can complete all sets"
}

Generate the workout plan as valid JSON only:"""

    try:
        print("\n3. Generating workout plan (may take 10-30 seconds)...")
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
        
        print("\n✅ Raw Response:")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # Try to parse JSON
        try:
            # Extract JSON if wrapped in markdown
            if "```json" in result:
                start = result.find("```json") + 7
                end = result.find("```", start)
                json_str = result[start:end].strip()
            elif "```" in result:
                start = result.find("```") + 3
                end = result.find("```", start)
                json_str = result[start:end].strip()
            else:
                # Try to find JSON object
                start = result.find("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
            
            plan = json.loads(json_str)
            
            print("\n✅ Successfully parsed JSON!")
            print(f"\nWorkout Days: {len(plan.get('workout_days', []))}")
            
            for day in plan.get('workout_days', []):
                print(f"\n{day.get('day_name', 'Day ' + str(day.get('day_number')))}")
                exercises = day.get('main_workout', [])
                print(f"  Exercises: {len(exercises)}")
                for ex in exercises[:3]:
                    print(f"    - {ex.get('name')}: {ex.get('sets')}x{ex.get('reps')}")
            
            # Save to file
            with open("lm_studio_test_output.json", "w") as f:
                json.dump(plan, f, indent=2)
            print("\n✅ Saved to lm_studio_test_output.json")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"\n⚠️  JSON parsing failed: {e}")
            print("Model generated text but not valid JSON")
            print("\nTip: Try adjusting the prompt or model temperature")
            return False
            
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LM STUDIO TEST SUITE")
    print("="*60)
    print("\nThis will test:")
    print("1. Connection to LM Studio server")
    print("2. Simple text generation")
    print("3. Workout plan generation with JSON")
    
    # Test 1: Connection
    client, model_name = test_connection()
    if not client:
        print("\n❌ Cannot proceed without connection")
        return
    
    # Test 2: Simple generation
    if not test_simple_generation(client, model_name):
        print("\n⚠️  Simple generation failed, but continuing...")
    
    # Test 3: Workout generation
    test_workout_generation(client, model_name)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. If all tests passed, your LM Studio is ready!")
    print("2. Update .env with: LLM_BASE_URL=http://127.0.0.1:1234/v1")
    print("3. Run: python -m uvicorn app.main:app --reload")
    print("4. Test full API at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()

# Made with Bob