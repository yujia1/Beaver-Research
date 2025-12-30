import os
import redis
import json
import logging
from typing import Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration from environment variables
# Prioritize Railway provided variables (REDISHOST, REDISPORT, REDISPASSWORD)
REDIS_HOST = os.getenv("REDISHOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDISPORT", os.getenv("REDIS_PORT", "6379")))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDISPASSWORD", os.getenv("REDIS_PASSWORD", None))

class RedisClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        """Initialize the Redis client with error handling"""
        try:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=1,  # Short timeout for fail-open
                socket_timeout=1
            )
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Caching disabled. Error: {str(e)}")
            self._client = None

    def get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if cache miss or Redis error."""
        if not self._client:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get error for key {key}: {str(e)}")
            return None

    def set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (seconds). Returns False on error."""
        if not self._client:
            return False
            
        try:
            serialized_value = json.dumps(value)
            return self._client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"Redis set error for key {key}: {str(e)}")
            return False

    def delete_cache(self, key_pattern: str) -> bool:
        """Delete keys matching pattern. Returns False on error."""
        if not self._client:
            return False
            
        try:
            # If plain key
            if '*' not in key_pattern:
                return self._client.delete(key_pattern) > 0
            
            # If pattern (use scan_iter for performance)
            keys = list(self._client.scan_iter(match=key_pattern))
            if keys:
                return self._client.delete(*keys) > 0
            return True
        except Exception as e:
            logger.warning(f"Redis delete error for pattern {key_pattern}: {str(e)}")
            return False

    def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel"""
        if not self._client:
            return False
        try:
            return self._client.publish(channel, message)
        except Exception as e:
            logger.warning(f"Redis publish error: {e}")
            return False

    def get_pubsub(self):
        """Get pubsub object"""
        if not self._client:
            return None
        return self._client.pubsub()

# Global instance
redis_client = RedisClient()
