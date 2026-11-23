"""Classes públicas para analisar os resultados do exame."""

from .analisador import AnalisadorDados
from .constantes import LOCALIZACAO, NOTAS, PRESENCA_DIA, REGIAO_POR_UF, REDE
from .fonte_dados import FonteCSV, FonteDados, FonteParquet
from .dashboard import Dashboard
from .indicador import (
    Indicador,
    IndicadorNota,
    IndicadorNumerico,
    IndicadorPercentual,
)
from .visualizador import GraficoBarras, Visualizador

__all__ = [
    "AnalisadorDados",
    "Dashboard",
    "FonteCSV",
    "FonteDados",
    "FonteParquet",
    "GraficoBarras",
    "Indicador",
    "IndicadorNota",
    "IndicadorNumerico",
    "IndicadorPercentual",
    "LOCALIZACAO",
    "NOTAS",
    "PRESENCA_DIA",
    "REGIAO_POR_UF",
    "REDE",
    "Visualizador",
]
