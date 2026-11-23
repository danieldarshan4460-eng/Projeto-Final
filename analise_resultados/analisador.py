"""Cálculos principais sobre os resultados do exame."""

import pandas as pd

from .constantes import LOCALIZACAO, NOTAS, PRESENCA_DIA, REGIAO_POR_UF, REDE
from .indicador import (
    IndicadorNota,
    IndicadorNumerico,
    IndicadorPercentual,
    IndicadorPontos,
)


class AnalisadorDados:
    """Calcula totais, presenças e médias a partir de uma tabela."""

    COLUNAS_NECESSARIAS = (
        *NOTAS,
        *PRESENCA_DIA.values(),
        "NU_SEQUENCIAL",
        "SG_UF_PROVA",
        "TP_DEPENDENCIA_ADM_ESC",
        "TP_LOCALIZACAO_ESC",
        "NU_NOTA_REDACAO",
        "TP_PRESENCA_CN",
        "TP_PRESENCA_CH",
        "TP_PRESENCA_MT",
    )

    def __init__(self, df):
        faltantes = [coluna for coluna in self.COLUNAS_NECESSARIAS if coluna not in df]
        if faltantes:
            nomes = ", ".join(faltantes)
            raise ValueError(f"Faltam colunas necessárias: {nomes}")
        self.__df = df

    @property
    def df(self):
        """Devolve a tabela analisada, sem permitir trocar a referência."""
        return self.__df

    @property
    def tamanho(self):
        """Devolve a quantidade de linhas da tabela."""
        return len(self.__df)

    def total_inscritos(self):
        """Devolve a quantidade de pessoas inscritas."""
        return int(self.tamanho)

    def taxa_presenca(self, dia):
        """Calcula a proporção de pessoas presentes em um dos dias."""
        if dia not in PRESENCA_DIA:
            raise ValueError("O dia deve ser 1 ou 2.")
        if self.tamanho == 0:
            return 0.0
        coluna = PRESENCA_DIA[dia]
        return float((self.__df[coluna] == 1).sum() / self.tamanho)

    def _linhas_completas(self):
        """Seleciona quem fez os dois dias e tem as cinco notas."""
        presentes = pd.Series(True, index=self.__df.index)
        for coluna in PRESENCA_DIA.values():
            presentes &= self.__df[coluna] == 1

        notas_preenchidas = self.__df[NOTAS].notna().all(axis=1)
        return self.__df.loc[presentes & notas_preenchidas]

    def _media_por_grupo(self, coluna, nomes):
        """Calcula pessoas e média para cada grupo informado."""
        dados = self._linhas_completas()
        grupos = dados[coluna].map(nomes)
        medias_por_pessoa = dados[NOTAS].mean(axis=1)

        tabela = pd.DataFrame(
            {
                "grupo": grupos,
                "media_geral": medias_por_pessoa,
            }
        ).dropna(subset=["grupo"])
        # Grupos sem nome não representam uma rede ou localização válida.
        tabela = tabela.loc[tabela["grupo"] != ""]

        resultado = (
            tabela.groupby("grupo", as_index=False, sort=False)
            .agg(
                pessoas=("media_geral", "size"),
                media_geral=("media_geral", "mean"),
            )
        )
        resultado["media_geral"] = resultado["media_geral"].round(1)
        return resultado.sort_values(
            "media_geral", ascending=False, ignore_index=True
        )[["grupo", "pessoas", "media_geral"]]

    def media_geral(self):
        """Calcula a média das cinco notas de quem fez tudo."""
        dados = self._linhas_completas()
        if dados.empty:
            return float("nan")
        return float(dados[NOTAS].mean(axis=1).mean())

    def media_por_rede(self):
        """Calcula a média por tipo de rede escolar."""
        return self._media_por_grupo("TP_DEPENDENCIA_ADM_ESC", REDE)

    def media_por_localizacao(self):
        """Calcula a média por localização da escola."""
        return self._media_por_grupo("TP_LOCALIZACAO_ESC", LOCALIZACAO)

    def media_por_regiao(self):
        """Calcula a média por região, usando a UF da prova."""
        return self._media_por_grupo("SG_UF_PROVA", REGIAO_POR_UF)

    def percentual_redacao_zero(self):
        """Calcula o percentual de quem fez redação e tirou zero."""
        dados = self._linhas_completas()
        if dados.empty:
            return float("nan")
        return float((dados["NU_NOTA_REDACAO"] == 0).mean())

    def percentual_nenhum_dia(self):
        """Calcula o percentual de pessoas que não fizeram nenhum dos dois dias."""
        if self.tamanho == 0:
            return float("nan")
        nenhuma = (
            (self.__df["TP_PRESENCA_LC"] == 0)
            & (self.__df["TP_PRESENCA_MT"] == 0)
        )
        return float(nenhuma.mean())

    def diferenca_privada_estadual(self):
        """Devolve a diferença entre as médias de rede privada e estadual."""
        medias = self.media_por_rede().set_index("grupo")["media_geral"]
        if "Privada" not in medias.index or "Estadual" not in medias.index:
            return float("nan")
        return float(medias["Privada"] - medias["Estadual"])

    def amplitude_medias_uf(self):
        """Devolve a maior diferença entre as médias das UFs."""
        dados = self._linhas_completas()
        if dados.empty:
            return float("nan")
        medias = dados.assign(
            media_geral=dados[NOTAS].mean(axis=1)
        ).groupby("SG_UF_PROVA")["media_geral"].mean()
        if medias.empty:
            return float("nan")
        return float(medias.max() - medias.min())

    def indicadores(self):
        """Cria os oito indicadores principais da análise."""
        return [
            IndicadorNumerico("Inscritos", self.total_inscritos(), "total de inscritos"),
            IndicadorPercentual("Presença no 1º dia", self.taxa_presenca(1), "presença no primeiro dia"),
            IndicadorPercentual("Presença no 2º dia", self.taxa_presenca(2), "presença no segundo dia"),
            IndicadorNota("Média geral", self.media_geral(), "média das cinco notas"),
            IndicadorPercentual("Redação zero", self.percentual_redacao_zero(), "percentual de redações zero"),
            IndicadorPercentual("Nenhum dia", self.percentual_nenhum_dia(), "percentual que não fez nenhum dia"),
            IndicadorPontos(
                "Privada x Estadual",
                self.diferenca_privada_estadual(),
                "diferença entre privada e estadual",
            ),
            IndicadorPontos(
                "Amplitude",
                self.amplitude_medias_uf(),
                "maior diferença entre médias das UFs",
            ),
        ]
