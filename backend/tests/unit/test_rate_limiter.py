"""Testes unitários para o rate limiter (backend.api.rate_limiter)."""

from unittest.mock import MagicMock
import pytest
from backend.api.rate_limiter import (
    RateLimitExceededError,
    _get_client_ip,
    rate_limiter,
)


def _build_request(path="/taxas", ip="1.2.3.4", forwarded_for=None) -> MagicMock:
    request = MagicMock()
    request.url.path = path
    request.client.host = ip
    request.headers = {"x-forwarded-for": forwarded_for} if forwarded_for else {}
    return request


def test_get_client_ip_prefers_x_forwarded_for() -> None:
    """Atrás de um proxy (Render), deve usar o primeiro IP do X-Forwarded-For."""
    request = _build_request(ip="10.0.0.1", forwarded_for="203.0.113.5, 10.0.0.1")
    assert _get_client_ip(request) == "203.0.113.5"


def test_get_client_ip_falls_back_to_request_client() -> None:
    """Sem proxy, deve usar o IP direto da conexão."""
    request = _build_request(ip="203.0.113.9")
    assert _get_client_ip(request) == "203.0.113.9"


def test_rate_limiter_allows_requests_under_the_limit() -> None:
    """Não deve levantar exceção enquanto o número de chamadas for <= o limite."""
    mock_redis = MagicMock()
    mock_redis.incr.side_effect = [1, 2, 3]
    dependency = rate_limiter(max_requests=3)
    request = _build_request()

    for _ in range(3):
        dependency(request, mock_redis)  # não deve levantar


def test_rate_limiter_blocks_requests_over_the_limit() -> None:
    """Deve levantar RateLimitExceededError ao ultrapassar o limite na janela."""
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 4
    dependency = rate_limiter(max_requests=3, window_seconds=60)
    request = _build_request()

    with pytest.raises(RateLimitExceededError) as exc_info:
        dependency(request, mock_redis)
    assert exc_info.value.retry_after_seconds == 60


def test_rate_limiter_sets_expire_only_on_first_increment() -> None:
    """A expiração da janela só deve ser definida no primeiro INCR (contagem 1)."""
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 1
    dependency = rate_limiter(max_requests=5, window_seconds=30)
    request = _build_request()

    dependency(request, mock_redis)

    mock_redis.expire.assert_called_once()
    assert mock_redis.expire.call_args[0][1] == 30


def test_rate_limiter_does_not_reexpire_after_first_increment() -> None:
    """Não deve chamar EXPIRE novamente após a primeira chamada da janela."""
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 2
    dependency = rate_limiter(max_requests=5)
    request = _build_request()

    dependency(request, mock_redis)

    mock_redis.expire.assert_not_called()


def test_rate_limiter_fails_open_when_redis_is_unavailable() -> None:
    """Uma falha no Redis não pode bloquear a requisição (fail-open)."""
    mock_redis = MagicMock()
    mock_redis.incr.side_effect = ConnectionError("Redis fora do ar")
    dependency = rate_limiter(max_requests=1)
    request = _build_request()

    dependency(request, mock_redis)  # não deve levantar
