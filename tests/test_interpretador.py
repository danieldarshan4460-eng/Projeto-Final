import unittest

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.interpretador import InterpretadorResultados
from analise_resultados.tratador import TratadorDados
from tests.dados_teste import criar_dados_brutos


class TestInterpretadorResultados(unittest.TestCase):
    def setUp(self):
        tratado = TratadorDados(criar_dados_brutos()).executar()
        self.analisador = AnalisadorDados(tratado)

    def test_gera_frases_com_os_numeros_calculados(self):
        texto = " ".join(InterpretadorResultados(self.analisador).gerar())
        self.assertIn("7 inscritos", texto)
        self.assertIn("508,0 pontos", texto)
        self.assertIn("AM (700,0)", texto)
        self.assertIn("BA (300,0)", texto)
        self.assertIn("rede federal", texto)
        self.assertIn("rede estadual", texto)
        self.assertIn("16,7%", texto)

    def test_nao_afirma_causalidade(self):
        texto = " ".join(InterpretadorResultados(self.analisador).gerar())
        self.assertIn("não prova", texto)

    def test_recorte_vazio_nao_quebra(self):
        vazio = self.analisador.filtrar(ufs=["RS"])
        self.assertEqual(InterpretadorResultados(vazio).gerar(), [])

    def test_texto_acompanha_o_filtro(self):
        so_sp = self.analisador.filtrar(ufs=["SP"])
        texto = " ".join(InterpretadorResultados(so_sp).gerar())
        self.assertIn("2 inscritos", texto)
        self.assertNotIn("Entre as UFs", texto)  # só há uma UF


if __name__ == "__main__":
    unittest.main()
