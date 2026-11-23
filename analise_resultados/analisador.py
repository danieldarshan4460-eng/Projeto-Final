"""Cálculos e tabelas feitas com Pandas."""

import numpy as np
import pandas as pd

from .indicador import IndicadorPontos, Nota, Numerico, Percentual


NOTAS = [
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC",
    "NU_NOTA_MT", "NU_NOTA_REDACAO",
]


class AnalisadorDados:
    """Separa os cálculos da leitura e da preparação dos dados."""

    def __init__(self, df: pd.DataFrame, copiar: bool = True):
        # `copiar=False` evita duplicar tabelas grandes quando o DataFrame
        # já é um resultado novo (por exemplo, o de um filtro).
        self.__df = df.copy(deep=True) if copiar else df
        self.__completos = None

    @property
    def df(self) -> pd.DataFrame:
        """Dados analisados (somente leitura: use `filtrar` para outro recorte)."""
        return self.__df

    def filtrar(
        self,
        regioes=None,
        ufs=None,
        redes=None,
        localizacoes=None,
    ):
        """Cria um novo analisador aplicando filtros opcionais.

        Lista vazia ou None significa "sem filtro" naquela coluna.
        """
        filtros = (
            ("REGIAO", regioes),
            ("SG_UF_PROVA", ufs),
            ("REDE_NOME", redes),
            ("LOCALIZACAO_NOME", localizacoes),
        )
        mascara = pd.Series(True, index=self.__df.index)
        for coluna, valores in filtros:
            if valores is not None and len(valores) > 0:
                if coluna in self.__df.columns:
                    mascara &= self.__df[coluna].isin(valores)

        # `.loc` com máscara já devolve um DataFrame novo.
        return AnalisadorDados(self.__df.loc[mascara], copiar=False)

    def media_por_uf(self) -> pd.DataFrame:
        """Calcula a média geral de quem fez os dois dias, por UF."""
        completos = self._participantes_completos()
        if completos.empty:
            return pd.DataFrame(columns=["grupo", "pessoas", "media_geral"])

        tabela = completos.groupby("SG_UF_PROVA", observed=False).agg(
            pessoas=("MEDIA_GERAL", "size"),
            media_geral=("MEDIA_GERAL", "mean"),
        ).reset_index()
        tabela = tabela.rename(columns={"SG_UF_PROVA": "grupo"})
        tabela["media_geral"] = tabela["media_geral"].astype("float64").round(1)
        return tabela.sort_values("media_geral", ascending=False).reset_index(drop=True)

    def media_por_rede(self) -> pd.DataFrame:
        return self._media_por_grupo("REDE_NOME")

    def media_por_localizacao(self) -> pd.DataFrame:
        return self._media_por_grupo("LOCALIZACAO_NOME")

    def media_por_regiao(self) -> pd.DataFrame:
        return self._media_por_grupo("REGIAO")

    def _media_por_grupo(self, coluna: str) -> pd.DataFrame:
        completos = self._participantes_completos()
        if completos.empty or coluna not in completos.columns:
            return pd.DataFrame(columns=["grupo", "pessoas", "media_geral"])
        # Quem não tem escola informada fica com texto vazio: não é um grupo.
        completos = completos.loc[completos[coluna].notna() & completos[coluna].ne("")]
        if completos.empty:
            return pd.DataFrame(columns=["grupo", "pessoas", "media_geral"])
        tabela = completos.groupby(coluna, observed=False).agg(
            pessoas=("MEDIA_GERAL", "size"),
            media_geral=("MEDIA_GERAL", "mean"),
        ).reset_index()
        tabela = tabela.rename(columns={coluna: "grupo"})
        tabela["media_geral"] = tabela["media_geral"].astype("float64").round(1)
        return tabela.sort_values("media_geral", ascending=False).reset_index(drop=True)

    def funil_presenca(self) -> pd.DataFrame:
        """Conta inscritos e combinações de presença nos dois dias."""
        total = len(self.df)
        dia1 = self.df["TP_PRESENCA_LC"] == 1 if "TP_PRESENCA_LC" in self.df else pd.Series(False, index=self.df.index)
        dia2 = self.df["TP_PRESENCA_MT"] == 1 if "TP_PRESENCA_MT" in self.df else pd.Series(False, index=self.df.index)

        linhas = [
            ("Inscritos", total),
            ("Fez o 1º dia", int(dia1.sum())),
            ("Fez o 2º dia", int(dia2.sum())),
            ("Fez os dois", int((dia1 & dia2).sum())),
            ("Só o 1º", int((dia1 & ~dia2).sum())),
            ("Só o 2º", int((~dia1 & dia2).sum())),
            ("Não fez nenhum", int((~dia1 & ~dia2).sum())),
        ]
        tabela = pd.DataFrame(linhas, columns=["etapa", "pessoas"])
        if total:
            tabela["percentual"] = (
                tabela["pessoas"].astype("float64") / total * 100
            ).round(1)
        else:
            tabela["percentual"] = 0.0
        return tabela

    def estatisticas_descritivas(self) -> pd.DataFrame:
        """Mostra estatísticas separadas para cada prova."""
        linhas = []
        for nota in NOTAS:
            if nota not in self.df.columns:
                continue
            valores = self.df.loc[self.df[nota].notna(), nota].astype("float64")
            if len(valores) == 0:
                linhas.append({
                    "nota": nota, "pessoas": 0, "media": float("nan"),
                    "mediana": float("nan"), "desvio": float("nan"),
                    "minimo": float("nan"), "maximo": float("nan"),
                })
            else:
                linhas.append({
                    "nota": nota,
                    "pessoas": int(len(valores)),
                    "media": round(float(valores.mean()), 1),
                    "mediana": round(float(valores.median()), 1),
                    "desvio": round(float(valores.std(ddof=1)), 1) if len(valores) > 1 else 0.0,
                    "minimo": round(float(valores.min()), 1),
                    "maximo": round(float(valores.max()), 1),
                })
        return pd.DataFrame(linhas)

    def _participantes_completos(self) -> pd.DataFrame:
        """Seleciona quem fez os dois dias e tem as cinco notas (calculado uma vez)."""
        if self.__completos is None:
            self.__completos = self._calcular_participantes_completos()
        return self.__completos

    def _calcular_participantes_completos(self) -> pd.DataFrame:
        dados = self.df
        colunas_presentes = [
            "TP_PRESENCA_LC", "TP_PRESENCA_MT",
            *NOTAS,
        ]
        if not all(c in dados.columns for c in colunas_presentes):
            return pd.DataFrame(columns=[*dados.columns, "MEDIA_GERAL"])

        fez_dois = (
            (dados["TP_PRESENCA_LC"] == 1)
            & (dados["TP_PRESENCA_MT"] == 1)
        )
        completos = dados.loc[fez_dois & dados[NOTAS].notna().all(axis=1)].copy()
        if completos.empty:
            completos["MEDIA_GERAL"] = pd.Series(dtype="float64")
            return completos

        notas = completos[NOTAS].astype("float64")
        completos["MEDIA_GERAL"] = notas.mean(axis=1)
        completos["MEDIA_GERAL"] = completos["MEDIA_GERAL"].astype("float64")
        return completos

    def media_geral(self) -> float:
        """Média geral de quem fez os dois dias e tem as cinco notas."""
        return self._media_geral()

    def _media_geral(self):
        completos = self._participantes_completos()
        if completos.empty:
            return float("nan")
        return float(completos["MEDIA_GERAL"].astype("float64").mean())

    def indicadores(self) -> list:
        """Entrega exatamente oito indicadores principais."""
        total = len(self.df)
        dia1 = self.df["TP_PRESENCA_LC"] == 1 if "TP_PRESENCA_LC" in self.df else pd.Series(False, index=self.df.index)
        dia2 = self.df["TP_PRESENCA_MT"] == 1 if "TP_PRESENCA_MT" in self.df else pd.Series(False, index=self.df.index)

        pct_dia1 = (dia1.sum() / total * 100) if total else float("nan")
        pct_dia2 = (dia2.sum() / total * 100) if total else float("nan")
        pct_nenhum = ((~dia1 & ~dia2).sum() / total * 100) if total else float("nan")

        if "NU_NOTA_REDACAO" in self.df.columns:
            fez_redacao = self.df["NU_NOTA_REDACAO"].notna()
            quantidade = int(fez_redacao.sum())
            pct_zero = (
                (self.df.loc[fez_redacao, "NU_NOTA_REDACAO"] == 0).sum()
                / quantidade * 100
            ) if quantidade else float("nan")
        else:
            pct_zero = float("nan")

        media_geral = self._media_geral()

        if "REDE_NOME" in self.df.columns:
            completos = self._participantes_completos()
            by_rede = completos.groupby("REDE_NOME", observed=False)["MEDIA_GERAL"].mean()
            privada = by_rede.get("Privada", float("nan"))
            estadual = by_rede.get("Estadual", float("nan"))
            diferenca = float(privada - estadual) if pd.notna(privada) and pd.notna(estadual) else float("nan")
        else:
            diferenca = float("nan")

        if "SG_UF_PROVA" in self.df.columns:
            completos = self._participantes_completos()
            medias_uf = completos.groupby("SG_UF_PROVA", observed=False)["MEDIA_GERAL"].mean()
            amplitude = float(medias_uf.max() - medias_uf.min()) if len(medias_uf) else float("nan")
        else:
            amplitude = float("nan")

        return [
            Numerico("Inscritos", total),
            Percentual("Presença no 1º dia", pct_dia1),
            Percentual("Presença no 2º dia", pct_dia2),
            Nota("Média geral", media_geral),
            Percentual("Redações com nota zero", pct_zero),
            Percentual("Não fez nenhum dia", pct_nenhum),
            IndicadorPontos("Diferença privada x estadual", diferenca),
            IndicadorPontos("Amplitude entre UFs", amplitude),
        ]

    def tabela_regiao_uf(self) -> pd.DataFrame:
        """Reúne inscritos, média geral e presença no 2º dia por UF."""
        if "SG_UF_PROVA" not in self.df.columns:
            return pd.DataFrame(columns=[
                "REGIAO", "UF", "inscritos", "media_geral", "presenca_2dia"
            ])

        inscritos = self.df.groupby("SG_UF_PROVA", observed=False).size()
        tabela = inscritos.reset_index(name="inscritos").rename(
            columns={"SG_UF_PROVA": "UF"}
        )

        if "REGIAO" in self.df.columns:
            regioes = self.df.groupby("SG_UF_PROVA", observed=False)["REGIAO"].first()
            tabela["REGIAO"] = tabela["UF"].map(regioes)
        else:
            tabela["REGIAO"] = ""

        completos = self._participantes_completos()
        if not completos.empty:
            medias = completos.groupby("SG_UF_PROVA", observed=False)["MEDIA_GERAL"].mean()
            tabela["media_geral"] = tabela["UF"].map(medias).round(1)
        else:
            tabela["media_geral"] = float("nan")

        if "TP_PRESENCA_MT" in self.df.columns:
            fez_dia2 = self.df["TP_PRESENCA_MT"].eq(1).groupby(
                self.df["SG_UF_PROVA"], observed=False
            ).sum()
            tabela["presenca_2dia"] = (
                tabela["UF"].map(fez_dia2).astype("float64")
                / tabela["inscritos"].astype("float64") * 100
            ).round(1)
        else:
            tabela["presenca_2dia"] = float("nan")

        tabela = tabela[["REGIAO", "UF", "inscritos", "media_geral", "presenca_2dia"]]
        return tabela.sort_values(["REGIAO", "UF"], na_position="last").reset_index(drop=True)

    def distribuicao_media_por_rede(self, largura=50) -> pd.DataFrame:
        """Distribui as médias gerais dentro de cada tipo de escola."""
        completos = self._participantes_completos()
        if completos.empty or "REDE_NOME" not in completos.columns:
            return pd.DataFrame(columns=["faixa", "rede", "percentual"])

        dados = completos.loc[
            completos["REDE_NOME"].notna()
            & completos["REDE_NOME"].ne("")
            & completos["MEDIA_GERAL"].notna()
        ].copy()
        if dados.empty:
            return pd.DataFrame(columns=["faixa", "rede", "percentual"])

        limites = np.arange(0, 1001, largura)
        if limites[-1] != 1000:
            limites = np.append(limites, 1000)

        linhas = []
        for rede, parte in dados.groupby("REDE_NOME", observed=False):
            medias = parte["MEDIA_GERAL"].clip(0, 1000).to_numpy(dtype="float64")
            contagens, _ = np.histogram(medias, bins=limites)
            total = int(contagens.sum())

            for inicio, contagem in zip(limites[:-1], contagens):
                percentual = contagem / total * 100 if total else 0.0
                linhas.append({
                    "faixa": int(inicio),
                    "rede": str(rede),
                    "percentual": round(float(percentual), 1),
                })

        return pd.DataFrame(linhas)

    def histograma_redacao(self, largura=20) -> pd.DataFrame:
        """Conta notas de redação em faixas de 0 a 1000 pontos."""
        if "NU_NOTA_REDACAO" not in self.df.columns:
            return pd.DataFrame(columns=["faixa", "pessoas"])

        notas = pd.to_numeric(
            self.df["NU_NOTA_REDACAO"].dropna(), errors="coerce"
        ).dropna()
        notas = notas.loc[(notas >= 0) & (notas <= 1000)].to_numpy(dtype="float64")

        limites = np.arange(0, 1001, largura)
        if limites[-1] != 1000:
            limites = np.append(limites, 1000)

        contagens, _ = np.histogram(notas, bins=limites)
        return pd.DataFrame({
            "faixa": limites[:-1].astype(int),
            "pessoas": contagens.astype(int),
        })
