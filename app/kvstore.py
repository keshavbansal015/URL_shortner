import redis
from redis import Redis
from typing import Optional, Iterable


class KVStoreService:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        socket_timeout: int = 5,
    ):
        self.client: Redis = Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_timeout=socket_timeout,
        )

        # Fail fast if Redis is unavailable
        try:
            self.client.ping()
        except redis.RedisError as e:
            raise RuntimeError(f"Redis connection failed: {e}")

    # -------------------------
    # Basic KV Operations
    # -------------------------

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return bool(self.client.set(name=key, value=value, ex=ex))

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def update(self, key: str, value: str) -> bool:
        # overwrite without changing TTL
        return bool(self.client.set(name=key, value=value, keepttl=True))

    # -------------------------
    # TTL / Expiration
    # -------------------------

    def get_ttl(self, key: str) -> Optional[int]:
        """
        Returns:
            None -> key doesn't exist OR no TTL set
            int  -> seconds remaining
        """
        ttl = self.client.ttl(key)

        if ttl < 0:  # -1 (no TTL) or -2 (no key)
            return None
        return ttl

    def set_with_ttl(self, key: str, value: str, ex: int) -> bool:
        return bool(self.client.set(name=key, value=value, ex=ex))

    def reset_ttl(self, key: str, ex: int) -> bool:
        """
        Re-applies TTL without modifying value.
        """
        value = self.get(key)
        if value is None:
            return False
        return self.set(key, value, ex=ex)

    # -------------------------
    # Atomic / Counters
    # -------------------------

    def incr(self, key: str) -> int:
        return int(self.client.incr(key))

    # -------------------------
    # Iteration (safe)
    # -------------------------

    def scan_keys(self, pattern: str = "*", batch_size: int = 100) -> Iterable[str]:
        cursor = 0
        while True:
            cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=batch_size)
            for k in keys:
                yield k
            if cursor == 0:
                break

    # -------------------------
    # Maintenance
    # -------------------------

    def clear_all(self) -> bool:
        return self.client.flushdb()

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass