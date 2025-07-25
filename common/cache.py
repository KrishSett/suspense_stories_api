# cache.py
import redis.asyncio as redis
import json

class RedisHashCache:
    def __init__(self, host="localhost", port=6379, db=0, cache_key="api_cache"):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.cache_key = cache_key

    async def h_set(self, field: str, value: any, ttl: int = 60):
        try:
            await self.redis_client.hset(self.cache_key, field, json.dumps(value))
            await self.redis_client.expire(self.cache_key, ttl)
        except Exception as e:
            raise Exception(f"[h_set] Redis error: {str(e)}")

    async def h_get(self, field: str):
        try:
            data = await self.redis_client.hget(self.cache_key, field)
            if data:
                return json.loads(data)
        except Exception as e:
            raise Exception(f"[h_get] Redis error: {str(e)}")
        return None

    async def h_del(self, field: str):
        try:
            await self.redis_client.hdel(self.cache_key, field)
        except Exception as e:
            raise Exception(f"[h_del] Redis error: {str(e)}")

    async def h_keys(self):
        try:
            return await self.redis_client.hkeys(self.cache_key)
        except Exception as e:
            raise Exception(f"[h_keys] Redis error: {str(e)}")

    async def h_get_all(self):
        try:
            data = await self.redis_client.hgetall(self.cache_key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            raise Exception(f"[h_get_all] Redis error: {str(e)}")
