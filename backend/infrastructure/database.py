import os
from upstash_redis import Redis


def get_redis_client():
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if not url or not token:
        raise RuntimeError("Variaveis UPSTASH_REDIS_REST_URL e TOKEN estao ausentes!")

    return Redis(url=url.strip(), token=token.strip())


redis_client = get_redis_client()