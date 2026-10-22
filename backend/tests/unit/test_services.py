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
