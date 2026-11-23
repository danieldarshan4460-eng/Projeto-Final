"""Dados pequenos e conhecidos para os testes (as contas podem ser feitas à mão)."""

import numpy as np
import pandas as pd

NAN = np.nan


def criar_dados_brutos() -> pd.DataFrame:
    """9 linhas: 1 duplicada (id 1) e 1 sem UF (id 8)."""
    linhas = [
        # id, UF,  rede, local, pLC, pMT, CN,  CH,  LC,  MT,  RED
        (1, "SP", 4, 1, 1, 1, 600, 600, 600, 600, 800),
        (2, "SP", 2, 1, 1, 1, 500, 500, 500, 500, 500),
        (3, "RJ", 2, 2, 1, 1, 400, 400, 400, 400, 400),
        (4, "BA", NAN, NAN, 1, 1, 300, 300, 300, 300, 300),
        (5, "BA", 2, 1, 1, 0, NAN, 500, 500, NAN, 0),
        (6, "PA", 3, 1, 0, 0, NAN, NAN, NAN, NAN, NAN),
        (1, "SP", 4, 1, 1, 1, 600, 600, 600, 600, 800),  # duplicada
        (8, NAN, 1, 1, 1, 1, 100, 100, 100, 100, 100),   # sem UF
        (9, "AM", 1, 1, 1, 1, 700, 700, 700, 700, 700),
    ]
    colunas = [
        "NU_SEQUENCIAL", "SG_UF_PROVA", "TP_DEPENDENCIA_ADM_ESC",
        "TP_LOCALIZACAO_ESC", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
        "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    ]
    return pd.DataFrame(linhas, columns=colunas)
