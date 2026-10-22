import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional
from backend.core import constants

logger = logging.getLogger("conversor_moedas")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RedisRateDAO:
    HASH_KEY = constants.RATE_HASH_KEY
    HISTORY_KEY = constants.RATE_HISTORY_KEY
    HISTORY_DAYS = constants.RATE_HISTORY_DAYS

    def __init__(self, redis_client):
        self.redis = redis_client

    def save_rate(
        self, currency: str, rate: float, source: str = constants.RATE_SOURCE_MANUAL
    ) -> dict:
        currency_upper = currency.upper()
        atualizado_em = _now_iso()
        payload = json.dumps(
            {"taxa": rate, "fonte": source, "atualizado_em": atualizado_em}
        )
        self.redis.hset(self.HASH_KEY, currency_upper, payload)
        return {
            "moeda": currency_upper,
            "taxa": rate,
            "fonte": source,
            "atualizado_em": atualizado_em,
        }

    def get_rate(self, currency: str) -> Optional[float]:
        details = self.get_rate_details(currency)
        return details["taxa"] if details else None

    def get_rate_details(self, currency: str) -> Optional[dict]:
        val = self.redis.hget(self.HASH_KEY, currency.upper())
        if val is None:
            return None
        return self._parse_rate_value(val)

    def get_all_rates(self) -> List[dict]:
        raw = self.redis.hgetall(self.HASH_KEY)
        taxas = []
        for moeda, val in raw.items():
            if isinstance(moeda, bytes):
                moeda = moeda.decode("utf-8")
            details = self._parse_rate_value(val)
            taxas.append({"moeda": moeda, **details})
        return taxas

    def delete_rate(self, currency: str) -> bool:
        removido = self.redis.hdel(self.HASH_KEY, currency.upper())
        return bool(removido)

    def _parse_rate_value(self, val) -> dict:
        try:
            parsed = json.loads(val)
            return {
                "taxa": float(parsed["taxa"]),
                "fonte": parsed["fonte"],
                "atualizado_em": parsed.get("atualizado_em"),
            }
        except (ValueError, TypeError, KeyError):
            # Compatibilidade com taxas gravadas antes da tag de fonte existir
            # (valor numérico puro, sem JSON).
            return {
                "taxa": float(val),
                "fonte": constants.RATE_SOURCE_MANUAL,
                "atualizado_em": None,
            }

    def add_rate_history_entry(self, moeda: str, taxa: float, fonte: str) -> None:
        agora = time.time()
        entrada = json.dumps(
            {
                "moeda": moeda,
                "taxa": taxa,
                "fonte": fonte,
                "atualizado_em": _now_iso(),
            }
        )
        self.redis.zadd(self.HISTORY_KEY, {entrada: agora})
        limite = agora - (self.HISTORY_DAYS * 86400)
        self.redis.zremrangebyscore(self.HISTORY_KEY, 0, limite)

    def get_rate_history(self) -> List[dict]:
        limite = time.time() - (self.HISTORY_DAYS * 86400)
        itens = self.redis.zrevrangebyscore(self.HISTORY_KEY, "+inf", limite)
        historico = []
        for item in itens:
            if isinstance(item, bytes):
                item = item.decode("utf-8")
            historico.append(json.loads(item))
        return historico


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
