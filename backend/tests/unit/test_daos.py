"""Testes unitários para a camada de Data Access Objects (DAOs).

Valida o comportamento individual dos métodos de persistência e leitura de taxas
e histórico de conversões no Redis utilizando dublês de teste (mocks).
"""

import json
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO


def test_save_and_get_rate_default_source_is_manual() -> None:
    """Testa o salvamento e busca de taxa via RedisRateDAO com a fonte padrão.

    Verifica se 'hset'/'hget' são chamados com as chaves corretas, se a taxa é
    gravada como JSON contendo a tag de fonte e timestamp, e se a leitura
    devolve o valor numérico esperado.

    Returns:
        None
    """
    mock_redis: MagicMock = MagicMock()
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    resultado = dao.save_rate("BRL", 5.0)
    args, _ = mock_redis.hset.call_args
    payload = json.loads(args[2])
    assert args[0:2] == ("taxas_cambio", "BRL")
    assert payload["taxa"] == 5.0
    assert payload["fonte"] == "manual"
    assert resultado["atualizado_em"] == payload["atualizado_em"]

    mock_redis.hget.return_value = args[2]
    rate: Optional[float] = dao.get_rate("BRL")
    assert rate == 5.0
    mock_redis.hget.assert_called_once_with("taxas_cambio", "BRL")


def test_save_rate_with_bcb_source() -> None:
    """Testa o cadastro de uma taxa com fonte explícita (ex: 'bcb')."""
    mock_redis: MagicMock = MagicMock()
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    dao.save_rate("USD", 1.0, source="bcb")
    args, _ = mock_redis.hset.call_args
    payload = json.loads(args[2])
    assert args[0:2] == ("taxas_cambio", "USD")
    assert payload["taxa"] == 1.0
    assert payload["fonte"] == "bcb"
    assert "atualizado_em" in payload


def test_get_rate_details_returns_taxa_fonte_e_timestamp() -> None:
    """Testa que get_rate_details devolve taxa, fonte e atualizado_em."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = (
        '{"taxa": 5.25, "fonte": "bcb", "atualizado_em": "2026-10-22T02:30:15+00:00"}'
    )
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    details = dao.get_rate_details("BRL")
    assert details == {
        "taxa": 5.25,
        "fonte": "bcb",
        "atualizado_em": "2026-10-22T02:30:15+00:00",
    }


def test_get_rate_falls_back_to_manual_for_legacy_plain_number() -> None:
    """Testa compatibilidade com taxas gravadas antes da tag de fonte existir."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = "5.0"
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    details = dao.get_rate_details("BRL")
    assert details == {"taxa": 5.0, "fonte": "manual", "atualizado_em": None}


def test_get_rate_returns_none_when_missing() -> None:
    """Testa que get_rate devolve None quando a moeda não está cadastrada."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hget.return_value = None
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    assert dao.get_rate("EUR") is None


def test_get_all_rates_returns_every_currency() -> None:
    """Testa que get_all_rates devolve todas as moedas cadastradas no hash."""
    mock_redis: MagicMock = MagicMock()
    mock_redis.hgetall.return_value = {
        "BRL": json.dumps(
            {"taxa": 5.0, "fonte": "bcb", "atualizado_em": "2026-10-22T02:00:00+00:00"}
        ),
        "ARS": json.dumps(
            {
                "taxa": 1000.0,
                "fonte": "manual",
                "atualizado_em": "2026-10-21T10:00:00+00:00",
            }
        ),
    }
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    taxas = dao.get_all_rates()
    moedas = {t["moeda"] for t in taxas}
    assert moedas == {"BRL", "ARS"}
    brl = next(t for t in taxas if t["moeda"] == "BRL")
    assert brl["taxa"] == 5.0
    assert brl["fonte"] == "bcb"


def test_add_rate_history_entry_prunes_entries_older_than_7_days() -> None:
    """Testa que add_rate_history_entry grava e poda o que passou dos 7 dias."""
    mock_redis: MagicMock = MagicMock()
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    dao.add_rate_history_entry("EUR", 6.1, "manual")

    zadd_args, _ = mock_redis.zadd.call_args
    assert zadd_args[0] == "historico_taxas"
    ((entrada, score),) = zadd_args[1].items()
    payload = json.loads(entrada)
    assert payload["moeda"] == "EUR"
    assert payload["taxa"] == 6.1

    zrem_args, _ = mock_redis.zremrangebyscore.call_args
    assert zrem_args[0] == "historico_taxas"
    assert zrem_args[1] == 0
    assert abs(zrem_args[2] - (score - 7 * 86400)) < 1


def test_get_rate_history_returns_newest_first() -> None:
    """Testa que get_rate_history devolve as entradas dentro da janela de 7 dias."""
    mock_redis: MagicMock = MagicMock()
    entradas = [
        json.dumps({"moeda": "BRL", "taxa": 5.1, "fonte": "bcb"}),
        json.dumps({"moeda": "EUR", "taxa": 6.0, "fonte": "manual"}),
    ]
    mock_redis.zrevrangebyscore.return_value = entradas
    dao: RedisRateDAO = RedisRateDAO(mock_redis)

    historico = dao.get_rate_history()
    assert [h["moeda"] for h in historico] == ["BRL", "EUR"]
    call_args = mock_redis.zrevrangebyscore.call_args[0]
    assert call_args[0] == "historico_taxas"
    assert call_args[1] == "+inf"
    assert abs(call_args[2] - (time.time() - 7 * 86400)) < 1


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
