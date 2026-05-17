"""Test the bodyparts endpoint with correct capitalization and encoding."""
import asyncio
import httpx
import json
from urllib.parse import quote

BASE_URL = "https://oss.exercisedb.dev/api/v1"

async def test_bodyparts_comprehensive():
    """Comprehensive test of the bodyparts endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 80)
        print("Testing /exercises/bodyparts Endpoint (Comprehensive)")
        print("=" * 80)
        
        # Get list of body parts
        print("\n1. Getting list of body parts...")
        print("-" * 80)
        bodyparts_response = await client.get(f"{BASE_URL}/bodyparts")
        bodyparts_data = bodyparts_response.json()
        body_parts = [bp['name'] for bp in bodyparts_data.get('data', [])]
        print(f"Available body parts: {body_parts}")
        
        # Test with single body part (capitalized)
        print("\n2. Testing single body part (Chest)...")
        print("-" * 80)
        try:
            # Capitalize first letter
            bodypart = "Chest"
            encoded_bodypart = quote(bodypart)
            url = f"{BASE_URL}/exercises/bodyparts?bodyParts={encoded_bodypart}&limit=10"
            print(f"URL: {url}")
            
            response = await client.get(url)
            data = response.json()
            print(f"Status: {response.status_code}")
            if 'meta' in data:
                print(f"Total exercises for '{bodypart}': {data['meta'].get('total')}")
                print(f"Has next page: {data['meta'].get('hasNextPage')}")
            print(f"Exercises returned: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"First exercise: {data['data'][0].get('name')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test with multiple body parts (capitalized, comma-separated)
        print("\n3. Testing multiple body parts (Chest,Shoulders)...")
        print("-" * 80)
        try:
            bodyparts = "Chest,Shoulders"
            encoded_bodyparts = quote(bodyparts)
            url = f"{BASE_URL}/exercises/bodyparts?bodyParts={encoded_bodyparts}&limit=10"
            print(f"URL: {url}")
            
            response = await client.get(url)
            data = response.json()
            print(f"Status: {response.status_code}")
            if 'meta' in data:
                print(f"Total exercises for '{bodyparts}': {data['meta'].get('total')}")
            print(f"Exercises returned: {len(data.get('data', []))}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test fetching ALL exercises via body parts
        print("\n4. Fetching ALL exercises via body parts...")
        print("-" * 80)
        try:
            # Capitalize all body parts
            capitalized_parts = [bp.capitalize() for bp in body_parts]
            all_bodyparts = ",".join(capitalized_parts)
            encoded_all = quote(all_bodyparts)
            
            print(f"Fetching with all body parts: {all_bodyparts}")
            url = f"{BASE_URL}/exercises/bodyparts?bodyParts={encoded_all}&limit=100"
            
            response = await client.get(url)
            data = response.json()
            print(f"Status: {response.status_code}")
            if 'meta' in data:
                print(f"✓ Total exercises (all body parts): {data['meta'].get('total')}")
                print(f"  Has pagination: {data['meta'].get('hasNextPage')}")
                print(f"  Next cursor: {data['meta'].get('nextCursor')}")
            print(f"  Exercises in first page: {len(data.get('data', []))}")
            
            # Check for duplicates in first page
            if data.get('data'):
                ids = [ex.get('exerciseId') for ex in data['data']]
                unique_ids = set(ids)
                if len(ids) != len(unique_ids):
                    print(f"  ⚠️  Found {len(ids) - len(unique_ids)} duplicate IDs in first page")
                else:
                    print(f"  ✓ No duplicates in first page")
                    
        except Exception as e:
            print(f"Error: {e}")
        
        # Compare with main endpoint
        print("\n5. Comparing with main /exercises endpoint...")
        print("-" * 80)
        try:
            main_response = await client.get(f"{BASE_URL}/exercises?limit=100")
            main_data = main_response.json()
            main_total = main_data.get('meta', {}).get('total', 0)
            print(f"Main endpoint total: {main_total}")
            
            bodyparts_total = data.get('meta', {}).get('total', 0) if 'data' in locals() else 0
            print(f"Body parts endpoint total: {bodyparts_total}")
            
            if bodyparts_total > main_total:
                print(f"\n✓ Body parts endpoint has MORE exercises (+{bodyparts_total - main_total})")
            elif bodyparts_total < main_total:
                print(f"\n⚠️  Body parts endpoint has FEWER exercises (-{main_total - bodyparts_total})")
            else:
                print(f"\n✓ Both endpoints have the same number of exercises")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("""
Based on the test results:

If bodyparts endpoint has MORE or EQUAL exercises:
  ✓ Switch to /exercises/bodyparts endpoint
  ✓ Fetch all body parts in one call: ?bodyParts=Chest,Back,Shoulders,...
  ✓ Use pagination with cursor
  ✓ Apply deduplication (if needed)

If main endpoint has MORE exercises:
  ✓ Keep current /exercises endpoint
  ✓ Simpler implementation
  ✓ Already working with deduplication
        """)

if __name__ == "__main__":
    asyncio.run(test_bodyparts_comprehensive())

# Made with Bob
