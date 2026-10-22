"""Testes E2E para os endpoints de cadastro de taxas."""

from fastapi.testclient import TestClient
from backend.main import app

client: TestClient = TestClient(app)


def test_save_rate_success() -> None:
    """Testa a criação de uma taxa via requisição HTTP POST."""
    response = client.post("/taxas/USD/1.0")
    assert response.status_code == 201
    assert response.json()["moeda"] == "USD"

    response_brl = client.post("/taxas/BRL/5.0")
    assert response_brl.status_code == 201
    assert response_brl.json()["moeda"] == "BRL"


def test_save_rate_invalid_value() -> None:
    """Testa o envio de taxa menor ou igual a zero."""
    response = client.post("/taxas/BRL/-5.0")
    assert response.status_code == 400
    assert "erro" in response.json()


def test_save_rate_non_numeric_value_returns_400() -> None:
    """Testa que um valor não numérico retorna 400 (e não o 422 padrão do FastAPI)."""
    response = client.post("/taxas/BRL/abc")
    assert response.status_code == 400
    assert "erro" in response.json()


def test_save_rate_response_includes_manual_source() -> None:
    """Testa que o cadastro manual de taxa marca a fonte como 'manual'."""
    response = client.post("/taxas/EUR/6.0")
    assert response.status_code == 201
    assert response.json()["fonte"] == "manual"
