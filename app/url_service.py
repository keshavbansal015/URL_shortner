import json
import hashlib
from datetime import datetime
from typing import Optional

from app.utils import encode
from app.kvstore import KVStoreService


class URLService:
    def __init__(self, kv: KVStoreService, base_url: str = "http://localhost:8000"):
        self.kv = kv
        self.base_url = base_url

    # -------------------------
    # Create short URL
    # -------------------------

    def shorten(self, long_url: str) -> dict:
        url_hash = hashlib.sha256(long_url.encode()).hexdigest() # size: 64 characters

        # 1. Deduplication
        existing_key = self.kv.get(f"long:{url_hash}")
        if existing_key:
            data = self._get_url_data(existing_key)
            return self._build_response(existing_key, data)

        # 2. Generate new key
        key_id = self.kv.incr("url_counter")
        short_key = encode(key_id)

        # 3. Structured JSON payload
        payload = {
            "long_url": long_url,
            "created_at": datetime.now().isoformat(),
            "clicks": 0
        }

        # 4. Store
        self.kv.set(f"short:{short_key}", json.dumps(payload))
        self.kv.set(f"long:{url_hash}", short_key)

        return self._build_response(short_key, payload)

    # -------------------------
    # Resolve URL + increment clicks
    # -------------------------

    def resolve(self, key: str) -> Optional[str]:
        raw = self.kv.get(f"short:{key}")
        if raw is None:
            return None

        data = json.loads(raw)

        # increment click count
        data["clicks"] += 1

        # write back (preserve TTL if any)
        self.kv.update(f"short:{key}", json.dumps(data))

        return data["long_url"]

    # -------------------------
    # Analytics
    # -------------------------

    def get_stats(self, key: str) -> Optional[dict]:
        raw = self.kv.get(f"short:{key}")
        if raw is None:
            return None

        data = json.loads(raw)

        return {
            "key": key,
            "long_url": data["long_url"],
            "clicks": data["clicks"],
            "created_at": data["created_at"],
            "short_url": f"{self.base_url}/{key}"
        }

    # -------------------------
    # Helpers
    # -------------------------

    def _get_url_data(self, key: str) -> dict:
        raw = self.kv.get(f"short:{key}")
        return json.loads(raw)

    def _build_response(self, key: str, data: dict) -> dict:
        return {
            "key": key,
            "long_url": data["long_url"],
            "short_url": f"{self.base_url}/{key}"
        }