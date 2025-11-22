"""
Embeddings utility for generating deterministic pseudo-vectors from workflow parameters.

This module provides functions for creating consistent vector representations
of workflow snapshots for semantic caching in Redis Stack.
"""

import hashlib
import struct
import array
from typing import List


def embed_snapshot(repo: str, team: str, window_days: int, dims: int = 128) -> List[float]:
    """
    Return deterministic pseudo-vector of given dims based on input hash.
    
    Creates a consistent vector representation by hashing the input parameters
    and converting the hash into a normalized float vector suitable for 
    cosine similarity search in Redis Stack.
    
    Args:
        repo: Repository name/identifier
        team: Team name/identifier  
        window_days: Analysis window in days
        dims: Vector dimensions (default: 32)
        
    Returns:
        List of float values representing the embedded vector
    """
    # Create deterministic input string
    input_string = f"{repo}|{team}|{window_days}"
    
    # Generate SHA-256 hash for consistency
    hash_bytes = hashlib.sha256(input_string.encode('utf-8')).digest()
    
    # Convert hash bytes to float vector
    vector = []
    
    for i in range(dims):
        # Use modular arithmetic to cycle through hash bytes
        byte_idx = (i * 4) % len(hash_bytes)
        byte_slice = hash_bytes[byte_idx:byte_idx + 4]
        
        # Pad with zeros if slice is shorter than 4 bytes
        if len(byte_slice) < 4:
            byte_slice += b'\x00' * (4 - len(byte_slice))
        
        # Convert 4 bytes to integer, then normalize to [0, 1]
        int_val = int.from_bytes(byte_slice, byteorder='big', signed=False)
        float_val = int_val / (2**32 - 1)
        
        vector.append(float_val)
    
    # Normalize vector for cosine similarity (unit vector)
    magnitude = sum(x * x for x in vector) ** 0.5
    if magnitude > 0:
        vector = [x / magnitude for x in vector]
    
    return vector


def to_f32bytes(vec: List[float]) -> bytes:
    """
    Pack float list into float32 bytes using array for better performance.
    
    Converts a list of Python floats into a packed binary representation
    suitable for storage in Redis Stack vector fields using array.array
    for better performance and memory efficiency.
    
    Args:
        vec: List of float values
        
    Returns:
        Packed bytes in float32 format
    """
    # Use array.array for efficient float32 packing
    float_array = array.array('f', vec)
    return float_array.tobytes()


def from_f32bytes(data: bytes, dims: int) -> List[float]:
    """
    Unpack float32 bytes back to float list.
    
    Utility function to convert packed binary data back to Python floats
    for debugging or analysis purposes.
    
    Args:
        data: Packed float32 bytes
        dims: Expected vector dimensions
        
    Returns:
        List of float values
    """
    return list(struct.unpack(f'<{dims}f', data))


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Utility function for testing and validation of vector similarities.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimensions")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(x * x for x in vec1) ** 0.5
    magnitude2 = sum(x * x for x in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)