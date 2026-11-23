"""Reúne indicadores e gráfico em uma apresentação simples."""

from pathlib import Path


class Dashboard:
    """Reúne gráficos e, se informado, os indicadores da análise."""

    def __init__(self, graficos, analisador=None):
        # Aceita também a forma antiga Dashboard(analisador, grafico).
        if isinstance(graficos, (list, tuple)):
            self.__graficos = list(graficos)
            self.__analisador = analisador
        else:
            self.__graficos = [analisador] if analisador is not None else []
            self.__analisador = graficos

    def indicadores(self):
        """Devolve os indicadores calculados pelo analisador."""
        if self.__analisador is None:
            raise ValueError("O dashboard não recebeu um analisador.")
        return self.__analisador.indicadores()

    def gerar_todos(self):
        """Cria e devolve as figuras de todos os gráficos."""
        return [grafico.gerar() for grafico in self.__graficos]

    def figura_media_por_rede(self):
        """Cria o gráfico das médias por rede escolar."""
        if self.__analisador is not None and self.__graficos:
            grafico = self.__graficos[0]
            if grafico.dados is None:
                grafico._definir_dados(self.__analisador.media_por_rede())
        if not self.__graficos:
            raise ValueError("O dashboard não recebeu gráficos.")
        return self.__graficos[0].gerar()

    def resumo_texto(self):
        """Devolve uma linha de texto para cada indicador."""
        return "\n".join(
            f"{indicador.nome}: {indicador.formatar()}"
            for indicador in self.indicadores()
        )

    def exportar(self, pasta):
        """Salva o gráfico de médias por rede na pasta indicada."""
        caminho = Path(pasta) / "media_por_rede.html"
        figura = self.figura_media_por_rede()
        self.__graficos[0].salvar_html(figura, caminho)
