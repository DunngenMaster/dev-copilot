"""
Redis Cloud vector operations for semantic workflow caching.

This module provides high-level functions for managing workflow documents
in Redis Cloud with vector similarity search capabilities using FT.SEARCH.
Supports SSL connections and graceful fallbacks.
"""

import redis
import logging
import struct
import math
from typing import Dict, Any, List, Optional, Tuple
from core.config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None
_semantic_enabled: bool = False


def get_client() -> redis.Redis:
    """
    Get Redis Cloud client instance with SSL support.
    
    Returns:
        Redis client configured for Redis Cloud operations
        
    Raises:
        ConnectionError: If unable to connect to Redis Cloud
    """
    global _redis_client, _semantic_enabled
    
    if _redis_client is not None:
        return _redis_client
    
    settings = get_settings()
    
    if not settings.redis_url:
        raise ConnectionError("REDIS_URL not configured")
    
    try:
        # Determine SSL from URL
        use_ssl = settings.redis_url.startswith('rediss://')
        
        if use_ssl:
            # For SSL connections (rediss://)
            _redis_client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=False,  # Keep binary for vector data
                socket_timeout=10,
                socket_connect_timeout=10,
                ssl_cert_reqs=None
            )
        else:
            # For regular connections (redis://)
            _redis_client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=False,
                socket_timeout=10,
                socket_connect_timeout=10
            )
        
        # Test connection
        _redis_client.ping()
        
        # Check if semantic cache (Search & Query) is available
        try:
            _redis_client.execute_command("FT._LIST")
            _semantic_enabled = True
            logger.info("Semantic cache enabled = True")
        except redis.ResponseError as e:
            if "unknown command" in str(e).lower():
                _semantic_enabled = False
                logger.info("Fallback to key-cache mode - Search & Query not available")
            else:
                raise
        
        logger.info(f"Connected to Redis at {settings.redis_url}")
        return _redis_client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise ConnectionError(f"Redis connection failed: {e}")


def ensure_index() -> bool:
    """
    Create the idx_workflows vector index if it doesn't exist.
    
    Creates a Redis Cloud FT.CREATE index for workflow documents with:
    - 32-dimensional float32 vectors
    - COSINE distance metric  
    - HNSW algorithm for fast approximate search
    - Prefix 'wfdoc:' for document organization
    
    Returns:
        True if index was created or already exists, False if not available
    """
    global _semantic_enabled
    
    # Ensure client is connected and semantic capabilities are checked
    client = get_client()
    
    if not _semantic_enabled:
        logger.info("Semantic cache disabled - skipping index creation")
        return False
    
    try:
        # Check if index already exists
        try:
            info = client.execute_command("FT.INFO", "idx_workflows")
            logger.info("Vector index 'idx_workflows' already exists")
            return True
        except redis.ResponseError as e:
            if "Unknown index name" not in str(e) and "unknown command" not in str(e) and "no such index" not in str(e):
                logger.error(f"Error checking index: {e}")
                raise
            # Index doesn't exist or FT commands not available
        
        # Create the vector index
        create_cmd = [
            "FT.CREATE", "idx_workflows",
            "ON", "HASH",
            "PREFIX", "1", "wfdoc:",
            "SCHEMA",
            "repo", "TAG",
            "team", "TAG", 
            "score", "NUMERIC", "SORTABLE",
            "sop", "TEXT",
            "embedding", "VECTOR", "HNSW", "6",
            "TYPE", "FLOAT32",
            "DIM", "32", 
            "DISTANCE_METRIC", "COSINE"
        ]
        
        result = client.execute_command(*create_cmd)
        logger.info(f"Created vector index 'idx_workflows': {result}")
        return True
        
    except redis.ResponseError as e:
        if "Index already exists" in str(e):
            logger.info("Vector index 'idx_workflows' already exists")
            return True
        elif "unknown command" in str(e):
            _semantic_enabled = False
            logger.warning("Search & Query not available - disabling semantic cache")
            return False
        else:
            logger.error(f"Failed to create vector index: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error creating vector index: {e}")
        return False


def upsert_workflow_doc(key: str, payload: Dict[str, Any], vector_bytes: bytes) -> bool:
    """
    Insert or update a workflow document in Redis Stack.
    
    Stores workflow analysis results as a Redis hash with vector embedding
    for semantic similarity search.
    
    Args:
        key: Document key (should start with 'wfdoc:')
        payload: Document fields (repo, team, score, sop)
        vector_bytes: Packed float32 vector bytes
        
    Returns:
        True if operation successful
        
    Raises:
        Exception: If document storage fails
    """
    client = get_client()
    
    try:
        # Prepare hash fields
        doc_fields = {
            "repo": payload.get("repo", ""),
            "team": payload.get("team", ""),
            "score": str(payload.get("score", 0)),  # Store as string for Redis
            "sop": payload.get("sop", ""),
            "embedding": vector_bytes  # Binary vector data
        }
        
        # Store document as Redis hash
        result = client.hset(key, mapping=doc_fields)
        
        logger.info(f"Stored workflow document: {key}")
        logger.debug(f"Document fields: repo={payload.get('repo')}, team={payload.get('team')}, score={payload.get('score')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to store workflow document {key}: {e}")
        raise


def knn_search(vector_bytes: bytes, k: int = 3, min_sim: float = 0.80) -> Optional[Dict[str, Any]]:
    """
    Perform k-nearest neighbor search on workflow vectors.
    
    Uses Redis Cloud FT.SEARCH with vector similarity to find the most
    similar workflow documents based on cosine distance.
    
    Args:
        vector_bytes: Query vector as packed float32 bytes
        k: Number of nearest neighbors to return
        min_sim: Minimum similarity threshold (0.80 = 80%)
        
    Returns:
        Dictionary with best match data and similarity, or None if no good matches
        
    Format:
        {
            "repo": str,
            "team": str, 
            "score": int,
            "sop": str,
            "similarity": float,
            "key": str
        }
    """
    global _semantic_enabled
    
    if not _semantic_enabled:
        logger.info("Semantic search disabled - returning None")
        return None
        
    client = get_client()
    
    try:
        # Build FT.SEARCH query for vector similarity
        search_cmd = [
            "FT.SEARCH", "idx_workflows",
            f"*=>[KNN {k} @embedding $B AS distance]",
            "PARAMS", "2",
            "B", vector_bytes,
            "SORTBY", "distance",
            "DIALECT", "2",
            "LIMIT", "0", str(k),
            "RETURN", "6", "repo", "team", "score", "sop", "distance", "__key"
        ]
        
        result = client.execute_command(*search_cmd)
        
        # Parse search results
        if not result or len(result) < 2:
            logger.info("KNN search: No documents found")
            return None
            
        # Result format: [count, doc1_key, doc1_fields, doc2_key, doc2_fields, ...]
        doc_count = result[0]
        if doc_count == 0:
            logger.info("KNN search: No matching documents")
            return None
        
        # Extract first (best) result
        best_key = result[1].decode() if isinstance(result[1], bytes) else result[1]
        best_fields = result[2]
        
        # Parse field data (list of [field_name, field_value, ...])
        field_dict = {}
        for i in range(0, len(best_fields), 2):
            field_name = best_fields[i].decode() if isinstance(best_fields[i], bytes) else best_fields[i]
            field_value = best_fields[i + 1]
            if isinstance(field_value, bytes):
                # Skip binary embedding field in results
                if field_name != "embedding":
                    field_dict[field_name] = field_value.decode()
            else:
                field_dict[field_name] = field_value
        
        # Calculate similarity from distance (similarity = 1 - distance)
        distance = float(field_dict.get("distance", 1.0))
        similarity = max(0.0, 1.0 - distance)
        
        logger.info(f"KNN search similarity={similarity:.2f}")
        
        # Check similarity threshold
        if similarity < min_sim:
            logger.info(f"KNN search: Best similarity {similarity:.2f} below threshold {min_sim}")
            return None
            
        # Build result
        result_doc = {
            "repo": field_dict.get("repo", ""),
            "team": field_dict.get("team", ""),
            "score": int(field_dict.get("score", 0)),
            "sop": field_dict.get("sop", ""),
            "similarity": similarity,
            "key": best_key
        }
        
        logger.info("CACHE HIT")
        logger.info(f"Retrieved document: {best_key}")
        
        return result_doc
        
    except redis.ResponseError as e:
        if "unknown command" in str(e):
            logger.warning("FT.SEARCH not available - semantic search disabled")
            _semantic_enabled = False
            return None
        logger.error(f"KNN search failed: {e}")
        return None
    except Exception as e:
        logger.error(f"KNN search failed: {e}")
        return None


def is_semantic_enabled() -> bool:
    """
    Check if semantic cache is enabled.
    
    Returns:
        True if semantic vector search is available
    """
    global _semantic_enabled
    return _semantic_enabled


def get_connection_info() -> Dict[str, Any]:
    """
    Get Redis connection information for debugging.
    
    Returns:
        Dictionary with connection status and details
    """
    settings = get_settings()
    
    # Test connection by calling get_client()
    connected = False
    semantic_enabled = False
    client_info = None
    
    try:
        client = get_client()
        connected = client.ping()
        semantic_enabled = _semantic_enabled
        
        # Get basic Redis info
        redis_info = client.info()
        client_info = {
            "redis_version": redis_info.get("redis_version"),
            "used_memory_human": redis_info.get("used_memory_human"),
            "connected_clients": redis_info.get("connected_clients"),
            "uptime_in_seconds": redis_info.get("uptime_in_seconds")
        }
    except Exception as e:
        client_info = f"Error getting info: {e}"
    
    info = {
        "redis_url": settings.redis_url,
        "semantic_cache": settings.semantic_cache,
        "vector_dims": settings.vector_dims,
        "connected": connected,
        "semantic_enabled": semantic_enabled,
        "client_info": client_info
    }

    return info
    """
    Get statistics about the workflow vector index.
    
    Returns:
        Dictionary with index statistics for monitoring
    """
    client = get_client()
    
    try:
        info = client.execute_command("FT.INFO", "idx_workflows")
        
        # Parse info response (list of [key, value, key, value, ...])
        stats = {}
        for i in range(0, len(info), 2):
            key = info[i].decode() if isinstance(info[i], bytes) else info[i]
            value = info[i + 1]
            if isinstance(value, bytes):
                value = value.decode()
            stats[key] = value
            
        return {
            "index_name": "idx_workflows",
            "num_docs": stats.get("num_docs", 0),
            "max_doc_id": stats.get("max_doc_id", 0),
            "num_terms": stats.get("num_terms", 0),
            "index_size_mb": float(stats.get("inverted_sz_mb", 0)),
            "vector_index_size_mb": float(stats.get("vector_index_sz_mb", 0))
        }
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        return {"error": str(e)}


def clear_all_docs() -> int:
    """
    Clear all workflow documents from the index (for testing).
    
    Returns:
        Number of documents deleted
    """
    client = get_client()
    
    try:
        # Get all document keys with wfdoc: prefix
        keys = client.keys("wfdoc:*")
        
        if not keys:
            return 0
            
        # Delete all documents
        deleted = client.delete(*keys)
        logger.info(f"Cleared {deleted} workflow documents")
        
        return deleted
        
    except Exception as e:
        logger.error(f"Failed to clear documents: {e}")
        return 0


def rag_retrieve(vector_bytes: bytes, k: int = 5) -> List[str]:
    """
    Retrieve top-k similar SOP documents for RAG context.
    
    Args:
        vector_bytes: Query vector as packed float32 bytes
        k: Number of documents to retrieve
        
    Returns:
        List of SOP text snippets (up to k items)
    """
    global _semantic_enabled
    
    if not _semantic_enabled:
        logger.info("RAG retrieve: semantic search disabled")
        return []
    
    client = get_client()
    
    try:
        # Search for similar workflow documents
        search_cmd = [
            "FT.SEARCH", "idx_workflows",
            f"*=>[KNN {k} @embedding $B AS distance]",
            "PARAMS", "2",
            "B", vector_bytes,
            "SORTBY", "distance",
            "DIALECT", "2",
            "LIMIT", "0", str(k),
            "RETURN", "2", "sop", "distance"
        ]
        
        result = client.execute_command(*search_cmd)
        
        if not result or len(result) < 2:
            return []
        
        # Parse results: [count, [key, [field, value, ...]], ...]
        docs = []
        results_list = result[1:]  # Skip count
        
        for item in results_list:
            if isinstance(item, list) and len(item) > 1:
                fields = item[1]
                # Extract sop field
                for i in range(0, len(fields), 2):
                    field_name = fields[i].decode() if isinstance(fields[i], bytes) else fields[i]
                    if field_name == "sop" and i + 1 < len(fields):
                        sop_text = fields[i + 1]
                        if isinstance(sop_text, bytes):
                            sop_text = sop_text.decode()
                        if sop_text and len(sop_text) > 10:
                            docs.append(str(sop_text))
                        break
        
        logger.info(f"RAG retrieve: found {len(docs)} relevant documents")
        return docs
        
    except Exception as e:
        logger.warning(f"RAG retrieve failed: {e}")
        return []