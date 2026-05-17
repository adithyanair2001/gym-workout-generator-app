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
    
    # LLM Configuration - Multiple Options
    # Option 1: Local MLX models (recommended for Mac)
    use_mlx: bool = True
    mlx_model_path: str = "/Users/adithyanair/.lmstudio/models/mlx-community/Qwen3.5-4B-MLX-4bit"
    
    # Option 2: Local GGUF models with LangChain
    use_gguf: bool = False
    gguf_model_path: str = ""
    gguf_n_ctx: int = 4096  # Context window size
    gguf_n_gpu_layers: int = 0  # Number of layers to offload to GPU (0 = CPU only)
    
    # Option 3 & 4: External LLM (Local servers or Public APIs)
    # For local servers (LM Studio, OLLAMA): http://127.0.0.1:PORT/v1
    # For OpenAI: https://api.openai.com/v1
    # For Anthropic: https://api.anthropic.com/v1
    # For Groq: https://api.groq.com/openai/v1
    llm_base_url: str = "http://127.0.0.1:8001/v1"
    llm_model: str = "local-model"
    llm_api_key: str = ""  # API key for public LLM services (OpenAI, Anthropic, Groq, etc.)
    
    # Common LLM Parameters
    llm_temperature: float = 0.7
    llm_max_tokens: int = 32000
    
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
