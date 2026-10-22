"""Módulo contendo os Data Transfer Objects (DTOs) para a API."""

from typing import Dict
from pydantic import BaseModel, Field


class RateResponseDTO(BaseModel):
    """DTO de resposta para a operação de cadastro de taxa de câmbio."""

    mensagem: str = Field(..., description="Mensagem de sucesso do cadastro.")
    moeda: str = Field(
        ...,
        description="Moeda cadastrada.",
        json_schema_extra={"example": "ARS"},
    )
    taxa: float = Field(
        ...,
        description="Valor da taxa gravada.",
        json_schema_extra={"example": 700.0},
    )
    fonte: str = Field(
        ...,
        description="Origem da taxa: 'manual' (cadastrada via API) ou 'bcb' (PTAX).",
        json_schema_extra={"example": "manual"},
    )


class ConversionResponseDTO(BaseModel):
    """DTO de resposta para a operação de conversão de moeda."""

    valor: float = Field(
        ...,
        description="Valor original submetido.",
        json_schema_extra={"example": 100.0},
    )
    moeda_origem: str = Field(
        ...,
        description="Moeda de origem.",
        json_schema_extra={"example": "BRL"},
    )
    moeda_destino: str = Field(
        ...,
        description="Moeda de destino.",
        json_schema_extra={"example": "ARS"},
    )
    convertido: float = Field(
        ...,
        description="Valor retornado.",
        json_schema_extra={"example": 14000.0},
    )


class BcbSyncResponseDTO(BaseModel):
    """DTO de resposta para a sincronização de taxas com o BCB/PTAX."""

    mensagem: str = Field(..., description="Mensagem de confirmação da sincronização.")
    taxas: Dict[str, float] = Field(
        ...,
        description="Taxas sincronizadas (moeda -> valor em relação a 1 USD).",
        json_schema_extra={"example": {"BRL": 5.0134, "USD": 1.0}},
    )


class ErrorResponseDTO(BaseModel):
    """DTO genérico para retorno padronizado de mensagens de erro."""

    erro: str = Field(..., description="Descrição detalhada da falha ocorrida.")
