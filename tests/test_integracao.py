import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.indicador import Nota, Numerico, Percentual
from analise_resultados.tratador import TratadorDados
from analise_resultados.visualizador import (
    Dashboard,
    GraficoBarras,
    GraficoDispersao,
    GraficoHistograma,
    GraficoLinhas,
    GraficoTreemap,
)


RAIZ = Path(__file__).resolve().parents[1]
CSV_REAL = RAIZ / "data" / "RESULTADOS_2025.csv"


@pytest.fixture
def dados_sinteticos() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NU_SEQUENCIAL": 1,
                "SG_UF_PROVA": "SP",
                "TP_DEPENDENCIA_ADM_ESC": 4,
                "TP_LOCALIZACAO_ESC": 1,
                "TP_PRESENCA_LC": 1,
                "TP_PRESENCA_MT": 1,
                "NU_NOTA_CN": 600,
                "NU_NOTA_CH": 650,
                "NU_NOTA_LC": 700,
                "NU_NOTA_MT": 750,
                "NU_NOTA_REDACAO": 800,
            },
            {
                "NU_SEQUENCIAL": 1,
                "SG_UF_PROVA": "SP",
                "TP_DEPENDENCIA_ADM_ESC": 4,
                "TP_LOCALIZACAO_ESC": 1,
                "TP_PRESENCA_LC": 1,
                "TP_PRESENCA_MT": 1,
                "NU_NOTA_CN": 600,
                "NU_NOTA_CH": 650,
                "NU_NOTA_LC": 700,
                "NU_NOTA_MT": 750,
                "NU_NOTA_REDACAO": 800,
            },
            {
                "NU_SEQUENCIAL": 2,
                "SG_UF_PROVA": "RJ",
                "TP_DEPENDENCIA_ADM_ESC": 2,
                "TP_LOCALIZACAO_ESC": 2,
                "TP_PRESENCA_LC": 1,
                "TP_PRESENCA_MT": 0,
                "NU_NOTA_CN": None,
                "NU_NOTA_CH": None,
                "NU_NOTA_LC": 500,
                "NU_NOTA_MT": None,
                "NU_NOTA_REDACAO": 600,
            },
            {
                "NU_SEQUENCIAL": 3,
                "SG_UF_PROVA": None,
                "TP_DEPENDENCIA_ADM_ESC": None,
                "TP_LOCALIZACAO_ESC": None,
                "TP_PRESENCA_LC": 0,
                "TP_PRESENCA_MT": 0,
                "NU_NOTA_CN": None,
                "NU_NOTA_CH": None,
                "NU_NOTA_LC": None,
                "NU_NOTA_MT": None,
                "NU_NOTA_REDACAO": None,
            },
        ]
    )


def test_tratador_remove_duplicados_ausencias_e_cria_colunas(dados_sinteticos):
    tratado = TratadorDados(dados_sinteticos)
    resultado = tratado.executar()

    assert len(dados_sinteticos) == 4
    assert len(resultado) == 2
    assert set(resultado["NU_SEQUENCIAL"]) == {1, 2}
    assert resultado.loc[resultado["NU_SEQUENCIAL"] == 1, "REGIAO"].iloc[0] == "Sudeste"
    assert resultado.loc[resultado["NU_SEQUENCIAL"] == 1, "REDE_NOME"].iloc[0] == "Privada"
    assert resultado.loc[resultado["NU_SEQUENCIAL"] == 2, "LOCALIZACAO_NOME"].iloc[0] == "Rural"
    assert tratado.relatorio["duplicados_removidos"] == 1
    assert tratado.relatorio["linhas_sem_uf_removidas"] == 1


def test_analisador_calcula_funil_media_tabela_e_distribuicoes(dados_sinteticos):
    dados = TratadorDados(dados_sinteticos).executar()
    analisador = AnalisadorDados(dados)

    funil = analisador.funil_presenca()
    assert funil.loc[funil["etapa"] == "Inscritos", "pessoas"].iloc[0] == 2
    assert funil.loc[funil["etapa"] == "Fez os dois", "pessoas"].iloc[0] == 1

    por_uf = analisador.tabela_regiao_uf()
    assert set(por_uf["UF"]) == {"SP", "RJ"}
    assert por_uf.loc[por_uf["UF"] == "SP", "media_geral"].iloc[0] == pytest.approx(700)

    distribuicao = analisador.distribuicao_media_por_rede(largura=50)
    assert not distribuicao.empty
    assert "Privada" in set(distribuicao["rede"])

    histograma = analisador.histograma_redacao(largura=20)
    assert histograma["pessoas"].sum() == 2


def test_formatadores_de_indicadores():
    assert Numerico("Total", 1234).formatar() == "1.234"
    assert Percentual("Presenca", 75.25).formatar() == "75,2%"
    assert Nota("Media", 650.15).formatar() == "650,1"


def test_dashboard_integra_os_cinco_graficos(dados_sinteticos):
    dados = TratadorDados(dados_sinteticos).executar()
    analisador = AnalisadorDados(dados)
    tabela = analisador.tabela_regiao_uf()

    graficos = [
        GraficoBarras(tabela),
        GraficoLinhas(analisador.distribuicao_media_por_rede(largura=50)),
        GraficoTreemap(tabela),
        GraficoDispersao(tabela),
        GraficoHistograma(analisador.histograma_redacao(largura=20), largura=20),
    ]
    figuras = Dashboard(graficos).gerar_todos()

    assert len(figuras) == 5
    assert all(figura.data for figura in figuras)


@pytest.mark.skipif(not CSV_REAL.is_file(), reason="CSV real ainda nao esta disponivel")
@pytest.mark.parametrize(
    ("script", "args"),
    [
        ("scripts/etapa2_exploracao.py", ["item1"]),
        ("scripts/etapa2_exploracao.py", ["item2"]),
        ("scripts/etapa2_exploracao.py", ["item3"]),
        ("scripts/etapa2_exploracao.py", ["item4"]),
        ("scripts/item4_duplicidades.py", []),
        ("scripts/item5_inconsistencias.py", []),
        ("scripts/item6_exploracao.py", []),
        ("scripts/item6b_graficos.py", []),
        ("scripts/item7_arquivo_reduzido.py", []),
        ("etapa5_graficos.py", []),
    ],
)
def test_integracao_scripts_com_csv_real(script, args):
    processo = subprocess.run(
        [sys.executable, str(RAIZ / script), *args],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert processo.returncode == 0, (
        f"Falha ao executar {script} {args}:\n"
        f"stdout:\n{processo.stdout}\n"
        f"stderr:\n{processo.stderr}"
    )


@pytest.mark.skipif(not CSV_REAL.is_file(), reason="CSV real ainda nao esta disponivel")
def test_integracao_artefatos_finais():
    artefatos = [
        RAIZ / "saidas" / "etapa2" / "duplicidades.csv",
        RAIZ / "saidas" / "etapa2" / "inconsistencias.csv",
        RAIZ / "saidas" / "etapa2" / "funil_presenca.csv",
        RAIZ / "saidas" / "etapa2" / "media_por_rede.csv",
        RAIZ / "saidas" / "etapa2" / "graficos" / "media_por_rede.html",
        RAIZ / "saidas" / "etapa2" / "graficos" / "presenca_por_uf.html",
        RAIZ / "saidas" / "etapa2" / "graficos" / "histograma_redacao.html",
        RAIZ / "data" / "resultados_reduzido.parquet",
        RAIZ / "saidas" / "etapa5" / "barras_media_uf.html",
        RAIZ / "saidas" / "etapa5" / "linhas_distribuicao_rede.html",
        RAIZ / "saidas" / "etapa5" / "treemap_brasil.html",
        RAIZ / "saidas" / "etapa5" / "dispersao_uf.html",
        RAIZ / "saidas" / "etapa5" / "histograma_redacao.html",
    ]
    for artefato in artefatos:
        assert artefato.is_file(), f"Artefato nao gerado: {artefato}"
        assert artefato.stat().st_size > 0, f"Artefato vazio: {artefato}"
