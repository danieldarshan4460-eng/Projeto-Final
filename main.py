"""Executa a análise dos resultados do exame."""

from analise_resultados import (
    AnalisadorDados,
    Dashboard,
    FonteCSV,
    FonteDados,
    FonteParquet,
    GraficoBarras,
    IndicadorPercentual,
)


def main():
    print("1) Criar os objetos")
    fonte = FonteParquet("data/resultados_reduzido.parquet")
    dados = fonte.carregar(colunas=AnalisadorDados.COLUNAS_NECESSARIAS)
    analisador = AnalisadorDados(dados)
    grafico = GraficoBarras(
        "Média geral por rede escolar",
        "grupo",
        "media_geral",
        "Rede escolar",
        "Média geral",
        dados=analisador.media_por_rede(),
    )
    dashboard = Dashboard([grafico], analisador=analisador)

    print("\n2) Usar os objetos")
    print(dashboard.resumo_texto())
    print("\nMédia por rede:")
    print(analisador.media_por_rede())
    print("\nMédia por localização:")
    print(analisador.media_por_localizacao())
    print("\nMédia por região:")
    print(analisador.media_por_regiao())
    dashboard.exportar("saidas/etapa3")
    print("\nGráfico salvo em saidas/etapa3/media_por_rede.html")

    print("\n3) Polimorfismo")
    for indicador in dashboard.indicadores():
        print(
            type(indicador).__name__,
            indicador.nome,
            indicador.formatar(),
        )

    fontes = [
        FonteParquet("data/resultados_reduzido.parquet"),
        FonteCSV("data/resultados.csv"),
    ]
    for fonte_exemplo in fontes:
        print(type(fonte_exemplo).__name__, fonte_exemplo.caminho)

    print("\n4) Herança")
    print("A fonte Parquet é uma FonteDados:", isinstance(fonte, FonteDados))
    try:
        FonteDados("x")
    except TypeError as erro:
        print("Não é possível criar a classe abstrata:", erro)

    print("\n5) Encapsulamento")
    indicador = IndicadorPercentual("Exemplo", 0.5)
    try:
        indicador.valor = 0.8
    except AttributeError as erro:
        print("O valor não pode ser alterado pela propriedade:", erro)


if __name__ == "__main__":
    main()
