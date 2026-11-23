"""Leitura de dados: uma classe base abstrata e uma fonte para cada formato."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class FonteDados(ABC):
    """Contrato de qualquer fonte de dados: `carregar(colunas)`.

    As validações comuns ficam aqui; cada subclasse só sabe ler o seu formato.
    """

    def __init__(self, caminho: str | Path):
        self._caminho = Path(caminho)

    @property
    def caminho(self) -> Path:
        return self._caminho

    def carregar(self, colunas: list[str]) -> pd.DataFrame:
        """Valida o pedido e devolve apenas as colunas solicitadas."""
        if not self._caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {self._caminho}")

        if "NU_SEQUENCIAL" not in colunas:
            raise ValueError("NU_SEQUENCIAL deve estar entre as colunas carregadas.")

        return self._ler(colunas)

    @abstractmethod
    def _ler(self, colunas: list[str]) -> pd.DataFrame:
        """Lê o arquivo no formato próprio da subclasse."""


class FonteParquet(FonteDados):
    """Carrega colunas selecionadas de um arquivo Parquet."""

    def _ler(self, colunas: list[str]) -> pd.DataFrame:
        return pd.read_parquet(self._caminho, columns=colunas)


class FonteCSV(FonteDados):
    """Carrega colunas selecionadas de um CSV do INEP (separador ';', latin1)."""

    def __init__(self, caminho: str | Path, sep: str = ";", encoding: str = "latin1"):
        super().__init__(caminho)
        self._sep = sep
        self._encoding = encoding

    def _ler(self, colunas: list[str]) -> pd.DataFrame:
        return pd.read_csv(
            self._caminho,
            sep=self._sep,
            encoding=self._encoding,
            usecols=lambda coluna: coluna in colunas,
        )
