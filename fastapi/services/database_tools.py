"""LangChain tools for database queries - enables LLM to directly query the exercise database."""
import logging
from typing import List, Dict, Optional
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
from fastapi.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class SearchExercisesInput(BaseModel):
    """Input schema for search_exercises tool."""
    query: str = Field(description="Natural language query describing the exercises needed (e.g., 'chest exercises with dumbbells for beginners')")
    n_results: int = Field(default=10, description="Number of exercises to return (default: 10, max: 50)")


class FilterByEquipmentInput(BaseModel):
    """Input schema for filter_by_equipment tool."""
    equipment_list: List[str] = Field(description="List of available equipment (e.g., ['barbell', 'dumbbell', 'body weight'])")
    n_results: int = Field(default=20, description="Number of exercises to return")


class GetExerciseDetailsInput(BaseModel):
    """Input schema for get_exercise_details tool."""
    exercise_id: str = Field(description="The exercise ID to get details for")


class DatabaseTools:
    """Collection of tools for LLM to query the exercise database."""
    
    def __init__(self, vector_store: VectorStoreService):
        """Initialize database tools.
        
        Args:
            vector_store: Vector store service instance
        """
        self.vector_store = vector_store
        logger.info("Database tools initialized")
    
    def search_exercises(self, query: str, n_results: int = 10) -> str:
        """Search for exercises using semantic search.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            
        Returns:
            Formatted string with exercise information
        """
        try:
            logger.info(f"Tool called: search_exercises(query='{query}', n_results={n_results})")
            
            # Limit results
            n_results = min(n_results, 50)
            
            # Search vector store
            exercises = self.vector_store.search_exercises(
                query=query,
                n_results=n_results
            )
            
            if not exercises:
                return "No exercises found matching your query."
            
            # Format results
            result = f"Found {len(exercises)} exercises:\n\n"
            for i, exercise in enumerate(exercises, 1):
                meta = exercise.get('metadata', {})
                result += f"{i}. {meta.get('name', 'Unknown')} (ID: {meta.get('exercise_id', '')})\n"
                result += f"   Target: {meta.get('target_muscles', '')}\n"
                result += f"   Equipment: {meta.get('equipment', '')}\n"
                result += f"   Body Parts: {meta.get('body_parts', '')}\n\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in search_exercises tool: {e}")
            return f"Error searching exercises: {str(e)}"
    
    def filter_by_equipment(self, equipment_list: List[str], n_results: int = 20) -> str:
        """Filter exercises by available equipment.
        
        Args:
            equipment_list: List of available equipment
            n_results: Number of results to return
            
        Returns:
            Formatted string with exercise information
        """
        try:
            logger.info(f"Tool called: filter_by_equipment(equipment={equipment_list}, n_results={n_results})")
            
            # Build query from equipment
            equipment_str = ', '.join(equipment_list)
            query = f"exercises using {equipment_str}"
            
            # Build metadata filter for database-level filtering (more efficient)
            # ChromaDB supports $or operator for multiple equipment options
            equipment_filters = []
            for equip in equipment_list:
                equipment_filters.append({"equipment": {"$contains": equip.lower()}})
            
            # Use $or to match any of the equipment types
            filters = {"$or": equipment_filters} if len(equipment_filters) > 1 else equipment_filters[0]
            
            # Search with equipment filter at database level
            exercises = self.vector_store.search_exercises(
                query=query,
                filters=filters,
                n_results=min(n_results, 50)
            )
            
            if not exercises:
                return f"No exercises found using equipment: {equipment_str}"
            
            # Format results
            result = f"Found {len(exercises)} exercises using {equipment_str}:\n\n"
            for i, exercise in enumerate(exercises, 1):
                meta = exercise.get('metadata', {})
                result += f"{i}. {meta.get('name', 'Unknown')} (ID: {meta.get('exercise_id', '')})\n"
                result += f"   Target: {meta.get('target_muscles', '')}\n"
                result += f"   Equipment: {meta.get('equipment', '')}\n\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in filter_by_equipment tool: {e}")
            return f"Error filtering exercises: {str(e)}"
    
    def get_exercise_details(self, exercise_id: str) -> str:
        """Get detailed information about a specific exercise.
        
        Args:
            exercise_id: Exercise ID
            
        Returns:
            Formatted string with detailed exercise information
        """
        try:
            logger.info(f"Tool called: get_exercise_details(exercise_id='{exercise_id}')")
            
            # Search for specific exercise
            exercises = self.vector_store.search_exercises(
                query=f"exercise id {exercise_id}",
                n_results=5
            )
            
            # Find exact match
            for ex in exercises:
                if ex.get('id') == exercise_id:
                    meta = ex.get('metadata', {})
                    doc = ex.get('document', '')
                    
                    result = f"Exercise Details:\n"
                    result += f"ID: {exercise_id}\n"
                    result += f"Name: {meta.get('name', 'Unknown')}\n"
                    result += f"Target Muscles: {meta.get('target_muscles', '')}\n"
                    result += f"Body Parts: {meta.get('body_parts', '')}\n"
                    result += f"Equipment: {meta.get('equipment', '')}\n"
                    result += f"GIF URL: {meta.get('gif_url', '')}\n"
                    result += f"\nDescription:\n{doc}\n"
                    
                    return result
            
            return f"Exercise with ID '{exercise_id}' not found."
            
        except Exception as e:
            logger.error(f"Error in get_exercise_details tool: {e}")
            return f"Error getting exercise details: {str(e)}"
    
    def get_langchain_tools(self) -> List[Tool]:
        """Get LangChain Tool objects for the agent.
        
        Returns:
            List of LangChain Tool objects
        """
        tools = [
            Tool(
                name="search_exercises",
                func=lambda query, n_results=10: self.search_exercises(query, n_results),
                description="""Search for exercises using natural language. 
                Use this when you need to find exercises based on:
                - Muscle groups (e.g., 'chest exercises', 'leg exercises')
                - Fitness goals (e.g., 'strength building', 'muscle growth')
                - Difficulty level (e.g., 'beginner exercises', 'advanced movements')
                - Exercise type (e.g., 'compound exercises', 'isolation exercises')
                
                Input: query (string), n_results (int, optional, default=10)
                Returns: List of exercises with IDs, names, targets, and equipment."""
            ),
            Tool(
                name="filter_by_equipment",
                func=lambda equipment_list, n_results=20: self.filter_by_equipment(equipment_list, n_results),
                description="""Filter exercises by available equipment.
                Use this when you need exercises that use specific equipment.
                
                Input: equipment_list (list of strings), n_results (int, optional, default=20)
                Example: equipment_list=['barbell', 'dumbbell', 'body weight']
                Returns: List of exercises that use the specified equipment."""
            ),
            Tool(
                name="get_exercise_details",
                func=self.get_exercise_details,
                description="""Get detailed information about a specific exercise by ID.
                Use this when you need full details about an exercise you found.
                
                Input: exercise_id (string)
                Returns: Detailed exercise information including instructions and GIF URL."""
            )
        ]
        
        return tools


# Made with Bob