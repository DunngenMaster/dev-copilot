import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
client = redis.from_url(redis_url, decode_responses=False)

# Delete all keys
keys = client.keys("*")
if keys:
    client.delete(*keys)
    print(f"Deleted {len(keys)} keys from Redis")
else:
    print("No keys found in Redis")

client.close()
