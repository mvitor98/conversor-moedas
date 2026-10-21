import os

rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if rest_url and rest_token:
    from upstash_redis import Redis

    redis_client = Redis(url=rest_url, token=rest_token)
else:
    import redis

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=10,
    )


def get_redis_client():
    return redis_client
