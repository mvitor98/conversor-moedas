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
