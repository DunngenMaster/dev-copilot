"""Direct test of the full workflow with logging."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from services.postman_client import run_collection_or_stub
from services.redis_vector import rag_retrieve
from services.anthropic_client import generate_sop
from utils.embeddings import embed_snapshot, to_f32bytes

print("\n" + "="*70)
print("FULL WORKFLOW SIMULATION")
print("="*70)

# 1. Generate embedding
repo, team, days = "test/service", "backend", 14
vector = embed_snapshot(repo, team, days, dims=32)
vector_bytes = to_f32bytes(vector)
print(f"\n[OK] Generated embedding for {repo}/{team}/{days}")

# 2. Collect metrics
print("\n--- Step 1: Collect Metrics ---")
metrics = run_collection_or_stub(repo, team, days)
print(f"[OK] Metrics collected: {len(metrics)} top-level keys")

# 3. RAG retrieval
print("\n--- Step 2: RAG Retrieval ---")
rag_docs = rag_retrieve(vector_bytes, k=5)
print(f"[OK] RAG documents retrieved: {len(rag_docs)}")

# 4. Claude generation
print("\n--- Step 3: Claude Generation ---")
try:
    result = generate_sop(metrics, rag_docs)
    print(f"[OK] SUCCESS!")
    print(f"  - Bottlenecks: {len(result['bottlenecks'])}")
    for i, bn in enumerate(result['bottlenecks'][:3], 1):
        print(f"    {i}. {bn}")
    print(f"  - SOP length: {len(result['sop'])} chars")
    print(f"  - Summary: {result['summary'][:100]}...")
    
except Exception as e:
    print(f"[FAIL] FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
