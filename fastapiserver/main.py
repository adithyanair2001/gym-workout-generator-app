"""Main FastAPI application for gym workout RAG system."""
# Standard library imports
import logging
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Local application imports
from fastapiserver.config import get_settings
from fastapiserver.middleware import RequestIDMiddleware
from fastapiserver.models.user_profile import UserProfile
from fastapiserver.models.workout_plan import WorkoutPlan
from fastapiserver.models.workout_request import WorkoutGenerationRequest
from fastapiserver.services.database_tools import DatabaseTools
from fastapiserver.services.exercisedb_client import ExerciseDBClient
from fastapiserver.services.gguf_service import GGUFService
from fastapiserver.services.llm_service import LLMService
from fastapiserver.services.mlx_agent_service import MLXAgentService
from fastapiserver.services.rag_pipeline import RAGPipeline
from fastapiserver.services.vector_store import VectorStoreService
from fastapiserver.services.service_factory import ServiceFactory
from fastapiserver.utils.logging_config import RequestIDFilter, setup_structured_logging

# Configure structured logging
settings_for_logging = get_settings()
setup_structured_logging(
    log_level=settings_for_logging.log_level,
    use_json=settings_for_logging.use_json_logging
)

# Add request ID filter to all loggers
request_id_filter = RequestIDFilter()
for handler in logging.root.handlers:
    handler.addFilter(request_id_filter)

logger = logging.getLogger(__name__)

# Global service instances
exercise_client = None
vector_store = None
llm_service = None
gguf_service = None
mlx_agent = None
database_tools = None
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global exercise_client, vector_store, llm_service, gguf_service, mlx_agent, database_tools, rag_pipeline
    
    settings = get_settings()
    
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Gym Workout RAG System")
    logger.info("=" * 60)
    
    try:
        # Initialize ExerciseDB client with larger page size to reduce API calls
        logger.info("Initializing ExerciseDB client...")
        exercise_client = ExerciseDBClient(
            api_url=settings.exercisedb_api_url,
            page_size=settings.exercisedb_page_size
        )
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStoreService(
            settings.chroma_db_path,
            settings.embedding_model
        )
        vector_store.initialize_collection()
        
        # Check if vector store exists and has content
        exercise_count = vector_store.collection.count() if vector_store.collection else 0
        
        logger.info(f"Vector store status: {exercise_count} exercises found")
        
        # Only fetch if database is truly empty (count == 0)
        if exercise_count == 0:
            logger.info("=" * 60)
            logger.info("Vector store is empty - starting exercise fetch")
            logger.info("=" * 60)
            exercises = await exercise_client.fetch_all_exercises()
            logger.info(f"Fetched {len(exercises)} exercises, creating embeddings...")
            await vector_store.add_exercises(exercises)
            logger.info("=" * 60)
            logger.info("Vector store initialized successfully")
            logger.info("=" * 60)
        else:
            logger.info("=" * 60)
            logger.info(f"✓ Vector store already contains {exercise_count} exercises")
            logger.info("  Skipping exercise fetch and embedding generation")
            logger.info(f"  To rebuild: rm -rf {settings.chroma_db_path}")
            logger.info("=" * 60)
        
        # Note: LLM services are now initialized lazily via ServiceFactory
        # Models are only loaded when actually needed for generation
        # This prevents unnecessary memory usage at startup
        
        logger.info("=" * 60)
        logger.info("LLM Configuration (Lazy Loading Enabled)")
        logger.info("=" * 60)
        
        if settings.use_mlx:
            logger.info(f"✓ MLX mode configured: {settings.mlx_model_path}")
            logger.info("  Model will load on first generation request")
        elif settings.use_gguf:
            logger.info(f"✓ GGUF mode configured: {settings.gguf_model_path}")
            logger.info("  Model will load on first generation request")
        else:
            logger.info(f"✓ External API configured: {settings.llm_base_url}")
            logger.info(f"  Model: {settings.llm_model}")
            if settings.llm_api_key:
                logger.info("  API key: Configured ✓")
            logger.info("  Connection will be established on first request")
        
        logger.info("=" * 60)
        logger.info("💡 Models load on-demand to save memory")
        logger.info("   Use dynamic model selection in UI for flexibility")
        logger.info("=" * 60)
        
        # Services will be created by ServiceFactory when needed
        mlx_agent = None
        database_tools = None
        llm_service = None
        gguf_service = None
        rag_pipeline = None
        
        logger.info("=" * 60)
        logger.info("Application startup complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    logger.info("=" * 60)
    
    # Cleanup MLX agent if it was initialized
    if mlx_agent:
        logger.info("Cleaning up MLX agent...")
        mlx_agent.cleanup()
        logger.info("✓ MLX agent cleaned up")
    
    # Clear service factory cache (cleans up any cached MLX services)
    logger.info("Clearing service factory cache...")
    ServiceFactory.clear_cache()
    logger.info("✓ Service factory cache cleared")
    
    # Close exercise client
    if exercise_client:
        await exercise_client.close()
        logger.info("✓ Exercise client closed")
    
    # Vector database is preserved for next startup
    logger.info(f"✓ Vector database preserved at: {settings.chroma_db_path}")
    logger.info(f"  To rebuild database: rm -rf {settings.chroma_db_path}")
    
    logger.info("=" * 60)
    logger.info("Application shutdown complete")
    logger.info("=" * 60)


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Gym Workout RAG API",
    description="AI-powered personalized workout plan generator using RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middlewares (order matters - last added is executed first)
settings = get_settings()

# 1. CORS middleware (outermost)
allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Request ID middleware (innermost - closest to handlers)
app.add_middleware(RequestIDMiddleware)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Gym Workout RAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "/api/v1/generate",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        settings = get_settings()
        vector_db_stats = vector_store.get_collection_stats() if vector_store else {"status": "not_initialized"}
        
        # Check LLM status based on configuration
        if settings.use_mlx:
            llm_mode = "mlx_agent"
            llm_status = "ready" if mlx_agent else "not_initialized"
        elif settings.use_gguf:
            llm_mode = "gguf_langchain"
            llm_status = "ready" if gguf_service else "not_initialized"
        else:
            llm_mode = "external_api"
            llm_status = "ready" if (llm_service and llm_service.test_connection()) else "not_connected"
        
        return {
            "status": "healthy",
            "vector_db": vector_db_stats,
            "llm_mode": llm_mode,
            "llm_status": llm_status,
            "services": {
                "exercise_client": exercise_client is not None,
                "vector_store": vector_store is not None,
                "llm_service": llm_service is not None,
                "gguf_service": gguf_service is not None,
                "mlx_agent": mlx_agent is not None,
                "rag_pipeline": rag_pipeline is not None
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/api/v1/admin/clear-cache")
async def clear_service_cache():
    """Clear the service factory cache and cleanup all cached services.
    
    This endpoint is useful for:
    - Freeing memory when switching between models
    - Forcing reload of models after configuration changes
    - Troubleshooting memory issues
    
    Returns:
        Status message with number of services cleared
    """
    try:
        cache_size = len(ServiceFactory._service_cache)
        ServiceFactory.clear_cache()
        logger.info(f"Service cache cleared via API endpoint ({cache_size} services)")
        return {
            "status": "success",
            "message": f"Service cache cleared ({cache_size} services cleaned up)",
            "services_cleared": cache_size
        }
    except Exception as e:
        logger.error(f"Error clearing service cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.post("/api/v1/generate", response_model=WorkoutPlan)
@limiter.limit("5/minute")  # Limit to 5 requests per minute per IP
async def generate_workout(request: Request, workout_request: WorkoutGenerationRequest):
    """Generate personalized workout plan with optional model configuration.
    
    This endpoint now supports dynamic model selection! You can either:
    1. Provide llm_config in the request to use a specific model
    2. Omit llm_config to use the default .env configuration
    
    Args:
        workout_request: Contains user_profile and optional llm_config
        
    Returns:
        Generated workout plan
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        user_profile = workout_request.user_profile
        llm_config = workout_request.llm_config
        
        # Log request details
        if llm_config:
            logger.info(f"Received workout generation request for {user_profile.fitness_level.value} user with {llm_config.model_type.value} model")
        else:
            logger.info(f"Received workout generation request for {user_profile.fitness_level.value} user (using .env defaults)")
        
        # Validate vector store is initialized
        if not vector_store:
            raise HTTPException(
                status_code=503,
                detail="Vector store not initialized. Please try again later."
            )
        
        # Create appropriate service using factory (disable caching for auto-cleanup)
        service = ServiceFactory.create_service(
            model_config=llm_config,
            vector_store=vector_store,
            use_cache=False  # Disable caching to allow cleanup after each request
        )
        
        try:
            # Determine if this is an MLX agent or RAG pipeline
            if isinstance(service, MLXAgentService):
                logger.info("Generating workout plan with MLX agent...")
                # Generate with MLX agent
                raw_response = service.generate_workout_plan(user_profile)
                
                # Parse JSON response
                workout_data = service.parse_json_response(raw_response)
                
                # Convert to WorkoutPlan model in custom format
                from fastapiserver.models.workout_plan import WorkoutDay, Exercise
                
                workout_groups = []
                for day_data in workout_data.get('workout_days', []):
                    selected_exercises = []
                    for ex_data in day_data.get('main_workout', []):
                        # Format instructions with $$ separator
                        instructions = ex_data.get('instructions', [])
                        if isinstance(instructions, list):
                            description = " $$ ".join(instructions)
                        else:
                            description = str(instructions)
                        
                        # Get target muscles
                        target_muscles = ex_data.get('target_muscles', [])
                        if isinstance(target_muscles, list):
                            target_muscles_str = target_muscles[0] if target_muscles else ''
                        else:
                            target_muscles_str = str(target_muscles)
                        
                        exercise = Exercise(
                            exerciseDbId=ex_data.get('exercise_id', ''),
                            exerciseName=ex_data.get('name', ''),
                            bodyPart='Unknown',  # Will be filled by RAG pipeline
                            equipments='Unknown',  # Will be filled by RAG pipeline
                            targetMuscles=target_muscles_str,
                            secondaryMuscles='',
                            mediaUrl=ex_data.get('gif_url', ''),
                            description=description
                        )
                        selected_exercises.append(exercise)
                    
                    workout_group = WorkoutDay(
                        groupName=day_data.get('day_name', f"Day {day_data.get('day_number', 1)}"),
                        isAiGenerated=True,
                        selectedExercises=selected_exercises
                    )
                    workout_groups.append(workout_group)
                
                workout_plan = WorkoutPlan(
                    workoutGroups=workout_groups
                )
            else:
                logger.info("Generating workout plan with RAG pipeline...")
                # Create RAG pipeline with the service
                pipeline = RAGPipeline(vector_store, service)
                # Generate workout plan with traditional RAG
                workout_plan = await pipeline.generate_workout_plan(user_profile)
            
            logger.info(f"Successfully generated workout plan with {len(workout_plan.workoutGroups)} workout groups")
            return workout_plan
            
        finally:
            # Cleanup: Unload model after generation is complete
            if isinstance(service, MLXAgentService):
                logger.info("Cleaning up MLX model from memory...")
                service.cleanup()
                logger.info("✓ MLX model unloaded successfully")
            elif isinstance(service, GGUFService):
                logger.info("Cleaning up GGUF model from memory...")
                # GGUF models are managed by llama-cpp-python, cleanup happens automatically
                # But we can explicitly delete the reference to help garbage collection
                del service
                import gc
                gc.collect()
                logger.info("✓ GGUF model reference cleared")
            else:
                # For API-based services, no cleanup needed (no local model loaded)
                logger.info("✓ API-based service, no model cleanup needed")
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating workout: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate workout plan: {str(e)}")


@app.get("/api/v1/exercises/search")
async def search_exercises(query: str, limit: int = 10):
    """Search exercises by query.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching exercises
    """
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        exercises = vector_store.search_exercises(query=query, n_results=limit)
        
        return {
            "query": query,
            "count": len(exercises),
            "exercises": exercises
        }
        
    except Exception as e:
        logger.error(f"Error searching exercises: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics."""
    try:
        stats = {
            "vector_db": vector_store.get_collection_stats() if vector_store else {},
            "llm_model": llm_service.model if llm_service else None,
            "services_initialized": {
                "exercise_client": exercise_client is not None,
                "vector_store": vector_store is not None,
                "llm_service": llm_service is not None,
                "rag_pipeline": rag_pipeline is not None
            }
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/models")
async def list_models():
    """List available models from the LLM provider.
    
    Returns:
        List of available models with their metadata
        
    Raises:
        HTTPException: If listing fails or service not available
    """
    try:
        settings = get_settings()
        
        # Only works with external LLM services (not MLX or GGUF)
        if settings.use_mlx:
            return {
                "provider": "mlx",
                "message": "MLX uses local models. Current model path configured.",
                "current_model": settings.mlx_model_path
            }
        elif settings.use_gguf:
            return {
                "provider": "gguf",
                "message": "GGUF uses local models. Current model path configured.",
                "current_model": settings.gguf_model_path
            }
        
        if not llm_service:
            raise HTTPException(
                status_code=503,
                detail="LLM service not initialized"
            )
        
        models = llm_service.list_models()
        
        return {
            "provider": "external_api",
            "base_url": settings.llm_base_url,
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "fastapi.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )

# Made with Bob
