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

    def save_rate(
        self, moeda: str, valor: float, fonte: str = constants.RATE_SOURCE_MANUAL
    ) -> dict:
        moeda = moeda.upper()
        if valor <= 0:
            raise ValueError("O valor da taxa deve ser maior que zero.")
        valor_arredondado = round(valor, 4)
        return self.rate_dao.save_rate(moeda, valor_arredondado, fonte)

    def convert(self, valor: float, origem: str, destino: str) -> dict:
        origem = origem.upper()
        destino = destino.upper()

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


CurrencyConverterService = CurrencyService
