"""Model configuration data models for dynamic LLM selection."""
from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum


class ModelType(str, Enum):
    """Supported model types."""
    MLX = "mlx"
    OMLX = "omlx"
    GGUF = "gguf"
    LOCAL_SERVER = "local_server"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class ModelConfig(BaseModel):
    """Configuration for LLM model selection."""
    
    model_type: ModelType = Field(..., description="Type of model to use")
    
    # MLX Configuration
    mlx_model_path: Optional[str] = Field(None, description="Path to MLX model directory")
    
    # OMLX Configuration
    llm_base_url: Optional[str] = Field(None, description="Base URL for LLM API")
    llm_model: Optional[str] = Field(None, description="Model name/identifier")
    llm_api_key: Optional[str] = Field(None, description="API key for authentication")
    
    # GGUF Configuration
    gguf_model_path: Optional[str] = Field(None, description="Path to GGUF model file")
    gguf_n_ctx: Optional[int] = Field(4096, description="Context window size", ge=512, le=32768)
    gguf_n_gpu_layers: Optional[int] = Field(0, description="Number of GPU layers", ge=0, le=100)
    
    # Common LLM Parameters
    temperature: float = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    max_tokens: int = Field(32000, description="Maximum tokens to generate", ge=100, le=100000)
    
    @validator('mlx_model_path')
    def validate_mlx_path(cls, v, values):
        """Validate MLX model path is provided when model_type is MLX."""
        if values.get('model_type') == ModelType.MLX and not v:
            raise ValueError("mlx_model_path is required when model_type is 'mlx'")
        return v
    
    @validator('gguf_model_path')
    def validate_gguf_path(cls, v, values):
        """Validate GGUF model path is provided when model_type is GGUF."""
        if values.get('model_type') == ModelType.GGUF and not v:
            raise ValueError("gguf_model_path is required when model_type is 'gguf'")
        return v
    
    @validator('llm_base_url')
    def validate_llm_url(cls, v, values):
        """Validate LLM base URL is provided for API-based models."""
        model_type = values.get('model_type')
        if model_type in [ModelType.OMLX, ModelType.LOCAL_SERVER, ModelType.OPENAI, 
                         ModelType.ANTHROPIC, ModelType.GROQ] and not v:
            raise ValueError(f"llm_base_url is required when model_type is '{model_type.value}'")
        return v
    
    @validator('llm_model')
    def validate_llm_model(cls, v, values):
        """Validate model name is provided for API-based models."""
        model_type = values.get('model_type')
        if model_type in [ModelType.OMLX, ModelType.OPENAI, ModelType.ANTHROPIC, ModelType.GROQ] and not v:
            raise ValueError(f"llm_model is required when model_type is '{model_type.value}'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_type": "omlx",
                "llm_base_url": "http://127.0.0.1:8000/v1",
                "llm_model": "mlx-community/Qwen3.5-4B-MLX-4bit",
                "llm_api_key": "your-api-key",
                "temperature": 0.7,
                "max_tokens": 32000
            }
        }


# Made with Bob