import json
import logging
from typing import List, Optional

logger = logging.getLogger("conversor_moedas")


class RedisRateDAO:
    HASH_KEY = "taxas_cambio"

    def __init__(self, redis_client):
        self.redis = redis_client

    def save_rate(self, currency: str, rate: float) -> dict:
        currency_upper = currency.upper()
        self.redis.hset(self.HASH_KEY, currency_upper, str(rate))
        return {"moeda": currency_upper, "taxa": rate}

    def get_rate(self, currency: str) -> Optional[float]:
        val = self.redis.hget(self.HASH_KEY, currency.upper())
        if val is not None:
            return float(val)
        return None


class RedisHistoryDAO:
    LIST_KEY = "historico_conversoes"
    MAX_ITEMS = 10

    def __init__(self, redis_client):
        self.redis = redis_client

    def add_conversion(self, conversion_data: dict) -> None:
        payload = json.dumps(conversion_data)
        self.redis.lpush(self.LIST_KEY, payload)
        self.redis.ltrim(self.LIST_KEY, 0, self.MAX_ITEMS - 1)

    def get_recent_conversions(self) -> List[dict]:
        raw_items = self.redis.lrange(self.LIST_KEY, 0, self.MAX_ITEMS - 1)
        if not raw_items:
            return []

        conversions = []
        for item in raw_items:
            if isinstance(item, bytes):
                item = item.decode("utf-8")
            if isinstance(item, str):
                conversions.append(json.loads(item))
            elif isinstance(item, dict):
                conversions.append(item)
        return conversions

    def get_history(self) -> List[dict]:
        return self.get_recent_conversions()
