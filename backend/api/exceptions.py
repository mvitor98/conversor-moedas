"""Módulo de tratamento centralizado de exceções HTTP da API."""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.core.logger import logger


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Mapeia exceções do tipo ValueError para retornos HTTP 400 Bad Request.

    Args:
        request (Request): Instância da requisição HTTP.
        exc (ValueError): Exceção capturada.

    Returns:
        JSONResponse: Resposta com status 400 e payload em formato JSON.
    """
    msg: str = str(exc)
    logger.warning(f"Erro 400 Bad Request em {request.url.path}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"erro": msg},
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Mapeia erros de validação de parâmetros (ex: valor não numérico) para 400.

    Por padrão o FastAPI retorna 422 para esses casos; a API do desafio exige
    400 Bad Request para entradas inválidas (ex: valores não numéricos).

    Args:
        request (Request): Instância da requisição HTTP.
        exc (RequestValidationError): Exceção capturada.

    Returns:
        JSONResponse: Resposta com status 400 e payload em formato JSON.
    """
    logger.warning(f"Erro 400 Bad Request em {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"erro": "Parâmetros inválidos."},
    )


async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Mapeia exceções do tipo KeyError para retornos HTTP 404 Not Found.

    Args:
        request (Request): Instância da requisição HTTP.
        exc (KeyError): Exceção capturada.

    Returns:
        JSONResponse: Resposta com status 404 e payload em formato JSON.
    """
    cleaned_msg: str = str(exc).strip("'\"")
    logger.warning(f"Erro 404 Not Found em {request.url.path}: {cleaned_msg}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"erro": cleaned_msg},
    )
