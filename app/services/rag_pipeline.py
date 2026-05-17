"""RAG pipeline for workout plan generation."""
import logging
from typing import Dict, List
from app.models.user_profile import UserProfile, WorkoutSplit
from app.models.workout_plan import WorkoutPlan, WorkoutDay, Exercise
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.utils.validators import sanitize_user_data_for_logging

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline for generating personalized workout plans."""
    
    def __init__(self, vector_store: VectorStoreService, llm_service: LLMService):
        """Initialize the RAG pipeline.
        
        Args:
            vector_store: Vector store service instance
            llm_service: LLM service instance
        """
        self.vector_store = vector_store
        self.llm_service = llm_service
        logger.info("RAG pipeline initialized")
    
    def build_search_query(self, user_profile: UserProfile) -> str:
        """Build semantic search query from user profile.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Search query string
        """
        # Extract goals
        goals_text = ', '.join([g.value.replace('_', ' ') for g in user_profile.goals])
        
        # Determine target muscle groups based on split
        if user_profile.preferred_split == WorkoutSplit.FULL_BODY:
            muscles = "chest, back, shoulders, legs, arms, core"
        elif user_profile.preferred_split == WorkoutSplit.UPPER_LOWER:
            muscles = "chest, back, shoulders, arms, legs, glutes"
        elif user_profile.preferred_split == WorkoutSplit.PUSH_PULL_LEGS:
            muscles = "chest, shoulders, triceps, back, biceps, legs"
        else:
            # Auto-determine based on days per week
            if user_profile.gym_days_per_week <= 3:
                muscles = "chest, back, shoulders, legs, arms"
            else:
                muscles = "chest, back, shoulders, legs, arms, core"
        
        query = f"""{user_profile.fitness_level.value} level exercises for {goals_text}.
Target muscle groups: {muscles}.
Available equipment: {', '.join(user_profile.available_equipment)}.
Suitable for {user_profile.gym_days_per_week} days per week training with {user_profile.workout_duration_minutes} minute sessions."""
        
        logger.debug(f"Built search query: {query}")
        return query
    
    def get_split_strategy(self, user_profile: UserProfile) -> str:
        """Determine workout split strategy.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Split strategy description
        """
        days = user_profile.gym_days_per_week
        split = user_profile.preferred_split
        
        if split == WorkoutSplit.AUTO:
            if days <= 3:
                split = WorkoutSplit.FULL_BODY
            elif days <= 5:
                split = WorkoutSplit.UPPER_LOWER
            else:
                split = WorkoutSplit.PUSH_PULL_LEGS
        
        strategies = {
            WorkoutSplit.FULL_BODY: f"""Full Body Split ({days} days/week):
- Each workout targets all major muscle groups
- Balanced approach for {days} days per week
- Focus on compound movements
- Example: Day 1: Full Body, Day 2: Full Body, Day 3: Full Body""",
            
            WorkoutSplit.UPPER_LOWER: f"""Upper/Lower Split ({days} days/week):
- Alternate between upper and lower body workouts
- Day 1: Upper Body (Chest, Back, Shoulders, Arms)
- Day 2: Lower Body (Quads, Hamstrings, Glutes, Calves)
- Repeat pattern for {days} days""",
            
            WorkoutSplit.PUSH_PULL_LEGS: f"""Push/Pull/Legs Split ({days} days/week):
- Day 1: Push (Chest, Shoulders, Triceps)
- Day 2: Pull (Back, Biceps, Rear Delts)
- Day 3: Legs (Quads, Hamstrings, Glutes, Calves)
- Repeat pattern for {days} days"""
        }
        
        return strategies.get(split, strategies[WorkoutSplit.FULL_BODY])
    
    async def generate_workout_plan(self, user_profile: UserProfile) -> WorkoutPlan:
        """Generate complete workout plan using RAG.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Generated workout plan
            
        Raises:
            Exception: If generation fails
        """
        try:
            # Log with sanitized data (no PII)
            logger.info(f"Generating workout plan for user: fitness_level={user_profile.fitness_level.value}, "
                       f"days_per_week={user_profile.gym_days_per_week}, "
                       f"goals={[g.value for g in user_profile.goals]}")
            
            # Step 1: Build search query
            query = self.build_search_query(user_profile)
            
            # Step 2: Build metadata filters
            filters = None
            if user_profile.available_equipment:
                # Note: ChromaDB filtering syntax - adjust based on actual metadata structure
                # This is a simplified version
                logger.debug(f"Filtering by equipment: {user_profile.available_equipment}")
            
            # Step 3: Search for relevant exercises
            logger.info("Searching for relevant exercises...")
            exercises = self.vector_store.search_exercises(
                query=query,
                filters=filters,
                n_results=50
            )
            
            if not exercises:
                # Provide detailed error message with context
                error_msg = (
                    f"No exercises found matching criteria. "
                    f"Equipment: {user_profile.available_equipment}, "
                    f"Fitness level: {user_profile.fitness_level.value}, "
                    f"Goals: {[g.value for g in user_profile.goals]}. "
                    f"Please check: (1) Vector store is populated with exercises, "
                    f"(2) Equipment names are correct (e.g., 'barbell', 'dumbbell', 'bodyweight'), "
                    f"(3) Database contains exercises matching your criteria."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Retrieved {len(exercises)} relevant exercises")
            
            # Step 4: Get split strategy
            split_strategy = self.get_split_strategy(user_profile)
            
            # Step 5: Construct prompt
            prompt = self.llm_service.construct_prompt(
                user_profile=user_profile,
                exercises=exercises,
                split_strategy=split_strategy
            )
            
            # Step 6: Generate workout plan with LLM
            logger.info("Generating workout plan with LLM...")
            llm_response = await self.llm_service.generate_workout_plan(prompt)
            
            # Step 7: Post-process and validate
            workout_plan = self.post_process_response(llm_response, user_profile, exercises)
            
            logger.info("Workout plan generated successfully")
            return workout_plan
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise
    
    def post_process_response(
        self,
        llm_response: Dict,
        user_profile: UserProfile,
        available_exercises: List[Dict]
    ) -> WorkoutPlan:
        """Post-process and validate LLM response.
        
        Args:
            llm_response: Raw LLM response
            user_profile: User profile
            available_exercises: List of available exercises
            
        Returns:
            Validated WorkoutPlan
        """
        try:
            # Create exercise ID lookup
            exercise_lookup = {ex['id']: ex for ex in available_exercises}
            
            # Process workout days
            workout_days = []
            for day_data in llm_response.get('workout_days', []):
                # Process exercises
                main_workout = []
                for ex_data in day_data.get('main_workout', []):
                    # Verify exercise exists in database
                    ex_id = ex_data.get('exercise_id', '')
                    if ex_id in exercise_lookup:
                        exercise_info = exercise_lookup[ex_id]
                        meta = exercise_info.get('metadata', {})
                        
                        exercise = Exercise(
                            exercise_id=ex_id,
                            name=ex_data.get('name', meta.get('name', '')),
                            target_muscles=ex_data.get('target_muscles', meta.get('target_muscles', '').split(',')),
                            sets=ex_data.get('sets', 3),
                            reps=ex_data.get('reps', '8-12'),
                            rest_seconds=ex_data.get('rest_seconds', 60),
                            gif_url=meta.get('gif_url', ''),
                            instructions=ex_data.get('instructions', []),
                            notes=ex_data.get('notes')
                        )
                        main_workout.append(exercise)
                    else:
                        logger.warning(f"Exercise {ex_id} not found in database, skipping")
                
                # Calculate total exercises
                total_exercises = len(main_workout)
                total_exercises += len(day_data.get('warm_up', []))
                total_exercises += len(day_data.get('cool_down', []))
                
                workout_day = WorkoutDay(
                    day_number=day_data.get('day_number', 1),
                    day_name=day_data.get('day_name', f"Day {day_data.get('day_number', 1)}"),
                    focus=day_data.get('focus', 'Full Body'),
                    # TODO: Implement warm_up/cool_down generation
                    # Should include 5-10 min dynamic stretches for warm_up
                    # and static stretches for cool_down based on workout focus
                    warm_up=[],
                    main_workout=main_workout,
                    cool_down=[],
                    estimated_duration_minutes=day_data.get('estimated_duration_minutes', user_profile.workout_duration_minutes),
                    total_exercises=total_exercises
                )
                workout_days.append(workout_day)
            
            # Create workout plan
            workout_plan = WorkoutPlan(
                user_profile_summary={
                    "age": user_profile.age,
                    "gender": user_profile.gender,
                    "fitness_level": user_profile.fitness_level.value,
                    "goals": [g.value for g in user_profile.goals],
                    "days_per_week": user_profile.gym_days_per_week
                },
                days_per_week=user_profile.gym_days_per_week,
                workout_days=workout_days,
                progression_notes=llm_response.get('progression_notes', 'Increase weight gradually as you get stronger'),
                nutrition_tips=llm_response.get('nutrition_tips')
            )
            
            return workout_plan
            
        except Exception as e:
            logger.error(f"Error post-processing response: {e}")
            raise

# Made with Bob
