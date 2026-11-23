"""Etapa 5: gera os gráficos interativos do projeto em arquivos HTML.

Uso:
    python etapa5_graficos.py                 # salva em saidas/etapa5
    python etapa5_graficos.py docs/graficos   # salva na pasta indicada (ex.: para a documentação)
"""

import sys
from pathlib import Path

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.fonte import FonteCSV, FonteDados, FonteParquet
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
ARQUIVO_PARQUET = RAIZ / "data" / "resultados_reduzido.parquet"
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
PASTA_SAIDA_PADRAO = RAIZ / "saidas" / "etapa5"

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

NOMES_ARQUIVOS = [
    "barras_media_uf.html",
    "linhas_distribuicao_rede.html",
    "treemap_brasil.html",
    "dispersao_uf.html",
    "histograma_redacao.html",
]


def escolher_fonte() -> FonteDados:
    """Prefere o Parquet reduzido (rápido); usa o CSV original se ele não existir."""
    if ARQUIVO_PARQUET.is_file():
        return FonteParquet(ARQUIVO_PARQUET)
    return FonteCSV(ARQUIVO_CSV)


def main(pasta_saida: Path = PASTA_SAIDA_PADRAO) -> None:
    """Carrega os dados, trata e salva os cinco gráficos."""
    dados = escolher_fonte().carregar(COLUNAS)
    dados = TratadorDados(dados).executar()
    analisador = AnalisadorDados(dados)

    tabela_regiao_uf = analisador.tabela_regiao_uf().dropna(subset=["media_geral"])
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

    pasta_saida.mkdir(parents=True, exist_ok=True)
    figuras = Dashboard(graficos).gerar_todos()

    for figura, nome in zip(figuras, NOMES_ARQUIVOS):
        figura.write_html(pasta_saida / nome, include_plotlyjs="cdn")

    print(f"Cinco gráficos salvos em {pasta_saida}")


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else PASTA_SAIDA_PADRAO
    main(destino)
