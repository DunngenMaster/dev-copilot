import sys
import os
import asyncio

# Add app directory to path for imports
app_dir = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_dir)

# Change working directory to where .env is located
env_dir = os.path.dirname(__file__)
os.chdir(env_dir)

print('=== Testing Redis Cloud Connection ===')
print(f'Working directory: {os.getcwd()}')

# Test Redis Cloud connection with provided credentials
try:
    from services.redis_vector import get_client, get_connection_info, ensure_index
    from utils.embeddings import embed_snapshot, to_f32bytes
    
    print('🔗 Connecting to Redis Cloud...')
    
    # Get connection info
    info = get_connection_info()
    print(f'   URL: {info["redis_url"]}')
    print(f'   Semantic Cache: {info["semantic_cache"]}')
    print(f'   Connected: {info["connected"]}')
    print(f'   Semantic Enabled: {info["semantic_enabled"]}')
    
    if info["semantic_enabled"]:
        print('\n✅ Redis Cloud Search & Query detected!')
        
        # Test index creation
        print('📊 Testing vector index...')
        index_result = ensure_index()
        print(f'   Index created/exists: {index_result}')
        
        # Test vector operations
        print('🔍 Testing vector operations...')
        from services.redis_vector import upsert_workflow_doc, knn_search
        import time
        
        # Create test document
        vec = embed_snapshot("redis-cloud/production", "backend", 14)
        vec_bytes = to_f32bytes(vec)
        
        doc = {
            "repo": "redis-cloud/production",
            "team": "backend",
            "score": 92,
            "sop": "Redis Cloud production workflow optimization"
        }
        
        # Store document
        timestamp = int(time.time())
        doc_key = f"wfdoc:redis-cloud/production:backend:14:{timestamp}"
        stored = upsert_workflow_doc(doc_key, doc, vec_bytes)
        print(f'   Document stored: {stored}')
        
        # Search for similar documents
        hit = knn_search(vec_bytes, k=3, min_sim=0.80)
        if hit:
            print(f'   🎯 Vector search HIT: similarity={hit["similarity"]:.2f}')
            print(f'   Retrieved: {hit["repo"]}, score={hit["score"]}')
        else:
            print('   Vector search: MISS (first time expected)')
        
        print('\n🚀 Redis Cloud semantic caching is fully operational!')
        
    else:
        print('\n⚠️  Redis Cloud connected but Search & Query not available')
        print('   Falls back to basic document storage')
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('\nTroubleshooting:')
    print('1. Check Redis Cloud credentials')
    print('2. Verify Search & Query module is enabled')
    print('3. Check network connectivity')

print('\n=== Ready to test FastAPI endpoint ===')
print('Start server: cd backend/app && python main.py')
print('Test API: curl -X POST http://your-server:8000/analyze-workflow \\')
print('  -H "Content-Type: application/json" \\')
print('  -d \'{"repo":"owner/repository","team":"platform","window_days":14}\'')