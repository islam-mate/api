import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


class CacheService:
    def __init__(self):
        self.client = None

    async def connect(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url, decode_responses=True)
        print("Cache connected")

    async def disconnect(self):
        if self.client:
            await self.client.close()
            print("Cache disconnected")

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0
