import unittest
from importlib.util import find_spec

from analise_resultados.analisador import AnalisadorDados
from analise_resultados.tratador import TratadorDados
from tests.dados_teste import criar_dados_brutos


@unittest.skipUnless(find_spec("plotly"), "plotly não instalado")
class TestVisualizador(unittest.TestCase):
    def setUp(self):
        from analise_resultados import visualizador

        self.v = visualizador
        analisador = AnalisadorDados(TratadorDados(criar_dados_brutos()).executar())
        # PA não tem ninguém com os dois dias: a média fica ausente e o gráfico precisa lidar com isso.
        self.tabela = analisador.tabela_regiao_uf()
        self.distribuicao = analisador.distribuicao_media_por_rede(largura=50)
        self.histograma = analisador.histograma_redacao(largura=20)

    def test_classe_base_e_abstrata(self):
        with self.assertRaises(TypeError):
            self.v.Visualizador()

    def test_cada_grafico_gera_uma_figura_com_dados(self):
        graficos = [
            self.v.GraficoBarras(self.tabela),
            self.v.GraficoLinhas(self.distribuicao),
            self.v.GraficoTreemap(self.tabela),
            self.v.GraficoDispersao(self.tabela),
            self.v.GraficoHistograma(self.histograma, largura=20),
        ]
        for grafico in graficos:
            with self.subTest(grafico=type(grafico).__name__):
                self.assertGreater(len(grafico.gerar().data), 0)

    def test_dashboard_usa_polimorfismo(self):
        graficos = [
            self.v.GraficoBarras(self.tabela),
            self.v.GraficoHistograma(self.histograma),
        ]
        figuras = self.v.Dashboard(graficos).gerar_todos()
        self.assertEqual(len(figuras), 2)


if __name__ == "__main__":
    unittest.main()
