"""Dashboard interativo dos resultados do ENEM 2025 (Streamlit).

Execute na raiz do projeto:  streamlit run app.py
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.fonte import FonteParquet
from analise_resultados.interpretador import InterpretadorResultados
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

COLUNAS = [
    "NU_SEQUENCIAL",
    "SG_UF_PROVA",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
]

ORDEM_REDES = ["Federal", "Estadual", "Municipal", "Privada"]
ORDEM_LOCALIZACOES = ["Urbana", "Rural"]

NOMES_PROVAS = {
    "NU_NOTA_CN": "Ciências da Natureza",
    "NU_NOTA_CH": "Ciências Humanas",
    "NU_NOTA_LC": "Linguagens e Códigos",
    "NU_NOTA_MT": "Matemática",
    "NU_NOTA_REDACAO": "Redação",
}

AJUDA_KPIS = {
    "Inscritos": "Total de inscritos no recorte selecionado.",
    "Presença no 1º dia": "Inscritos que fizeram as provas do 1º dia (Linguagens e Ciências Humanas).",
    "Presença no 2º dia": "Inscritos que fizeram as provas do 2º dia (Natureza e Matemática).",
    "Média geral": "Média simples das cinco notas de quem fez os dois dias e tem todas as notas.",
    "Redações com nota zero": "Percentual de zeros entre quem tem nota de redação.",
    "Não fez nenhum dia": "Inscritos que faltaram aos dois dias.",
    "Diferença privada x estadual": "Média geral da rede privada menos a da rede estadual.",
    "Amplitude entre UFs": "Maior média por UF menos a menor média por UF.",
}


def inteiro_br(valor: int) -> str:
    """Inteiro com ponto como separador de milhar."""
    return f"{int(valor):,}".replace(",", ".")


@dataclass
class ResultadosPainel:
    """Tudo o que o painel mostra para um conjunto de filtros."""

    inscritos: int
    indicadores: list
    tabela_uf: pd.DataFrame
    distribuicao_rede: pd.DataFrame
    histograma: pd.DataFrame
    estatisticas: pd.DataFrame
    funil: pd.DataFrame
    frases: list[str]


@st.cache_resource(show_spinner="Carregando e tratando os dados (só na primeira vez)...")
def carregar_dados():
    """Lê o Parquet, trata e prepara as opções dos filtros. Roda uma vez por sessão do servidor."""
    bruto = FonteParquet(ARQUIVO_PARQUET).carregar(COLUNAS)
    tratador = TratadorDados(bruto)
    tratado = tratador.executar()

    mapa_uf = (
        tratado[["REGIAO", "SG_UF_PROVA"]]
        .drop_duplicates()
        .sort_values(["REGIAO", "SG_UF_PROVA"])
    )
    redes_presentes = set(tratado["REDE_NOME"].unique())
    locais_presentes = set(tratado["LOCALIZACAO_NOME"].unique())
    opcoes = {
        "regioes": sorted(mapa_uf["REGIAO"].unique()),
        "ufs": sorted(mapa_uf["SG_UF_PROVA"].unique()),
        "regiao_da_uf": dict(zip(mapa_uf["SG_UF_PROVA"], mapa_uf["REGIAO"])),
        "redes": [r for r in ORDEM_REDES if r in redes_presentes],
        "localizacoes": [x for x in ORDEM_LOCALIZACOES if x in locais_presentes],
    }
    return AnalisadorDados(tratado, copiar=False), tratador.relatorio, opcoes


@st.cache_resource(max_entries=16, show_spinner="Calculando indicadores...")
def calcular_resultados(_base, regioes, ufs, redes, localizacoes) -> ResultadosPainel:
    """Aplica os filtros e calcula todas as tabelas (guardado por combinação de filtros)."""
    analisador = _base.filtrar(
        regioes=list(regioes),
        ufs=list(ufs),
        redes=list(redes),
        localizacoes=list(localizacoes),
    )
    return ResultadosPainel(
        inscritos=len(analisador.df),
        indicadores=analisador.indicadores(),
        tabela_uf=analisador.tabela_regiao_uf(),
        distribuicao_rede=analisador.distribuicao_media_por_rede(largura=50),
        histograma=analisador.histograma_redacao(largura=20),
        estatisticas=analisador.estatisticas_descritivas(),
        funil=analisador.funil_presenca(),
        frases=InterpretadorResultados(analisador).gerar(),
    )


class PainelENEM:
    """Organiza as seções do dashboard: cada método desenha uma parte da página."""

    def __init__(self):
        self.__base, self.__relatorio, self.__opcoes = carregar_dados()

    def executar(self) -> None:
        self._cabecalho()
        filtros = self._filtros()
        resultados = calcular_resultados(self.__base, *filtros)

        if resultados.inscritos == 0:
            st.warning("Nenhum inscrito atende a esses filtros. Remova algum filtro na barra lateral.")
            return

        self._kpis(resultados)
        self._graficos(resultados)
        self._tabelas(resultados)
        self._analise(resultados)
        self._rodape()

    # ------------------------------------------------------------------ seções

    def _cabecalho(self) -> None:
        st.title("📊 Desempenho no ENEM 2025")
        st.markdown(
            "Dashboard interativo com os **resultados do ENEM 2025** (INEP — Dados Abertos). "
            "Use os filtros na barra lateral para comparar regiões, UFs e tipos de escola."
        )
        with st.expander("Como os dados foram tratados"):
            st.markdown(
                f"- Duplicados removidos (pelo número sequencial): **{inteiro_br(self.__relatorio['duplicados_removidos'])}**\n"
                f"- Linhas sem UF da prova removidas: **{inteiro_br(self.__relatorio['linhas_sem_uf_removidas'])}**\n"
                "- Notas ausentes **não** são substituídas: quem faltou não recebe nota inventada.\n"
                "- A *média geral* é a média simples das cinco notas e só existe para quem fez os dois dias.\n"
                "- Tipo de escola e localização só existem para inscritos com escola informada."
            )

    def _filtros(self) -> tuple:
        opcoes = self.__opcoes
        st.sidebar.header("Filtros")
        st.sidebar.caption("Deixe vazio para considerar todos.")

        regioes = st.sidebar.multiselect("Região", opcoes["regioes"])
        ufs_disponiveis = [
            uf for uf in opcoes["ufs"]
            if not regioes or opcoes["regiao_da_uf"][uf] in regioes
        ]
        ufs = st.sidebar.multiselect("UF da prova", ufs_disponiveis)
        redes = st.sidebar.multiselect("Tipo de escola", opcoes["redes"])
        localizacoes = st.sidebar.multiselect("Localização da escola", opcoes["localizacoes"])
        return tuple(regioes), tuple(ufs), tuple(redes), tuple(localizacoes)

    def _kpis(self, resultados: ResultadosPainel) -> None:
        st.subheader("Indicadores principais")
        indicadores = resultados.indicadores
        for grupo in (indicadores[:4], indicadores[4:]):
            colunas = st.columns(4)
            for coluna, indicador in zip(colunas, grupo):
                coluna.metric(
                    indicador.descricao,
                    indicador.formatar(),
                    help=AJUDA_KPIS.get(indicador.descricao),
                )

    def _graficos(self, resultados: ResultadosPainel) -> None:
        st.subheader("Visualizações")
        tabela = resultados.tabela_uf.dropna(subset=["media_geral"])
        if tabela.empty:
            st.info("Não há participantes com os dois dias e as cinco notas neste recorte.")
            return

        graficos = [
            GraficoBarras(tabela),
            GraficoLinhas(resultados.distribuicao_rede),
            GraficoTreemap(tabela),
            GraficoDispersao(tabela),
            GraficoHistograma(resultados.histograma, largura=20),
        ]
        barras, linhas, treemap, dispersao, histograma = Dashboard(graficos).gerar_todos()
        barras.update_layout(height=max(400, 24 * len(tabela) + 120))

        aba_uf, aba_mapa, aba_escola, aba_redacao = st.tabs(
            ["Média por UF", "Inscritos por região e UF", "Tipo de escola", "Redação"]
        )
        with aba_uf:
            esquerda, direita = st.columns(2)
            esquerda.plotly_chart(barras)
            direita.plotly_chart(dispersao)
        with aba_mapa:
            st.plotly_chart(treemap)
            st.caption("O tamanho do bloco é o número de inscritos; a cor é a média geral.")
        with aba_escola:
            if resultados.distribuicao_rede.empty:
                st.info("Sem dados de tipo de escola neste recorte.")
            else:
                st.plotly_chart(linhas)
        with aba_redacao:
            st.plotly_chart(histograma)

    def _tabelas(self, resultados: ResultadosPainel) -> None:
        st.subheader("Tabelas de dados")
        aba_uf, aba_provas, aba_funil = st.tabs(
            ["Resumo por UF", "Estatísticas por prova", "Funil de presença"]
        )

        with aba_uf:
            resumo = resultados.tabela_uf.rename(columns={
                "REGIAO": "Região", "UF": "UF", "inscritos": "Inscritos",
                "media_geral": "Média geral", "presenca_2dia": "Presença no 2º dia (%)",
            })
            st.dataframe(resumo, hide_index=True)
            csv = resumo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
            st.download_button(
                "Baixar tabela (CSV)", data=csv,
                file_name="resumo_por_uf.csv", mime="text/csv",
            )

        with aba_provas:
            estatisticas = resultados.estatisticas.copy()
            estatisticas["nota"] = estatisticas["nota"].map(NOMES_PROVAS)
            estatisticas = estatisticas.rename(columns={
                "nota": "Prova", "pessoas": "Pessoas", "media": "Média",
                "mediana": "Mediana", "desvio": "Desvio padrão",
                "minimo": "Mínimo", "maximo": "Máximo",
            })
            st.dataframe(estatisticas, hide_index=True)
            st.caption("Considera todos que fizeram cada prova.")

        with aba_funil:
            funil = resultados.funil.rename(columns={
                "etapa": "Etapa", "pessoas": "Pessoas", "percentual": "% dos inscritos",
            })
            st.dataframe(funil, hide_index=True)

    def _analise(self, resultados: ResultadosPainel) -> None:
        st.subheader("Análise interpretativa")
        st.caption("O texto é gerado a partir dos filtros escolhidos.")
        for frase in resultados.frases:
            st.markdown(f"- {frase}")
        st.markdown(
            "**Limitações.** Tipo de escola e localização existem só para inscritos com escola "
            "informada (no arquivo completo, cerca de 64% dos inscritos não têm escola informada), "
            "então essas comparações não representam todos os participantes. As diferenças entre "
            "grupos são descritivas: renda, escolaridade dos pais e outros fatores não foram "
            "analisados e podem explicar parte delas."
        )

    def _rodape(self) -> None:
        st.divider()
        st.caption("Projeto Final — Programação Orientada a Objetos · Dados: INEP (Dados Abertos)")


def main() -> None:
    st.set_page_config(page_title="ENEM 2025 — Dashboard", page_icon="📊", layout="wide")
    if not ARQUIVO_PARQUET.is_file():
        st.error(f"Arquivo de dados não encontrado: `{ARQUIVO_PARQUET.relative_to(RAIZ)}`")
        st.markdown(
            "1. Coloque `RESULTADOS_2025.csv` (INEP) na pasta `data/`.\n"
            "2. Rode `python scripts/item7_arquivo_reduzido.py` para gerar o arquivo Parquet reduzido.\n"
            "3. Recarregue esta página."
        )
        st.stop()
    PainelENEM().executar()


main()
