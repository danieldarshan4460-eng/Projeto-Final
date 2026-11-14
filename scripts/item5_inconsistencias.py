"""Etapa 2 - Item 5: inconsistências.

Procura linhas com valores que "não combinam" entre si. Só CONTA e mostra;
não corrige nada no arquivo original.
Como rodar (com o .venv ativo, na pasta do projeto):
    python scripts\\item5_inconsistencias.py
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
PASTA_SAIDA = RAIZ / "saidas" / "etapa2"
TAMANHO_BLOCO = 500_000

# Cada prova e a coluna de presença que corresponde a ela.
PROVAS = {"CN": "TP_PRESENCA_CN", "CH": "TP_PRESENCA_CH",
          "LC": "TP_PRESENCA_LC", "MT": "TP_PRESENCA_MT"}
COMPETENCIAS = [f"NU_NOTA_COMP{i}" for i in range(1, 6)]
COLUNAS = (
    ["TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC", "SG_UF_ESC", "SG_UF_PROVA",
     "TP_STATUS_REDACAO", "NU_NOTA_REDACAO", *COMPETENCIAS]
    + [f"NU_NOTA_{p}" for p in PROVAS] + list(PROVAS.values())
)


def verificar_bloco(bloco: pd.DataFrame) -> dict[str, int]:
    """Devolve quantas linhas do bloco quebram cada regra."""
    r: dict[str, int] = {}

    for prova, col_presenca in PROVAS.items():
        nota = bloco[f"NU_NOTA_{prova}"]
        presente = bloco[col_presenca] == 1
        r[f"Nota {prova} fora de 0 a 1000"] = int(((nota < 0) | (nota > 1000)).sum())
        r[f"Nota {prova} preenchida, mas presença diferente de 1"] = int((nota.notna() & ~presente).sum())
        r[f"Presença 1 em {prova}, mas sem nota"] = int((nota.isna() & presente).sum())
        r[f"Presença com código fora de 0, 1 e 2 em {prova}"] = int((~bloco[col_presenca].isin([0, 1, 2])).sum())

    red = bloco["NU_NOTA_REDACAO"]
    r["Nota da redação fora de 0 a 1000"] = int(((red < 0) | (red > 1000)).sum())
    r["Redação preenchida, mas presença LC diferente de 1"] = int((red.notna() & (bloco["TP_PRESENCA_LC"] != 1)).sum())
    r["Presença LC 1, mas redação sem nota"] = int((red.isna() & (bloco["TP_PRESENCA_LC"] == 1)).sum())

    soma = bloco[COMPETENCIAS].sum(axis=1, min_count=5)   # vazio se faltar alguma
    r["Redação diferente da soma das 5 competências"] = int((red.notna() & soma.notna() & (red != soma)).sum())
    r["Redação com nota, mas competências incompletas"] = int((red.notna() & soma.isna()).sum())
    r["Nota de redação zero com status 1 (sem problemas)"] = int(((red == 0) & (bloco["TP_STATUS_REDACAO"] == 1)).sum())
    r["Nota de redação maior que zero com status diferente de 1"] = int(((red > 0) & (bloco["TP_STATUS_REDACAO"] != 1) & bloco["TP_STATUS_REDACAO"].notna()).sum())

    dep, loc = bloco["TP_DEPENDENCIA_ADM_ESC"], bloco["TP_LOCALIZACAO_ESC"]
    r["Dependência administrativa fora de 1 a 4"] = int((dep.notna() & ~dep.isin([1, 2, 3, 4])).sum())
    r["Localização da escola fora de 1 a 2"] = int((loc.notna() & ~loc.isin([1, 2])).sum())
    r["UF da escola diferente da UF da prova (só quem tem escola)"] = int(
        (bloco["SG_UF_ESC"].notna() & (bloco["SG_UF_ESC"] != bloco["SG_UF_PROVA"])).sum())
    return r


def main() -> None:
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    total, soma = 0, {}
    blocos = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="latin1",
                         usecols=COLUNAS, chunksize=TAMANHO_BLOCO)
    for numero, bloco in enumerate(blocos, start=1):
        total += len(bloco)
        for regra, qtde in verificar_bloco(bloco).items():
            soma[regra] = soma.get(regra, 0) + qtde
        print(f"Bloco {numero}: {len(bloco):,} linhas verificadas")

    tabela = pd.DataFrame({"verificacao": list(soma), "linhas": list(soma.values())})
    tabela["percentual"] = (tabela["linhas"] / total * 100).round(3)
    tabela.to_csv(PASTA_SAIDA / "inconsistencias.csv", index=False)

    print(f"\n=== Resultado do item 5 (total de linhas: {total:,}) ===")
    print(tabela.to_string(index=False))
    print(f"\nSalvo em {PASTA_SAIDA / 'inconsistencias.csv'}")


if __name__ == "__main__":
    main()