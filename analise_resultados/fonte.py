"""Leitura de dados em formato Parquet."""

from pathlib import Path

import pandas as pd


class FonteParquet:
    """Carrega colunas selecionadas de um arquivo Parquet."""

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def carregar(self, colunas: list[str]) -> pd.DataFrame:
        """Lê e devolve apenas as colunas solicitadas."""
        if not self.caminho.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho}")

        if "NU_SEQUENCIAL" not in colunas:
            raise ValueError("NU_SEQUENCIAL deve estar entre as colunas carregadas.")

        return pd.read_parquet(self.caminho, columns=colunas)
