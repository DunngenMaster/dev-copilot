"""Quick environment test for Claude integration."""

import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

print("="*60)
print("ENVIRONMENT CHECK")
print("="*60)

# Check all required keys
keys_to_check = [
    "REDIS_URL",
    "ANTHROPIC_API_KEY",
    "SANITY_TOKEN",
    "POSTMAN_API_KEY",
    "SEMANTIC_CACHE"
]

for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # Mask sensitive parts
        if len(value) > 20:
            display = f"{value[:10]}...{value[-6:]}"
        else:
            display = value
        print(f"✓ {key}: {display}")
    else:
        print(f"✗ {key}: NOT SET")

print("\n" + "="*60)
print("QUICK CLAUDE TEST")
print("="*60)

try:
    from services.anthropic_client import generate_sop
    
    stub_metrics = {
        "prs": {"total": 10, "avg_time_to_first_review_h": 24},
        "issues": {"total": 20, "reopen_rate": 0.05}
    }
    
    result = generate_sop(stub_metrics, [])
    print(f"✓ Claude responded with {len(result.get('bottlenecks', []))} bottlenecks")
    print(f"✓ SOP length: {len(result.get('sop', ''))} chars")
    print("✓ SUCCESS: Claude integration working!")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
