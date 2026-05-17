
#!/usr/bin/env python3
"""Test script to verify ExerciseDB pagination works correctly."""

import asyncio
import logging

from app.services.exercisedb_client import ExerciseDBClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pagination():
    """Test that pagination fetches all exercises."""
    print("\n" + "="*60)
    print("Testing ExerciseDB Pagination")
    print("="*60)
    
    # Initialize client
    client = ExerciseDBClient("https://oss.exercisedb.dev/api/v1/exercises")
    
    try:
        # Fetch all exercises
        print("\nFetching all exercises with pagination...")
        exercises = await client.fetch_all_exercises()
        
        print("\n" + "="*60)
        print(f"✅ SUCCESS: Fetched {len(exercises)} total exercises")
        print("="*60)
        
        # Show some sample exercises
        print("\nFirst 3 exercises:")
        for i, ex in enumerate(exercises[:3], 1):
            print(f"{i}. {ex.get('name', 'Unknown')} - {ex.get('exerciseId', 'N/A')}")
        
        print("\nLast 3 exercises:")
        for i, ex in enumerate(exercises[-3:], len(exercises)-2):
            print(f"{i}. {ex.get('name', 'Unknown')} - {ex.get('exerciseId', 'N/A')}")
        
        # Verify we got more than just one page
        if len(exercises) > 10:
            print(f"\n✅ Pagination working! Got {len(exercises)} exercises (more than 10)")
        else:
            print(f"\n⚠️  Warning: Only got {len(exercises)} exercises. Pagination may not be working.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error("Test failed", exc_info=True)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_pagination())

# Made with Bob
