"""Testes unitários para a camada de Data Access Objects (DAOs).

Valida o comportamento individual dos métodos de persistência e leitura de taxas
e histórico de conversões no Redis utilizando dublês de teste (mocks).
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO


def test_save_and_get_rate_default_source_is_manual() -> None:
    """Testa o salvamento e busca de taxa via RedisRateDAO com a fonte padrão.

    Verifica se 'hset'/'hget' são chamados com as chaves corretas, se a taxa é
    gravada como JSON contendo a tag de fonte e se a leitura devolve o valor
    numérico esperado.

    Returns:
        None
    """
    mock_redis: MagicMock = MagicMock()
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    dao.save_rate("BRL", 5.0)
    mock_redis.hset.assert_called_once_with(
        "taxas_cambio", "BRL", '{"taxa": 5.0, "fonte": "manual"}'
    )

    mock_redis.hget.return_value = '{"taxa": 5.0, "fonte": "manual"}'
    rate: Optional[float] = dao.get_rate("BRL")
    assert rate == 5.0
    mock_redis.hget.assert_called_once_with("taxas_cambio", "BRL")


def test_save_rate_with_bcb_source() -> None:
    """Testa o cadastro de uma taxa com fonte explícita (ex: 'bcb')."""
    mock_redis: MagicMock = MagicMock()
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    dao.save_rate("USD", 1.0, source="bcb")
    mock_redis.hset.assert_called_once_with(
        "taxas_cambio", "USD", '{"taxa": 1.0, "fonte": "bcb"}'
    )


def test_get_rate_details_returns_taxa_and_fonte() -> None:
    """Testa que get_rate_details devolve tanto a taxa quanto a fonte."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = '{"taxa": 5.25, "fonte": "bcb"}'
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    details = dao.get_rate_details("BRL")
    assert details == {"taxa": 5.25, "fonte": "bcb"}


def test_get_rate_falls_back_to_manual_for_legacy_plain_number() -> None:
    """Testa compatibilidade com taxas gravadas antes da tag de fonte existir."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = "5.0"
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    details = dao.get_rate_details("BRL")
    assert details == {"taxa": 5.0, "fonte": "manual"}


def test_get_rate_returns_none_when_missing() -> None:
    """Testa que get_rate devolve None quando a moeda não está cadastrada."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = None
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    assert dao.get_rate("EUR") is None


def test_add_and_get_history() -> None:
    """Testa a adição e leitura do histórico de conversões via RedisHistoryDAO.

    Garante que as operações 'lpush' e 'ltrim' são disparadas no Redis e que
    os dados retornados são corretamente desserializados de JSON para dicionário.

    Returns:
        None
    """
    mock_redis: MagicMock = MagicMock()
    json_payload: str = (
        '{"valor": 100, "moeda_origem": "BRL", '
        '"moeda_destino": "ARS", "convertido": 14000}'
    )
    mock_redis.lrange.return_value = [json_payload]
    dao: RedisHistoryDAO = RedisHistoryDAO(mock_redis)

    data: Dict[str, Any] = {
        "valor": 100,
        "moeda_origem": "BRL",
        "moeda_destino": "ARS",
        "convertido": 14000,
    }
    dao.add_conversion(data)
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once_with("historico_conversoes", 0, 4)

    history: List[Dict[str, Any]] = dao.get_recent_conversions()
    assert len(history) == 1
    assert history[0]["convertido"] == 14000
