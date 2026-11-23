"""Demonstração simples da estrutura orientada a objetos da etapa 3."""

from analise_resultados import (
    AnalisadorDados,
    FonteCSV,
    FonteDados,
    FonteParquet,
    GraficoBarras,
    TratadorDados,
    Visualizador,
)


COLUNAS_ETAPA4 = (
    "NU_SEQUENCIAL",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "SG_UF_PROVA",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_CH",
    "TP_PRESENCA_CN",
    "TP_PRESENCA_MT",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
)


def main():
    print("1) Criar objetos")
    fonte = FonteParquet("data/resultados_reduzido.parquet")
    dados = fonte.carregar(colunas=COLUNAS_ETAPA4)
    tratador = TratadorDados(dados)
    analisador = AnalisadorDados(tratador.df)
    grafico = GraficoBarras(
        "Média geral por rede escolar",
        "grupo",
        "media_geral",
        "Rede escolar",
        "Média geral",
        dados=analisador.media_por_rede(),
    )
    print("FonteParquet, TratadorDados, AnalisadorDados e GraficoBarras criados.")

    print("\n2) Usar objetos")
    for indicador in analisador.indicadores():
        print(f"{indicador.descricao}: {indicador.formatar()}")

    print("\nMédia por rede:")
    print(analisador.media_por_rede().to_string(index=False))

    print("\n3) Polimorfismo")
    for indicador in analisador.indicadores():
        print(type(indicador).__name__, indicador.formatar())

    fontes = [
        FonteParquet("data/resultados_reduzido.parquet"),
        FonteCSV("data/RESULTADOS_2025.csv"),
    ]
    for fonte_exemplo in fontes:
        print(type(fonte_exemplo).__name__, fonte_exemplo.caminho)

    print("\n4) Herança")
    print("A fonte Parquet é uma FonteDados:", isinstance(fonte, FonteDados))
    try:
        FonteDados("x")
    except TypeError as erro:
        print("FonteDados():", type(erro).__name__)
    try:
        Visualizador()
    except TypeError as erro:
        print("Visualizador():", type(erro).__name__)

    print("\n5) Encapsulamento")
    indicador = analisador.indicadores()[0]
    valor_antes = indicador.valor
    try:
        indicador.valor = 0
    except AttributeError:
        print("indicador.valor não pode ser trocado.")
    print("Valor do indicador continua:", indicador.valor, "(era", valor_antes, ")")

    df_antes = analisador.df.copy()
    try:
        analisador.df = None
    except AttributeError:
        print("analisador.df não pode ser trocado.")
    print("Tabela continua igual:", analisador.df.equals(df_antes))

    print("\n6) Filtro sem alterar o original")
    total_antes = tratador.df.shape[0]
    filtrado = tratador.filtrar(regiao="Nordeste", rede="Estadual")
    total_depois = tratador.df.shape[0]
    analisador_filtrado = AnalisadorDados(filtrado)
    print("Total antes:", total_antes)
    print("Total depois:", total_depois)
    print("Total filtrado:", analisador_filtrado.total_inscritos())


if __name__ == "__main__":
    main()
