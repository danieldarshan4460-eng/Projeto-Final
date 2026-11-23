"""Demonstração da análise completa da Etapa 4."""

from pathlib import Path

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.fonte import FonteParquet
from analise_resultados.tratador import TratadorDados


RAIZ = Path(__file__).resolve().parent
ARQUIVO_PARQUET = RAIZ / "data" / "resultados_reduzido.parquet"

COLUNAS = [
    "NU_SEQUENCIAL",
    "SG_UF_PROVA",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
]


def numero_brasileiro(valor: float) -> str:
    """Formata número com separador brasileiro."""
    return f"{float(valor):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro_brasileiro(valor: int) -> str:
    """Formata inteiro com separador de milhares brasileiro."""
    return f"{int(valor):,}".replace(",", ".")


def main() -> None:
    """Lê, trata e apresenta todos os resultados solicitados."""
    fonte = FonteParquet(ARQUIVO_PARQUET)
    dados_originais = fonte.carregar(COLUNAS)

    tratador = TratadorDados(dados_originais)
    dados_tratados = tratador.executar()

    print("1. Relatório do tratamento")
    relatorio = tratador.relatorio
    print(f"Duplicados removidos: {relatorio['duplicados_removidos']}")
    print("Notas vazias:")
    for coluna, quantidade in relatorio["notas_ausentes"].items():
        print(f"- {coluna}: {inteiro_brasileiro(quantidade)}")

    analisador = AnalisadorDados(dados_tratados)

    print("\n2. Oito indicadores")
    for indicador in analisador.indicadores():
        print(f"- {indicador.descricao}: {indicador.formatar()}")

    print("\n3. Funil de presença")
    for linha in analisador.funil_presenca().itertuples(index=False):
        if linha.etapa == "Inscritos":
            continue
        print(
            f"- {linha.etapa}: {inteiro_brasileiro(linha.pessoas)} "
            f"({numero_brasileiro(linha.percentual).replace('%', '')}% )"
        )

    print("\n4. Estatísticas descritivas")
    nomes = {
        "NU_NOTA_CN": "CN",
        "NU_NOTA_CH": "CH",
        "NU_NOTA_LC": "LC",
        "NU_NOTA_MT": "MT",
        "NU_NOTA_REDACAO": "Redação",
    }
    for linha in analisador.estatisticas_descritivas().itertuples(index=False):
        print(
            f"- {nomes[linha.nota]}: "
            f"média {numero_brasileiro(linha.media)}, "
            f"mediana {numero_brasileiro(linha.mediana)}, "
            f"desvio {numero_brasileiro(linha.desvio)}"
        )

    print("\n5. Médias por grupo")

    print("Média por rede:")
    for linha in analisador.media_por_rede().itertuples(index=False):
        print(f"- {linha.grupo}: {numero_brasileiro(linha.media_geral)}")

    print("Média por localização:")
    for linha in analisador.media_por_localizacao().itertuples(index=False):
        print(f"- {linha.grupo}: {numero_brasileiro(linha.media_geral)}")

    print("Média por região:")
    for linha in analisador.media_por_regiao().itertuples(index=False):
        print(f"- {linha.grupo}: {numero_brasileiro(linha.media_geral)}")

    por_uf = analisador.media_por_uf()
    print("Média por UF - 3 maiores:")
    for linha in por_uf.head(3).itertuples(index=False):
        print(f"- {linha.grupo}: {numero_brasileiro(linha.media_geral)}")

    print("Média por UF - 3 menores:")
    menores = por_uf.sort_values("media_geral", ascending=True).head(3)
    for linha in menores.itertuples(index=False):
        print(f"- {linha.grupo}: {numero_brasileiro(linha.media_geral)}")

    print("\n6. Filtro: Nordeste + Estadual")
    inscritos_antes = len(analisador.df)
    filtrado = analisador.filtrar(regioes=["Nordeste"], redes=["Estadual"])
    print(f"- Inscritos: {inteiro_brasileiro(len(filtrado.df))}")

    funil_filtrado = filtrado.funil_presenca()
    for etapa in ("Fez o 1º dia", "Fez o 2º dia", "Fez os dois"):
        linha = funil_filtrado.loc[funil_filtrado["etapa"] == etapa].iloc[0]
        print(f"- {etapa}: {inteiro_brasileiro(linha['pessoas'])}")

    for indicador in filtrado.indicadores():
        print(f"- {indicador.descricao}: {indicador.formatar()}")

    print("\n7. Prova de que o original não mudou")
    print(f"- Inscritos no original antes de filtrar: {inteiro_brasileiro(inscritos_antes)}")
    print(f"- Inscritos no original depois de filtrar: {inteiro_brasileiro(len(analisador.df))}")
    print(f"- Inscritos no recorte filtrado: {inteiro_brasileiro(len(filtrado.df))}")


if __name__ == "__main__":
    main()
