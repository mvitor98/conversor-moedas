"""Módulo de rotas (Controllers MVC) para a API do Conversor de Moedas."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
import redis
from backend.api.dtos import ConversionResponseDTO, ErrorResponseDTO, RateResponseDTO
from backend.domain.services import CurrencyService
from backend.domain.strategies import RedisRateStrategy
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO
from backend.infrastructure.redis_client import get_redis_client

router: APIRouter = APIRouter()


def get_currency_service(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> CurrencyService:
    """Injeta as dependências e constrói o serviço CurrencyService.

    Args:
        redis_client (redis.Redis): Cliente ativo do Redis injetado.

    Returns:
        CurrencyService: Instância pronta do serviço de domínio.
    """
    rate_dao: RedisRateDAO = RedisRateDAO(redis_client)
    history_dao: RedisHistoryDAO = RedisHistoryDAO(redis_client)
    strategy: RedisRateStrategy = RedisRateStrategy(rate_dao)
    return CurrencyService(strategy, rate_dao, history_dao)


@router.post(
    "/taxas/{moeda}/{valor}",
    status_code=status.HTTP_201_CREATED,
    response_model=RateResponseDTO,
    responses={400: {"model": ErrorResponseDTO}},
    summary="Cadastra ou atualiza uma taxa de câmbio",
    description=(
        "Armazena a taxa de câmbio de uma moeda tomando o Dólar (USD) como base."
    ),
)
def save_rate(
    moeda: str,
    valor: float,
    service: CurrencyService = Depends(get_currency_service),
) -> Dict[str, Any]:
    """Endpoint para cadastrar uma taxa de câmbio.

    Args:
        moeda (str): Código da moeda (ex: ARS, BRL).
        valor (float): Quanto 1 USD vale na moeda especificada (> 0).
        service (CurrencyService): Serviço injetado.

    Returns:
        Dict[str, Any]: Dicionário de confirmação.
    """
    service.save_rate(moeda, valor)
    return {
        "mensagem": "Taxa salva com sucesso.",
        "moeda": moeda.upper(),
        "taxa": valor,
    }


@router.get(
    "/converter/{valor}/{moeda_origem}/{moeda_destino}",
    status_code=status.HTTP_200_OK,
    response_model=ConversionResponseDTO,
    responses={
        400: {"model": ErrorResponseDTO},
        404: {"model": ErrorResponseDTO},
    },
    summary="Converte um valor entre duas moedas",
    description="Calcula o valor convertido entre duas moedas cadastradas.",
)
def convert_currency(
    valor: float,
    moeda_origem: str,
    moeda_destino: str,
    service: CurrencyService = Depends(get_currency_service),
) -> Dict[str, Any]:
    """Endpoint para executar a conversão de moedas.

    Args:
        valor (float): Valor numérico a ser convertido (> 0).
        moeda_origem (str): Moeda de origem.
        moeda_destino (str): Moeda de destino.
        service (CurrencyService): Serviço injetado.

    Returns:
        Dict[str, Any]: Resultado do cálculo da conversão.
    """
    return service.convert(valor, moeda_origem, moeda_destino)


@router.get(
    "/conversoes",
    status_code=status.HTTP_200_OK,
    response_model=List[ConversionResponseDTO],
    responses={404: {"model": ErrorResponseDTO}},
    summary="Lista o histórico das últimas 5 conversões",
    description="Retorna as conversões mais recentes executadas no sistema.",
)
def get_conversion_history(
    service: CurrencyService = Depends(get_currency_service),
) -> List[Dict[str, Any]]:
    """Endpoint para listar o histórico das últimas 5 conversões.

    Args:
        service (CurrencyService): Serviço injetado.

    Returns:
        List[Dict[str, Any]]: Lista contendo as conversões mais recentes.
    """
    return service.get_history()
