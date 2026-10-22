"""Testes unitários para a seleção de cliente Redis/Upstash (redis_client.py)."""

from unittest.mock import MagicMock, patch
from backend.core.config import settings
from backend.infrastructure.redis_client import get_redis_client


def test_get_redis_client_uses_upstash_when_credentials_set(monkeypatch) -> None:
    """Deve usar o cliente HTTP REST do Upstash quando URL e token estão configurados."""
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_URL", " https://fake-upstash.io ")
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_TOKEN", " fake-token ")

    fake_instance = MagicMock()
    with patch("upstash_redis.Redis", return_value=fake_instance) as mock_upstash:
        client = get_redis_client()

    mock_upstash.assert_called_once_with(
        url="https://fake-upstash.io", token="fake-token"
    )
    assert client is fake_instance


def test_get_redis_client_falls_back_to_tcp_without_upstash_credentials(
    monkeypatch,
) -> None:
    """Deve usar o cliente TCP tradicional quando as credenciais do Upstash estão ausentes."""
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_URL", None)
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_TOKEN", None)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    fake_instance = MagicMock()
    with patch("redis.Redis.from_url", return_value=fake_instance) as mock_from_url:
        client = get_redis_client()

    mock_from_url.assert_called_once_with(
        "redis://localhost:6379/0", decode_responses=True
    )
    assert client is fake_instance


def test_get_redis_client_falls_back_to_tcp_with_partial_upstash_credentials(
    monkeypatch,
) -> None:
    """Deve ignorar o Upstash se apenas uma das duas credenciais estiver presente."""
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_URL", "https://fake-upstash.io")
    monkeypatch.setattr(settings, "UPSTASH_REDIS_REST_TOKEN", None)
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    fake_instance = MagicMock()
    with patch("redis.Redis.from_url", return_value=fake_instance) as mock_from_url:
        client = get_redis_client()

    mock_from_url.assert_called_once_with(
        "redis://localhost:6379/0", decode_responses=True
    )
    assert client is fake_instance
