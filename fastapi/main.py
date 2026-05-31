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
from fastapi.config import get_settings
from fastapi.middleware import RequestIDMiddleware
from fastapi.models.user_profile import UserProfile
from fastapi.models.workout_plan import WorkoutPlan
from fastapi.services.database_tools import DatabaseTools
from fastapi.services.exercisedb_client import ExerciseDBClient
from fastapi.services.gguf_service import GGUFService
from fastapi.services.llm_service import LLMService
from fastapi.services.mlx_agent_service import MLXAgentService
from fastapi.services.rag_pipeline import RAGPipeline
from fastapi.services.vector_store import VectorStoreService
from fastapi.utils.logging_config import RequestIDFilter, setup_structured_logging

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
        
        # Initialize LLM service based on configuration
        if settings.use_mlx:
            logger.info("=" * 60)
            logger.info("Using MLX local model (agent mode)")
            logger.info(f"Model: {settings.mlx_model_path}")
            logger.info("=" * 60)
            
            # Initialize database tools for MLX agent
            logger.info("Initializing database tools...")
            database_tools = DatabaseTools(vector_store)
            logger.info("Database tools initialized")
            
            # Initialize MLX agent service
            logger.info("Initializing MLX agent service...")
            mlx_agent = MLXAgentService(
                model_path=settings.mlx_model_path,
                database_tools=database_tools,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            logger.info("MLX agent service initialized")
            
            # For MLX agent, we don't use RAG pipeline
            rag_pipeline = None
            llm_service = None
            gguf_service = None
        elif settings.use_gguf:
            logger.info("=" * 60)
            logger.info("Using GGUF model with LangChain")
            logger.info(f"Model: {settings.gguf_model_path}")
            logger.info(f"Context: {settings.gguf_n_ctx}, GPU layers: {settings.gguf_n_gpu_layers}")
            logger.info("=" * 60)
            
            # Initialize GGUF service
            logger.info("Initializing GGUF service...")
            gguf_service = GGUFService(
                model_path=settings.gguf_model_path,
                n_ctx=settings.gguf_n_ctx,
                n_gpu_layers=settings.gguf_n_gpu_layers,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            logger.info("GGUF service initialized")
            
            # Initialize RAG pipeline with GGUF
            logger.info("Initializing RAG pipeline...")
            rag_pipeline = RAGPipeline(vector_store, gguf_service)
            logger.info("RAG pipeline initialized")
            
            mlx_agent = None
            database_tools = None
            llm_service = None
        else:
            logger.info("=" * 60)
            logger.info("Using external LLM API")
            logger.info(f"URL: {settings.llm_base_url}")
            logger.info(f"Model: {settings.llm_model}")
            if settings.llm_api_key:
                logger.info("API key: Configured ✓")
            logger.info("=" * 60)
            
            # Initialize LLM service with API key
            logger.info("Initializing LLM service...")
            llm_service = LLMService(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            logger.info("LLM service initialized (will connect on first use)")
            
            # Initialize RAG pipeline
            logger.info("Initializing RAG pipeline...")
            rag_pipeline = RAGPipeline(vector_store, llm_service)
            logger.info("RAG pipeline initialized")
            
            mlx_agent = None
            database_tools = None
            gguf_service = None
        
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


@app.post("/api/v1/generate", response_model=WorkoutPlan)
@limiter.limit("5/minute")  # Limit to 5 requests per minute per IP
async def generate_workout(request: Request, user_profile: UserProfile):
    """Generate personalized workout plan.
    
    Args:
        user_profile: User profile with fitness information
        
    Returns:
        Generated workout plan
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        settings = get_settings()
        logger.info(f"Received workout generation request for {user_profile.fitness_level.value} user")
        
        # Use MLX agent or RAG pipeline based on configuration
        if settings.use_mlx:
            # Validate MLX agent is initialized
            if not mlx_agent:
                raise HTTPException(
                    status_code=503,
                    detail="MLX agent not initialized. Please try again later."
                )
            
            logger.info("Generating workout plan with MLX agent...")
            # Generate with MLX agent
            raw_response = mlx_agent.generate_workout_plan(user_profile)
            
            # Parse JSON response
            workout_data = mlx_agent.parse_json_response(raw_response)
            
            # Convert to WorkoutPlan model directly
            from fastapi.models.workout_plan import WorkoutDay, Exercise
            
            workout_days = []
            for day_data in workout_data.get('workout_days', []):
                main_workout = []
                for ex_data in day_data.get('main_workout', []):
                    exercise = Exercise(
                        exercise_id=ex_data.get('exercise_id', ''),
                        name=ex_data.get('name', ''),
                        target_muscles=ex_data.get('target_muscles', []),
                        sets=ex_data.get('sets', 3),
                        reps=ex_data.get('reps', '8-12'),
                        rest_seconds=ex_data.get('rest_seconds', 60),
                        gif_url=ex_data.get('gif_url', ''),
                        instructions=ex_data.get('instructions', []),
                        notes=ex_data.get('notes')
                    )
                    main_workout.append(exercise)
                
                workout_day = WorkoutDay(
                    day_number=day_data.get('day_number', 1),
                    day_name=day_data.get('day_name', f"Day {day_data.get('day_number', 1)}"),
                    focus=day_data.get('focus', 'Full Body'),
                    warm_up=[],
                    main_workout=main_workout,
                    cool_down=[],
                    estimated_duration_minutes=day_data.get('estimated_duration_minutes', user_profile.workout_duration_minutes),
                    total_exercises=len(main_workout)
                )
                workout_days.append(workout_day)
            
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
                progression_notes=workout_data.get('progression_notes', 'Increase weight gradually as you get stronger'),
                nutrition_tips=workout_data.get('nutrition_tips')
            )
        else:
            # Validate RAG pipeline is initialized
            if not rag_pipeline:
                raise HTTPException(
                    status_code=503,
                    detail="RAG pipeline not initialized. Please try again later."
                )
            
            logger.info("Generating workout plan with RAG pipeline...")
            # Generate workout plan with traditional RAG
            workout_plan = await rag_pipeline.generate_workout_plan(user_profile)
        
        logger.info(f"Successfully generated workout plan with {len(workout_plan.workout_days)} days")
        return workout_plan
        
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
