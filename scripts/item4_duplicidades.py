"""Etapa 2 - Item 4: duplicidades.

Pergunta: algum NU_SEQUENCIAL aparece mais de uma vez no arquivo?
Como rodar (com o .venv ativo, na pasta do projeto):
    python scripts\\item4_duplicidades.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
PASTA_SAIDA = RAIZ / "saidas" / "etapa2"
TAMANHO_BLOCO = 500_000


def ler_identificadores() -> tuple[np.ndarray, int]:
    """Lê SÓ a coluna NU_SEQUENCIAL, em blocos, e devolve (ids, qtde de vazios).

    Ler uma coluna só deixa tudo leve: 4,8 milhões de números cabem folgados
    na memória (cerca de 40 MB).
    """
    pedacos, vazios = [], 0
    blocos = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="latin1",
                         usecols=["NU_SEQUENCIAL"], chunksize=TAMANHO_BLOCO)
    for numero, bloco in enumerate(blocos, start=1):
        coluna = bloco["NU_SEQUENCIAL"]
        vazios += int(coluna.isna().sum())
        pedacos.append(coluna.dropna().to_numpy(dtype="int64"))
        print(f"Bloco {numero}: {len(bloco):,} linhas lidas")
    return np.concatenate(pedacos), vazios


def contar_repetidos(ids: np.ndarray) -> dict:
    """Usa np.unique para achar identificadores que aparecem mais de uma vez."""
    valores, vezes = np.unique(ids, return_counts=True)
    repetidos = valores[vezes > 1]
    return {
        "linhas_com_id": int(ids.size),
        "ids_unicos": int(valores.size),
        "ids_repetidos": int(repetidos.size),
        "linhas_em_excesso": int(ids.size - valores.size),
        "lista_repetidos": repetidos,
    }


def mostrar_exemplos(repetidos: np.ndarray, quantos: int = 5) -> None:
    """Se houver repetidos, mostra as linhas completas (sem TX_*) para comparar."""
    exemplo = set(int(i) for i in repetidos[:quantos])
    achadas = []
    blocos = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="latin1",
                         usecols=lambda c: not c.startswith("TX_"),
                         chunksize=TAMANHO_BLOCO)
    for bloco in blocos:
        achadas.append(bloco[bloco["NU_SEQUENCIAL"].isin(exemplo)])
    linhas = pd.concat(achadas).sort_values("NU_SEQUENCIAL")
    print("\nExemplos de linhas com o mesmo NU_SEQUENCIAL:")
    print(linhas.to_string(index=False))
    for numero, grupo in linhas.groupby("NU_SEQUENCIAL"):
        iguais = len(grupo) - len(grupo.drop_duplicates())
        print(f"ID {numero}: {len(grupo)} linhas, {iguais} totalmente iguais a outra.")


def main() -> None:
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    ids, vazios = ler_identificadores()
    r = contar_repetidos(ids)

    print("\n=== Resultado do item 4 ===")
    print(f"Linhas com NU_SEQUENCIAL preenchido: {r['linhas_com_id']:,}")
    print(f"NU_SEQUENCIAL vazios:                {vazios:,}")
    print(f"Identificadores únicos:              {r['ids_unicos']:,}")
    print(f"Identificadores repetidos:           {r['ids_repetidos']:,}")
    print(f"Linhas em excesso (duplicadas):      {r['linhas_em_excesso']:,}")

    resumo = pd.DataFrame([{
        "linhas_com_id": r["linhas_com_id"], "ids_vazios": vazios,
        "ids_unicos": r["ids_unicos"], "ids_repetidos": r["ids_repetidos"],
        "linhas_em_excesso": r["linhas_em_excesso"]}])
    resumo.to_csv(PASTA_SAIDA / "duplicidades.csv", index=False)

    if r["ids_repetidos"] == 0:
        print("\nNenhum identificador repetido. Como cada linha tem um "
              "NU_SEQUENCIAL diferente, também NÃO existem linhas totalmente "
              "duplicadas: não há o que remover.")
    else:
        pd.Series(r["lista_repetidos"][:1000], name="NU_SEQUENCIAL").to_csv(
            PASTA_SAIDA / "ids_repetidos.csv", index=False)
        mostrar_exemplos(r["lista_repetidos"])
    print(f"\nResumo salvo em {PASTA_SAIDA / 'duplicidades.csv'}")


if __name__ == "__main__":
    main()