import logging
from typing import Any, Dict

class ScraperError(Exception):

    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class NetworkError(ScraperError):
    """network-related issues"""
    pass

class ParseError(ScraperError):
    """in event parsing fails"""
    pass

def configure_logging():
    """
    configure logging with a standard format and level
    
    returns:
        logging.Logger: Configured logger
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)

#Global logger
logger = configure_logging()

def log_error(error: Exception, context: Dict[str, Any] = None):
    """
    log an error with optional context
    
    arguments:
        error (Exception): error to log
        context (Dict[str, Any], optional): Additional context information
    """
    error_details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
    }
    
    if context:
        error_details['context'] = context
    
    logger.error(f"Error occurred: {error_details}")