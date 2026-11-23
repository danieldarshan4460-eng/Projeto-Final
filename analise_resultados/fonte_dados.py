"""Classes para carregar dados de arquivos."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class FonteDados(ABC):
    """Define o comportamento básico de uma fonte de dados."""

    def __init__(self, caminho):
        self.__caminho = Path(caminho)

    @property
    def caminho(self):
        """Devolve o caminho do arquivo, sem permitir sua troca pela propriedade."""
        return self.__caminho

    def _verificar_arquivo(self):
        """Garante que o arquivo informado existe."""
        if not self.__caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.__caminho}")

    @abstractmethod
    def carregar(self, colunas=None):
        """Carrega o arquivo e devolve seus dados em uma tabela."""
        raise NotImplementedError


class FonteParquet(FonteDados):
    """Carrega dados de um arquivo Parquet."""

    def carregar(self, colunas=None):
        self._verificar_arquivo()
        return pd.read_parquet(self.caminho, columns=colunas)


class FonteCSV(FonteDados):
    """Carrega dados de um arquivo CSV."""

    def __init__(
        self,
        caminho,
        sep=";",
        encoding="latin1",
        usecols=None,
        nrows=None,
    ):
        super().__init__(caminho)
        self._sep = sep
        self._encoding = encoding
        self.__usecols = usecols
        self.__nrows = nrows

    def carregar(self, colunas=None, nrows=None):
        self._verificar_arquivo()
        if colunas is None:
            colunas = self.__usecols
        if nrows is None:
            nrows = self.__nrows
        return pd.read_csv(
            self.caminho,
            sep=self._sep,
            encoding=self._encoding,
            usecols=colunas,
            nrows=nrows,
        )
