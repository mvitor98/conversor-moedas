"""Testes unitários para a camada de Data Access Objects (DAOs).

Valida o comportamento individual dos métodos de persistência e leitura de taxas
e histórico de conversões no Redis utilizando dublês de teste (mocks).
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO


def test_save_and_get_rate() -> None:
    """Testa o salvamento e busca de taxa de câmbio via RedisRateDAO com mock.

    Verifica se os comandos 'hset' e 'hget' do Redis são invocados com as chaves
    e valores corretos e se a conversão de tipo de retorno ocorre adequadamente.

    Returns:
        None
    """
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = "5.0"
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    dao.save_rate("BRL", 5.0)
    mock_redis.hset.assert_called_once_with("taxas_cambio", "BRL", "5.0")

    rate: Optional[float] = dao.get_rate("BRL")
    assert rate == 5.0
    mock_redis.hget.assert_called_once_with("taxas_cambio", "BRL")


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
    mock_redis.ltrim.assert_called_once_with("historico_conversoes", 0, 9)

    history: List[Dict[str, Any]] = dao.get_recent_conversions()
    assert len(history) == 1
    assert history[0]["convertido"] == 14000
