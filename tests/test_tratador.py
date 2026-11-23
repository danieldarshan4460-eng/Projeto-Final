import unittest

from analise_resultados.tratador import TratadorDados
from tests.dados_teste import criar_dados_brutos


class TestTratadorDados(unittest.TestCase):
    def setUp(self):
        self.bruto = criar_dados_brutos()
        self.tratador = TratadorDados(self.bruto)
        self.tratado = self.tratador.executar()

    def test_remove_duplicados_e_linhas_sem_uf(self):
        self.assertEqual(len(self.tratado), 7)
        self.assertTrue(self.tratado["NU_SEQUENCIAL"].is_unique)
        self.assertEqual(self.tratador.relatorio["duplicados_removidos"], 1)
        self.assertEqual(self.tratador.relatorio["linhas_sem_uf_removidas"], 1)

    def test_nao_altera_o_dataframe_original(self):
        self.assertEqual(len(self.bruto), 9)
        self.assertNotIn("REGIAO", self.bruto.columns)

    def test_cria_colunas_derivadas(self):
        linha = self.tratado.set_index("NU_SEQUENCIAL")
        self.assertEqual(linha.loc[1, "REGIAO"], "Sudeste")
        self.assertEqual(linha.loc[1, "REDE_NOME"], "Privada")
        self.assertEqual(linha.loc[3, "LOCALIZACAO_NOME"], "Rural")
        self.assertEqual(linha.loc[9, "REGIAO"], "Norte")

    def test_escola_ausente_vira_texto_vazio(self):
        linha = self.tratado.set_index("NU_SEQUENCIAL")
        self.assertEqual(linha.loc[4, "REDE_NOME"], "")

    def test_nao_preenche_nota_ausente(self):
        linha = self.tratado.set_index("NU_SEQUENCIAL")
        self.assertTrue(linha.loc[6, "NU_NOTA_CN"] != linha.loc[6, "NU_NOTA_CN"])  # NaN

    def test_relatorio_conta_notas_ausentes(self):
        ausentes = self.tratador.relatorio["notas_ausentes"]
        self.assertEqual(ausentes["NU_NOTA_CN"], 2)  # ids 5 e 6 (após remover duplicados/sem UF)

    def test_relatorio_devolve_copia(self):
        relatorio = self.tratador.relatorio
        relatorio["duplicados_removidos"] = 999
        self.assertEqual(self.tratador.relatorio["duplicados_removidos"], 1)


if __name__ == "__main__":
    unittest.main()
