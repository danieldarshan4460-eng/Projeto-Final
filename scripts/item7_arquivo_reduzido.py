"""Etapa 2 - Item 7: cria uma cópia reduzida dos resultados em Parquet."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
ARQUIVO_PARQUET = RAIZ / "data" / "resultados_reduzido.parquet"
TAMANHO_BLOCO = 500_000
TIPOS_INTEIROS = {
    "Int8": np.iinfo("int8"),
    "Int16": np.iinfo("int16"),
    "Int32": np.iinfo("int32"),
}


def descobrir_colunas() -> tuple[list[str], list[str]]:
    """Lê só o cabeçalho e separa as colunas que ficam das que serão removidas."""
    colunas_originais = pd.read_csv(
        ARQUIVO_CSV, sep=";", encoding="latin1", nrows=0
    ).columns.tolist()
    colunas_mantidas = [
        coluna
        for coluna in colunas_originais
        if not coluna.startswith(("TX_", "CO_PROVA_")) and "_AV" not in coluna
    ]
    return colunas_originais, colunas_mantidas


def tipo_da_coluna(coluna: str) -> str:
    """Escolhe o tipo reduzido conforme o começo do nome da coluna."""
    if coluna == "NU_ANO":
        return "Int16"
    if coluna.startswith("NU_NOTA_"):
        return "float32"
    if coluna.startswith("CO_UF_"):
        return "Int8"
    if coluna.startswith(("CO_", "NU_")):
        return "Int32"
    if coluna.startswith("TP_"):
        return "Int8"
    if coluna.startswith(("SG_", "NO_")):
        return "string"
    raise ValueError(f"Não há tipo definido para a coluna mantida: {coluna}")


def preparar_bloco(bloco: pd.DataFrame, numero: int) -> pd.DataFrame:
    """Converte as colunas do bloco sem permitir estouro silencioso de inteiros."""
    for coluna in bloco.columns:
        tipo = tipo_da_coluna(coluna)
        if tipo in TIPOS_INTEIROS:
            try:
                valores = pd.to_numeric(bloco[coluna], errors="raise")
            except (TypeError, ValueError) as erro:
                raise ValueError(
                    f"Valor inválido na coluna {coluna}, bloco {numero}; "
                    f"esperado um inteiro do tipo {tipo}."
                ) from erro

            validos = valores.dropna()
            if not ((validos % 1) == 0).all():
                raise ValueError(
                    f"Há valor não inteiro na coluna {coluna}, bloco {numero}; "
                    f"esperado o tipo {tipo}."
                )

            limites = TIPOS_INTEIROS[tipo]
            fora_do_intervalo = (validos < limites.min) | (validos > limites.max)
            if fora_do_intervalo.any():
                valores_fora = validos[fora_do_intervalo]
                minimo = int(valores_fora.min())
                maximo = int(valores_fora.max())
                raise ValueError(
                    f"Valor fora do intervalo de {tipo} na coluna {coluna}, "
                    f"bloco {numero}. Intervalo permitido: {limites.min} a "
                    f"{limites.max}; valores observados: {minimo} a {maximo}."
                )
            bloco[coluna] = valores.astype(tipo)
        elif tipo == "float32":
            try:
                valores = pd.to_numeric(bloco[coluna], errors="raise")
            except (TypeError, ValueError) as erro:
                raise ValueError(
                    f"Valor inválido na coluna {coluna}, bloco {numero}; "
                    "esperado um número."
                ) from erro
            limite = np.finfo(np.float32).max
            if (valores.abs() > limite).any():
                raise ValueError(
                    f"Valor fora do intervalo de float32 na coluna {coluna}, "
                    f"bloco {numero}. Limite absoluto: {limite}."
                )
            bloco[coluna] = valores.astype("float32")
        else:
            bloco[coluna] = bloco[coluna].astype("string")
    return bloco


def gravar_parquet(colunas: list[str]) -> int:
    """Lê o CSV em blocos e grava cada um no Parquet com compressão Zstandard."""
    tipos_texto = {
        coluna: "string"
        for coluna in colunas
        if coluna.startswith(("SG_", "NO_"))
    }
    blocos = pd.read_csv(
        ARQUIVO_CSV,
        sep=";",
        encoding="latin1",
        usecols=colunas,
        dtype=tipos_texto,
        chunksize=TAMANHO_BLOCO,
    )
    iterador = iter(blocos)
    try:
        primeiro_bloco = next(iterador)
    except StopIteration as erro:
        raise ValueError("O arquivo CSV não contém linhas para gravar.") from erro

    primeiro_bloco = preparar_bloco(primeiro_bloco, 1)
    primeira_tabela = pa.Table.from_pandas(
        primeiro_bloco, preserve_index=False
    )
    esquema = primeira_tabela.schema
    total_linhas = len(primeiro_bloco)
    print(f"Bloco 1: {total_linhas:,} linhas gravadas")

    with pq.ParquetWriter(
        ARQUIVO_PARQUET, schema=esquema, compression="zstd"
    ) as escritor:
        escritor.write_table(primeira_tabela)
        for numero, bloco in enumerate(iterador, start=2):
            bloco = preparar_bloco(bloco, numero)
            tabela = pa.Table.from_pandas(
                bloco,
                schema=esquema,
                preserve_index=False,
                safe=True,
            )
            escritor.write_table(tabela)
            total_linhas += len(bloco)
            print(f"Bloco {numero}: {len(bloco):,} linhas gravadas")

    return total_linhas


def contar_presencas_lc() -> int:
    """Conta quem fez LC lendo apenas essa coluna do arquivo Parquet."""
    arquivo = pq.ParquetFile(ARQUIVO_PARQUET)
    total = 0
    for lote in arquivo.iter_batches(
        columns=["TP_PRESENCA_LC"], batch_size=TAMANHO_BLOCO
    ):
        presencas = pc.equal(lote.column(0), 1)
        quantidade = pc.sum(pc.cast(presencas, pa.int64())).as_py()
        total += int(quantidade or 0)
    return total


def mostrar_conferencia(
    total_linhas_gravadas: int,
    total_colunas: int,
    colunas_mantidas: int,
) -> None:
    """Compara as linhas gravadas com os metadados e mostra os tamanhos."""
    metadados = pq.ParquetFile(ARQUIVO_PARQUET).metadata
    print(f"\nColunas mantidas: {colunas_mantidas} de {total_colunas}")
    print(f"Linhas gravadas: {total_linhas_gravadas:,}")
    print(f"Linhas nos metadados do Parquet: {metadados.num_rows:,}")
    if metadados.num_rows != total_linhas_gravadas:
        raise RuntimeError(
            "A quantidade de linhas nos metadados do Parquet não corresponde "
            "à quantidade de linhas gravadas."
        )
    if metadados.num_columns != colunas_mantidas:
        raise RuntimeError(
            "A quantidade de colunas nos metadados do Parquet não corresponde "
            "à quantidade de colunas mantidas."
        )
    print("Conferência de linhas e colunas: OK")

    tamanho_csv_mb = ARQUIVO_CSV.stat().st_size / 1_000_000
    tamanho_parquet_mb = ARQUIVO_PARQUET.stat().st_size / 1_000_000
    print(f"Tamanho do CSV: {tamanho_csv_mb:,.1f} MB")
    print(f"Tamanho do Parquet: {tamanho_parquet_mb:,.1f} MB")


def main() -> None:
    """Confere a entrada, cria o Parquet e imprime os resultados da conferência."""
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")

    colunas_originais, colunas_mantidas = descobrir_colunas()
    if "TP_PRESENCA_LC" not in colunas_mantidas:
        raise ValueError("A coluna TP_PRESENCA_LC não foi encontrada no CSV.")

    print(
        f"Colunas mantidas: {len(colunas_mantidas)} "
        f"de {len(colunas_originais)}"
    )
    total_linhas_gravadas = gravar_parquet(colunas_mantidas)
    mostrar_conferencia(
        total_linhas_gravadas,
        len(colunas_originais),
        len(colunas_mantidas),
    )

    presencas_lc = contar_presencas_lc()
    print(f"Linhas com TP_PRESENCA_LC == 1: {presencas_lc:,}")
    print(
        '\nPara ler depois: '
        'pd.read_parquet("data/resultados_reduzido.parquet")'
    )


if __name__ == "__main__":
    main()
