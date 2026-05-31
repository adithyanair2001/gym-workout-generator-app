"""
Request ID middleware for FastAPI
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapiserver.utils.logging_config import generate_request_id, set_request_id
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add request ID.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with X-Request-ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID') or generate_request_id()
        
        # Set request ID in context for logging
        set_request_id(request_id)
        
        # Add to request state for access in handlers
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={'request_id': request_id}
        )
        
        # Process request
        response: Response = await call_next(request)
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id
        
        # Log response
        logger.info(
            f"Response {response.status_code}",
            extra={'request_id': request_id}
        )
        
        return response

# Made with Bob