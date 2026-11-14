"""Leitura inicial do arquivo de resultados do ENEM, em blocos."""

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


# O caminho é relativo ao projeto, então o script funciona de qualquer pasta.
ARQUIVO_CSV = Path(__file__).resolve().parents[1] / "data" / "RESULTADOS_2025.csv"
TAMANHO_BLOCO = 500_000

# Nesta primeira etapa, lemos apenas colunas numéricas e de identificação
# necessárias para as contagens e somas. Respostas e gabaritos ficam de fora.
COLUNAS_PRESENCA = [
    "TP_PRESENCA_LC",
    "TP_PRESENCA_CH",
    "TP_PRESENCA_CN",
    "TP_PRESENCA_MT",
]
COLUNAS_NOTAS = [
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
]
COLUNAS_LEITURA = [
    "NU_SEQUENCIAL",
    "CO_ESCOLA",
    "SG_UF_ESC",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "SG_UF_PROVA",
    *COLUNAS_PRESENCA,
    *COLUNAS_NOTAS,
    "TP_STATUS_REDACAO",
]

# Códigos e identificadores são inteiros; as notas aceitam valores ausentes.
TIPOS_COLUNAS = {
    "NU_SEQUENCIAL": "Int32",
    "CO_ESCOLA": "Int32",
    "SG_UF_ESC": "category",
    "TP_DEPENDENCIA_ADM_ESC": "Int8",
    "TP_LOCALIZACAO_ESC": "Int8",
    "SG_UF_PROVA": "category",
    **{coluna: "Int8" for coluna in COLUNAS_PRESENCA},
    **{coluna: "float32" for coluna in COLUNAS_NOTAS},
    "TP_STATUS_REDACAO": "Int8",
}


def mostrar_amostra(caminho: Path = ARQUIVO_CSV) -> pd.DataFrame:
    """Mostra as cinco primeiras linhas para conferir o conteúdo do arquivo."""
    amostra = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        nrows=5,
        usecols=COLUNAS_LEITURA,
        dtype=TIPOS_COLUNAS,
    )
    print("Amostra (primeiras 5 linhas):")
    print(amostra.to_string(index=False))
    return amostra


def ler_csv_em_blocos(
    caminho: Path = ARQUIVO_CSV,
    tamanho_bloco: int = TAMANHO_BLOCO,
) -> dict[str, object]:
    """Soma contagens e notas bloco a bloco, sem guardar o CSV inteiro."""
    total_linhas = 0
    presencas = {coluna: Counter() for coluna in COLUNAS_PRESENCA}
    somas_notas = Counter()
    quantidades_notas = Counter()
    escolas_distintas: set[int] = set()
    registros_com_escola = 0

    blocos = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        usecols=COLUNAS_LEITURA,
        dtype=TIPOS_COLUNAS,
        chunksize=tamanho_bloco,
    )

    for numero_bloco, bloco in enumerate(blocos, start=1):
        total_linhas += len(bloco)

        # Contamos cada código como aparece; seu significado será conferido
        # pelos próprios dados antes de ser interpretado.
        for coluna in COLUNAS_PRESENCA:
            contagens = bloco[coluna].value_counts(dropna=False)
            presencas[coluna].update(contagens.to_dict())

        for coluna in COLUNAS_NOTAS:
            notas = bloco[coluna].dropna()
            somas_notas[coluna] += float(notas.sum())
            quantidades_notas[coluna] += int(notas.size)

        escolas = bloco["CO_ESCOLA"].dropna()
        registros_com_escola += int(escolas.size)
        escolas_distintas.update(int(codigo) for codigo in escolas.unique())

        print(
            f"Bloco {numero_bloco}: {len(bloco):,} linhas lidas "
            f"({total_linhas:,} no total)."
        )

    resumo: dict[str, object] = {
        "total_linhas": total_linhas,
        "presencas": presencas,
        "somas_notas": somas_notas,
        "quantidades_notas": quantidades_notas,
        "registros_com_escola": registros_com_escola,
        "escolas_distintas": len(escolas_distintas),
    }

    print(f"\nTotal de linhas: {total_linhas:,}")
    print(f"Registros com escola: {registros_com_escola:,}")
    print(f"Escolas distintas: {len(escolas_distintas):,}")
    for coluna in COLUNAS_PRESENCA:
        print(f"\nContagem de {coluna}: {dict(presencas[coluna])}")

    return resumo


def agrupar_variavel(nome: str) -> str:
    """Classifica uma coluna do arquivo em um grupo temático."""
    if nome.startswith(("TX_RESPOSTAS_", "TX_GABARITO_")):
        return "texto/respostas"
    if "_AV" in nome:
        return "avaliadores"
    if nome.startswith("TP_PRESENCA_"):
        return "presença"
    if nome in {"NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT"}:
        return "notas"
    if nome == "TP_STATUS_REDACAO" or nome == "NU_NOTA_REDACAO":
        return "redação"
    if nome.startswith("NU_NOTA_COMP") and "_AV" not in nome:
        return "redação"
    if nome.endswith("_ESC") or nome == "CO_ESCOLA":
        return "escola"
    if nome.startswith("CO_PROVA_") or nome == "TP_LINGUA":
        return "prova (versão e opção)"
    if nome.endswith("_PROVA"):
        return "local da prova"
    if nome in {"NU_SEQUENCIAL", "NU_ANO"}:
        return "identificação"
    raise ValueError(f"Coluna sem grupo definido: {nome}")


def uso_na_analise(nome: str) -> str:
    """Indica se a coluna será usada, ignorada ou só conferida na análise."""
    if "_AV" in nome:
        return "só checagem"
    if nome.startswith(("TX_", "CO_PROVA_")) or nome == "TP_LINGUA":
        return "não"
    if (
        nome in {"NU_SEQUENCIAL", "NU_ANO", "SG_UF_PROVA"}
        or nome.endswith("_ESC")
        or nome.startswith(("TP_PRESENCA_", "NU_NOTA_"))
        or nome == "TP_STATUS_REDACAO"
    ):
        return "sim"
    return "não"


def gerar_tabela_variaveis(
    caminho: Path = ARQUIVO_CSV,
) -> pd.DataFrame:
    """Monta, salva e mostra a tabela de nomes, tipos, exemplos e grupos."""
    colunas = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        nrows=0,
    ).columns.tolist()
    amostra = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        usecols=colunas,
        nrows=100,
    )

    linhas = []
    for coluna in colunas:
        exemplo = next(
            (
                valor
                for valor in amostra[coluna]
                if pd.notna(valor)
                and not (isinstance(valor, str) and not valor.strip())
            ),
            "Não encontrado na amostra",
        )
        if coluna.startswith("NU_NOTA") and exemplo != "Não encontrado na amostra":
            exemplo = round(float(exemplo), 1)
        linhas.append(
            {
                "nome": coluna,
                "tipo": str(amostra[coluna].dtype),
                "exemplo": exemplo,
                "grupo": agrupar_variavel(coluna),
                "usada_na_analise": uso_na_analise(coluna),
            }
        )

    tabela = pd.DataFrame(
        linhas,
        columns=["nome", "tipo", "exemplo", "grupo", "usada_na_analise"],
    )
    destino = Path(__file__).resolve().parents[1] / "saidas" / "etapa2" / "variaveis.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(destino, index=False)
    print(f"Tabela de variáveis ({len(tabela)} colunas), salva em {destino}:")
    print(tabela.to_string(index=False))
    return tabela


def calcular_ausentes(
    caminho: Path = ARQUIVO_CSV,
    tamanho_bloco: int = 100_000,
) -> pd.DataFrame:
    """Conta vazios por coluna em blocos e separa os esperados dos potenciais."""
    colunas = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        nrows=0,
    ).columns.tolist()
    blocos = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        usecols=colunas,
        chunksize=tamanho_bloco,
    )
    total_linhas = 0
    vazios_totais = Counter()
    vazios_esperados = Counter()
    registros_sem_escola_e_dependencia = 0

    presenca_por_nota = {
        "NU_NOTA_CN": "TP_PRESENCA_CN",
        "NU_NOTA_CH": "TP_PRESENCA_CH",
        "NU_NOTA_LC": "TP_PRESENCA_LC",
        "NU_NOTA_MT": "TP_PRESENCA_MT",
    }

    for numero_bloco, bloco in enumerate(blocos, start=1):
        total_linhas += len(bloco)
        ausente = bloco.isna()
        vazios_totais.update(ausente.sum().to_dict())

        for coluna in colunas:
            if coluna in presenca_por_nota:
                presenca = bloco[presenca_por_nota[coluna]]
            elif (
                coluna == "NU_NOTA_REDACAO"
                or coluna.startswith("NU_NOTA_COMP")
                or coluna.startswith("TP_STATUS_REDACAO")
                or coluna.startswith("NU_NOTA_AV")
            ):
                presenca = bloco["TP_PRESENCA_LC"]
            else:
                continue
            sem_presenca = presenca.notna() & presenca.ne(1)
            vazios_esperados[coluna] += int(
                (ausente[coluna] & sem_presenca).sum()
            )

        registros_sem_escola_e_dependencia += int(
            (ausente["CO_ESCOLA"] & ausente["TP_DEPENDENCIA_ADM_ESC"]).sum()
        )
        print(
            f"Bloco {numero_bloco}: {len(bloco):,} linhas lidas "
            f"({total_linhas:,} no total)."
        )

    linhas = []
    for coluna in colunas:
        total_vazios = int(vazios_totais[coluna])
        esperados = int(vazios_esperados[coluna])
        linhas.append(
            {
                "nome": coluna,
                "vazios": total_vazios,
                "percentual_vazios": round(100 * total_vazios / total_linhas, 1),
                "vazios_esperados": esperados,
                "vazios_potenciais": total_vazios - esperados,
            }
        )

    tabela = pd.DataFrame(linhas)
    destino = Path(__file__).resolve().parents[1] / "saidas" / "etapa2" / "ausentes.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(destino, index=False)

    top15 = tabela.sort_values(
        ["vazios", "nome"],
        ascending=[False, True],
    ).head(15)
    print(f"\nPercentual de vazios por coluna, salvo em {destino}.")
    print("\n15 colunas com mais vazios:")
    print(top15.to_string(index=False))

    esperados = tabela[tabela["vazios_esperados"] > 0].sort_values(
        "vazios_esperados", ascending=False
    )
    potenciais = tabela[tabela["vazios_potenciais"] > 0].sort_values(
        "vazios_potenciais", ascending=False
    )
    print("\n(a) Vazios esperados (ausência de prova indicada na presença):")
    print(esperados[["nome", "vazios_esperados"]].to_string(index=False))
    print("\n(b) Vazios potenciais (não explicados pela regra de presença acima):")
    print(potenciais[["nome", "vazios_potenciais"]].to_string(index=False))

    for coluna in ("CO_ESCOLA", "TP_DEPENDENCIA_ADM_ESC"):
        linha = tabela.loc[tabela["nome"] == coluna].iloc[0]
        print(
            f"\n{coluna}: {linha['vazios']:,} vazios "
            f"({linha['percentual_vazios']:.1f}% do total)."
        )
    percentual_conjunto = 100 * registros_sem_escola_e_dependencia / total_linhas
    print(
        "Registros sem CO_ESCOLA e TP_DEPENDENCIA_ADM_ESC: "
        f"{registros_sem_escola_e_dependencia:,} "
        f"({percentual_conjunto:.1f}% do total)."
    )
    return tabela


def verificar_duplicidades(
    caminho: Path = ARQUIVO_CSV,
    tamanho_bloco: int = 100_000,
) -> pd.DataFrame:
    """Localiza IDs repetidos e, se houver, compara somente as linhas envolvidas."""
    partes = []
    for bloco in pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        usecols=["NU_SEQUENCIAL"],
        chunksize=tamanho_bloco,
    ):
        partes.append(bloco["NU_SEQUENCIAL"].to_numpy())

    sequenciais = (
        np.concatenate(partes)
        if partes
        else np.array([], dtype="int64")
    )
    sequenciais_validos = sequenciais[pd.notna(sequenciais)]
    valores, contagens = np.unique(sequenciais_validos, return_counts=True)
    repetidos = valores[contagens > 1]
    destino = Path(__file__).resolve().parents[1] / "saidas" / "etapa2" / "duplicidades.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)

    colunas_resultado = [
        "status",
        "NU_SEQUENCIAL",
        "ocorrencias",
        "registros_csv",
        "linhas_totalmente_iguais",
        "colunas_diferentes",
    ]
    resultados = []

    print(f"NU_SEQUENCIAL repetidos encontrados: {len(repetidos):,}")
    if repetidos.size:
        # A busca principal lê apenas o identificador; esta segunda passagem
        # é necessária para comparar os campos das linhas com IDs repetidos.
        colunas = pd.read_csv(
            caminho,
            sep=";",
            encoding="latin1",
            nrows=0,
        ).columns.tolist()
        linhas_repetidas = []
        total_linhas = 0
        for bloco in pd.read_csv(
            caminho,
            sep=";",
            encoding="latin1",
            chunksize=tamanho_bloco,
        ):
            inicio_registro = total_linhas + 2
            bloco["_registro_csv"] = np.arange(
                inicio_registro,
                inicio_registro + len(bloco),
            )
            total_linhas += len(bloco)
            linhas_repetidas.append(
                bloco.loc[bloco["NU_SEQUENCIAL"].isin(repetidos)]
            )

        linhas = pd.concat(linhas_repetidas, ignore_index=True)
        for numero, (sequencial, grupo) in enumerate(
            linhas.groupby("NU_SEQUENCIAL", sort=False),
            start=1,
        ):
            diferentes = []
            for coluna in colunas:
                valores_coluna = grupo[coluna]
                primeiro = valores_coluna.iloc[0]
                if pd.isna(primeiro):
                    diferem = valores_coluna.notna().any()
                else:
                    diferem = (
                        valores_coluna.isna() | valores_coluna.ne(primeiro)
                    ).any()
                if diferem:
                    diferentes.append(coluna)

            registros = grupo["_registro_csv"].astype(int).tolist()
            resultados.append(
                {
                    "status": "NU_SEQUENCIAL repetido",
                    "NU_SEQUENCIAL": sequencial,
                    "ocorrencias": len(grupo),
                    "registros_csv": ", ".join(map(str, registros)),
                    "linhas_totalmente_iguais": not diferentes,
                    "colunas_diferentes": ", ".join(diferentes),
                }
            )

            if numero <= 5:
                print(
                    f"\nExemplo {numero}: NU_SEQUENCIAL={sequencial}, "
                    f"{len(grupo)} ocorrências nos registros {registros}."
                )
                if diferentes:
                    print("Colunas diferentes:", ", ".join(diferentes))
                    print(
                        grupo[["_registro_csv", *diferentes]].to_string(
                            index=False
                        )
                    )
                else:
                    print("As linhas são totalmente iguais em todas as colunas.")

        if len(repetidos) > 5:
            print(f"\nForam omitidos {len(repetidos) - 5:,} exemplos do terminal.")
    else:
        print("Nenhuma comparação de linhas é necessária.")
        resultados.append(
            {
                "status": "Nenhum NU_SEQUENCIAL repetido",
                "NU_SEQUENCIAL": "",
                "ocorrencias": 0,
                "registros_csv": "",
                "linhas_totalmente_iguais": "",
                "colunas_diferentes": "",
            }
        )

    tabela = pd.DataFrame(resultados, columns=colunas_resultado)
    tabela.to_csv(destino, index=False)
    print(f"\nResultado salvo em {destino}.")
    print(
        "Se NU_SEQUENCIAL for único, não pode haver linhas totalmente repetidas: "
        "duas linhas iguais também teriam o mesmo NU_SEQUENCIAL."
    )
    return tabela


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exploração dos resultados do ENEM.")
    parser.add_argument(
        "item",
        nargs="?",
        default="item1",
        metavar="itemN",
        help=(
            "item1: contagens; item2: variáveis; "
            "item3: valores ausentes; item4: duplicidades"
        ),
    )
    args = parser.parse_args()

    if args.item not in {"item1", "item2", "item3", "item4"}:
        parser.error("os itens implementados são item1, item2, item3 e item4")

    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")

    if args.item == "item2":
        gerar_tabela_variaveis()
    elif args.item == "item3":
        calcular_ausentes()
    elif args.item == "item4":
        verificar_duplicidades()
    else:
        mostrar_amostra()
        ler_csv_em_blocos()
