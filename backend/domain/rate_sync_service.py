"""Serviço de sincronização das taxas de câmbio com a API PTAX do Banco Central."""

from backend.core import constants
from backend.core.logger import logger
from backend.domain.services import CurrencyService
from backend.infrastructure.bcb_client import fetch_ptax_rate


class RateSyncService:
    """Orquestra o pré-carregamento e a atualização das taxas base do sistema."""

    def __init__(self, currency_service: CurrencyService):
        self.currency_service = currency_service

    def sync_from_bcb(self) -> dict:
        """Busca a cotação BRL/USD mais recente no BCB e grava com fonte 'bcb'.

        Returns:
            dict: Mapa moeda -> taxa com os valores sincronizados.

        Raises:
            RuntimeError: Se a API do BCB estiver inacessível ou sem dados.
        """
        # O parâmetro @moeda do PTAX é a moeda ESTRANGEIRA consultada; o retorno já
        # vem expresso em BRL. Ou seja, fetch_ptax_rate("USD") devolve "quantos BRL
        # valem 1 USD" — exatamente a taxa que o nosso modelo espera para o BRL.
        taxa_brl = fetch_ptax_rate("USD")
        resultado_brl = self.currency_service.save_rate(
            "BRL", taxa_brl, fonte=constants.RATE_SOURCE_BCB
        )
        resultado_usd = self.currency_service.save_rate(
            constants.BASE_CURRENCY, 1.0, fonte=constants.RATE_SOURCE_BCB
        )
        logger.info(f"Taxas sincronizadas via BCB/PTAX: BRL={taxa_brl}")
        return {
            resultado_brl["moeda"]: resultado_brl["taxa"],
            resultado_usd["moeda"]: resultado_usd["taxa"],
        }

    def seed_fallback_rate_if_missing(self, moeda: str, valor_padrao: float) -> None:
        """Garante uma taxa mínima de referência para moedas fora do PTAX."""
        if self.currency_service.rate_dao.get_rate(moeda) is None:
            self.currency_service.save_rate(
                moeda, valor_padrao, fonte=constants.RATE_SOURCE_MANUAL
            )
            logger.info(f"Taxa de referência semeada para {moeda}: {valor_padrao}")

    def ensure_preloaded_rates(self) -> dict:
        """Garante que BRL/USD/ARS existam no startup, sem derrubar a aplicação.

        BRL e USD vêm do BCB; ARS não é coberto pelo PTAX e recebe um valor de
        referência fixo (fonte 'manual') apenas se ainda não houver taxa cadastrada.
        """
        taxas_sincronizadas = {}
        try:
            taxas_sincronizadas = self.sync_from_bcb()
        except RuntimeError as exc:
            logger.warning(f"Sincronizacao com o BCB falhou no startup: {exc}")

        self.seed_fallback_rate_if_missing("ARS", constants.ARS_FALLBACK_RATE)
        return taxas_sincronizadas
