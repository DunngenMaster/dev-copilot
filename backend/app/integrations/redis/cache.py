import os
import json
import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import redis
from redis.exceptions import ConnectionError, TimeoutError


def embed_snapshot(repo: str, team: str, window_days: int) -> List[float]:
    """
    Generate a deterministic pseudo-vector for workflow snapshot caching.
    
    This creates a 32-dimensional vector based on the hash of input parameters.
    In production, this would be replaced with a real embedding model.
    
    Args:
        repo: Repository identifier (e.g., "owner/repo")
        team: Team name
        window_days: Analysis window in days
        
    Returns:
        List of 32 floats representing the snapshot embedding
    """
    # Create a deterministic hash from the inputs
    input_string = f"{repo}|{team}|{window_days}"
    hash_bytes = hashlib.sha256(input_string.encode('utf-8')).digest()
    
    # Convert hash bytes to 32 floats in range [0, 1]
    vector = []
    for i in range(32):
        # Take 4 bytes at a time to create float values
        byte_idx = (i * 4) % len(hash_bytes)
        byte_slice = hash_bytes[byte_idx:byte_idx + 4]
        
        # If we run out of bytes, pad with zeros
        if len(byte_slice) < 4:
            byte_slice += b'\x00' * (4 - len(byte_slice))
        
        # Convert 4 bytes to int, then normalize to [0, 1]
        int_val = int.from_bytes(byte_slice, byteorder='big')
        float_val = int_val / (2**32 - 1)  # Normalize to [0, 1]
        
        vector.append(float_val)
    
    return vector


class SemanticCache:
    """Redis-based semantic cache with in-memory fallback for vector similarity search."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}  # In-memory fallback
        self.use_redis = False
        
    def connect_from_env(self) -> bool:
        """
        Connect to Redis using REDIS_URL from environment variables.
        Falls back to in-memory storage if connection fails or env var missing.
        
        Returns:
            bool: True if Redis connection successful, False if using in-memory fallback
        """
        redis_url = os.getenv("REDIS_URL")
        
        if not redis_url:
            print("REDIS_URL not found in environment. Using in-memory cache fallback.")
            return False
            
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            print(f"Connected to Redis at {redis_url}")
            return True
            
        except (ConnectionError, TimeoutError, Exception) as e:
            print(f"Failed to connect to Redis: {e}. Using in-memory cache fallback.")
            self.redis_client = None
            self.use_redis = False
            return False
    
    def _cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vector1) != len(vector2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(a * a for a in vector2))
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)
    
    def search_snapshot(self, vector: List[float], k: int = 3, min_sim: float = 0.80) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the cache.
        
        Args:
            vector: Query vector to search for
            k: Maximum number of results to return
            min_sim: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of dictionaries containing 'key', 'similarity', and 'payload' for each match
        """
        if self.use_redis and self.redis_client:
            return self._search_redis(vector, k, min_sim)
        else:
            return self._search_memory(vector, k, min_sim)
    
    def _search_redis(self, vector: List[float], k: int, min_sim: float) -> List[Dict[str, Any]]:
        """Search for similar vectors in Redis."""
        try:
            # Get all keys with the cache prefix
            pattern = "semantic_cache:*"
            keys = self.redis_client.keys(pattern)
            
            results = []
            
            for key in keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        cached_item = json.loads(data)
                        cached_vector = cached_item.get("vector", [])
                        
                        similarity = self._cosine_similarity(vector, cached_vector)
                        
                        if similarity >= min_sim:
                            results.append({
                                "key": key.replace("semantic_cache:", ""),
                                "similarity": similarity,
                                "payload": cached_item.get("payload", {})
                            })
                            
                except json.JSONDecodeError:
                    continue
                    
            # Sort by similarity (descending) and return top k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:k]
            
        except Exception as e:
            print(f"Redis search failed: {e}. Falling back to memory search.")
            return self._search_memory(vector, k, min_sim)
    
    def _search_memory(self, vector: List[float], k: int, min_sim: float) -> List[Dict[str, Any]]:
        """Search for similar vectors in memory cache."""
        results = []
        
        for key, cached_item in self.memory_cache.items():
            cached_vector = cached_item.get("vector", [])
            
            similarity = self._cosine_similarity(vector, cached_vector)
            
            if similarity >= min_sim:
                results.append({
                    "key": key,
                    "similarity": similarity,
                    "payload": cached_item.get("payload", {})
                })
        
        # Sort by similarity (descending) and return top k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:k]
    
    def upsert_snapshot(self, key: str, vector: List[float], payload: Dict[str, Any]) -> bool:
        """
        Store or update a vector snapshot with associated payload.
        
        Args:
            key: Unique identifier for the snapshot
            vector: Vector representation
            payload: Associated data/metadata
            
        Returns:
            bool: True if successfully stored, False otherwise
        """
        data = {
            "vector": vector,
            "payload": payload
        }
        
        if self.use_redis and self.redis_client:
            return self._upsert_redis(key, data)
        else:
            return self._upsert_memory(key, data)
    
    def _upsert_redis(self, key: str, data: Dict[str, Any]) -> bool:
        """Store snapshot in Redis."""
        try:
            redis_key = f"semantic_cache:{key}"
            self.redis_client.set(redis_key, json.dumps(data))
            return True
            
        except Exception as e:
            print(f"Redis upsert failed: {e}. Falling back to memory storage.")
            return self._upsert_memory(key, data)
    
    def _upsert_memory(self, key: str, data: Dict[str, Any]) -> bool:
        """Store snapshot in memory cache."""
        try:
            self.memory_cache[key] = data
            return True
            
        except Exception as e:
            print(f"Memory upsert failed: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Clear all cached data."""
        if self.use_redis and self.redis_client:
            try:
                pattern = "semantic_cache:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                return True
            except Exception as e:
                print(f"Redis clear failed: {e}")
                
        # Clear memory cache
        self.memory_cache.clear()
        return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "backend": "redis" if self.use_redis else "memory",
            "connected": self.use_redis and self.redis_client is not None
        }
        
        if self.use_redis and self.redis_client:
            try:
                pattern = "semantic_cache:*"
                keys = self.redis_client.keys(pattern)
                stats["total_keys"] = len(keys)
            except Exception:
                stats["total_keys"] = "unknown"
        else:
            stats["total_keys"] = len(self.memory_cache)
            
        return stats


# Global cache instance
semantic_cache = SemanticCache()