"""
Configuration factory
"""
import os
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig

def get_config():
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "staging": ProductionConfig,  # Use production config for staging
    }
    
    return config_map.get(env, DevelopmentConfig)()
