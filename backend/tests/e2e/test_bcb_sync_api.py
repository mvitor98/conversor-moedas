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


def test_sync_bcb_rates_for_specific_currency() -> None:
    """Testa a sincronização de uma única moeda via query param ?moeda=."""
    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate",
        side_effect=lambda moeda: {"USD": 5.0, "EUR": 6.0}[moeda],
    ):
        response = client.post("/taxas/sincronizar-bcb?moeda=EUR")

    assert response.status_code == 200
    assert response.json()["taxas"] == {"EUR": round(5.0 / 6.0, 4)}


def test_sync_bcb_rates_without_moeda_also_updates_registered_currency() -> None:
    """A sincronização geral (sem ?moeda=) deve atualizar toda moeda já
    cadastrada que o PTAX cobre, não só BRL/USD."""
    client.post("/taxas/GBP/0.75")

    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate",
        side_effect=lambda moeda: {"USD": 5.0, "GBP": 4.0}[moeda],
    ):
        response = client.post("/taxas/sincronizar-bcb")

    assert response.status_code == 200
    taxas = response.json()["taxas"]
    assert taxas["BRL"] == 5.0
    assert taxas["USD"] == 1.0
    assert taxas["GBP"] == round(5.0 / 4.0, 4)

    get_response = client.get("/taxas")
    gbp = next(item for item in get_response.json() if item["moeda"] == "GBP")
    assert gbp["fonte"] == "bcb"


def test_sync_bcb_rates_for_unsupported_currency_returns_400() -> None:
    """Testa que pedir sincronização de uma moeda fora do PTAX retorna 400."""
    response = client.post("/taxas/sincronizar-bcb?moeda=ARS")
    assert response.status_code == 400
    assert "erro" in response.json()


def test_sync_bcb_rates_returns_502_when_bcb_unavailable() -> None:
    """Testa que uma falha na API do BCB retorna 502, não derruba a aplicação."""
    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate",
        side_effect=RuntimeError("BCB fora do ar"),
    ):
        response = client.post("/taxas/sincronizar-bcb")

    assert response.status_code == 502
    assert "erro" in response.json()
