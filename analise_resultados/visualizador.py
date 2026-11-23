"""Classes para criar e salvar gráficos."""

from abc import ABC, abstractmethod
from pathlib import Path

import plotly.express as px


class Visualizador(ABC):
    """Define o comportamento básico para criar um gráfico."""

    def __init__(self, titulo=None, dados=None):
        self._titulo = titulo
        self.__dados = dados

    @property
    def titulo(self):
        return self._titulo

    @property
    def dados(self):
        """Devolve os dados do gráfico, sem permitir troca pela propriedade."""
        return self.__dados

    def _definir_dados(self, dados):
        """Atualiza os dados usados pelo gráfico."""
        self.__dados = dados

    @abstractmethod
    def gerar(self):
        """Cria e devolve um gráfico."""
        raise NotImplementedError

    def salvar_html(self, figura, caminho):
        """Salva o gráfico em HTML e cria a pasta se ela ainda não existir."""
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        figura.write_html(caminho, include_plotlyjs="cdn")


class GraficoBarras(Visualizador):
    """Cria um gráfico de barras com os valores escritos sobre as barras."""

    def __init__(
        self, titulo, coluna_x, coluna_y, rotulo_x, rotulo_y, dados=None
    ):
        super().__init__(titulo, dados)
        self._coluna_x = coluna_x
        self._coluna_y = coluna_y
        self._rotulo_x = rotulo_x
        self._rotulo_y = rotulo_y

    def gerar(self, dados=None):
        dados = dados if dados is not None else self.dados
        if dados is None:
            raise ValueError("Este gráfico ainda não recebeu dados.")
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


class GraficoLinhas(Visualizador):
    """Cria um gráfico de linhas."""

    def __init__(self, titulo, coluna_x, coluna_y, dados=None):
        super().__init__(titulo, dados)
        self._coluna_x = coluna_x
        self._coluna_y = coluna_y

    def gerar(self, dados=None):
        dados = dados if dados is not None else self.dados
        return px.line(dados, x=self._coluna_x, y=self._coluna_y, title=self.titulo)


class GraficoPizza(Visualizador):
    """Cria um gráfico de pizza."""

    def __init__(self, titulo, coluna_nomes, coluna_valores, dados=None):
        super().__init__(titulo, dados)
        self._coluna_nomes = coluna_nomes
        self._coluna_valores = coluna_valores

    def gerar(self, dados=None):
        dados = dados if dados is not None else self.dados
        return px.pie(
            dados,
            names=self._coluna_nomes,
            values=self._coluna_valores,
            title=self.titulo,
        )


class GraficoDispersao(Visualizador):
    """Cria um gráfico de pontos em dois eixos."""

    def __init__(self, titulo, coluna_x, coluna_y, dados=None):
        super().__init__(titulo, dados)
        self._coluna_x = coluna_x
        self._coluna_y = coluna_y

    def gerar(self, dados=None):
        dados = dados if dados is not None else self.dados
        return px.scatter(
            dados,
            x=self._coluna_x,
            y=self._coluna_y,
            title=self.titulo,
        )


class GraficoHistograma(Visualizador):
    """Cria um histograma a partir de uma coluna."""

    def __init__(self, titulo, coluna, dados=None):
        super().__init__(titulo, dados)
        self._coluna = coluna

    def gerar(self, dados=None):
        dados = dados if dados is not None else self.dados
        return px.histogram(dados, x=self._coluna, title=self.titulo)
