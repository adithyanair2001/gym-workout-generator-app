"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # ExerciseDB
    exercisedb_api_url: str = "https://oss.exercisedb.dev/api/v1/exercises"
    exercisedb_page_size: int = 100  # Number of exercises to fetch per page (max: 200)
    
    # Vector Database
    chroma_db_path: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM Configuration
    use_mlx: bool = True  # Use MLX local model instead of LM Studio
    mlx_model_path: str = "/Users/adithyanair/.lmstudio/models/mlx-community/Qwen3.5-4B-MLX-4bit"  # Path to MLX model (Qwen3.5 4B - newer, better performance)
    
    # LM Studio Configuration (only used if use_mlx=False)
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_model: str = "local-model"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 16430  # Optimized for Llama-3.2-3B context window
    lm_studio_api_key: str = "lm-studio"  # API key for LM Studio (default for local)
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Made with Bob
