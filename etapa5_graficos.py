"""Etapa 5: gera os gráficos interativos do projeto."""

from pathlib import Path

import pandas as pd

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.tratador import TratadorDados
from analise_resultados.visualizador import (
    Dashboard,
    GraficoBarras,
    GraficoDispersao,
    GraficoHistograma,
    GraficoLinhas,
    GraficoTreemap,
)


RAIZ = Path(__file__).resolve().parent
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
PASTA_SAIDA = RAIZ / "saidas" / "etapa5"

COLUNAS = [
    "NU_SEQUENCIAL",
    "SG_UF_PROVA",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
]


def main() -> None:
    """Carrega os dados, trata e salva os cinco gráficos."""
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")

    dados = pd.read_csv(
        ARQUIVO_CSV,
        sep=";",
        encoding="latin1",
        usecols=lambda coluna: coluna in COLUNAS,
    )

    dados = TratadorDados(dados).executar()
    analisador = AnalisadorDados(dados)

    tabela_regiao_uf = analisador.tabela_regiao_uf()
    distribuicao_rede = analisador.distribuicao_media_por_rede(largura=50)
    histograma_redacao = analisador.histograma_redacao(largura=20)

    graficos = [
        GraficoBarras(tabela_regiao_uf),
        GraficoLinhas(distribuicao_rede),
        GraficoTreemap(tabela_regiao_uf),
        GraficoDispersao(
            tabela_regiao_uf,
            eixo_x="Presença no 2º dia (%)",
            eixo_y="Média geral (pontos)",
        ),
        GraficoHistograma(histograma_redacao, largura=20),
    ]

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    figuras = Dashboard(graficos).gerar_todos()

    nomes = [
        "barras_media_uf.html",
        "linhas_distribuicao_rede.html",
        "treemap_brasil.html",
        "dispersao_uf.html",
        "histograma_redacao.html",
    ]

    for figura, nome in zip(figuras, nomes):
        figura.write_html(
            PASTA_SAIDA / nome,
            include_plotlyjs="cdn",
        )

    print(f"Cinco gráficos salvos em {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
