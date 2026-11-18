"""Cálculos e tabelas feitas com Pandas."""

import pandas as pd

from .indicador import IndicadorPontos, Nota, Numerico, Percentual


NOTAS = [
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC",
    "NU_NOTA_MT", "NU_NOTA_REDACAO",
]


class AnalisadorDados:
    """Separa os cálculos da leitura e da preparação dos dados."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy(deep=True)

    def filtrar(
        self,
        regioes=None,
        ufs=None,
        redes=None,
        localizacoes=None,
    ):
        """Cria um novo analisador aplicando filtros opcionais."""
        resultado = self.df.copy(deep=True)

        filtros = (
            ("REGIAO", regioes),
            ("SG_UF_PROVA", ufs),
            ("REDE_NOME", redes),
            ("LOCALIZACAO_NOME", localizacoes),
        )
        for coluna, valores in filtros:
            if valores is not None and len(valores) > 0:
                if coluna in resultado.columns:
                    resultado = resultado.loc[resultado[coluna].isin(valores)].copy()

        return AnalisadorDados(resultado)

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
        tabela["percentual"] = (
            tabela["pessoas"].astype("float64") / total * 100
            if total else 0.0
        ).round(1)
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
        """Seleciona quem fez os dois dias e tem as cinco notas."""
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
            return completos

        notas = completos[NOTAS].astype("float64")
        completos["MEDIA_GERAL"] = notas.mean(axis=1)
        completos["MEDIA_GERAL"] = completos["MEDIA_GERAL"].astype("float64")
        return completos

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
