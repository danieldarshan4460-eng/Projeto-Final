"""Classes para criar e salvar gráficos."""

from abc import ABC, abstractmethod
from pathlib import Path

import plotly.express as px


class Visualizador(ABC):
    """Define o comportamento básico para criar um gráfico."""

    def __init__(self, titulo):
        self._titulo = titulo

    @property
    def titulo(self):
        return self._titulo

    @abstractmethod
    def gerar(self, dados):
        """Cria e devolve um gráfico."""
        raise NotImplementedError

    def salvar_html(self, figura, caminho):
        """Salva o gráfico em HTML e cria a pasta se ela ainda não existir."""
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        figura.write_html(caminho, include_plotlyjs="cdn")


class GraficoBarras(Visualizador):
    """Cria um gráfico de barras com os valores escritos sobre as barras."""

    def __init__(self, titulo, coluna_x, coluna_y, rotulo_x, rotulo_y):
        super().__init__(titulo)
        self._coluna_x = coluna_x
        self._coluna_y = coluna_y
        self._rotulo_x = rotulo_x
        self._rotulo_y = rotulo_y

    def gerar(self, dados):
        figura = px.bar(
            dados,
            x=self._coluna_x,
            y=self._coluna_y,
            title=self.titulo,
            labels={
                self._coluna_x: self._rotulo_x,
                self._coluna_y: self._rotulo_y,
            },
            text=self._coluna_y,
        )
        figura.update_traces(textposition="outside")
        return figura
