import logging
import os

logger = logging.getLogger("conversor_moedas")


def get_redis_client():
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    # 1. FORÇAR UPSTASH REST SE AS VARIÁVEIS EXISTIREM (RENDER)
    if rest_url and rest_token:
        rest_url = rest_url.strip().strip('"').strip("'")
        rest_token = rest_token.strip().strip('"').strip("'")

        try:
            from upstash_redis import Redis

            logger.info("Conectado ao Upstash via HTTP REST.")
            return Redis(url=rest_url, token=rest_token)
        except ImportError:
            msg = (
                "ERRO FATAL: O pacote 'upstash-redis' não foi "
                "instalado pelo Render. Limpe o Build Cache."
            )
            logger.critical(msg)
            raise RuntimeError(msg)

    # 2. TENTAR TCP CASO REDIS_URL EXISTA
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        import redis

        redis_url = redis_url.strip().strip('"').strip("'")
        ssl_kwargs = (
            {"ssl_cert_reqs": None} if redis_url.startswith("rediss://") else {}
        )
        pool = redis.ConnectionPool.from_url(
            redis_url, decode_responses=True, **ssl_kwargs
        )
        return redis.Redis(connection_pool=pool)

    # 3. MODO LOCAL
    logger.warning("AVISO: Variáveis não encontradas. Conectando a localhost:6379.")
    import redis

    pool = redis.ConnectionPool.from_url(
        "redis://localhost:6379", decode_responses=True
    )
    return redis.Redis(connection_pool=pool)


redis_client = get_redis_client()
