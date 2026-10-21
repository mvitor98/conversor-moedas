import os
import logging

logger = logging.getLogger("conversor_moedas")

rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().strip('"').strip("'")
rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip().strip('"').strip("'")
redis_url = os.getenv("REDIS_URL", "").strip().strip('"').strip("'")

if rest_url and rest_token:
    logger.info("Inicializando conexão Upstash HTTP REST...")
    from upstash_redis import Redis

    redis_client = Redis(url=rest_url, token=rest_token)
elif redis_url:
    logger.info(f"Inicializando conexão Redis TCP ({redis_url})...")
    import redis

    ssl_kwargs = {}
    if redis_url.startswith("rediss://"):
        ssl_kwargs = {"ssl_cert_reqs": None}

    pool = redis.ConnectionPool.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=10,
        retry_on_timeout=True,
        **ssl_kwargs,
    )
    redis_client = redis.Redis(connection_pool=pool)
else:
    logger.warning(
        "Nenhuma variável de nuvem encontrada. Usando localhost:6379 para dev local."
    )
    import redis

    pool = redis.ConnectionPool.from_url(
        "redis://localhost:6379", decode_responses=True
    )
    redis_client = redis.Redis(connection_pool=pool)


def get_redis_client():
    return redis_client
