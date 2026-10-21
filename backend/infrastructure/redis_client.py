"""Módulo de gerenciamento da conexão com o banco de dados Redis."""

import redis
from backend.core.config import settings
from backend.core.logger import logger


def get_redis_client() -> redis.Redis:
    """Retorna uma instância ativa do cliente Redis conectada ao pool.

    Returns:
        redis.Redis: Objeto de conexão com o Redis.
    """
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return client
    except Exception as exc:
        logger.error(f"Erro ao conectar ao Redis: {str(exc)}")
        raise exc
