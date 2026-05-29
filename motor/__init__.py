"""Motor de calculo de prazos processuais civeis do TJAM."""
from .calendario import CalendarioTJAM, Classificacao, Feriado
from .prazo import PassoMemoria, ResultadoPrazo, calcular_prazo
from .prazos import CatalogoPrazos, PrazoNomeado, calcular_prazo_nomeado

__all__ = [
    "CalendarioTJAM",
    "Classificacao",
    "Feriado",
    "PassoMemoria",
    "ResultadoPrazo",
    "calcular_prazo",
    "CatalogoPrazos",
    "PrazoNomeado",
    "calcular_prazo_nomeado",
]
