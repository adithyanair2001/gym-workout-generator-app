"""Service factory for dynamic LLM service initialization."""
import logging
from typing import Union, Optional

from fastapiserver.models.model_config import ModelConfig, ModelType
from fastapiserver.services.llm_service import LLMService
from fastapiserver.services.gguf_service import GGUFService
from fastapiserver.services.vector_store import VectorStoreService
from fastapiserver.config import get_settings

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating LLM services based on configuration."""
    
    # Service cache for reusing instances with same configuration
    _service_cache = {}
    _cache_enabled = True
    
    @classmethod
    def enable_cache(cls, enabled: bool = True):
        """Enable or disable service caching.
        
        Args:
            enabled: Whether to enable caching
        """
        cls._cache_enabled = enabled
        if not enabled:
            cls.clear_cache()
    
    @classmethod
    def clear_cache(cls):
        """Clear the service cache and cleanup all cached services."""
        logger.info(f"Clearing service cache with {len(cls._service_cache)} services")
        cls._service_cache.clear()
        logger.info("Service cache cleared")

    @classmethod
    def cleanup_service(cls, cache_key: str):
        """Cleanup and remove a specific service from cache.

        Args:
            cache_key: Cache key of the service to cleanup
        """
        if cache_key in cls._service_cache:
            del cls._service_cache[cache_key]
            logger.info(f"Removed service from cache: {cache_key}")
    
    @classmethod
    def _get_cache_key(cls, model_config: ModelConfig) -> str:
        """Generate cache key from model configuration.

        Args:
            model_config: Model configuration

        Returns:
            Cache key string
        """
        if model_config.model_type == ModelType.GGUF:
            return f"gguf:{model_config.gguf_model_path}:{model_config.gguf_n_ctx}:{model_config.gguf_n_gpu_layers}"
        else:
            # For API-based services
            return f"{model_config.model_type.value}:{model_config.llm_base_url}:{model_config.llm_model}:{model_config.temperature}"
    
    @classmethod
    def create_service(
        cls,
        model_config: Optional[ModelConfig],
        vector_store: VectorStoreService,
        use_cache: bool = True
    ) -> Union[GGUFService, LLMService]:
        """Create appropriate LLM service based on configuration.
        
        Args:
            model_config: Model configuration (None to use .env defaults)
            vector_store: Vector store service instance
            use_cache: Whether to use cached service if available
            
        Returns:
            Initialized LLM service instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        # If no config provided, use .env defaults
        if model_config is None:
            logger.info("No model config provided, using .env defaults")
            return cls._create_from_env(vector_store)
        
        # Check cache if enabled
        if use_cache and cls._cache_enabled:
            cache_key = cls._get_cache_key(model_config)
            if cache_key in cls._service_cache:
                logger.info(f"Using cached service for {model_config.model_type.value}")
                return cls._service_cache[cache_key]
        
        # Create new service based on type
        logger.info(f"Creating new {model_config.model_type.value} service")

        if model_config.model_type == ModelType.GGUF:
            service = cls._create_gguf_service(model_config)
        else:
            service = cls._create_api_service(model_config)
        
        # Cache the service
        if use_cache and cls._cache_enabled:
            cache_key = cls._get_cache_key(model_config)
            cls._service_cache[cache_key] = service
            logger.info(f"Cached service with key: {cache_key}")
        
        return service
    
    @classmethod
    def _create_from_env(cls, vector_store: VectorStoreService) -> Union[GGUFService, LLMService]:
        """Create service from .env configuration.

        Args:
            vector_store: Vector store service instance

        Returns:
            Initialized LLM service instance
        """
        settings = get_settings()

        if settings.use_gguf:
            logger.info("Creating GGUF service from .env configuration")
            return GGUFService(
                model_path=settings.gguf_model_path,
                n_ctx=settings.gguf_n_ctx,
                n_gpu_layers=settings.gguf_n_gpu_layers,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
        else:
            logger.info("Creating LLM service from .env configuration")
            model = settings.llm_model
            if not model or model in ("local-model", ""):
                model = cls._resolve_model(settings.llm_base_url, settings.llm_api_key)
            return LLMService(
                base_url=settings.llm_base_url,
                model=model,
                api_key=settings.llm_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
    
    @classmethod
    def _create_gguf_service(cls, config: ModelConfig) -> GGUFService:
        """Create GGUF service.
        
        Args:
            config: Model configuration
            
        Returns:
            Initialized GGUF service
        """
        if not config.gguf_model_path:
            raise ValueError("gguf_model_path is required for GGUF model")
        
        return GGUFService(
            model_path=config.gguf_model_path,
            n_ctx=config.gguf_n_ctx or 4096,
            n_gpu_layers=config.gguf_n_gpu_layers or 0,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    
    @classmethod
    def _create_api_service(cls, config: ModelConfig) -> LLMService:
        """Create API-based LLM service.
        
        Args:
            config: Model configuration
            
        Returns:
            Initialized LLM service
        """
        if not config.llm_base_url:
            raise ValueError("llm_base_url is required for API-based models")
        
        # Set default base URLs for public APIs if not provided
        if config.model_type == ModelType.OPENAI and not config.llm_base_url:
            config.llm_base_url = "https://api.openai.com/v1"
        elif config.model_type == ModelType.ANTHROPIC and not config.llm_base_url:
            config.llm_base_url = "https://api.anthropic.com/v1"
        elif config.model_type == ModelType.GROQ and not config.llm_base_url:
            config.llm_base_url = "https://api.groq.com/openai/v1"
        
        model = config.llm_model
        if not model or model in ("local-model", ""):
            model = cls._resolve_model(config.llm_base_url, config.llm_api_key or "")
        return LLMService(
            base_url=config.llm_base_url,
            model=model,
            api_key=config.llm_api_key or "",
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

    @classmethod
    def _resolve_model(cls, base_url: str, api_key: str = "") -> str:
        """Fetch the first available model from the server.

        Called when no model name is configured, so the server is queried
        at runtime and the first model ID is used automatically.

        Args:
            base_url: OpenAI-compatible base URL (e.g. http://host:1234/v1)
            api_key:  Optional API key for the request

        Returns:
            Model ID string, or 'local-model' as a last-resort fallback
        """
        import requests as _requests
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            resp = _requests.get(f"{base_url}/models", headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if data:
                model_id = data[0]["id"]
                logger.info(f"Auto-resolved model from {base_url}: {model_id}")
                return model_id
            logger.warning(f"No models returned from {base_url}, falling back to 'local-model'")
        except Exception as e:
            logger.warning(f"Could not auto-resolve model from {base_url}: {e}. Falling back to 'local-model'")
        return "local-model"


# Made with Bob