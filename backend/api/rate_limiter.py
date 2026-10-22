"""Rate limiting por IP, usando o mesmo cliente Redis já configurado na API.

Implementação própria (janela fixa via INCR/EXPIRE) em vez de uma lib como
slowapi: slowapi/limits exigem uma conexão `redis://` direta, incompatível com
o modo Upstash REST usado em produção. Como `get_redis_client()` já abstrai os
dois modos (TCP e REST) com a mesma interface (INCR/EXPIRE), basta reaproveitá-lo.
"""

from typing import Callable

import redis
from fastapi import Depends, Request

from backend.core import constants
from backend.core.logger import logger
from backend.infrastructure.redis_client import get_redis_client


class RateLimitExceededError(Exception):
    """Levantada quando um cliente excede o limite de requisições permitido."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Limite de requisições excedido.")


def _get_client_ip(request: Request) -> str:
    """Obtém o IP real do cliente, considerando proxies reversos (Render)."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def rate_limiter(
    max_requests: int, window_seconds: int = constants.RATE_LIMIT_WINDOW_SECONDS
) -> Callable:
    """Cria uma dependência do FastAPI que limita requisições por IP/rota.

    Usa uma janela fixa: a cada `window_seconds`, cada IP pode fazer no máximo
    `max_requests` chamadas à rota. Implementado com INCR (atômico) + EXPIRE
    no primeiro incremento da janela.

    Args:
        max_requests (int): Número máximo de requisições na janela.
        window_seconds (int): Duração da janela, em segundos.

    Returns:
        Callable: Dependência injetável via `Depends(...)`.

    Raises:
        RateLimitExceededError: Se o limite for excedido (-> 429, ver
            `backend.api.exceptions.rate_limit_handler`).
    """

    def dependency(
        request: Request,
        redis_client: redis.Redis = Depends(get_redis_client),
    ) -> None:
        client_ip = _get_client_ip(request)
        key = f"ratelimit:{request.url.path}:{client_ip}"

        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, window_seconds)
        except Exception as exc:  # noqa: BLE001 - nunca bloquear por falha no Redis
            logger.warning(f"Rate limiter indisponível (fail-open): {exc}")
            return

        if current > max_requests:
            raise RateLimitExceededError(retry_after_seconds=window_seconds)

    return dependency
