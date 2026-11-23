import unittest

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.tratador import TratadorDados
from tests.dados_teste import criar_dados_brutos


class TestAnalisadorDados(unittest.TestCase):
    def setUp(self):
        tratado = TratadorDados(criar_dados_brutos()).executar()
        self.analisador = AnalisadorDados(tratado)

    def test_media_geral(self):
        # ids 1, 2, 3, 4 e 9 fizeram os dois dias com as cinco notas.
        self.assertAlmostEqual(self.analisador.media_geral(), 508.0, places=3)

    def test_media_por_uf_ordenada(self):
        tabela = self.analisador.media_por_uf()
        self.assertEqual(tabela["grupo"].tolist(), ["AM", "SP", "RJ", "BA"])
        self.assertEqual(tabela["media_geral"].tolist(), [700.0, 570.0, 400.0, 300.0])

    def test_media_por_rede_ignora_quem_nao_tem_escola(self):
        tabela = self.analisador.media_por_rede()
        self.assertNotIn("", tabela["grupo"].tolist())
        self.assertEqual(tabela["grupo"].tolist(), ["Federal", "Privada", "Estadual"])
        self.assertEqual(tabela["media_geral"].tolist(), [700.0, 640.0, 450.0])

    def test_media_por_localizacao_e_regiao(self):
        local = self.analisador.media_por_localizacao().set_index("grupo")
        self.assertEqual(local.loc["Urbana", "media_geral"], 613.3)
        self.assertEqual(local.loc["Rural", "media_geral"], 400.0)
        regiao = self.analisador.media_por_regiao().set_index("grupo")
        self.assertEqual(regiao.loc["Sudeste", "pessoas"], 3)

    def test_funil_de_presenca(self):
        funil = self.analisador.funil_presenca().set_index("etapa")["pessoas"]
        self.assertEqual(funil["Inscritos"], 7)
        self.assertEqual(funil["Fez o 1º dia"], 6)
        self.assertEqual(funil["Fez o 2º dia"], 5)
        self.assertEqual(funil["Fez os dois"], 5)
        self.assertEqual(funil["Só o 1º"], 1)
        self.assertEqual(funil["Só o 2º"], 0)
        self.assertEqual(funil["Não fez nenhum"], 1)

    def test_estatisticas_descritivas(self):
        est = self.analisador.estatisticas_descritivas().set_index("nota")
        self.assertEqual(est.loc["NU_NOTA_CN", "pessoas"], 5)
        self.assertEqual(est.loc["NU_NOTA_CN", "media"], 500.0)
        self.assertEqual(est.loc["NU_NOTA_CN", "mediana"], 500.0)
        self.assertEqual(est.loc["NU_NOTA_REDACAO", "minimo"], 0.0)
        self.assertEqual(est.loc["NU_NOTA_REDACAO", "maximo"], 800.0)

    def test_oito_indicadores(self):
        indicadores = self.analisador.indicadores()
        self.assertEqual(len(indicadores), 8)
        formatados = {i.descricao: i.formatar() for i in indicadores}
        self.assertEqual(formatados["Inscritos"], "7")
        self.assertEqual(formatados["Redações com nota zero"], "16,7%")
        self.assertEqual(formatados["Média geral"], "508,0")
        self.assertEqual(formatados["Diferença privada x estadual"], "190,0 pontos")
        self.assertEqual(formatados["Amplitude entre UFs"], "400,0 pontos")

    def test_filtrar_cria_novo_analisador_sem_alterar_o_original(self):
        filtrado = self.analisador.filtrar(regioes=["Sudeste"], redes=["Estadual"])
        self.assertEqual(len(filtrado.df), 2)  # ids 2 e 3
        self.assertEqual(len(self.analisador.df), 7)
        self.assertIsNot(filtrado, self.analisador)

    def test_filtro_vazio_nao_filtra(self):
        self.assertEqual(len(self.analisador.filtrar(regioes=[], ufs=None).df), 7)

    def test_filtro_sem_resultado_nao_quebra(self):
        vazio = self.analisador.filtrar(ufs=["RS"])
        self.assertEqual(len(vazio.df), 0)
        self.assertEqual(len(vazio.indicadores()), 8)
        self.assertTrue(vazio.media_por_uf().empty)
        self.assertEqual(vazio.funil_presenca().loc[0, "pessoas"], 0)

    def test_tabela_regiao_uf(self):
        tabela = self.analisador.tabela_regiao_uf()
        self.assertEqual(
            list(tabela.columns),
            ["REGIAO", "UF", "inscritos", "media_geral", "presenca_2dia"],
        )
        sp = tabela.set_index("UF").loc["SP"]
        self.assertEqual(sp["inscritos"], 2)
        self.assertEqual(sp["media_geral"], 570.0)
        self.assertEqual(sp["presenca_2dia"], 100.0)

    def test_histograma_redacao_conta_todas_as_notas_validas(self):
        hist = self.analisador.histograma_redacao(largura=20)
        self.assertEqual(int(hist["pessoas"].sum()), 6)
        self.assertEqual(int(hist.loc[hist["faixa"] == 0, "pessoas"].iloc[0]), 1)

    def test_distribuicao_por_rede_soma_100_em_cada_rede(self):
        dist = self.analisador.distribuicao_media_por_rede(largura=50)
        somas = dist.groupby("rede")["percentual"].sum().round(0)
        self.assertTrue((somas == 100).all())
        self.assertNotIn("", dist["rede"].tolist())


if __name__ == "__main__":
    unittest.main()
