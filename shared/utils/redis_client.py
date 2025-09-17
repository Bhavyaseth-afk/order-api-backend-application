"""
Redis client utilities for OrderAPI microservices.
"""
import redis
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling.
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Redis."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self._client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def publish(self, channel: str, message: Any) -> bool:
        """Publish message to Redis channel."""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            return bool(self._client.publish(channel, message))
        except Exception as e:
            logger.error(f"Redis PUBLISH error for channel {channel}: {e}")
            return False
    
    def subscribe(self, channels: list):
        """Subscribe to Redis channels."""
        try:
            pubsub = self._client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE error for channels {channels}: {e}")
            return None


# Global Redis client instance
_redis_client = None


def get_redis_client() -> RedisClient:
    """Get global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
