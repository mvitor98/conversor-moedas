"""Testes E2E para os endpoints de conversão e histórico."""

from fastapi.testclient import TestClient
from backend.main import app

client: TestClient = TestClient(app)


def test_conversion_flow_e2e() -> None:
    """Testa o fluxo completo: cadastrar taxas -> converter -> consultar histórico."""
    client.post("/taxas/BRL/5.0")
    client.post("/taxas/ARS/700.0")

    response = client.get("/converter/100/BRL/ARS")
    assert response.status_code == 200
    data = response.json()
    assert data["convertido"] == 14000.0

    history_resp = client.get("/conversoes")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["convertido"] == 14000.0


def test_conversion_same_currency_error() -> None:
    """Testa tentativa de conversão com moedas iguais."""
    response = client.get("/converter/100/BRL/BRL")
    assert response.status_code == 400
    assert "erro" in response.json()


def test_conversion_with_non_numeric_amount_returns_400() -> None:
    """Testa que um valor não numérico retorna 400 (e não o 422 padrão do FastAPI)."""
    response = client.get("/converter/abc/BRL/USD")
    assert response.status_code == 400
    assert "erro" in response.json()


def test_conversion_with_unregistered_currency_returns_404() -> None:
    """Testa que converter com uma moeda sem taxa cadastrada retorna 404."""
    client.post("/taxas/BRL/5.0")

    response = client.get("/converter/100/BRL/XYZ")
    assert response.status_code == 404
    assert "erro" in response.json()


def test_get_history_returns_404_when_empty() -> None:
    """Testa que o histórico vazio retorna 404, conforme o contrato da API."""
    response = client.get("/conversoes")
    assert response.status_code == 404
    assert "erro" in response.json()
