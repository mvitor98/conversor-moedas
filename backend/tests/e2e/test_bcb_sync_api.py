"""Testes E2E para o endpoint de sincronização de taxas com o BCB/PTAX."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

client: TestClient = TestClient(app)


def test_sync_bcb_rates_success() -> None:
    """Testa a sincronização bem-sucedida de BRL/USD via BCB/PTAX."""
    with patch("backend.domain.rate_sync_service.fetch_ptax_rate", return_value=5.0134):
        response = client.post("/taxas/sincronizar-bcb")

    assert response.status_code == 200
    data = response.json()
    assert data["taxas"] == {"BRL": 5.0134, "USD": 1.0}


def test_sync_bcb_rates_returns_502_when_bcb_unavailable() -> None:
    """Testa que uma falha na API do BCB retorna 502, não derruba a aplicação."""
    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate",
        side_effect=RuntimeError("BCB fora do ar"),
    ):
        response = client.post("/taxas/sincronizar-bcb")

    assert response.status_code == 502
    assert "erro" in response.json()
