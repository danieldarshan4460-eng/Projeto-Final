"""Formatadores simples para mostrar indicadores."""

import math

import pandas as pd


class Indicador:
    """Guarda uma descrição e um valor para um indicador."""

    def __init__(self, descricao: str, valor):
        self.descricao = descricao
        self.valor = valor

    def _valor_valido(self) -> bool:
        if self.valor is None:
            return False
        try:
            return not pd.isna(self.valor)
        except (TypeError, ValueError):
            return False

    def formatar(self) -> str:
        if not self._valor_valido():
            return "—"
        return str(self.valor)


class Numerico(Indicador):
    """Indicador inteiro ou com separador brasileiro."""

    def formatar(self) -> str:
        if not self._valor_valido():
            return "—"
        numero = float(self.valor)
        if math.isclose(numero, round(numero), rel_tol=0, abs_tol=1e-9):
            return f"{int(round(numero)):,}".replace(",", ".")
        return f"{numero:.1f}".replace(".", ",")


class Percentual(Indicador):
    """Indicador mostrado em porcentagem."""

    def formatar(self) -> str:
        if not self._valor_valido():
            return "—"
        return f"{float(self.valor):.1f}".replace(".", ",") + "%"


class Nota(Indicador):
    """Indicador no formato de nota."""

    def formatar(self) -> str:
        if not self._valor_valido():
            return "—"
        return f"{float(self.valor):.1f}".replace(".", ",")


class IndicadorPontos(Indicador):
    """Indicador com unidade de pontos."""

    def formatar(self) -> str:
        if not self._valor_valido():
            return "—"
        return f"{float(self.valor):.1f}".replace(".", ",") + " pontos"
