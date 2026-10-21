import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Configuração resiliente do Pool de Conexões para Redis na Nuvem (Upstash)
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    health_check_interval=30,
    socket_timeout=10,
    socket_connect_timeout=10,
    retry_on_timeout=True,
    socket_keepalive=True,
)


def get_redis_client() -> redis.Redis:
    return redis_client
