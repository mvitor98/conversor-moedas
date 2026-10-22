"""Testes unitários para o RateSyncService (sincronização com o BCB/PTAX)."""

from unittest.mock import MagicMock, patch
import pytest
from backend.domain.rate_sync_service import RateSyncService
from backend.domain.services import CurrencyService


def _build_sync_service() -> tuple:
    mock_rate_dao = MagicMock()
    mock_rate_dao.save_rate.side_effect = lambda moeda, valor, fonte: {
        "moeda": moeda,
        "taxa": valor,
        "fonte": fonte,
    }
    service = CurrencyService(MagicMock(), mock_rate_dao, MagicMock())
    return RateSyncService(service), mock_rate_dao


def test_sync_from_bcb_saves_brl_and_usd_with_bcb_source() -> None:
    """Deve gravar BRL (buscado no BCB) e USD=1.0, ambos com fonte 'bcb'."""
    sync_service, _ = _build_sync_service()

    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate", return_value=5.0134
    ) as mock_fetch:
        resultado = sync_service.sync_from_bcb()

    mock_fetch.assert_called_once_with("USD")
    assert resultado == {"BRL": 5.0134, "USD": 1.0}


def test_sync_currency_from_bcb_uses_cross_rate_via_brl() -> None:
    """Para moedas que não são BRL/USD, calcula a taxa cruzada via BRL."""
    sync_service, _ = _build_sync_service()

    def fake_fetch(moeda):
        return {"USD": 5.0, "EUR": 6.0}[moeda]

    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate", side_effect=fake_fetch
    ):
        resultado = sync_service.sync_currency_from_bcb("EUR")

    assert resultado == {"EUR": round(5.0 / 6.0, 4)}


def test_sync_currency_from_bcb_usd_is_always_one() -> None:
    """USD é a moeda-base: deve sempre gravar 1.0 sem chamar o BCB."""
    sync_service, _ = _build_sync_service()

    with patch("backend.domain.rate_sync_service.fetch_ptax_rate") as mock_fetch:
        resultado = sync_service.sync_currency_from_bcb("usd")

    mock_fetch.assert_not_called()
    assert resultado == {"USD": 1.0}


def test_sync_currency_from_bcb_raises_for_unsupported_currency() -> None:
    """Moeda fora da cobertura do PTAX deve levantar ValueError (-> 400)."""
    sync_service, _ = _build_sync_service()

    with pytest.raises(ValueError, match="ARS"):
        sync_service.sync_currency_from_bcb("ARS")


def test_ensure_preloaded_rates_seeds_ars_fallback_when_missing() -> None:
    """Deve semear ARS com fonte 'manual' quando ainda não houver taxa cadastrada."""
    sync_service, mock_rate_dao = _build_sync_service()
    mock_rate_dao.get_rate.return_value = None

    with patch("backend.domain.rate_sync_service.fetch_ptax_rate", return_value=5.0):
        sync_service.ensure_preloaded_rates()

    ars_calls = [
        call for call in mock_rate_dao.save_rate.call_args_list if call.args[0] == "ARS"
    ]
    assert len(ars_calls) == 1
    assert ars_calls[0].args[2] == "manual"


def test_ensure_preloaded_rates_does_not_overwrite_existing_ars() -> None:
    """Não deve sobrescrever uma taxa ARS já cadastrada (manual ou não)."""
    sync_service, mock_rate_dao = _build_sync_service()
    mock_rate_dao.get_rate.return_value = 950.0

    with patch("backend.domain.rate_sync_service.fetch_ptax_rate", return_value=5.0):
        sync_service.ensure_preloaded_rates()

    ars_calls = [
        call for call in mock_rate_dao.save_rate.call_args_list if call.args[0] == "ARS"
    ]
    assert ars_calls == []


def test_ensure_preloaded_rates_survives_bcb_failure() -> None:
    """Uma falha ao consultar o BCB não pode interromper o pré-carregamento."""
    sync_service, mock_rate_dao = _build_sync_service()
    mock_rate_dao.get_rate.return_value = None

    with patch(
        "backend.domain.rate_sync_service.fetch_ptax_rate",
        side_effect=RuntimeError("BCB fora do ar"),
    ):
        resultado = sync_service.ensure_preloaded_rates()

    assert resultado == {}
    ars_calls = [
        call for call in mock_rate_dao.save_rate.call_args_list if call.args[0] == "ARS"
    ]
    assert len(ars_calls) == 1
