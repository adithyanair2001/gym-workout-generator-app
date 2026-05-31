"""ExerciseDB API client for fetching exercise data."""
import asyncio
import logging
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)


class ExerciseDBClient:
    """Client for interacting with ExerciseDB API."""
    
    def __init__(self, api_url: str, page_size: int = 100):
        """Initialize the ExerciseDB client.
        
        Args:
            api_url: Base URL for the ExerciseDB API
            page_size: Number of exercises to fetch per page (default: 100, max: 200)
        """
        self.api_url = api_url
        self.page_size = min(page_size, 200)  # Cap at 200 to respect API limits
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_all_exercises(self) -> List[Dict]:
        """Fetch all exercises from ExerciseDB API with pagination support.
        
        The API uses cursor-based pagination and returns:
        {
            "success": true,
            "meta": {
                "total": 1500,
                "hasNextPage": true,
                "nextCursor": "cursor_string"
            },
            "data": [...]
        }
        
        Returns:
            List of all exercise dictionaries from all pages
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        all_exercises = []
        cursor = None
        page = 1
        
        try:
            logger.info(f"Fetching exercises from {self.api_url}...")
            
            while True:
                # Build URL with cursor and limit parameters
                params = []
                if cursor:
                    params.append(f"cursor={cursor}")
                params.append(f"limit={self.page_size}")
                
                url = f"{self.api_url}?{'&'.join(params)}"
                
                logger.info(f"Fetching page {page} (limit={self.page_size})..." + (f" (cursor: {cursor})" if cursor else ""))
                
                # Retry logic with exponential backoff for rate limiting
                max_retries = 5  # Increased from 3 to 5
                retry_delay = 2.0  # Increased from 1.0 to 2.0 seconds
                response_data = None
                
                for attempt in range(max_retries):
                    try:
                        response = await self.client.get(url)
                        response.raise_for_status()
                        response_data = response.json()
                        break  # Success, exit retry loop
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 429 and attempt < max_retries - 1:
                            # Rate limited, wait and retry with exponential backoff
                            wait_time = retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                        else:
                            # Not rate limited or max retries reached
                            logger.error(f"Failed after {attempt + 1} attempts: {e}")
                            raise
                
                if response_data is None:
                    raise RuntimeError("Failed to fetch data after retries")
                
                # Extract data from response
                if isinstance(response_data, dict) and 'data' in response_data:
                    page_exercises = response_data['data']
                    
                    # Check pagination metadata
                    meta = response_data.get('meta', {})
                    total = meta.get('total', 0)
                    has_next = meta.get('hasNextPage', False)
                    next_cursor = meta.get('nextCursor')
                    
                    # Add exercises to collection
                    all_exercises.extend(page_exercises)
                    
                    logger.info(f"Page {page}: Fetched {len(page_exercises)} exercises (Total so far: {len(all_exercises)}/{total})")
                    
                    # Stop conditions (in order of priority):
                    # 1. Reached the reported total from API
                    if total > 0 and len(all_exercises) >= total:
                        logger.info(f"✓ Reached reported total of {total} exercises, stopping pagination")
                        break
                    
                    # 2. Safety limit - hard cap at 2000 exercises to prevent infinite loops
                    if len(all_exercises) >= 2000:
                        logger.warning(f"⚠ Reached safety limit of 2000 exercises (reported total: {total}), stopping pagination")
                        break
                    
                    # 3. No more pages available
                    if not has_next or not next_cursor:
                        logger.info(f"✓ No more pages available, stopping pagination")
                        break
                    
                    # Continue to next page
                    cursor = next_cursor
                    page += 1
                    # Add longer delay to avoid rate limiting (429 errors)
                    await asyncio.sleep(2.5)
                else:
                    # Fallback for non-paginated response
                    all_exercises = response_data if isinstance(response_data, list) else []
                    break
            
            logger.info(f"Successfully fetched all {len(all_exercises)} exercises from {page} page(s)")
            return all_exercises
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch exercises from ExerciseDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching exercises: {e}")
            raise
    
    async def fetch_exercise_by_id(self, exercise_id: str) -> Dict:
        """Fetch a single exercise by ID.
        
        Args:
            exercise_id: Exercise ID to fetch
            
        Returns:
            Exercise dictionary
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            url = f"{self.api_url}/{exercise_id}"
            logger.debug(f"Fetching exercise {exercise_id} from {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch exercise {exercise_id}: {e}")
            raise
    
    def parse_exercise(self, raw_data: Dict) -> Dict:
        """Parse raw API response into exercise dictionary.
        
        Args:
            raw_data: Raw exercise data from API
            
        Returns:
            Parsed exercise dictionary
        """
        # Just return the raw data as a dictionary
        # No need for a separate ExerciseDB model
        return raw_data
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.debug("ExerciseDB client closed")

# Made with Bob
