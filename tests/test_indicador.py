import unittest

from analise_resultados.indicador import (
    Indicador, IndicadorPontos, Nota, Numerico, Percentual,
)


class TestIndicador(unittest.TestCase):
    def test_atributos_somente_leitura(self):
        indicador = Indicador("Teste", 5)
        self.assertEqual(indicador.descricao, "Teste")
        self.assertEqual(indicador.valor, 5)
        with self.assertRaises(AttributeError):
            indicador.valor = 10

    def test_formatacao_de_cada_tipo(self):
        self.assertEqual(Numerico("Inscritos", 4810772).formatar(), "4.810.772")
        self.assertEqual(Numerico("Média", 12.34).formatar(), "12,3")
        self.assertEqual(Percentual("Presença", 71.94).formatar(), "71,9%")
        self.assertEqual(Nota("Média geral", 508.04).formatar(), "508,0")
        self.assertEqual(IndicadorPontos("Diferença", 113.26).formatar(), "113,3 pontos")

    def test_valores_invalidos_viram_traco(self):
        for classe in (Indicador, Numerico, Percentual, Nota, IndicadorPontos):
            self.assertEqual(classe("x", None).formatar(), "—")
            self.assertEqual(classe("x", float("nan")).formatar(), "—")

    def test_polimorfismo(self):
        indicadores = [Numerico("a", 1000), Percentual("b", 10), Nota("c", 500)]
        self.assertEqual([i.formatar() for i in indicadores], ["1.000", "10,0%", "500,0"])


if __name__ == "__main__":
    unittest.main()
