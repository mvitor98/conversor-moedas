"""Testes unitários para a camada de serviços (CurrencyService)."""

from typing import Any, Dict
from unittest.mock import MagicMock
import pytest
from backend.domain.services import CurrencyService


def test_convert_success() -> None:
    """Testa o cálculo de conversão entre BRL e ARS com sucesso."""
    mock_strategy: MagicMock = MagicMock()
    mock_rate_dao: MagicMock = MagicMock()
    mock_history_dao: MagicMock = MagicMock()

    mock_strategy.get_rate.side_effect = lambda c: 5.0 if c == "BRL" else 700.0

    service: CurrencyService = CurrencyService(
        mock_strategy, mock_rate_dao, mock_history_dao
    )
    res: Dict[str, Any] = service.convert(100.0, "BRL", "ARS")

    assert res["convertido"] == 14000.0
    mock_history_dao.add_conversion.assert_called_once()


def test_convert_same_currency_raises_value_error() -> None:
    """Testa se tentar converter para a mesma moeda gera ValueError."""
    service: CurrencyService = CurrencyService(MagicMock(), MagicMock(), MagicMock())
    with pytest.raises(ValueError, match="não pode ser igual"):
        service.convert(100.0, "BRL", "BRL")


def test_convert_missing_rate_raises_key_error() -> None:
    """Testa se moeda sem taxa gravada gera KeyError."""
    mock_strategy: MagicMock = MagicMock()
    mock_strategy.get_rate.return_value = None

    service: CurrencyService = CurrencyService(mock_strategy, MagicMock(), MagicMock())
    with pytest.raises(KeyError, match=r"Moeda\(s\) sem taxa cadastrada"):
        service.convert(100.0, "BRL", "ARS")


def test_save_rate_defaults_to_manual_source() -> None:
    """Testa se save_rate grava a taxa com fonte 'manual' por padrão."""
    mock_rate_dao: MagicMock = MagicMock()
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    service.save_rate("BRL", 5.0)
    mock_rate_dao.save_rate.assert_called_once_with("BRL", 5.0, "manual")


def test_save_rate_accepts_explicit_source() -> None:
    """Testa se save_rate repassa uma fonte explícita (ex: 'bcb') ao DAO."""
    mock_rate_dao: MagicMock = MagicMock()
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    service.save_rate("USD", 1.0, fonte="bcb")
    mock_rate_dao.save_rate.assert_called_once_with("USD", 1.0, "bcb")


def test_get_history_raises_key_error_when_empty() -> None:
    """Testa se get_history gera KeyError (-> 404) quando não há conversões."""
    mock_history_dao: MagicMock = MagicMock()
    mock_history_dao.get_recent_conversions.return_value = []

    service: CurrencyService = CurrencyService(
        MagicMock(), MagicMock(), mock_history_dao
    )
    with pytest.raises(KeyError, match="Nenhuma conversão registrada"):
        service.get_history()


def test_save_rate_logs_history_when_value_changes() -> None:
    """Deve registrar uma entrada de histórico quando o valor da taxa muda."""
    mock_rate_dao: MagicMock = MagicMock()
    mock_rate_dao.get_rate_details.return_value = {"taxa": 5.0, "fonte": "manual"}
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    service.save_rate("BRL", 5.2)

    mock_rate_dao.add_rate_history_entry.assert_called_once_with("BRL", 5.2, "manual")


def test_save_rate_skips_history_when_value_unchanged() -> None:
    """Não deve registrar histórico se o valor salvo é igual ao anterior."""
    mock_rate_dao: MagicMock = MagicMock()
    mock_rate_dao.get_rate_details.return_value = {"taxa": 5.2, "fonte": "manual"}
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    service.save_rate("BRL", 5.2)

    mock_rate_dao.add_rate_history_entry.assert_not_called()


def test_save_rate_logs_history_on_first_registration() -> None:
    """Deve registrar histórico quando a moeda ainda não tinha taxa cadastrada."""
    mock_rate_dao: MagicMock = MagicMock()
    mock_rate_dao.get_rate_details.return_value = None
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    service.save_rate("EUR", 6.0)

    mock_rate_dao.add_rate_history_entry.assert_called_once_with("EUR", 6.0, "manual")


def test_get_all_rates_sorts_by_most_recent_and_raises_when_empty() -> None:
    """Testa que get_all_rates ordena por atualizado_em (desc) e levanta 404 vazio."""
    mock_rate_dao: MagicMock = MagicMock()
    mock_rate_dao.get_all_rates.return_value = [
        {
            "moeda": "ARS",
            "taxa": 1000.0,
            "fonte": "manual",
            "atualizado_em": "2026-10-20T10:00:00+00:00",
        },
        {
            "moeda": "BRL",
            "taxa": 5.0,
            "fonte": "bcb",
            "atualizado_em": "2026-10-22T10:00:00+00:00",
        },
    ]
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    taxas = service.get_all_rates()
    assert [t["moeda"] for t in taxas] == ["BRL", "ARS"]

    mock_rate_dao.get_all_rates.return_value = []
    with pytest.raises(KeyError, match="Nenhuma taxa cadastrada"):
        service.get_all_rates()


def test_get_rate_history_raises_key_error_when_empty() -> None:
    """Testa que get_rate_history gera KeyError (-> 404) quando não há mudanças."""
    mock_rate_dao: MagicMock = MagicMock()
    mock_rate_dao.get_rate_history.return_value = []
    service: CurrencyService = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())

    with pytest.raises(KeyError, match="Nenhuma mudança de taxa"):
        service.get_rate_history()
