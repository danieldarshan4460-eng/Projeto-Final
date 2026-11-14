"""Etapa 2 - Item 6B: gráficos interativos com Plotly."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
ARQUIVO_MEDIA_REDE = RAIZ / "saidas" / "etapa2" / "media_por_rede.csv"
PASTA_ETAPA2 = RAIZ / "saidas" / "etapa2"
PASTA_GRAFICOS = PASTA_ETAPA2 / "graficos"
TAMANHO_BLOCO = 500_000
COLUNAS_LEITURA = [
    "SG_UF_PROVA",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    "NU_NOTA_REDACAO",
]
LIMITES_REDACAO = np.arange(0, 1001, 20)


def processar_dados_grandes() -> tuple[pd.DataFrame, np.ndarray, int]:
    """Conta presenças por UF e notas de redação, lendo cada bloco uma vez."""
    totais_uf: dict[str, list[int]] = {}
    contagens_redacao = np.zeros(len(LIMITES_REDACAO) - 1, dtype=np.int64)
    total_redacoes_validas = 0

    blocos = pd.read_csv(
        ARQUIVO_CSV,
        sep=";",
        encoding="latin1",
        usecols=COLUNAS_LEITURA,
        dtype={
            "TP_PRESENCA_LC": "float32",
            "TP_PRESENCA_MT": "float32",
            "NU_NOTA_REDACAO": "float32",
        },
        chunksize=TAMANHO_BLOCO,
    )

    for bloco in blocos:
        bloco["_dia1"] = bloco["TP_PRESENCA_LC"].eq(1).astype("int8")
        bloco["_dia2"] = bloco["TP_PRESENCA_MT"].eq(1).astype("int8")
        por_uf = bloco.groupby("SG_UF_PROVA").agg(
            inscritos=("_dia1", "size"),
            dia1=("_dia1", "sum"),
            dia2=("_dia2", "sum"),
        )

        for uf, linha in por_uf.iterrows():
            uf = str(uf)
            acumulado = totais_uf.setdefault(uf, [0, 0, 0])
            acumulado[0] += int(linha["inscritos"])
            acumulado[1] += int(linha["dia1"])
            acumulado[2] += int(linha["dia2"])

        notas = bloco["NU_NOTA_REDACAO"].dropna().to_numpy(dtype=np.float64)
        contagens_bloco, _ = np.histogram(notas, bins=LIMITES_REDACAO)
        contagens_redacao += contagens_bloco
        total_redacoes_validas += int(notas.size)

    linhas_uf = [
        {
            "SG_UF_PROVA": uf,
            "inscritos": valores[0],
            "presenca_1o_dia_pct": valores[1] / valores[0] * 100,
            "presenca_2o_dia_pct": valores[2] / valores[0] * 100,
        }
        for uf, valores in totais_uf.items()
        if valores[0] > 0
    ]
    presenca_por_uf = pd.DataFrame(linhas_uf).sort_values(
        "presenca_1o_dia_pct", ascending=False
    )
    return presenca_por_uf, contagens_redacao, total_redacoes_validas


def criar_grafico_media_por_rede() -> None:
    """Desenha a média geral por rede e mostra pessoas ao passar o mouse."""
    dados = pd.read_csv(ARQUIVO_MEDIA_REDE, index_col=0)
    dados.index.name = "tipo_escola"
    dados = dados.reset_index().sort_values("media_geral", ascending=False)

    figura = px.bar(
        dados,
        x="tipo_escola",
        y="media_geral",
        text="media_geral",
        custom_data=["pessoas"],
        title="Média geral por tipo de escola",
        labels={
            "tipo_escola": "Tipo de escola",
            "media_geral": "Média geral (pontos)",
        },
    )
    figura.update_traces(
        texttemplate="%{y:.1f}",
        textposition="outside",
        hovertemplate=(
            "%{x}<br>Média geral: %{y:.1f} pontos"
            "<br>Pessoas: %{customdata[0]:,.0f}<extra></extra>"
        ),
    )
    figura.update_yaxes(rangemode="tozero", title="Média geral (pontos)")
    figura.write_html(PASTA_GRAFICOS / "media_por_rede.html")


def criar_grafico_presenca(presenca_por_uf: pd.DataFrame) -> None:
    """Desenha as presenças dos dois dias e salva a tabela por UF."""
    presenca_por_uf.to_csv(PASTA_ETAPA2 / "presenca_por_uf.csv", index=False)
    ufs = presenca_por_uf["SG_UF_PROVA"]
    inscritos = presenca_por_uf["inscritos"]

    figura = go.Figure()
    figura.add_bar(
        name="1º dia (LC)",
        x=ufs,
        y=presenca_por_uf["presenca_1o_dia_pct"],
        customdata=inscritos,
        hovertemplate=(
            "%{x}<br>%{fullData.name}: %{y:.2f}%"
            "<br>Inscritos: %{customdata:,.0f}<extra></extra>"
        ),
    )
    figura.add_bar(
        name="2º dia (MT)",
        x=ufs,
        y=presenca_por_uf["presenca_2o_dia_pct"],
        customdata=inscritos,
        hovertemplate=(
            "%{x}<br>%{fullData.name}: %{y:.2f}%"
            "<br>Inscritos: %{customdata:,.0f}<extra></extra>"
        ),
    )
    figura.update_layout(
        barmode="group",
        title="Presença nos dias de prova por UF",
        xaxis_title="UF da prova",
        yaxis_title="Presença (%)",
    )
    figura.update_yaxes(range=[0, 100])
    figura.write_html(PASTA_GRAFICOS / "presenca_por_uf.html")


def criar_grafico_histograma(
    contagens: np.ndarray, total_redacoes_validas: int
) -> float:
    """Salva o histograma e retorna o percentual de notas entre 0 e 20."""
    limites_inferiores = LIMITES_REDACAO[:-1]
    limites_superiores = LIMITES_REDACAO[1:]
    percentual = (
        contagens / total_redacoes_validas * 100
        if total_redacoes_validas
        else np.zeros_like(contagens, dtype=np.float64)
    )
    dados = pd.DataFrame(
        {
            "limite_inferior": limites_inferiores,
            "limite_superior": limites_superiores,
            "pessoas": contagens,
            "percentual": percentual,
            "faixa": [
                f"{inicio:.0f} a {fim:.0f}"
                for inicio, fim in zip(limites_inferiores, limites_superiores)
            ],
        }
    )
    dados.to_csv(PASTA_ETAPA2 / "histograma_redacao.csv", index=False)

    figura = px.bar(
        dados,
        x="faixa",
        y="pessoas",
        custom_data=["percentual"],
        title="Distribuição das notas de redação",
        labels={"faixa": "Faixa da nota (pontos)", "pessoas": "Pessoas"},
    )
    figura.update_traces(
        hovertemplate=(
            "Nota: %{x} pontos<br>Pessoas: %{y:,.0f}"
            "<br>Redações: %{customdata[0]:.2f}%<extra></extra>"
        )
    )
    figura.update_layout(xaxis_tickangle=-45)
    figura.write_html(PASTA_GRAFICOS / "histograma_redacao.html")
    return float(percentual[0])


def imprimir_resumo(
    presenca_por_uf: pd.DataFrame, percentual_faixa_0_20: float
) -> None:
    """Mostra as quatro UFs extremas no 2º dia e o percentual da faixa inicial."""
    por_segundo_dia = presenca_por_uf.sort_values("presenca_2o_dia_pct")
    menores = por_segundo_dia.head(4)
    maiores = por_segundo_dia.tail(4).sort_values(
        "presenca_2o_dia_pct", ascending=False
    )

    print("Quatro UFs com menor presença no 2º dia:")
    for _, linha in menores.iterrows():
        print(f"  {linha['SG_UF_PROVA']}: {linha['presenca_2o_dia_pct']:.2f}%")

    print("\nQuatro UFs com maior presença no 2º dia:")
    for _, linha in maiores.iterrows():
        print(f"  {linha['SG_UF_PROVA']}: {linha['presenca_2o_dia_pct']:.2f}%")

    print(
        "\nRedações na faixa de 0 a 20 pontos: "
        f"{percentual_faixa_0_20:.2f}%"
    )


def main() -> None:
    """Confere os arquivos, processa os dados e cria os três gráficos."""
    if not ARQUIVO_MEDIA_REDE.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO_MEDIA_REDE}. "
            "Rode o item 6A antes do item 6B."
        )
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")

    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    criar_grafico_media_por_rede()
    presenca_por_uf, contagens_redacao, total_redacoes_validas = (
        processar_dados_grandes()
    )
    criar_grafico_presenca(presenca_por_uf)
    percentual_faixa_0_20 = criar_grafico_histograma(
        contagens_redacao, total_redacoes_validas
    )
    imprimir_resumo(presenca_por_uf, percentual_faixa_0_20)
    print(f"\nGráficos salvos em {PASTA_GRAFICOS}")


if __name__ == "__main__":
    main()
