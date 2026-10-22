"""Ponto de entrada da aplicação FastAPI do Conversor de Moedas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from backend.api.exceptions import (
    key_error_handler,
    validation_error_handler,
    value_error_handler,
)
from backend.api.routers import router
from backend.core.logger import logger
from backend.domain.rate_sync_service import RateSyncService
from backend.domain.services import CurrencyService
from backend.domain.strategies import RedisRateStrategy
from backend.infrastructure.daos import RedisHistoryDAO, RedisRateDAO
from backend.infrastructure.redis_client import get_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pré-carrega as taxas base no startup (BRL/USD via BCB, ARS como referência).

    Falhas aqui (Redis ou BCB fora do ar) não podem impedir o boot da aplicação,
    por isso qualquer erro é apenas logado como aviso.
    """
    try:
        redis_client = get_redis_client()
        rate_dao = RedisRateDAO(redis_client)
        history_dao = RedisHistoryDAO(redis_client)
        strategy = RedisRateStrategy(rate_dao)
        service = CurrencyService(strategy, rate_dao, history_dao)
        RateSyncService(service).ensure_preloaded_rates()
    except Exception as exc:  # noqa: BLE001 - startup nao pode falhar por isso
        logger.warning(f"Pre-carregamento de taxas falhou no startup: {exc}")

    yield


app: FastAPI = FastAPI(
    title="API Conversor de Moedas - MELI",
    description="API RESTful para conversão de moedas e gestão de taxas.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Habilitar CORS para permitira integração do Frontend na Vercel/GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar tratadores globais de erros
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(KeyError, key_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Registrar rotas da API
app.include_router(router)
