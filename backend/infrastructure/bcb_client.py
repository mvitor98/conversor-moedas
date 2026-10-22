"""Cliente de integração com a API PTAX (Olinda) do Banco Central do Brasil."""

from datetime import date, timedelta
from typing import List

import httpx

PTAX_BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)"
)
PTAX_CLOSING_BULLETIN = "Fechamento PTAX"
REQUEST_TIMEOUT_SECONDS = 5.0

# Moedas estrangeiras cotadas pelo PTAX (consulta "quantos BRL vale 1 unidade
# da moeda"). BRL não é uma moeda "estrangeira" consultável por este endpoint
# (a cotação de USD já devolve BRL/USD diretamente).
PTAX_SUPPORTED_CURRENCIES = frozenset(
    {"AUD", "CAD", "CHF", "DKK", "EUR", "GBP", "JPY", "NOK", "SEK", "USD"}
)


def _fetch_quotes_for_date(moeda: str, dia: date) -> List[dict]:
    """Consulta as cotações PTAX publicadas pelo BCB em um dia específico."""
    url = (
        f"{PTAX_BASE_URL}?@moeda='{moeda}'"
        f"&@dataCotacao='{dia.strftime('%m-%d-%Y')}'&$format=json"
    )
    response = httpx.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json().get("value", [])


def fetch_ptax_rate(moeda: str, lookback_days: int = 7) -> float:
    """Busca a cotação de fechamento PTAX mais recente para a moeda informada.

    O BCB não publica cotação em finais de semana e feriados, por isso a busca
    percorre os últimos `lookback_days` dias até encontrar um boletim de
    "Fechamento PTAX".

    Args:
        moeda (str): Código da moeda no padrão PTAX (ex: "USD", "EUR").
        lookback_days (int): Quantos dias retroceder procurando uma cotação.

    Returns:
        float: Quantos reais (BRL) valem 1 unidade da moeda consultada.

    Raises:
        RuntimeError: Se nenhuma cotação for encontrada no período ou a API
            do BCB estiver inacessível.
    """
    hoje = date.today()
    for dias_atras in range(lookback_days):
        dia = hoje - timedelta(days=dias_atras)
        try:
            cotacoes = _fetch_quotes_for_date(moeda, dia)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Falha ao consultar a API PTAX do BCB: {exc}") from exc

        fechamento = next(
            (c for c in cotacoes if c.get("tipoBoletim") == PTAX_CLOSING_BULLETIN),
            None,
        )
        if fechamento is not None:
            return float(fechamento["cotacaoVenda"])

    raise RuntimeError(
        f"Nenhuma cotacao PTAX de fechamento encontrada para {moeda} "
        f"nos ultimos {lookback_days} dias."
    )
