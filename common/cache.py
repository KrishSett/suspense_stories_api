import redis.asyncio as redis
import json
from config import config

class RedisHashCache:
    def __init__(self, prefix=None):
        self.redis_client = redis.Redis(
            host=config["redis_host"],
            port=config["redis_port"],
            db=config["redis_db"],
            decode_responses=True
        )
        self.prefix = prefix

    def generate_slug(self, params: dict) -> str:
        if not params:
            return ""
        return "|".join([f"{k}={v}" for k, v in params.items()])

    def build_cache_key(self, cache_key: str, params: dict = None) -> str:
        slug = self.generate_slug(params)
        if self.prefix and slug:
            return f"{self.prefix}|{cache_key}|{slug}"
        elif self.prefix:
            return f"{self.prefix}|{cache_key}"
        elif slug:
            return f"{cache_key}|{slug}"
        else:
            return cache_key

    async def h_set(self, cache_key: str, field: str, value: any, params: dict = None, ttl: int = 60):
        try:
            final_key = self.build_cache_key(cache_key, params)
            await self.redis_client.hset(final_key, field, json.dumps(value))
            await self.redis_client.expire(final_key, ttl)
        except Exception as e:
            raise Exception(f"[h_set] Redis error: {str(e)}")

    async def h_get(self, cache_key: str, field: str, params: dict = None):
        try:
            final_key = self.build_cache_key(cache_key, params)
            data = await self.redis_client.hget(final_key, field)
            if data:
                return json.loads(data)
        except Exception as e:
            raise Exception(f"[h_get] Redis error: {str(e)}")
        return None

    async def h_del(self, cache_key: str, field: str, params: dict = None):
        try:
            final_key = self.build_cache_key(cache_key, params)
            await self.redis_client.hdel(final_key, field)
        except Exception as e:
            raise Exception(f"[h_del] Redis error: {str(e)}")

    async def h_keys(self, cache_key: str, params: dict = None):
        try:
            final_key = self.build_cache_key(cache_key, params)
            return await self.redis_client.hkeys(final_key)
        except Exception as e:
            raise Exception(f"[h_keys] Redis error: {str(e)}")

    async def h_get_all(self, cache_key: str, params: dict = None):
        try:
            final_key = self.build_cache_key(cache_key, params)
            data = await self.redis_client.hgetall(final_key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            raise Exception(f"[h_get_all] Redis error: {str(e)}")
