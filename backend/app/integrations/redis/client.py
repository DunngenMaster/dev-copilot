"""
Minimal Redis wrapper for dev-copilot operations.

Provides simple JSON storage, retrieval, and rolling history functionality.
"""

import json
import redis
from typing import Dict, Any, Optional, Union
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


def get_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance, connecting if necessary.
    
    Returns:
        Redis client or None if connection fails
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    settings = get_settings()
    
    if not settings.redis_url:
        logger.warning("REDIS_URL not configured - Redis operations will fail")
        return None
    
    try:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Test connection
        _redis_client.ping()
        logger.info(f"Connected to Redis at {settings.redis_url}")
        return _redis_client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_client = None
        return None


def get_json(key: str) -> Optional[Dict[str, Any]]:
    """
    Get JSON data from Redis.
    
    Args:
        key: Redis key to retrieve
        
    Returns:
        Parsed JSON dict or None if key doesn't exist or error occurs
    """
    client = get_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value is None:
            return None
        
        return json.loads(value)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Redis key '{key}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting JSON from Redis key '{key}': {e}")
        return None


def set_json(key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """
    Store JSON data in Redis with optional TTL.
    
    Args:
        key: Redis key to store under
        value: Dictionary to serialize and store
        ttl: Time to live in seconds (None for no expiration)
        
    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False
    
    try:
        json_value = json.dumps(value, default=str)  # default=str handles datetime objects
        
        if ttl:
            result = client.setex(key, ttl, json_value)
        else:
            result = client.set(key, json_value)
        
        return bool(result)
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing JSON for key '{key}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error setting JSON in Redis key '{key}': {e}")
        return False


def push_history(key: str, item: Dict[str, Any], max_len: int = 20) -> bool:
    """
    Push item to the front of a Redis list, maintaining max length.
    
    This creates a rolling history where new items are added to the front
    and old items beyond max_len are removed from the back.
    
    Args:
        key: Redis list key
        item: Dictionary to add to history
        max_len: Maximum number of items to keep in list
        
    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False
    
    try:
        # Serialize the item
        json_item = json.dumps(item, default=str)
        
        # Use pipeline for atomic operations
        pipe = client.pipeline()
        
        # Push new item to front of list
        pipe.lpush(key, json_item)
        
        # Trim list to max length
        pipe.ltrim(key, 0, max_len - 1)
        
        # Execute all operations
        pipe.execute()
        
        logger.debug(f"Added item to history '{key}', max_len={max_len}")
        return True
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing item for history key '{key}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error pushing to Redis history '{key}': {e}")
        return False


def get_history(key: str, limit: Optional[int] = None) -> list[Dict[str, Any]]:
    """
    Get history items from Redis list.
    
    Args:
        key: Redis list key
        limit: Maximum number of items to return (None for all)
        
    Returns:
        List of dictionaries from the history
    """
    client = get_client()
    if not client:
        return []
    
    try:
        if limit:
            items = client.lrange(key, 0, limit - 1)
        else:
            items = client.lrange(key, 0, -1)
        
        # Parse JSON items
        result = []
        for item in items:
            try:
                result.append(json.loads(item))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON item in history '{key}': {item[:50]}...")
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting history from Redis key '{key}': {e}")
        return []


def clear_key(key: str) -> bool:
    """
    Delete a key from Redis.
    
    Args:
        key: Redis key to delete
        
    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False
    
    try:
        result = client.delete(key)
        return bool(result)
        
    except Exception as e:
        logger.error(f"Error deleting Redis key '{key}': {e}")
        return False


def get_connection_info() -> Dict[str, Any]:
    """
    Get Redis connection information for debugging.
    
    Returns:
        Dictionary with connection status and details
    """
    settings = get_settings()
    client = get_client()
    
    info = {
        "redis_url": settings.redis_url,
        "connected": client is not None,
        "client_info": None
    }
    
    if client:
        try:
            # Get basic Redis info
            redis_info = client.info()
            info["client_info"] = {
                "redis_version": redis_info.get("redis_version"),
                "used_memory_human": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds")
            }
        except Exception as e:
            info["client_info"] = f"Error getting info: {e}"
    
    return info