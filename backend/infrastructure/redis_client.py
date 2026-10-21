"""Módulo de gerenciamento da conexão com o banco de dados Redis."""

import redis
from backend.core.config import settings
from backend.core.logger import logger


def get_redis_client():
    """Retorna uma instância ativa do cliente Redis ou Upstash REST.

    Returns:
        Cliente de conexão com o Redis/Upstash.
    """
    try:
        # Se as credenciais do Upstash REST estiverem configuradas, usa o HTTP REST
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            from upstash_redis import Redis as UpstashRedis

            logger.info("Conectando ao Upstash via HTTP REST.")
            return UpstashRedis(
                url=settings.UPSTASH_REDIS_REST_URL.strip(),
                token=settings.UPSTASH_REDIS_REST_TOKEN.strip(),
            )

        # Caso contrário, usa o cliente Redis tradicional (TCP)
        logger.info(f"Conectando ao Redis via TCP: {settings.REDIS_URL}")
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return client
    except Exception as exc:
        logger.error(f"Erro ao conectar ao Redis/Upstash: {str(exc)}")
        raise exc