"""
Development environment configuration
"""
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    LOG_LEVEL = "DEBUG"
    
    # Relaxed rate limiting for development
    RATE_LIMIT_PER_MINUTE = 1000
