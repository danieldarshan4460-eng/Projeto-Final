"""Classes para carregar dados de arquivos."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class FonteDados(ABC):
    """Define o comportamento básico de uma fonte de dados."""

    def __init__(self, caminho):
        self._caminho = Path(caminho)

    @property
    def caminho(self):
        """Devolve o caminho do arquivo, sem permitir sua troca pela propriedade."""
        return self._caminho

    def _verificar_arquivo(self):
        """Garante que o arquivo informado existe."""
        if not self._caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {self._caminho}")

    @abstractmethod
    def carregar(self, colunas=None):
        """Carrega o arquivo e devolve seus dados em uma tabela."""
        raise NotImplementedError


class FonteParquet(FonteDados):
    """Carrega dados de um arquivo Parquet."""

    def carregar(self, colunas=None):
        self._verificar_arquivo()
        return pd.read_parquet(self._caminho, columns=colunas)


class FonteCSV(FonteDados):
    """Carrega dados de um arquivo CSV."""

    def __init__(self, caminho, sep=";", encoding="latin1"):
        super().__init__(caminho)
        self._sep = sep
        self._encoding = encoding

    def carregar(self, colunas=None, limite_linhas=None):
        self._verificar_arquivo()
        return pd.read_csv(
            self._caminho,
            sep=self._sep,
            encoding=self._encoding,
            usecols=colunas,
            nrows=limite_linhas,
        )
