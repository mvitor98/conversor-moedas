"""Módulo de constantes de negócio da aplicação (não configuráveis via ambiente)."""

# Limites de valor aceitos na conversão de moedas
CONVERSION_MIN_AMOUNT: float = 0.01  # Centavos
CONVERSION_MAX_AMOUNT: float = 1_000_000_000_000.0  # 10^12 (1 Trilhao)

# Chaves de persistência no Redis
RATE_HASH_KEY: str = "taxas_cambio"
HISTORY_LIST_KEY: str = "historico_conversoes"
HISTORY_MAX_ITEMS: int = 10
