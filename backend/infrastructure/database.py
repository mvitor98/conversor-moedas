import logging
import os

logger = logging.getLogger("conversor_moedas")


def get_redis_client():
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().strip('"').strip("'")
    rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip().strip('"').strip("'")
    redis_url = os.getenv("REDIS_URL", "").strip().strip('"').strip("'")

    # 1. Modo HTTP REST (Upstash - Recomendado para Serverless)
    if rest_url and rest_token:
        try:
            from upstash_redis import Redis

            logger.info("Conectado ao Upstash via HTTP REST Client.")
            return Redis(url=rest_url, token=rest_token)
        except ImportError:
            logger.error("Pacote 'upstash-redis' não instalado.")

    # 2. Modo TCP (redis-py) com auto-correção de TLS para Upstash
    if redis_url:
        import redis

        if "upstash.io" in redis_url and redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "rediss://", 1)

        ssl_kwargs = {}
        if redis_url.startswith("rediss://"):
            ssl_kwargs = {"ssl_cert_reqs": None}

        logger.info(f"Conectado ao Redis via TCP: {redis_url.split('@')[-1]}")
        pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10,
            health_check_interval=15,
            retry_on_timeout=True,
            **ssl_kwargs,
        )
        return redis.Redis(connection_pool=pool)

    # 3. Ambiente Local (Apenas fora do Render)
    if not os.getenv("RENDER"):
        import redis

        logger.info("Executando em ambiente local (localhost:6379).")
        pool = redis.ConnectionPool.from_url(
            "redis://localhost:6379", decode_responses=True
        )
        return redis.Redis(connection_pool=pool)

    # 4. Bloqueio no Render caso faltem variáveis de ambiente
    env_vars_found = [k for k in os.environ.keys() if "REDIS" in k]
    msg = (
        "ERRO CRÍTICO NO RENDER: Nenhuma variável de conexão Redis foi encontrada. "
        f"Variáveis detectadas: {env_vars_found}. "
        "Cadastre UPSTASH_REDIS_REST_URL e UPSTASH_REDIS_REST_TOKEN no Render."
    )
    logger.critical(msg)
    raise RuntimeError(msg)


redis_client = get_redis_client()
