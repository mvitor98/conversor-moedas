"""Serviço de sincronização das taxas de câmbio com a API PTAX do Banco Central."""

from backend.core import constants
from backend.core.logger import logger
from backend.domain.services import CurrencyService
from backend.infrastructure.bcb_client import PTAX_SUPPORTED_CURRENCIES, fetch_ptax_rate


class RateSyncService:
    """Orquestra o pré-carregamento e a atualização das taxas base do sistema."""

    def __init__(self, currency_service: CurrencyService):
        self.currency_service = currency_service

    def sync_currency_from_bcb(self, moeda: str) -> dict:
        """Busca no BCB/PTAX a cotação de uma moeda específica e grava com fonte 'bcb'.

        O PTAX só cota moedas estrangeiras contra o BRL. Para obter "quanto vale
        1 USD" na moeda pedida, calcula-se a taxa cruzada via BRL quando
        necessário.

        Args:
            moeda (str): Código da moeda (ex: "BRL", "USD", "EUR").

        Returns:
            dict: Mapa moeda -> taxa com o valor sincronizado.

        Raises:
            ValueError: Se a moeda não for coberta pela API PTAX do BCB.
            RuntimeError: Se a API do BCB estiver inacessível ou sem dados.
        """
        moeda = moeda.upper()

        if moeda == constants.BASE_CURRENCY:
            taxa = 1.0
        elif moeda == "BRL":
            # @moeda no PTAX é a moeda ESTRANGEIRA consultada; o retorno já vem
            # expresso em BRL, entao fetch_ptax_rate("USD") ja e "quantos BRL
            # valem 1 USD" - exatamente a taxa que o BRL precisa.
            taxa = fetch_ptax_rate("USD")
        elif moeda in PTAX_SUPPORTED_CURRENCIES:
            brl_por_usd = fetch_ptax_rate("USD")
            brl_pela_moeda = fetch_ptax_rate(moeda)
            taxa = brl_por_usd / brl_pela_moeda
        else:
            raise ValueError(f"{moeda} não é coberta pela API PTAX do Banco Central.")

        resultado = self.currency_service.save_rate(
            moeda, taxa, fonte=constants.RATE_SOURCE_BCB
        )
        logger.info(f"Taxa sincronizada via BCB/PTAX: {moeda}={taxa}")
        return {resultado["moeda"]: resultado["taxa"]}

    def sync_from_bcb(self) -> dict:
        """Sincroniza BRL/USD e qualquer outra moeda já cadastrada coberta pelo PTAX.

        BRL e USD continuam obrigatórios: uma falha ao sincronizá-los propaga
        (comportamento inalterado, mapeado para 502 pelo router). Além deles,
        toda moeda já cadastrada no banco que o PTAX cobre também é
        atualizada — assim, uma moeda cadastrada manualmente ou via BCB numa
        sincronização anterior (ex: EUR) continua acompanhando o câmbio sem
        precisar ser sincronizada uma a uma. Uma falha ao sincronizar uma
        dessas moedas extras (ex: sem cotação dela no período) é registrada
        em log e não derruba a sincronização das demais.

        Returns:
            dict: Mapa moeda -> taxa com os valores sincronizados com sucesso.

        Raises:
            RuntimeError: Se BRL ou USD não puderem ser sincronizados.
        """
        taxas = {}
        taxas.update(self.sync_currency_from_bcb("BRL"))
        taxas.update(self.sync_currency_from_bcb(constants.BASE_CURRENCY))

        moedas_cadastradas = {
            registro["moeda"]
            for registro in self.currency_service.rate_dao.get_all_rates()
        }
        moedas_extras = (moedas_cadastradas & PTAX_SUPPORTED_CURRENCIES) - set(taxas)
        for moeda in sorted(moedas_extras):
            try:
                taxas.update(self.sync_currency_from_bcb(moeda))
            except RuntimeError as exc:
                logger.warning(f"Falha ao sincronizar {moeda} via BCB/PTAX: {exc}")

        return taxas

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
