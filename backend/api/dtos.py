"""Módulo contendo os Data Transfer Objects (DTOs) para a API."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class RateResponseDTO(BaseModel):
    """DTO de resposta para a operação de cadastro de taxa de câmbio."""

    mensagem: str = Field(
        ...,
        description="Mensagem de sucesso do cadastro.",
        json_schema_extra={"example": "Taxa salva com sucesso."},
    )
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
    atualizado_em: str = Field(
        ...,
        description="Data/hora (UTC, precisão de segundo) do registro.",
        json_schema_extra={"example": "2026-10-22T02:30:15+00:00"},
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


class RateRecordDTO(BaseModel):
    """DTO de resposta para uma taxa cadastrada ou uma entrada de histórico."""

    moeda: str = Field(..., description="Moeda.", json_schema_extra={"example": "EUR"})
    taxa: float = Field(
        ...,
        description="Valor da taxa em relação a 1 USD.",
        json_schema_extra={"example": 0.92},
    )
    fonte: str = Field(
        ...,
        description="Origem da taxa: 'manual' ou 'bcb' (PTAX).",
        json_schema_extra={"example": "bcb"},
    )
    atualizado_em: Optional[str] = Field(
        None,
        description=(
            "Data/hora (UTC, precisão de segundo) do registro. Nulo para taxas "
            "gravadas antes dessa informação existir."
        ),
        json_schema_extra={"example": "2026-10-22T02:30:15+00:00"},
    )


class RateDeleteResponseDTO(BaseModel):
    """DTO de resposta para a exclusão de uma taxa de câmbio."""

    mensagem: str = Field(
        ...,
        description="Mensagem de confirmação da exclusão.",
        json_schema_extra={"example": "Taxa removida com sucesso."},
    )
    moeda: str = Field(
        ..., description="Moeda removida.", json_schema_extra={"example": "EUR"}
    )


class BcbSyncResponseDTO(BaseModel):
    """DTO de resposta para a sincronização de taxas com o BCB/PTAX."""

    mensagem: str = Field(
        ...,
        description="Mensagem de confirmação da sincronização.",
        json_schema_extra={"example": "Taxas sincronizadas com sucesso via BCB/PTAX."},
    )
    taxas: Dict[str, float] = Field(
        ...,
        description="Taxas sincronizadas (moeda -> valor em relação a 1 USD).",
        json_schema_extra={"example": {"BRL": 5.0134, "USD": 1.0}},
    )


class ErrorResponseDTO(BaseModel):
    """DTO genérico para retorno padronizado de mensagens de erro."""

    erro: str = Field(
        ...,
        description="Descrição detalhada da falha ocorrida.",
        json_schema_extra={"example": "Moeda(s) sem taxa cadastrada."},
    )
