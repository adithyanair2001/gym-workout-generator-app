"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # CORS Configuration
    allowed_origins: str = "http://localhost:5000,http://localhost:7500"
    
    # Frontend Configuration
    frontend_url: str = "http://localhost:7500"
    
    # ExerciseDB
    exercisedb_api_url: str = "https://oss.exercisedb.dev/api/v1/exercises"
    exercisedb_page_size: int = 100  # Number of exercises to fetch per page (max: 200)
    
    # Vector Database
    chroma_db_path: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM Configuration - Multiple Options
    # NOTE: Models are now loaded lazily (on-demand) to save memory
    # Set all to False to use dynamic model selection from UI

    # Option 1: Local GGUF models with LangChain
    use_gguf: bool = False
    gguf_model_path: str = ""
    gguf_n_ctx: int = 4096  # Context window size
    gguf_n_gpu_layers: int = 0  # Number of layers to offload to GPU (0 = CPU only)
    
    # Option 2 & 3: External LLM (Local servers or Public APIs)
    # llm_base_url       — used when running locally (no Docker)
    # llm_base_url_docker — used inside Docker/Colima; set in .env as
    #                       LLM_BASE_URL_DOCKER=http://host.docker.internal:PORT/v1
    # docker-compose.yml injects LLM_BASE_URL=<LLM_BASE_URL_DOCKER value> so
    # the app always reads llm_base_url regardless of runtime.
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_model: str = ""
    llm_api_key: str = ""  # API key for public LLM services (OpenAI, Anthropic, Groq, etc.)
    
    # Common LLM Parameters
    llm_temperature: float = 0.7
    llm_max_tokens: int = 32000
    
    # Logging
    log_level: str = "INFO"
    use_json_logging: bool = False  # Set to True for production JSON logs
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow unknown env vars (e.g. LLM_BASE_URL_DOCKER, FASTAPI_URL)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Made with Bob
