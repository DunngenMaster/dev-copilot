#!/usr/bin/env python3
"""Quick setup script for hackathon demo."""

import subprocess
import sys
import os

def main():
    print("🚀 Setting up hackathon demo environment...\n")
    
    # 1. Clear Redis cache
    print("1️⃣ Clearing Redis cache...")
    try:
        from app.services.redis_vector import clear_all_docs
        deleted = clear_all_docs()
        print(f"   ✓ Deleted {deleted} documents\n")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}\n")
    
    # 2. Rebuild vector index
    print("2️⃣ Rebuilding vector index (128 dimensions)...")
    try:
        from app.services.redis_vector import ensure_index
        ensure_index()
        print("   ✓ Index created\n")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}\n")
    
    # 3. Check environment variables
    print("3️⃣ Checking environment variables...")
    required_vars = [
        "REDIS_URL",
        "ANTHROPIC_API_KEY",
        "SANITY_PROJECT_ID",
        "SANITY_TOKEN",
        "GITHUB_TOKEN"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            print(f"   ❌ Missing: {var}")
        else:
            print(f"   ✓ {var} configured")
    
    if missing:
        print(f"\n⚠️  Please add missing variables to .env file\n")
    else:
        print("\n✅ All environment variables configured\n")
    
    # 4. Test Newman
    print("4️⃣ Testing Newman CLI...")
    try:
        result = subprocess.run(
            ["newman", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✓ Newman {result.stdout.strip()} installed\n")
        else:
            print("   ❌ Newman not working\n")
    except FileNotFoundError:
        print("   ❌ Newman not installed - run: npm install -g newman\n")
    except Exception as e:
        print(f"   ⚠️  Error: {e}\n")
    
    # 5. Summary
    print("=" * 50)
    print("✅ Setup complete! Next steps:")
    print("   1. Start backend: cd backend && uvicorn app.main:app --reload")
    print("   2. Start frontend: cd frontend/frontend && npm start")
    print("   3. Open browser: http://localhost:3000")
    print("   4. Run test: python test_api.ps1")
    print("=" * 50)

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    main()
