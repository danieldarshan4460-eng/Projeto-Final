import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path

from analise_resultados.fonte import FonteCSV, FonteDados, FonteParquet
from tests.dados_teste import criar_dados_brutos


class TestFonteDados(unittest.TestCase):
    def test_classe_base_e_abstrata(self):
        with self.assertRaises(TypeError):
            FonteDados("qualquer.csv")

    def test_arquivo_inexistente(self):
        for classe in (FonteCSV, FonteParquet):
            with self.assertRaises(FileNotFoundError):
                classe("nao_existe.dados").carregar(["NU_SEQUENCIAL"])

    def test_exige_nu_sequencial(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.csv"
            criar_dados_brutos().to_csv(caminho, sep=";", index=False, encoding="latin1")
            with self.assertRaises(ValueError):
                FonteCSV(caminho).carregar(["SG_UF_PROVA"])

    def test_csv_carrega_apenas_colunas_pedidas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.csv"
            criar_dados_brutos().to_csv(caminho, sep=";", index=False, encoding="latin1")
            fonte = FonteCSV(caminho)
            df = fonte.carregar(["NU_SEQUENCIAL", "SG_UF_PROVA"])
            self.assertEqual(sorted(df.columns), ["NU_SEQUENCIAL", "SG_UF_PROVA"])
            self.assertEqual(len(df), 9)
            self.assertEqual(fonte.caminho, caminho)

    @unittest.skipUnless(find_spec("pyarrow"), "pyarrow não instalado")
    def test_parquet_carrega_apenas_colunas_pedidas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.parquet"
            criar_dados_brutos().to_parquet(caminho)
            df = FonteParquet(caminho).carregar(["NU_SEQUENCIAL", "NU_NOTA_CN"])
            self.assertEqual(sorted(df.columns), ["NU_NOTA_CN", "NU_SEQUENCIAL"])

    def test_polimorfismo_das_fontes(self):
        self.assertTrue(issubclass(FonteCSV, FonteDados))
        self.assertTrue(issubclass(FonteParquet, FonteDados))


if __name__ == "__main__":
    unittest.main()
