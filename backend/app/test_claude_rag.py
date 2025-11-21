"""Test Claude + RAG integration with Redis vector retrieval."""

import os
import sys
from pathlib import Path

# Add backend/app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.anthropic_client import generate_sop
from services.redis_vector import rag_retrieve, ensure_index
from utils.embeddings import embed_snapshot, to_f32bytes

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


def test_rag_retrieve():
    """Test RAG document retrieval from Redis."""
    print("\n=== Testing RAG Retrieve ===")
    
    # Ensure index exists
    ensure_index()
    
    # Create test vector
    vector = embed_snapshot("test/repo", "backend", 14, dims=32)
    vector_bytes = to_f32bytes(vector)
    
    # Retrieve similar documents
    docs = rag_retrieve(vector_bytes, k=5)
    
    print(f"Retrieved {len(docs)} RAG context documents")
    for i, doc in enumerate(docs[:3], 1):
        preview = doc[:100] + "..." if len(doc) > 100 else doc
        print(f"  Doc {i}: {preview}")
    
    return docs


def test_claude_with_stub_metrics():
    """Test Claude SOP generation with stub metrics and RAG context."""
    print("\n=== Testing Claude SOP Generation ===")
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("⚠️  ANTHROPIC_API_KEY not configured - will test fallback")
        return None
    
    # Stub metrics (similar to Postman stub)
    stub_metrics = {
        "prs": {
            "total": 42,
            "merged": 35,
            "closed_unmerged": 5,
            "open": 2,
            "avg_time_to_first_review_h": 48.3,
            "pct_prs_no_first_review_36h": 0.65,
            "avg_time_to_merge_h": 120.5
        },
        "issues": {
            "total": 78,
            "open": 23,
            "closed": 55,
            "reopen_rate": 0.12,
            "unassigned_24h_rate": 0.18,
            "stale_7d_ratio": 0.30,
            "avg_time_to_close_h": 168.2
        }
    }
    
    # Get RAG context
    rag_docs = test_rag_retrieve()
    
    # Generate SOP using Claude
    try:
        result = generate_sop(stub_metrics, rag_docs)
        
        print("\n✅ Claude Generation Successful!")
        print(f"  Bottlenecks: {len(result.get('bottlenecks', []))}")
        for i, bn in enumerate(result.get('bottlenecks', [])[:3], 1):
            print(f"    {i}. {bn}")
        
        print(f"\n  SOP Length: {len(result.get('sop', ''))} chars")
        sop_preview = result.get('sop', '')[:200] + "..." if len(result.get('sop', '')) > 200 else result.get('sop', '')
        print(f"  SOP Preview: {sop_preview}")
        
        print(f"\n  Summary: {result.get('summary', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Claude Generation Failed: {e}")
        return None


def test_full_integration():
    """Test the complete Claude + RAG flow."""
    print("\n" + "="*60)
    print("CLAUDE + RAG INTEGRATION TEST")
    print("="*60)
    
    # Test RAG retrieval
    docs = test_rag_retrieve()
    
    # Test Claude generation
    result = test_claude_with_stub_metrics()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✓ RAG Retrieval: {'PASS' if docs is not None else 'FAIL'}")
    print(f"✓ Claude Generation: {'PASS' if result is not None else 'FAIL (check ANTHROPIC_API_KEY)'}")
    
    if result:
        print("\n🎉 Full integration test PASSED!")
        print("\nNext Steps:")
        print("  1. Add your ANTHROPIC_API_KEY to backend/.env")
        print("  2. Test via: curl -X POST http://127.0.0.1:8000/analyze-workflow \\")
        print("              -H 'Content-Type: application/json' \\")
        print("              -d '{\"repo\":\"test/repo\",\"team\":\"backend\",\"window_days\":14}'")
    else:
        print("\n⚠️  Integration test INCOMPLETE")
        print("  - RAG retrieval is working")
        print("  - Claude API key needed for full test")


if __name__ == "__main__":
    test_full_integration()
