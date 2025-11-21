"""
Example usage of the SemanticCache for workflow analysis caching.

This demonstrates how to use the semantic cache to store and retrieve
workflow analysis results based on vector similarity.
"""

import os
from typing import List
from app.integrations.redis.cache import semantic_cache, embed_snapshot


def example_usage():
    """Demonstrate SemanticCache usage for workflow analysis."""
    
    # Set up environment (optional - will use in-memory if not set)
    # os.environ["REDIS_URL"] = "redis://localhost:6379"
    
    # Connect to cache (Redis or in-memory fallback)
    connected = semantic_cache.connect_from_env()
    print(f"Cache backend: {'Redis' if connected else 'In-memory'}")
    
    # Example: Cache a workflow analysis result
    repo = "owner/repo"
    team = "platform"
    window_days = 14
    
    # Generate deterministic vector for this workflow snapshot
    workflow_vector = embed_snapshot(repo, team, window_days)
    print(f"Generated vector (first 5 dims): {workflow_vector[:5]}")
    
    repo_key = f"{repo}-{team}-{window_days}d"
    
    # Workflow analysis payload
    analysis_payload = {
        "repo": "owner/repo",
        "team": "platform",
        "window_days": 14,
        "health_score": 73,
        "bottlenecks": [
            "41% of PRs wait >36h for first review",
            "18% issue reopen rate exceeds 10% threshold"
        ],
        "metrics": {
            "avg_time_to_first_review_h": 42.5,
            "avg_time_to_merge_h": 96.2,
            "unassigned_24h_rate": 0.12,
            "reopen_rate": 0.18,
            "stale_7d_ratio": 0.08
        },
        "timestamp": "2025-11-21T10:30:00Z"
    }
    
    # Store the analysis
    success = semantic_cache.upsert_snapshot(
        key=repo_key,
        vector=workflow_vector,
        payload=analysis_payload
    )
    print(f"Stored analysis: {success}")
    
    # Search for similar workflow patterns
    # Generate a slightly different vector (same repo/team, different window)
    similar_vector = embed_snapshot(repo, team, 7)  # Different window_days
    
    similar_results = semantic_cache.search_snapshot(
        vector=similar_vector,
        k=3,
        min_sim=0.50  # Lower threshold since deterministic vectors may be less similar
    )
    
    print(f"\nFound {len(similar_results)} similar workflow patterns:")
    for result in similar_results:
        print(f"- Key: {result['key']}")
        print(f"  Similarity: {result['similarity']:.3f}")
        print(f"  Health Score: {result['payload']['health_score']}")
        print(f"  Repo: {result['payload']['repo']}")
        print()
    
    # Get cache statistics
    stats = semantic_cache.get_cache_stats()
    print("Cache Stats:", stats)
    

def test_cache_miss_scenario():
    """Test scenario where no similar vectors are found."""
    
    # Very different parameters that should create a different vector
    different_vector = embed_snapshot("different/repo", "backend", 30)
    
    results = semantic_cache.search_snapshot(
        vector=different_vector,
        k=3,
        min_sim=0.80
    )
    
    print(f"Cache miss test - Found {len(results)} results (should be 0)")


def test_deterministic_vectors():
    """Test that the same inputs always generate the same vectors."""
    
    vector1 = embed_snapshot("owner/repo", "platform", 14)
    vector2 = embed_snapshot("owner/repo", "platform", 14)
    
    print(f"Deterministic test - Vectors equal: {vector1 == vector2}")
    print(f"Vector length: {len(vector1)}")
    print(f"Sample values: {vector1[:3]}")


if __name__ == "__main__":
    example_usage()
    test_cache_miss_scenario()
    test_deterministic_vectors()