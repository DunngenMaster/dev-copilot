"""Clear Redis cache and force fresh Claude generation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.redis_vector import clear_all_docs
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

deleted = clear_all_docs()
print(f"Cleared {deleted} cached workflow documents from Redis")
print("Next request will be a cache MISS and trigger fresh Claude generation")
