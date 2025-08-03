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
        self.prefix = prefix or ""
        self.ttl = 1800  # Default TTL of 30 minutes

    def generate_slug(self, params: dict) -> str:
        """Generate a slug string from params."""
        if not params:
            return ""
        return "|".join([f"{k}={v}" for k, v in params.items()])

    def build_cache_key(self, cache_key: str) -> str:
        """Add prefix to cache key."""
        return f"{self.prefix}|{cache_key}" if self.prefix else cache_key

    def build_field_key(self, field: str, params: dict = None) -> str:
        """Add params as suffix to field key."""
        slug = self.generate_slug(params)
        return f"{field}|{slug}" if slug else field

    async def h_set(self, cache_key: str, field: str, value: any, params: dict = None):
        try:
            cache_key = self.build_cache_key(cache_key)
            field_key = self.build_field_key(field, params)

            await self.redis_client.hset(cache_key, field_key, json.dumps(value))
            await self.redis_client.expire(cache_key, self.ttl)
        except Exception as e:
            raise Exception(f"[h_set] Redis error: {str(e)}")

    async def h_get(self, cache_key: str, field: str, params: dict = None):
        try:
            cache_key = self.build_cache_key(cache_key)
            field_key = self.build_field_key(field, params)

            data = await self.redis_client.hget(cache_key, field_key)
            if data:
                return json.loads(data)
        except Exception as e:
            raise Exception(f"[h_get] Redis error: {str(e)}")
        return None

    async def h_del(self, cache_key: str, field: str, params: dict = None):
        try:
            cache_key = self.build_cache_key(cache_key)
            field_key = self.build_field_key(field, params)

            await self.redis_client.hdel(cache_key, field_key)
        except Exception as e:
            raise Exception(f"[h_del] Redis error: {str(e)}")

    async def h_keys(self, cache_key: str):
        try:
            cache_key = self.build_cache_key(cache_key)
            return await self.redis_client.hkeys(cache_key)
        except Exception as e:
            raise Exception(f"[h_keys] Redis error: {str(e)}")

    async def h_get_all(self, cache_key: str):
        try:
            cache_key = self.build_cache_key(cache_key)
            data = await self.redis_client.hgetall(cache_key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            raise Exception(f"[h_get_all] Redis error: {str(e)}")

    async def h_del_wildcard(self, cache_key: str, pattern: str):
        try:
            cache_key = self.build_cache_key(cache_key)
            all_keys = await self.redis_client.hkeys(cache_key)

            # Match fields starting with the given pattern
            keys_to_delete = [key for key in all_keys if key.startswith(pattern)]

            if keys_to_delete:
                await self.redis_client.hdel(cache_key, *keys_to_delete)

            return True
        except Exception as e:
            raise Exception(f"[h_del_wildcard] Redis error: {str(e)}")
