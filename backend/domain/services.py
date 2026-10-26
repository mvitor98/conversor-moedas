import re

from backend.core import constants
from backend.domain.strategies import RateStrategy
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO


class CurrencyService:
    def __init__(
        self,
        rate_strategy: RateStrategy,
        rate_dao: RedisRateDAO,
        history_dao: RedisHistoryDAO,
    ):
        self.rate_strategy = rate_strategy
        self.rate_dao = rate_dao
        self.history_dao = history_dao

    @staticmethod
    def _validar_formato_moeda(moeda: str) -> None:
        """Rejeita códigos de moeda com formato inválido (400), antes de
        verificar se há taxa cadastrada (404)."""
        if not re.match(constants.CURRENCY_CODE_PATTERN, moeda):
            raise ValueError(
                f"'{moeda}' não é um código de moeda válido "
                "(use de 3 a 5 letras, ex: BRL, EUR, CLP)."
            )

    def save_rate(
        self, moeda: str, valor: float, fonte: str = constants.RATE_SOURCE_MANUAL
    ) -> dict:
        moeda = moeda.upper()
        self._validar_formato_moeda(moeda)
        if valor <= 0:
            raise ValueError("O valor da taxa deve ser maior que zero.")
        valor_arredondado = round(valor, 4)

        taxa_anterior = self.rate_dao.get_rate_details(moeda)
        resultado = self.rate_dao.save_rate(moeda, valor_arredondado, fonte)

        if taxa_anterior is None or taxa_anterior["taxa"] != valor_arredondado:
            self.rate_dao.add_rate_history_entry(moeda, valor_arredondado, fonte)

        return resultado

    def convert(self, valor: float, origem: str, destino: str) -> dict:
        origem = origem.upper()
        destino = destino.upper()
        self._validar_formato_moeda(origem)
        self._validar_formato_moeda(destino)

        if origem == destino:
            raise ValueError("A moeda de origem e destino não pode ser igual.")

        if (
            valor < constants.CONVERSION_MIN_AMOUNT
            or valor > constants.CONVERSION_MAX_AMOUNT
        ):
            min_valor = constants.CONVERSION_MIN_AMOUNT
            msg = f"O valor deve estar entre {min_valor} e 1 trilhao."
            raise ValueError(msg)

        taxa_origem = self.rate_strategy.get_rate(origem)
        taxa_destino = self.rate_strategy.get_rate(destino)

        if taxa_origem is None or taxa_destino is None:
            raise KeyError("Moeda(s) sem taxa cadastrada.")

        valor_em_usd = valor / taxa_origem
        valor_convertido = round(valor_em_usd * taxa_destino, 4)

        resultado = {
            "valor": round(valor, 4),
            "moeda_origem": origem,
            "moeda_destino": destino,
            "convertido": valor_convertido,
        }

        self.history_dao.add_conversion(resultado)
        return resultado

    def get_history(self) -> list:
        if hasattr(self.history_dao, "get_recent_conversions"):
            historico = self.history_dao.get_recent_conversions()
        else:
            historico = self.history_dao.get_history()

        if not historico:
            raise KeyError("Nenhuma conversão registrada.")
        return historico

    def get_all_rates(self) -> list:
        taxas = self.rate_dao.get_all_rates()
        if not taxas:
            raise KeyError("Nenhuma taxa cadastrada.")
        taxas.sort(key=lambda t: t.get("atualizado_em") or "", reverse=True)
        return taxas

    def get_rate_history(self) -> list:
        historico = self.rate_dao.get_rate_history()
        if not historico:
            raise KeyError("Nenhuma mudança de taxa registrada nos últimos dias.")
        return historico

    def delete_rate(self, moeda: str) -> str:
        moeda = moeda.upper()
        taxa_atual = self.rate_dao.get_rate_details(moeda)
        if taxa_atual is None:
            raise KeyError("Nenhuma taxa cadastrada para essa moeda.")
        if taxa_atual["fonte"] != constants.RATE_SOURCE_MANUAL:
            raise ValueError(
                "Só é possível excluir taxas cadastradas manualmente. "
                "Taxas sincronizadas com o BCB são atualizadas automaticamente."
            )
        self.rate_dao.delete_rate(moeda)
        return moeda


CurrencyConverterService = CurrencyService
