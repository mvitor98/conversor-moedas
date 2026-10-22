"""Módulo de constantes de negócio da aplicação (não configuráveis via ambiente)."""

# Limites de valor aceitos na conversão de moedas
CONVERSION_MIN_AMOUNT: float = 0.01  # Centavos
CONVERSION_MAX_AMOUNT: float = 1_000_000_000_000.0  # 10^12 (1 Trilhao)

# Chaves de persistência no Redis
RATE_HASH_KEY: str = "taxas_cambio"
HISTORY_LIST_KEY: str = "historico_conversoes"
HISTORY_MAX_ITEMS: int = 5
RATE_HISTORY_KEY: str = "historico_taxas"
RATE_HISTORY_DAYS: int = 7

# Tags de proveniência de uma taxa de câmbio
RATE_SOURCE_MANUAL: str = "manual"
RATE_SOURCE_BCB: str = "bcb"

# Moeda base do sistema (sempre 1.0 em relação a si mesma)
BASE_CURRENCY: str = "USD"

# ARS não é coberto pela API PTAX do Banco Central (ver bcb_client.py). Valor de
# referência inicial para pré-carregamento; atualizável via POST /taxas/ARS/{valor}.
ARS_FALLBACK_RATE: float = 1000.0

# Rate limiting (janela fixa, por IP, contado no Redis já configurado)
RATE_LIMIT_WINDOW_SECONDS: int = 60
RATE_LIMIT_READ_MAX: int = 100  # consultas (GET): conversão, históricos, listagens
RATE_LIMIT_WRITE_MAX: int = 20  # cadastro manual de taxa
RATE_LIMIT_SYNC_MAX: int = 10  # sincronização com o BCB (chama uma API externa)
