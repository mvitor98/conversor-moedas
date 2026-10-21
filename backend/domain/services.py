"""Módulo de serviços de domínio para cálculo de conversão e histórico.

Contém a lógica central de conversão monetária baseada em Dólar (USD)
e orquestra as interações entre os DAOs de taxas e histórico.
"""

from typing import Any, Dict, List, Optional
from backend.domain.strategies import RateStrategy
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO


class CurrencyService:
    """Serviço responsável por executar cálculos de conversão e gestão de taxas."""

    def __init__(
        self,
        rate_strategy: RateStrategy,
        rate_dao: RedisRateDAO,
        history_dao: RedisHistoryDAO,
    ) -> None:
        """Inicializa o serviço de conversão de moedas.

        Args:
            rate_strategy (RateStrategy): Estratégia utilizada para obter taxas.
            rate_dao (RedisRateDAO): DAO para salvar e gerenciar taxas.
            history_dao (RedisHistoryDAO): DAO para persistir o histórico.
        """
        self.rate_strategy: RateStrategy = rate_strategy
        self.rate_dao: RedisRateDAO = rate_dao
        self.history_dao: RedisHistoryDAO = history_dao

    def save_rate(self, currency: str, rate: float) -> None:
        """Cadastra ou atualiza uma taxa de câmbio após validações.

        Args:
            currency (str): Código identificador da moeda (ex: BRL).
            rate (float): Taxa de câmbio em relação a 1 USD.

        Raises:
            ValueError: Se o valor da taxa for menor ou igual a zero.
        """
        if rate <= 0:
            raise ValueError("O valor da taxa de câmbio deve ser maior que zero.")

        cleaned_currency: str = currency.strip().upper()
        if not cleaned_currency.isalpha():
            raise ValueError("O código da moeda deve conter apenas letras.")

        self.rate_dao.save_rate(cleaned_currency, rate)

    def convert(
        self, amount: float, origin_currency: str, destination_currency: str
    ) -> Dict[str, Any]:
        """Realiza o cálculo da conversão entre duas moedas.

        Fórmula: valor_convertido = (valor / taxa_origem) * taxa_destino

        Args:
            amount (float): Quantia a ser convertida.
            origin_currency (str): Código da moeda de origem.
            destination_currency (str): Código da moeda de destino.

        Returns:
            Dict[str, Any]: Dicionário com o resultado formatado da conversão.

        Raises:
            ValueError: Se o valor <= 0, moedas inválidas ou de origem igual a destino.
            KeyError: Se alguma das moedas não tiver taxa cadastrada.
        """
        if amount <= 0:
            raise ValueError("O valor para conversão deve ser maior que zero.")

        origin: str = origin_currency.strip().upper()
        destination: str = destination_currency.strip().upper()

        if not origin.isalpha() or not destination.isalpha():
            raise ValueError("Os códigos das moedas devem conter apenas letras.")

        if origin == destination:
            raise ValueError("A moeda de origem não pode ser igual à de destino.")

        origin_rate: Optional[float] = self.rate_strategy.get_rate(origin)
        destination_rate: Optional[float] = self.rate_strategy.get_rate(destination)

        missing_currencies: List[str] = []
        if origin_rate is None:
            missing_currencies.append(origin)
        if destination_rate is None:
            missing_currencies.append(destination)

        if missing_currencies:
            missing_str: str = ", ".join(missing_currencies)
            raise KeyError(f"Moeda(s) sem taxa cadastrada: {missing_str}")

        converted_raw: float = (amount / origin_rate) * destination_rate
        converted_value: float = round(converted_raw, 2)

        result: Dict[str, Any] = {
            "valor": amount,
            "moeda_origem": origin,
            "moeda_destino": destination,
            "convertido": converted_value,
        }

        self.history_dao.add_conversion(result)
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """Recupera as últimas 5 conversões gravadas no histórico.

        Returns:
            List[Dict[str, Any]]: Lista de registros de conversões recentes.

        Raises:
            KeyError: Se o histórico estiver vazio.
        """
        history: List[Dict[str, Any]] = self.history_dao.get_recent_conversions()
        if not history:
            raise KeyError("Ainda não existe nenhuma conversão registrada.")
        return history
