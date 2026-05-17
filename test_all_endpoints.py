"""Test all available ExerciseDB API endpoints."""
import asyncio
import httpx
import json

BASE_URL = "https://oss.exercisedb.dev/api/v1"

async def test_all_endpoints():
    """Test all available ExerciseDB API endpoints."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 80)
        print("Testing ALL ExerciseDB API Endpoints")
        print("=" * 80)
        
        # 1. GET /api/v1/exercises
        print("\n1. GET /api/v1/exercises")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises?limit=10")
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if 'meta' in data:
                print(f"  Total: {data['meta'].get('total')}")
                print(f"  Has pagination: {data['meta'].get('hasNextPage')}")
            print(f"  Exercises returned: {len(data.get('data', []))}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # 2. GET /api/v1/exercises/search
        print("\n2. GET /api/v1/exercises/search")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises/search?query=bench+press&limit=10")
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if 'meta' in data:
                print(f"  Total matches: {data['meta'].get('total')}")
            print(f"  Exercises returned: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"  First result: {data['data'][0].get('name')}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # 3. GET /api/v1/exercises/bodyparts
        print("\n3. GET /api/v1/exercises/bodyparts")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises/bodyparts?bodyParts=chest&limit=10")
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if 'meta' in data:
                print(f"  Total for 'chest': {data['meta'].get('total')}")
            print(f"  Exercises returned: {len(data.get('data', []))}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # 4. GET /api/v1/exercises/muscles
        print("\n4. GET /api/v1/exercises/muscles")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises/muscles?targetMuscles=pectorals&limit=10")
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if 'meta' in data:
                print(f"  Total for 'pectorals': {data['meta'].get('total')}")
            print(f"  Exercises returned: {len(data.get('data', []))}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # 5. GET /api/v1/exercises/equipments
        print("\n5. GET /api/v1/exercises/equipments")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises/equipments?equipments=barbell&limit=10")
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if 'meta' in data:
                print(f"  Total for 'barbell': {data['meta'].get('total')}")
            print(f"  Exercises returned: {len(data.get('data', []))}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # 6. GET /api/v1/exercises/{exerciseId}
        print("\n6. GET /api/v1/exercises/{exerciseId}")
        print("-" * 80)
        try:
            # First get an exercise ID from the main endpoint
            first_response = await client.get(f"{BASE_URL}/exercises?limit=1")
            first_data = first_response.json()
            if first_data.get('data'):
                exercise_id = first_data['data'][0]['exerciseId']
                response = await client.get(f"{BASE_URL}/exercises/{exercise_id}")
                data = response.json()
                print(f"✓ Status: {response.status_code}")
                print(f"  Exercise ID: {exercise_id}")
                print(f"  Exercise name: {data.get('data', {}).get('name')}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print("\n" + "=" * 80)
        print("ANALYSIS: Which endpoint to use?")
        print("=" * 80)
        
        # Compare totals
        print("\nFetching totals from each filtering endpoint...")
        totals = {}
        
        try:
            # Get all body parts and sum their totals
            bodyparts_resp = await client.get(f"{BASE_URL}/bodyparts")
            bodyparts = bodyparts_resp.json().get('data', [])
            bodypart_total = 0
            for bp in bodyparts:
                bp_resp = await client.get(f"{BASE_URL}/exercises/bodyparts?bodyParts={bp['name']}&limit=1")
                bp_data = bp_resp.json()
                count = bp_data.get('meta', {}).get('total', 0)
                bodypart_total += count
                print(f"  {bp['name']}: {count} exercises")
            totals['bodyparts'] = bodypart_total
            print(f"\n  Total via bodyparts: {bodypart_total}")
        except Exception as e:
            print(f"  Error getting bodyparts total: {e}")
        
        try:
            # Get main endpoint total
            main_resp = await client.get(f"{BASE_URL}/exercises?limit=1")
            main_total = main_resp.json().get('meta', {}).get('total', 0)
            totals['main'] = main_total
            print(f"  Total via main endpoint: {main_total}")
        except Exception as e:
            print(f"  Error getting main total: {e}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        if totals.get('bodyparts', 0) > totals.get('main', 0):
            print(f"""
✓ Use /exercises/bodyparts endpoint!
  - Fetching by body parts gives MORE exercises ({totals['bodyparts']} vs {totals['main']})
  - Can fetch all exercises by iterating through body parts
  - Avoids duplicate IDs issue
  - More organized data structure
            """)
        else:
            print(f"""
✓ Use /exercises endpoint (current approach)
  - Main endpoint has all {totals['main']} exercises
  - Simpler implementation
  - Fewer API calls
  - Already handles deduplication
            """)

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())

# Made with Bob
