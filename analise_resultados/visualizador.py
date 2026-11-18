"""Classes simples para criar os gráficos da Etapa 5."""

import plotly.express as px


class Visualizador:
    """Base de todos os gráficos."""

    def gerar(self):
        """Cada classe filha cria e devolve uma figura."""
        raise NotImplementedError("A classe filha deve implementar gerar().")


class GraficoBarras(Visualizador):
    """Barras horizontais com média geral por UF."""

    def __init__(self, dados):
        self.dados = dados

    def gerar(self):
        dados = self.dados.sort_values("media_geral", ascending=True)
        figura = px.bar(
            dados,
            x="media_geral",
            y="UF",
            color="REGIAO",
            orientation="h",
            custom_data=["inscritos", "presenca_2dia", "REGIAO"],
            title="Média geral por UF",
            labels={
                "media_geral": "Média geral (pontos)",
                "UF": "UF da prova",
                "REGIAO": "Região",
            },
        )
        figura.update_traces(
            hovertemplate=(
                "UF: %{y}<br>Região: %{customdata[2]}"
                "<br>Média geral: %{x:.1f} pontos"
                "<br>Inscritos: %{customdata[0]:,.0f}"
                "<br>Presença no 2º dia: %{customdata[1]:.1f}%<extra></extra>"
            )
        )
        figura.update_layout(
            xaxis_title="Média geral (pontos)",
            yaxis_title="UF da prova",
        )
        return figura


class GraficoLinhas(Visualizador):
    """Distribuição da média geral para cada tipo de escola."""

    def __init__(self, dados):
        self.dados = dados

    def gerar(self):
        figura = px.line(
            self.dados,
            x="faixa",
            y="percentual",
            color="rede",
            markers=True,
            title="Distribuição da média geral por tipo de escola",
            labels={
                "faixa": "Faixa da média geral (pontos)",
                "percentual": "Pessoas da rede (%)",
                "rede": "Tipo de escola",
            },
        )
        figura.update_traces(
            hovertemplate=(
                "Tipo de escola: %{fullData.name}"
                "<br>Faixa inicial: %{x:.0f} pontos"
                "<br>Pessoas da rede: %{y:.1f}%<extra></extra>"
            )
        )
        figura.update_layout(
            xaxis_title="Faixa da média geral (pontos)",
            yaxis_title="Pessoas da rede (%)",
        )
        return figura


class GraficoTreemap(Visualizador):
    """Brasil dividido em regiões e UFs."""

    def __init__(self, dados):
        self.dados = dados

    def gerar(self):
        dados = self.dados.copy()
        dados["Brasil"] = "Brasil"
        figura = px.treemap(
            dados,
            path=["Brasil", "REGIAO", "UF"],
            values="inscritos",
            color="media_geral",
            color_continuous_scale=[(0, "red"), (0.5, "yellow"), (1, "green")],
            custom_data=["presenca_2dia"],
            title="Inscritos e média geral por região e UF",
            labels={
                "inscritos": "Inscritos",
                "media_geral": "Média geral (pontos)",
            },
        )
        figura.update_traces(
            hovertemplate=(
                "%{label}<br>Inscritos: %{value:,.0f}"
                "<br>Média geral: %{color:.1f} pontos"
                "<br>Presença no 2º dia: %{customdata[0]:.1f}%<extra></extra>"
            )
        )
        figura.update_layout(coloraxis_colorbar_title="Média geral (pontos)")
        return figura


class GraficoDispersao(Visualizador):
    """Dispersão de presença no 2º dia e média geral por UF."""

    def __init__(self, dados, eixo_x="Presença no 2º dia (%)", eixo_y="Média geral (pontos)"):
        self.dados = dados
        self.eixo_x = eixo_x
        self.eixo_y = eixo_y

    def gerar(self):
        figura = px.scatter(
            self.dados,
            x="presenca_2dia",
            y="media_geral",
            size="inscritos",
            color="REGIAO",
            text="UF",
            custom_data=["inscritos"],
            title="Presença no 2º dia × média geral por UF",
            labels={
                "presenca_2dia": self.eixo_x,
                "media_geral": self.eixo_y,
                "inscritos": "Inscritos",
                "REGIAO": "Região",
            },
        )
        figura.update_traces(
            textposition="top center",
            hovertemplate=(
                "UF: %{text}<br>Presença no 2º dia: %{x:.1f}%"
                "<br>Média geral: %{y:.1f} pontos"
                "<br>Inscritos: %{customdata[0]:,.0f}"
                "<br>Região: %{legendgroup}<extra></extra>"
            ),
        )
        figura.update_layout(
            xaxis_title=self.eixo_x,
            yaxis_title=self.eixo_y,
        )
        return figura


class GraficoHistograma(Visualizador):
    """Gráfico de barras feito com contagens já calculadas."""

    def __init__(self, dados, largura=20):
        self.dados = dados
        self.largura = largura

    def gerar(self):
        dados = self.dados.copy()
        dados["faixa_texto"] = (
            dados["faixa"].astype(str)
            + "–"
            + (dados["faixa"] + self.largura).astype(str)
        )
        figura = px.bar(
            dados,
            x="faixa_texto",
            y="pessoas",
            title="Distribuição das notas de redação",
            labels={
                "faixa_texto": "Faixa da nota de redação (pontos)",
                "pessoas": "Pessoas",
            },
        )
        figura.update_traces(
            hovertemplate=(
                "Faixa: %{x} pontos"
                "<br>Pessoas: %{y:,.0f}<extra></extra>"
            )
        )
        figura.update_layout(
            xaxis_title="Faixa da nota de redação (pontos)",
            yaxis_title="Pessoas",
            xaxis_tickangle=-45,
        )
        return figura


class Dashboard:
    """Recebe uma lista de gráficos e não precisa saber seus tipos."""

    def __init__(self, graficos):
        self.graficos = graficos

    def gerar_todos(self):
        """Gera todas as figuras usando o método gerar() de cada gráfico."""
        return [grafico.gerar() for grafico in self.graficos]
