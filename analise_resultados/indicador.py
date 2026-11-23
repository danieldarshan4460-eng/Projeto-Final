"""Indicadores formatados para exibição."""

import pandas as pd


class Indicador:
    """Guarda um nome, um valor e uma descrição."""

    def __init__(self, nome, valor, descricao=""):
        self.__nome = nome
        self.__valor = valor
        self.__descricao = descricao

    @property
    def nome(self):
        return self.__nome

    @property
    def valor(self):
        return self.__valor

    @property
    def descricao(self):
        return self.__descricao

    def _valor_vazio(self):
        """Identifica valores ausentes, como None ou NaN."""
        return self.__valor is None or pd.isna(self.__valor) or self.__valor == ""

    def formatar(self):
        """Mostra o valor como um número inteiro com separador de milhar."""
        if self._valor_vazio():
            return "—"
        return f"{int(self.__valor):,}".replace(",", ".")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"nome={self.__nome!r}, valor={self.__valor!r}, "
            f"descricao={self.__descricao!r})"
        )


class IndicadorNumerico(Indicador):
    """Mostra um número inteiro com separador de milhar."""


class IndicadorPercentual(Indicador):
    """Mostra um valor entre zero e um como porcentagem."""

    def formatar(self):
        if self._valor_vazio():
            return "—"
        return f"{float(self.valor) * 100:.1f}%".replace(".", ",")


class IndicadorNota(Indicador):
    """Mostra uma nota com uma casa decimal."""

    def formatar(self):
        if self._valor_vazio():
            return "—"
        return f"{float(self.valor):.1f}".replace(".", ",")


class IndicadorPontos(Indicador):
    """Mostra uma diferença ou amplitude em pontos."""

    def formatar(self):
        if self._valor_vazio():
            return "—"
        return f"{float(self.valor):.1f}".replace(".", ",")
