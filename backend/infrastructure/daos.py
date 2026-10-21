"""Data Access Objects (DAOs) para abstração de persistência no Redis."""

import json
from typing import Dict, List, Optional
import redis
from backend.core.logger import logger


class RedisRateDAO:
    """DAO responsável pelo gerenciamento de taxas de câmbio no Redis."""

    HASH_KEY = "taxas_cambio"

    def __init__(self, redis_client: redis.Redis) -> None:
        """Inicializa o DAO com a instância do cliente Redis."""
        self.redis = redis_client

    def save_rate(self, currency: str, rate: float) -> None:
        """Cadastra ou atualiza uma taxa de câmbio no Redis.

        Args:
            currency (str): Código da moeda (ex: BRL).
            rate (float): Valor equivalente em relação ao USD.
        """
        currency_upper = currency.upper()
        self.redis.hset(self.HASH_KEY, currency_upper, str(rate))
        logger.info(f"Taxa salva com sucesso no Redis: {currency_upper} = {rate}")

    def get_rate(self, currency: str) -> Optional[float]:
        """Busca a taxa de câmbio de uma moeda específica.

        Args:
            currency (str): Código da moeda (ex: BRL).

        Returns:
            Optional[float]: Valor da taxa ou None se não encontrada.
        """
        rate = self.redis.hget(self.HASH_KEY, currency.upper())
        return float(rate) if rate is not None else None

    def get_all_rates(self) -> Dict[str, float]:
        """Retorna todas as taxas de câmbio cadastradas.

        Returns:
            Dict[str, float]: Dicionário com código e valor das taxas.
        """
        rates = self.redis.hgetall(self.HASH_KEY)
        return {k: float(v) for k, v in rates.items()}


class RedisHistoryDAO:
    """DAO responsável pelo histórico das últimas conversões no Redis."""

    LIST_KEY = "historico_conversoes"
    MAX_ITEMS = 5

    def __init__(self, redis_client: redis.Redis) -> None:
        """Inicializa o DAO com a instância do cliente Redis."""
        self.redis = redis_client

    def add_conversion(self, conversion_data: dict) -> None:
        """Adiciona uma nova conversão mantendo o limite de 5 itens mais recentes.

        Args:
            conversion_data (dict): Dados da conversão realizada.
        """
        data_str = json.dumps(conversion_data)
        self.redis.lpush(self.LIST_KEY, data_str)
        self.redis.ltrim(self.LIST_KEY, 0, self.MAX_ITEMS - 1)
        logger.info(f"Conversão adicionada ao histórico no Redis: {conversion_data}")

    def get_recent_conversions(self) -> List[dict]:
        """Recupera as últimas conversões gravadas.

        Returns:
            List[dict]: Lista de conversões formatadas.
        """
        raw_items = self.redis.lrange(self.LIST_KEY, 0, self.MAX_ITEMS - 1)
        return [json.loads(item) for item in raw_items]
