"""Módulo de rotas (Controllers MVC) para a API do Conversor de Moedas."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import redis
from backend.api.dtos import (
    BcbSyncResponseDTO,
    ConversionResponseDTO,
    ErrorResponseDTO,
    RateDeleteResponseDTO,
    RateRecordDTO,
    RateResponseDTO,
)
from backend.api.rate_limiter import rate_limiter
from backend.core import constants
from backend.domain.rate_sync_service import RateSyncService
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


def get_rate_sync_service(
    service: CurrencyService = Depends(get_currency_service),
) -> RateSyncService:
    """Injeta as dependências e constrói o serviço RateSyncService.

    Args:
        service (CurrencyService): Serviço de domínio injetado.

    Returns:
        RateSyncService: Instância pronta do serviço de sincronização BCB.
    """
    return RateSyncService(service)


@router.post(
    "/taxas/{moeda}/{valor}",
    status_code=status.HTTP_201_CREATED,
    response_model=RateResponseDTO,
    responses={
        400: {"model": ErrorResponseDTO},
        429: {"model": ErrorResponseDTO},
    },
    summary="Cadastra ou atualiza uma taxa de câmbio",
    description=(
        "Armazena a taxa de câmbio de uma moeda tomando o Dólar (USD) como base."
    ),
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_WRITE_MAX))],
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
    resultado = service.save_rate(moeda, valor, fonte=constants.RATE_SOURCE_MANUAL)
    return {
        "mensagem": "Taxa salva com sucesso.",
        "moeda": resultado["moeda"],
        "taxa": resultado["taxa"],
        "fonte": resultado["fonte"],
        "atualizado_em": resultado["atualizado_em"],
    }


@router.get(
    "/converter/{valor}/{moeda_origem}/{moeda_destino}",
    status_code=status.HTTP_200_OK,
    response_model=ConversionResponseDTO,
    responses={
        400: {"model": ErrorResponseDTO},
        404: {"model": ErrorResponseDTO},
        429: {"model": ErrorResponseDTO},
    },
    summary="Converte um valor entre duas moedas",
    description="Calcula o valor convertido entre duas moedas cadastradas.",
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_READ_MAX))],
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
    responses={404: {"model": ErrorResponseDTO}, 429: {"model": ErrorResponseDTO}},
    summary="Lista o histórico das últimas 5 conversões",
    description="Retorna as conversões mais recentes executadas no sistema.",
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_READ_MAX))],
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


@router.get(
    "/taxas",
    status_code=status.HTTP_200_OK,
    response_model=List[RateRecordDTO],
    responses={404: {"model": ErrorResponseDTO}, 429: {"model": ErrorResponseDTO}},
    summary="Lista as taxas atualmente cadastradas",
    description="Retorna todas as taxas cadastradas, mais recente primeiro.",
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_READ_MAX))],
)
def get_registered_rates(
    service: CurrencyService = Depends(get_currency_service),
) -> List[Dict[str, Any]]:
    """Endpoint para listar as taxas de câmbio cadastradas atualmente.

    Args:
        service (CurrencyService): Serviço injetado.

    Returns:
        List[Dict[str, Any]]: Lista de taxas cadastradas.
    """
    return service.get_all_rates()


@router.delete(
    "/taxas/{moeda}",
    status_code=status.HTTP_200_OK,
    response_model=RateDeleteResponseDTO,
    responses={
        400: {"model": ErrorResponseDTO},
        404: {"model": ErrorResponseDTO},
        429: {"model": ErrorResponseDTO},
    },
    summary="Remove uma taxa cadastrada manualmente",
    description=(
        "Exclui a taxa cadastrada para a moeda informada. Só é permitido para "
        "taxas de fonte 'manual' — taxas sincronizadas com o BCB não podem ser "
        "excluídas, pois são atualizadas automaticamente."
    ),
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_WRITE_MAX))],
)
def delete_rate(
    moeda: str,
    service: CurrencyService = Depends(get_currency_service),
) -> Dict[str, Any]:
    """Endpoint para excluir uma taxa de câmbio cadastrada manualmente.

    Args:
        moeda (str): Código da moeda a ser removida.
        service (CurrencyService): Serviço injetado.

    Returns:
        Dict[str, Any]: Mensagem de confirmação e a moeda removida.
    """
    moeda_removida = service.delete_rate(moeda)
    return {"mensagem": "Taxa removida com sucesso.", "moeda": moeda_removida}


@router.get(
    "/taxas/historico",
    status_code=status.HTTP_200_OK,
    response_model=List[RateRecordDTO],
    responses={404: {"model": ErrorResponseDTO}, 429: {"model": ErrorResponseDTO}},
    summary="Histórico de mudanças de taxa (últimos 7 dias)",
    description=(
        "Retorna as mudanças de valor de taxas de câmbio nos últimos 7 dias, "
        "mais recente primeiro. Só registra uma entrada quando o valor muda."
    ),
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_READ_MAX))],
)
def get_rate_history(
    service: CurrencyService = Depends(get_currency_service),
) -> List[Dict[str, Any]]:
    """Endpoint para listar o histórico de mudanças de taxa dos últimos 7 dias.

    Args:
        service (CurrencyService): Serviço injetado.

    Returns:
        List[Dict[str, Any]]: Lista de mudanças de taxa recentes.
    """
    return service.get_rate_history()


@router.post(
    "/taxas/sincronizar-bcb",
    status_code=status.HTTP_200_OK,
    response_model=BcbSyncResponseDTO,
    responses={
        429: {"model": ErrorResponseDTO},
        502: {"model": ErrorResponseDTO},
    },
    summary="Sincroniza as taxas oficiais do Banco Central (PTAX)",
    description=(
        "Sem o parâmetro 'moeda', busca a cotação BRL/USD mais recente no PTAX "
        "e atualiza as taxas base do sistema. Com 'moeda', sincroniza apenas "
        "aquela moeda (deve ser uma das cobertas pelo PTAX)."
    ),
    dependencies=[Depends(rate_limiter(constants.RATE_LIMIT_SYNC_MAX))],
)
def sync_bcb_rates(
    moeda: Optional[str] = None,
    sync_service: RateSyncService = Depends(get_rate_sync_service),
) -> Dict[str, Any]:
    """Endpoint para forçar a sincronização das taxas com o BCB/PTAX.

    Args:
        moeda (Optional[str]): Moeda específica a sincronizar. Se omitido,
            sincroniza BRL e USD.
        sync_service (RateSyncService): Serviço de sincronização injetado.

    Returns:
        Dict[str, Any]: Mensagem de confirmação e as taxas sincronizadas.

    Raises:
        HTTPException: 502 se a API do BCB estiver inacessível.
    """
    try:
        if moeda:
            taxas = sync_service.sync_currency_from_bcb(moeda)
        else:
            taxas = sync_service.sync_from_bcb()
    except RuntimeError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY, content={"erro": str(exc)}
        )

    return {
        "mensagem": "Taxas sincronizadas com sucesso via BCB/PTAX.",
        "taxas": taxas,
    }
