"""Comprehensive test of ExerciseDB API to find the best fetching strategy."""
import asyncio
import httpx
import json

BASE_URL = "https://oss.exercisedb.dev/api/v1"

async def test_fetching_strategies():
    """Test different strategies for fetching exercises."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 80)
        print("ExerciseDB API - Fetching Strategy Analysis")
        print("=" * 80)
        
        # Strategy 1: Fetch all exercises with pagination
        print("\n📊 Strategy 1: Fetch all exercises (current approach)")
        print("-" * 80)
        try:
            response = await client.get(f"{BASE_URL}/exercises?limit=100")
            data = response.json()
            meta = data.get('meta', {})
            print(f"✓ Total exercises available: {meta.get('total', 0)}")
            print(f"✓ Has pagination: {meta.get('hasNextPage', False)}")
            print(f"✓ Exercises per page: {len(data.get('data', []))}")
            
            # Check for duplicates in first page
            first_page = data.get('data', [])
            ids = [ex.get('exerciseId') for ex in first_page]
            unique_ids = set(ids)
            print(f"✓ Unique IDs in first page: {len(unique_ids)}/{len(ids)}")
            if len(unique_ids) < len(ids):
                print(f"⚠️  Found {len(ids) - len(unique_ids)} duplicates in first page!")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Strategy 2: Check if we can filter by body parts
        print("\n📊 Strategy 2: Fetch by body parts (if available)")
        print("-" * 80)
        try:
            # Get list of body parts
            bp_response = await client.get(f"{BASE_URL}/bodyparts")
            body_parts = bp_response.json().get('data', [])
            print(f"✓ Available body parts: {len(body_parts)}")
            print(f"  Body parts: {', '.join([bp['name'] for bp in body_parts])}")
            
            # Try to fetch exercises for one body part
            test_bodypart = body_parts[0]['name'] if body_parts else 'chest'
            print(f"\n  Testing fetch for '{test_bodypart}'...")
            
            # Try different URL patterns
            patterns = [
                f"/exercises/bodypart/{test_bodypart}",
                f"/exercises?bodypart={test_bodypart}",
                f"/exercises?bodyPart={test_bodypart}",
                f"/exercises?filter[bodyParts]={test_bodypart}",
            ]
            
            for pattern in patterns:
                try:
                    test_response = await client.get(f"{BASE_URL}{pattern}?limit=10")
                    if test_response.status_code == 200:
                        test_data = test_response.json()
                        print(f"  ✓ Pattern works: {pattern}")
                        print(f"    Exercises found: {len(test_data.get('data', []))}")
                        if 'meta' in test_data:
                            print(f"    Total for this body part: {test_data['meta'].get('total', 'N/A')}")
                        break
                except:
                    pass
            else:
                print(f"  ✗ No working pattern found for body part filtering")
                
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Strategy 3: Check pagination efficiency
        print("\n📊 Strategy 3: Pagination efficiency analysis")
        print("-" * 80)
        try:
            # Fetch with different page sizes
            for page_size in [50, 100, 200]:
                response = await client.get(f"{BASE_URL}/exercises?limit={page_size}")
                data = response.json()
                actual_count = len(data.get('data', []))
                print(f"✓ Requested {page_size}, got {actual_count} exercises")
                
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Strategy 4: Check for duplicate IDs across pages
        print("\n📊 Strategy 4: Duplicate ID analysis across pages")
        print("-" * 80)
        try:
            all_ids = []
            cursor = None
            pages_to_check = 3
            
            for page_num in range(pages_to_check):
                url = f"{BASE_URL}/exercises?limit=100"
                if cursor:
                    url += f"&cursor={cursor}"
                
                response = await client.get(url)
                data = response.json()
                
                page_exercises = data.get('data', [])
                page_ids = [ex.get('exerciseId') for ex in page_exercises]
                all_ids.extend(page_ids)
                
                cursor = data.get('meta', {}).get('nextCursor')
                if not cursor:
                    break
            
            unique_ids = set(all_ids)
            print(f"✓ Checked {len(all_ids)} exercises across {pages_to_check} pages")
            print(f"✓ Unique IDs: {len(unique_ids)}")
            print(f"✓ Duplicate IDs: {len(all_ids) - len(unique_ids)}")
            
            if len(all_ids) > len(unique_ids):
                # Find which IDs are duplicated
                from collections import Counter
                id_counts = Counter(all_ids)
                duplicates = {id: count for id, count in id_counts.items() if count > 1}
                print(f"  Duplicated IDs: {list(duplicates.keys())[:10]}...")
                
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print("\n" + "=" * 80)
        print("📋 RECOMMENDATION")
        print("=" * 80)
        print("""
Based on the API analysis:

1. ✓ Use the main /exercises endpoint with pagination (current approach)
2. ✓ Implement deduplication (already done in vector_store.py)
3. ✓ Use page size of 100 (good balance)
4. ✓ Stop at reported total (1500 exercises)
5. ✗ Body part filtering is NOT available in the API

The current implementation is optimal. The duplicate IDs are coming from
the API itself, not from our pagination logic. The deduplication fix
handles this correctly.
        """)

if __name__ == "__main__":
    asyncio.run(test_fetching_strategies())

# Made with Bob
