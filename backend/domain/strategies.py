"""Módulo contendo a definição do padrão Strategy para obtenção de taxas de câmbio.

Permite isolar a estratégia de consulta de taxas do serviço de cálculo,
possibilitando alternar entre banco Redis ou APIs externas sem alterar a
regra principal.
"""

from abc import ABC, abstractmethod
from typing import Optional
from backend.infrastructure.daos import RedisRateDAO


class RateStrategy(ABC):
    """Interface abstrata que define a estratégia de busca de taxas de câmbio."""

    @abstractmethod
    def get_rate(self, currency: str) -> Optional[float]:
        """Obtém a taxa de câmbio da moeda informada em relação ao USD base.

        Args:
            currency (str): Código identificador da moeda (ex: BRL, ARS, USD).

        Returns:
            Optional[float]: O valor da taxa em relação a 1 USD ou None se inexistente.
        """
        pass


class RedisRateStrategy(RateStrategy):
    """Estratégia concreta que recupera as taxas de câmbio armazenadas no Redis."""

    def __init__(self, rate_dao: RedisRateDAO) -> None:
        """Inicializa a estratégia RedisRateStrategy.

        Args:
            rate_dao (RedisRateDAO): Instância do DAO para acesso às taxas no Redis.
        """
        self.rate_dao: RedisRateDAO = rate_dao

    def get_rate(self, currency: str) -> Optional[float]:
        """Consulta a taxa de câmbio no banco Redis.

        Args:
            currency (str): Código da moeda a ser consultada.

        Returns:
            Optional[float]: Valor numérico da taxa ou None.
        """
        return self.rate_dao.get_rate(currency)
