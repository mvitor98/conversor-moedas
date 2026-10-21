"""Ponto de entrada da aplicação FastAPI do Conversor de Moedas."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.exceptions import key_error_handler, value_error_handler
from backend.api.routers import router

app: FastAPI = FastAPI(
    title="API Conversor de Moedas - MELI",
    description="API RESTful para conversão de moedas e gestão de taxas.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# Registrar rotas da API
app.include_router(router)
