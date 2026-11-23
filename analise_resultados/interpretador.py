"""Texto de análise interpretativa gerado a partir dos resultados calculados."""

import pandas as pd

from .analisador import AnalisadorDados


def _numero(valor: float, casas: int = 1) -> str:
    """Formata número no padrão brasileiro (milhar com ponto, decimal com vírgula)."""
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


class InterpretadorResultados:
    """Transforma as tabelas de um `AnalisadorDados` em frases de interpretação.

    O texto muda junto com os filtros do dashboard, porque é montado a partir
    do analisador recebido (que já pode estar filtrado).
    """

    def __init__(self, analisador: AnalisadorDados):
        self.__analisador = analisador

    def gerar(self) -> list[str]:
        """Devolve as frases que têm dados suficientes para serem escritas."""
        construtores = (
            self._frase_presenca,
            self._frase_media,
            self._frase_ufs,
            self._frase_redes,
            self._frase_localizacao,
            self._frase_redacao,
        )
        frases = []
        for construir in construtores:
            frase = construir()
            if frase:
                frases.append(frase)
        return frases

    def _frase_presenca(self) -> str | None:
        funil = self.__analisador.funil_presenca().set_index("etapa")
        total = int(funil.loc["Inscritos", "pessoas"])
        if total == 0:
            return None
        dia1 = funil.loc["Fez o 1º dia", "percentual"]
        dia2 = funil.loc["Fez o 2º dia", "percentual"]
        nenhum = funil.loc["Não fez nenhum", "percentual"]
        return (
            f"Dos {_numero(total, 0)} inscritos, {_numero(dia1)}% fizeram o 1º dia e "
            f"{_numero(dia2)}% fizeram o 2º dia; {_numero(nenhum)}% faltaram aos dois dias. "
            "A média geral abaixo considera apenas quem fez os dois dias."
        )

    def _frase_media(self) -> str | None:
        media = self.__analisador.media_geral()
        if pd.isna(media):
            return None
        return f"A média geral do recorte selecionado é de {_numero(media)} pontos (escala de 0 a 1.000)."

    def _frase_ufs(self) -> str | None:
        tabela = self.__analisador.media_por_uf()
        if len(tabela) < 2:
            return None
        melhor = tabela.iloc[0]
        pior = tabela.iloc[-1]
        amplitude = melhor["media_geral"] - pior["media_geral"]
        return (
            f"Entre as UFs, a maior média é de {melhor['grupo']} ({_numero(melhor['media_geral'])}) "
            f"e a menor é de {pior['grupo']} ({_numero(pior['media_geral'])}), "
            f"uma amplitude de {_numero(amplitude)} pontos."
        )

    def _frase_redes(self) -> str | None:
        tabela = self.__analisador.media_por_rede()
        if len(tabela) < 2:
            return None
        melhor = tabela.iloc[0]
        pior = tabela.iloc[-1]
        diferenca = melhor["media_geral"] - pior["media_geral"]
        return (
            f"Por tipo de escola, a rede {melhor['grupo'].lower()} tem a maior média "
            f"({_numero(melhor['media_geral'])}) e a rede {pior['grupo'].lower()} a menor "
            f"({_numero(pior['media_geral'])}), diferença de {_numero(diferenca)} pontos. "
            "É uma comparação descritiva: não prova que o tipo de escola causa a diferença."
        )

    def _frase_localizacao(self) -> str | None:
        tabela = self.__analisador.media_por_localizacao().set_index("grupo")
        if not {"Urbana", "Rural"}.issubset(tabela.index):
            return None
        urbana = tabela.loc["Urbana", "media_geral"]
        rural = tabela.loc["Rural", "media_geral"]
        return (
            f"Escolas urbanas têm média de {_numero(urbana)} e rurais de {_numero(rural)}, "
            f"diferença de {_numero(urbana - rural)} pontos."
        )

    def _frase_redacao(self) -> str | None:
        for indicador in self.__analisador.indicadores():
            if indicador.descricao == "Redações com nota zero":
                texto = indicador.formatar()
                if texto != "—":
                    return f"Entre quem fez a redação, {texto} tirou nota zero."
        return None
