"""
Structured logging configuration with request IDs
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from contextvars import ContextVar

# Context variable to store request ID across async calls
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format with request IDs.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get request ID from context
        request_id = request_id_var.get('')
        
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        if request_id:
            log_data['request_id'] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data)


def setup_structured_logging(log_level: str = "INFO", use_json: bool = False):
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting (True) or standard formatting (False)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            defaults={'request_id': 'N/A'}
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def set_request_id(request_id: str):
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def get_request_id() -> str:
    """Get the request ID from the current context."""
    return request_id_var.get('')


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to the log record."""
        record.request_id = get_request_id() or 'N/A'
        return True

# Made with Bob