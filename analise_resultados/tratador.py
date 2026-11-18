"""Preparação dos dados antes das análises."""

import pandas as pd


REGIAO_POR_UF = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste",
    "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste",
    "MT": "Centro-Oeste", "ES": "Sudeste", "MG": "Sudeste",
    "RJ": "Sudeste", "SP": "Sudeste", "PR": "Sul",
    "RS": "Sul", "SC": "Sul",
}

REDE = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
LOCALIZACAO = {1: "Urbana", 2: "Rural"}


class TratadorDados:
    """Responsável apenas por limpar e preparar uma cópia dos dados."""

    def __init__(self, df: pd.DataFrame):
        # Uma cópia evita que o DataFrame recebido pelo usuário seja alterado.
        self.__df = df.copy(deep=True)
        self.__relatorio = {
            "duplicados_removidos": 0,
            "notas_ausentes": {},
            "linhas_sem_uf_removidas": 0,
        }

    def remover_duplicados(self) -> None:
        """Remove linhas repetidas pelo número sequencial."""
        antes = len(self.__df)
        self.__df = self.__df.drop_duplicates(subset=["NU_SEQUENCIAL"])
        self.__relatorio["duplicados_removidos"] = antes - len(self.__df)

    def tratar_ausentes(self) -> None:
        """Conta ausências; não troca nota vazia por outra nota."""
        colunas_notas = [
            "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC",
            "NU_NOTA_MT", "NU_NOTA_REDACAO",
        ]
        existentes = [c for c in colunas_notas if c in self.__df.columns]
        self.__relatorio["notas_ausentes"] = {
            c: int(self.__df[c].isna().sum()) for c in existentes
        }

        if "SG_UF_PROVA" in self.__df.columns:
            antes = len(self.__df)
            self.__df = self.__df.loc[self.__df["SG_UF_PROVA"].notna()].copy()
            self.__relatorio["linhas_sem_uf_removidas"] = antes - len(self.__df)

    def criar_colunas_derivadas(self) -> None:
        """Cria nomes das regiões, redes e localizações."""
        if "SG_UF_PROVA" in self.__df.columns:
            self.__df["REGIAO"] = self.__df["SG_UF_PROVA"].map(REGIAO_POR_UF)

        if "TP_DEPENDENCIA_ADM_ESC" in self.__df.columns:
            codigo_rede = pd.to_numeric(
                self.__df["TP_DEPENDENCIA_ADM_ESC"], errors="coerce"
            )
            self.__df["REDE_NOME"] = codigo_rede.map(REDE).fillna("")

        if "TP_LOCALIZACAO_ESC" in self.__df.columns:
            codigo_local = pd.to_numeric(
                self.__df["TP_LOCALIZACAO_ESC"], errors="coerce"
            )
            self.__df["LOCALIZACAO_NOME"] = codigo_local.map(LOCALIZACAO).fillna("")

    def executar(self) -> pd.DataFrame:
        """Executa a preparação completa na ordem certa."""
        self.remover_duplicados()
        self.tratar_ausentes()
        self.criar_colunas_derivadas()
        return self.__df

    @property
    def relatorio(self) -> dict:
        """Devolve um relatório com os dados registrados durante o tratamento."""
        return self.__relatorio.copy()
