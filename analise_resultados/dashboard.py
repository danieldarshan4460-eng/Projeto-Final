"""Reúne indicadores e gráfico em uma apresentação simples."""

from pathlib import Path


class Dashboard:
    """Usa um analisador e um gráfico para montar um resumo dos dados."""

    def __init__(self, analisador, grafico_barras):
        self.__analisador = analisador
        self.__grafico_barras = grafico_barras

    def indicadores(self):
        """Devolve os indicadores calculados pelo analisador."""
        return self.__analisador.indicadores()

    def figura_media_por_rede(self):
        """Cria o gráfico das médias por rede escolar."""
        dados = self.__analisador.media_por_rede()
        return self.__grafico_barras.gerar(dados)

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
        self.__grafico_barras.salvar_html(figura, caminho)
