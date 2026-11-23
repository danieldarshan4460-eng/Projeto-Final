"""Demonstração do filtro regional por rede."""

from analise_resultados import (
    AnalisadorDados,
    FonteParquet,
    TratadorDados,
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
    fonte = FonteParquet("data/resultados_reduzido.parquet")
    dados = fonte.carregar(colunas=COLUNAS_ETAPA4)
    tratador = TratadorDados(dados)
    analisador_original = AnalisadorDados(tratador.df)
    total_original = analisador_original.total_inscritos()

    filtrado = tratador.filtrar(regiao="Nordeste", rede="Estadual")
    analisador_filtrado = AnalisadorDados(filtrado)

    print("Total antes do filtro:", total_original)
    print("Total do original depois do filtro:", analisador_original.total_inscritos())
    print("Total filtrado:", analisador_filtrado.total_inscritos())


if __name__ == "__main__":
    main()
