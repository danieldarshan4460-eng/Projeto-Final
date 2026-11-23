"""Prepara e filtra os dados antes da análise."""

import pandas as pd

from .constantes import LOCALIZACAO, REGIAO_POR_UF, REDE


class TratadorDados:
    """Adiciona nomes simples aos códigos e permite filtros sem alteração do original."""

    def __init__(self, df):
        if "NU_SEQUENCIAL" not in df:
            raise ValueError("Falta a coluna obrigatória NU_SEQUENCIAL.")

        faltantes = [
            "TP_DEPENDENCIA_ADM_ESC",
            "TP_LOCALIZACAO_ESC",
            "SG_UF_PROVA",
        ]
        faltantes = [coluna for coluna in faltantes if coluna not in df]
        if faltantes:
            raise ValueError("Faltam colunas necessárias: " + ", ".join(faltantes))

        self.__df = df.copy()
        self.__df["REDE_NOME"] = self.__df["TP_DEPENDENCIA_ADM_ESC"].map(REDE)
        self.__df["LOCALIZACAO_NOME"] = self.__df["TP_LOCALIZACAO_ESC"].map(
            LOCALIZACAO
        )
        self.__df["REGIAO_NOME"] = self.__df["SG_UF_PROVA"].map(REGIAO_POR_UF)

        sem_escola = (
            "CO_ESCOLA" in self.__df
            and self.__df["CO_ESCOLA"].isna()
        )
        if isinstance(sem_escola, bool):
            sem_escola = pd.Series(False, index=self.__df.index)
        self.__df.loc[sem_escola, ["REDE_NOME", "LOCALIZACAO_NOME"]] = pd.NA

    @property
    def df(self):
        """Devolve uma cópia da tabela já tratada."""
        return self.__df.copy()

    def filtrar(
        self,
        regiao=None,
        rede=None,
        localizacao=None,
    ):
        """Devolve uma cópia filtrada; nunca modifica a tabela original."""
        resultado = self.__df.copy()

        if regiao is not None:
            resultado = resultado.loc[resultado["REGIAO_NOME"] == regiao]
        if rede is not None:
            resultado = resultado.loc[resultado["REDE_NOME"] == rede]
        if localizacao is not None:
            resultado = resultado.loc[
                resultado["LOCALIZACAO_NOME"] == localizacao
            ]

        return resultado.copy()
