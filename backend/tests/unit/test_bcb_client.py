"""Testes unitários para o cliente da API PTAX do Banco Central (bcb_client.py)."""

from unittest.mock import MagicMock, patch
import httpx
import pytest
from backend.infrastructure.bcb_client import fetch_ptax_rate


def _make_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_fetch_ptax_rate_returns_closing_quote() -> None:
    """Deve retornar a cotacaoVenda do boletim 'Fechamento PTAX' do dia atual."""
    payload = {
        "value": [
            {"tipoBoletim": "Abertura", "cotacaoVenda": 5.01},
            {"tipoBoletim": "Fechamento PTAX", "cotacaoVenda": 5.0134},
        ]
    }
    with patch("httpx.get", return_value=_make_response(payload)) as mock_get:
        taxa = fetch_ptax_rate("USD")

    assert taxa == 5.0134
    assert mock_get.call_count == 1


def test_fetch_ptax_rate_skips_days_without_closing_bulletin() -> None:
    """Deve buscar dias anteriores (fins de semana/feriados) até achar um boletim."""
    empty_day = {"value": []}
    closing_day = {"value": [{"tipoBoletim": "Fechamento PTAX", "cotacaoVenda": 5.5}]}
    with patch(
        "httpx.get",
        side_effect=[_make_response(empty_day), _make_response(closing_day)],
    ) as mock_get:
        taxa = fetch_ptax_rate("USD", lookback_days=5)

    assert taxa == 5.5
    assert mock_get.call_count == 2


def test_fetch_ptax_rate_raises_when_no_data_in_lookback_window() -> None:
    """Deve levantar RuntimeError se nenhum dia no período tiver cotação."""
    empty_day = {"value": []}
    with patch("httpx.get", return_value=_make_response(empty_day)):
        with pytest.raises(RuntimeError, match="Nenhuma cotacao PTAX"):
            fetch_ptax_rate("USD", lookback_days=3)


def test_fetch_ptax_rate_wraps_network_errors() -> None:
    """Deve envolver falhas de rede/HTTP em um RuntimeError claro."""
    with patch("httpx.get", side_effect=httpx.ConnectTimeout("timeout")):
        with pytest.raises(RuntimeError, match="Falha ao consultar a API PTAX"):
            fetch_ptax_rate("USD", lookback_days=1)
