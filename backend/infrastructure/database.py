import logging
import os

logger = logging.getLogger("conversor_moedas")


def get_redis_client():
    r_url = os.getenv("UPSTASH_REDIS_REST_URL")
    r_tok = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if r_url and r_tok:
        try:
            from upstash_redis import Redis
            logger.info("Upstash REST ON.")
            return Redis(url=r_url.strip(), token=r_tok.strip())
        except ImportError:
            raise RuntimeError("upstash-redis ausente no Render.")

    if os.getenv("RENDER"):
        raise ValueError("Variaveis do Upstash ausentes no Render.")

    import redis
    pool = redis.ConnectionPool.from_url(
        "redis://localhost:6379", decode_responses=True
    )
    return redis.Redis(connection_pool=pool)


redis_client = get_redis_client()