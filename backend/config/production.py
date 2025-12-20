"""
Production environment configuration
"""
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    LOG_LEVEL = "WARNING"
    
    # Strict rate limiting for production
    RATE_LIMIT_PER_MINUTE = 60
    
    # Force HTTPS in production
    FORCE_HTTPS = True
    
    # Production CORS - should be overridden with actual domain
    CORS_ORIGINS = ["https://yourdomain.com"]
