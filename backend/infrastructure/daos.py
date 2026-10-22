import json
import logging
from typing import List, Optional
from backend.core import constants

logger = logging.getLogger("conversor_moedas")


class RedisRateDAO:
    HASH_KEY = constants.RATE_HASH_KEY

    def __init__(self, redis_client):
        self.redis = redis_client

    def save_rate(
        self, currency: str, rate: float, source: str = constants.RATE_SOURCE_MANUAL
    ) -> dict:
        currency_upper = currency.upper()
        payload = json.dumps({"taxa": rate, "fonte": source})
        self.redis.hset(self.HASH_KEY, currency_upper, payload)
        return {"moeda": currency_upper, "taxa": rate, "fonte": source}

    def get_rate(self, currency: str) -> Optional[float]:
        details = self.get_rate_details(currency)
        return details["taxa"] if details else None

    def get_rate_details(self, currency: str) -> Optional[dict]:
        val = self.redis.hget(self.HASH_KEY, currency.upper())
        if val is None:
            return None

        try:
            parsed = json.loads(val)
            return {"taxa": float(parsed["taxa"]), "fonte": parsed["fonte"]}
        except (ValueError, TypeError, KeyError):
            # Compatibilidade com taxas gravadas antes da tag de fonte existir
            # (valor numérico puro, sem JSON).
            return {"taxa": float(val), "fonte": constants.RATE_SOURCE_MANUAL}


class RedisHistoryDAO:
    LIST_KEY = constants.HISTORY_LIST_KEY
    MAX_ITEMS = constants.HISTORY_MAX_ITEMS

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
