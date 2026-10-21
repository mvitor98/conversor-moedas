"""Fixtures globais para isolamento e dublês de teste com Pytest."""

from typing import Generator
import fakeredis
import pytest
from backend.infrastructure.redis_client import get_redis_client
from backend.main import app


@pytest.fixture(autouse=True)
def override_redis_dependency() -> Generator[fakeredis.FakeRedis, None, None]:
    """Sobrescreve a dependência do Redis na API por um banco em memória."""
    fake_client: fakeredis.FakeRedis = fakeredis.FakeRedis(decode_responses=True)
    app.dependency_overrides[get_redis_client] = lambda: fake_client
    yield fake_client
    app.dependency_overrides.clear()
