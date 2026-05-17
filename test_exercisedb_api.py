"""Test script to explore ExerciseDB API endpoints."""
import asyncio
import httpx
import json

BASE_URL = "https://oss.exercisedb.dev/api/v1"

async def test_api():
    """Test various ExerciseDB API endpoints."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 80)
        print("Testing ExerciseDB API Endpoints")
        print("=" * 80)
        
        # Test 1: Get exercises (main endpoint)
        print("\n1. Testing /exercises endpoint (first page):")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises?limit=10")
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Response structure: {json.dumps({k: type(v).__name__ for k, v in data.items()}, indent=2)}")
            if 'meta' in data:
                print(f"Meta: {json.dumps(data['meta'], indent=2)}")
            if 'data' in data and len(data['data']) > 0:
                print(f"First exercise sample: {json.dumps(data['data'][0], indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Get body parts list
        print("\n2. Testing /bodyparts endpoint:")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/bodyparts")
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Get exercises by body parts (correct endpoint: /exercises/bodyparts)
        print("\n3. Testing /exercises/bodyparts endpoint:")
        print("-" * 80)
        try:
            # First get the list of body parts
            bodyparts_response = await client.get(f"{BASE_URL}/bodyparts")
            bodyparts_data = bodyparts_response.json()
            
            if bodyparts_data.get('success') and bodyparts_data.get('data'):
                # Use the first body part from the response
                first_bodypart = bodyparts_data['data'][0]['name']
                print(f"Testing with body part: '{first_bodypart}'")
                
                # Now fetch exercises for that body part using the correct endpoint
                response = await client.get(f"{BASE_URL}/exercises/bodyparts?bodyParts={first_bodypart}&limit=10")
                data = response.json()
                print(f"Status: {response.status_code}")
                print(f"Response structure: {json.dumps({k: type(v).__name__ for k, v in data.items()}, indent=2)}")
                if 'meta' in data:
                    print(f"Meta: {json.dumps(data['meta'], indent=2)}")
                if 'data' in data:
                    print(f"Number of exercises returned: {len(data['data'])}")
                    if len(data['data']) > 0:
                        print(f"First exercise sample: {json.dumps(data['data'][0], indent=2)}")
                        
                # Test with multiple body parts
                print(f"\n  Testing with multiple body parts (chest,back):")
                multi_response = await client.get(f"{BASE_URL}/exercises/bodyparts?bodyParts=chest,back&limit=10")
                multi_data = multi_response.json()
                print(f"  Status: {multi_response.status_code}")
                if 'meta' in multi_data:
                    print(f"  Total exercises: {multi_data['meta'].get('total', 'N/A')}")
                if 'data' in multi_data:
                    print(f"  Exercises returned: {len(multi_data['data'])}")
            else:
                print("Could not get body parts list")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 4: Get equipment list
        print("\n4. Testing /equipments endpoint:")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/equipments")
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 5: Get target muscles list
        print("\n5. Testing /targetmuscles endpoint:")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/targetmuscles")
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 80)
        print("API Testing Complete")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_api())

# Made with Bob
