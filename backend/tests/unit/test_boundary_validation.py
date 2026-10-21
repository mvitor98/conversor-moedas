from unittest.mock import MagicMock
import pytest
from backend.domain.services import CurrencyService


def test_convert_amount_below_minimum_raises_value_error():
    mock_strategy = MagicMock()
    mock_rate_dao = MagicMock()
    mock_history_dao = MagicMock()
    service = CurrencyService(mock_strategy, mock_rate_dao, mock_history_dao)

    with pytest.raises(ValueError) as exc_info:
        service.convert(0.001, "BRL", "USD")
    assert "deve estar entre 0.01" in str(exc_info.value)


def test_convert_amount_above_maximum_raises_value_error():
    mock_strategy = MagicMock()
    mock_rate_dao = MagicMock()
    mock_history_dao = MagicMock()
    service = CurrencyService(mock_strategy, mock_rate_dao, mock_history_dao)

    with pytest.raises(ValueError) as exc_info:
        service.convert(1_000_000_000_001.0, "BRL", "USD")
    assert "1 trilhao" in str(exc_info.value)
