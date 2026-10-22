"""Testes E2E para os endpoints de cadastro de taxas."""

from fastapi.testclient import TestClient
from backend.core import constants
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


def test_save_rate_response_includes_timestamp() -> None:
    """Testa que o cadastro de taxa retorna o timestamp de atualização."""
    response = client.post("/taxas/GBP/0.8")
    assert response.status_code == 201
    assert "atualizado_em" in response.json()


def test_get_registered_rates_returns_404_when_empty() -> None:
    """Testa que GET /taxas retorna 404 quando não há nenhuma taxa cadastrada."""
    response = client.get("/taxas")
    assert response.status_code == 404
    assert "erro" in response.json()


def test_get_registered_rates_lists_saved_currencies() -> None:
    """Testa que GET /taxas lista as taxas cadastradas, com fonte e timestamp."""
    client.post("/taxas/BRL/5.0")
    client.post("/taxas/ARS/1000.0")

    response = client.get("/taxas")
    assert response.status_code == 200
    moedas = {item["moeda"] for item in response.json()}
    assert {"BRL", "ARS"}.issubset(moedas)
    assert all("atualizado_em" in item for item in response.json())


def test_get_registered_rates_handles_legacy_entry_without_timestamp(
    override_redis_dependency,
) -> None:
    """Taxas gravadas antes do campo atualizado_em existir (valor numérico puro
    no Redis, sem JSON) não podem derrubar o endpoint com 500: o DTO de resposta
    precisa aceitar atualizado_em nulo para esses registros legados."""
    override_redis_dependency.hset(constants.RATE_HASH_KEY, "JPY", "150.0")
    client.post("/taxas/BRL/5.0")

    response = client.get("/taxas")

    assert response.status_code == 200
    por_moeda = {item["moeda"]: item for item in response.json()}
    assert por_moeda["JPY"]["atualizado_em"] is None
    assert por_moeda["JPY"]["fonte"] == "manual"
    assert por_moeda["BRL"]["atualizado_em"] is not None


def test_get_rate_history_returns_404_when_empty() -> None:
    """Testa que GET /taxas/historico retorna 404 quando não há mudanças."""
    response = client.get("/taxas/historico")
    assert response.status_code == 404
    assert "erro" in response.json()


def test_get_rate_history_logs_only_on_value_change() -> None:
    """Testa que o histórico só ganha uma entrada nova quando o valor muda."""
    client.post("/taxas/CLP/900.0")
    client.post("/taxas/CLP/900.0")  # mesmo valor, não deve duplicar
    client.post("/taxas/CLP/910.0")  # valor mudou, deve registrar

    response = client.get("/taxas/historico")
    assert response.status_code == 200
    entradas_clp = [item for item in response.json() if item["moeda"] == "CLP"]
    assert len(entradas_clp) == 2


def test_save_rate_is_rate_limited_per_ip() -> None:
    """Testa que chamadas excessivas ao cadastro de taxa retornam 429."""
    for _ in range(constants.RATE_LIMIT_WRITE_MAX):
        response = client.post("/taxas/NZD/1.5")
        assert response.status_code == 201

    limited_response = client.post("/taxas/NZD/1.5")
    assert limited_response.status_code == 429
    assert "erro" in limited_response.json()
    assert "Retry-After" in limited_response.headers
