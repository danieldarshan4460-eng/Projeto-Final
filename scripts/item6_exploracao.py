"""Etapa 2 - Item 6, parte A: funil de presença e estatísticas das notas.

Responde: quantos inscritos fazem as provas? Como são as notas de quem fez?
A média geral é a média das 5 notas (CN, CH, LC, MT e redação), calculada só
para quem fez os DOIS dias de prova.
Como rodar (com o .venv ativo, na pasta do projeto):
    python scripts\\item6a_funil_estatisticas.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ / "data" / "RESULTADOS_2025.csv"
PASTA_SAIDA = RAIZ / "saidas" / "etapa2"
TAMANHO_BLOCO = 500_000

NOTAS = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
COLUNAS = (["TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC", "SG_UF_PROVA",
            "TP_PRESENCA_LC", "TP_PRESENCA_CH", "TP_PRESENCA_CN", "TP_PRESENCA_MT"]
           + NOTAS)
TIPOS = {nota: "float32" for nota in NOTAS}

# Códigos conforme o dicionário do ENEM (confira no dicionário do INEP).
REDE = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
LOCALIZACAO = {1: "Urbana", 2: "Rural"}
REGIAO_POR_UF = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte", "AL": "Nordeste", "BA": "Nordeste",
    "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste", "DF": "Centro-Oeste",
    "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}
SOMAR = NOTAS + ["MEDIA_GERAL", "REDACAO_ZERO", "QTDE"]


def somar_grupo(acumulado: pd.DataFrame | None, novo: pd.DataFrame) -> pd.DataFrame:
    """Junta as somas do bloco atual com as dos blocos anteriores."""
    return novo if acumulado is None else acumulado.add(novo, fill_value=0)


def processar() -> dict:
    """Lê o arquivo em blocos e guarda só contagens, somas e as notas de quem fez prova."""
    funil = dict(total=0, dia1=0, dia2=0, ambos=0, so_dia1=0, so_dia2=0,
                 nenhum=0, dias_inconsistentes=0)
    notas_validas = {nota: [] for nota in NOTAS}
    grupos = {nome: None for nome in ["rede", "localizacao", "regiao", "uf"]}

    blocos = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="latin1",
                         usecols=COLUNAS, dtype=TIPOS, chunksize=TAMANHO_BLOCO)
    for numero, b in enumerate(blocos, start=1):
        # ---- funil (1º dia = LC/CH, 2º dia = CN/MT; código 1 = fez a prova) ----
        dia1 = b["TP_PRESENCA_LC"] == 1
        dia2 = b["TP_PRESENCA_MT"] == 1
        funil["total"] += len(b)
        funil["dia1"] += int(dia1.sum())
        funil["dia2"] += int(dia2.sum())
        funil["ambos"] += int((dia1 & dia2).sum())
        funil["so_dia1"] += int((dia1 & ~dia2).sum())
        funil["so_dia2"] += int((~dia1 & dia2).sum())
        funil["nenhum"] += int((~dia1 & ~dia2).sum())
        # as provas do mesmo dia deveriam ter a mesma presença
        funil["dias_inconsistentes"] += int(((b["TP_PRESENCA_LC"] != b["TP_PRESENCA_CH"]) |
                                              (b["TP_PRESENCA_CN"] != b["TP_PRESENCA_MT"])).sum())

        # ---- notas de quem fez cada prova (para as estatísticas descritivas) ----
        for nota in NOTAS:
            notas_validas[nota].append(b[nota].dropna().to_numpy())

        # ---- média geral: só quem fez os dois dias (as 5 notas existem) ----
        c = b[dia1 & dia2 & b[NOTAS].notna().all(axis=1)].copy()
        c[NOTAS] = c[NOTAS].astype("float64")
        c["MEDIA_GERAL"] = c[NOTAS].mean(axis=1)
        c["REDACAO_ZERO"] = (c["NU_NOTA_REDACAO"] == 0).astype(float)
        c["QTDE"] = 1
        c["REGIAO"] = c["SG_UF_PROVA"].map(REGIAO_POR_UF)
        for nome, chave in [("rede", "TP_DEPENDENCIA_ADM_ESC"), ("localizacao", "TP_LOCALIZACAO_ESC"),
                            ("regiao", "REGIAO"), ("uf", "SG_UF_PROVA")]:
            grupos[nome] = somar_grupo(grupos[nome], c.groupby(chave)[SOMAR].sum())
        print(f"Bloco {numero}: {len(b):,} linhas lidas")
    return {"funil": funil, "notas": notas_validas, "grupos": grupos}


def tabela_funil(f: dict) -> pd.DataFrame:
    linhas = [
        ("Inscritos (todas as linhas)", f["total"]),
        ("Fez o 1º dia (LC e CH)", f["dia1"]),
        ("Fez o 2º dia (CN e MT)", f["dia2"]),
        ("Fez os dois dias", f["ambos"]),
        ("Fez só o 1º dia", f["so_dia1"]),
        ("Fez só o 2º dia", f["so_dia2"]),
        ("Não fez nenhum dia", f["nenhum"]),
    ]
    t = pd.DataFrame(linhas, columns=["etapa", "pessoas"])
    t["percentual"] = (t["pessoas"] / f["total"] * 100).round(1)
    return t


def tabela_estatisticas(notas: dict) -> pd.DataFrame:
    """Média, mediana, desvio, mínimo e máximo de cada nota (só de quem fez a prova)."""
    saida = {}
    for nota, pedacos in notas.items():
        v = np.concatenate(pedacos).astype("float64")
        saida[nota] = {"pessoas": v.size, "media": v.mean(), "mediana": np.median(v),
                       "desvio": v.std(ddof=1), "minimo": v.min(), "maximo": v.max(),
                       "pct_zero": (v == 0).mean() * 100}
    return pd.DataFrame(saida).T.round(1)


def tabela_grupo(soma: pd.DataFrame, nomes: dict | None = None) -> pd.DataFrame:
    t = pd.DataFrame({"pessoas": soma["QTDE"].astype(int)})
    t["media_geral"] = soma["MEDIA_GERAL"] / soma["QTDE"]
    for nota in NOTAS:
        t[nota.replace("NU_NOTA_", "").lower()] = soma[nota] / soma["QTDE"]
    t["redacao_zero_pct"] = soma["REDACAO_ZERO"] / soma["QTDE"] * 100
    t = t.round(1)
    if nomes:
        t.index = [nomes.get(int(i), i) for i in t.index]
    return t.sort_values("media_geral", ascending=False)


def main() -> None:
    if not ARQUIVO_CSV.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    r = processar()

    funil = tabela_funil(r["funil"])
    estat = tabela_estatisticas(r["notas"])
    g = r["grupos"]
    tabelas = {
        "media_por_rede": tabela_grupo(g["rede"], REDE),
        "media_por_localizacao": tabela_grupo(g["localizacao"], LOCALIZACAO),
        "media_por_regiao": tabela_grupo(g["regiao"]),
        "media_por_uf": tabela_grupo(g["uf"]),
    }
    funil.to_csv(PASTA_SAIDA / "funil_presenca.csv", index=False)
    estat.to_csv(PASTA_SAIDA / "estatisticas_notas.csv")
    for nome, t in tabelas.items():
        t.to_csv(PASTA_SAIDA / f"{nome}.csv")

    print("\n=== FUNIL DE PRESENÇA ===")
    print(funil.to_string(index=False))
    print(f"(Linhas em que as provas do mesmo dia têm presença diferente: "
          f"{r['funil']['dias_inconsistentes']:,})")
    print("\n=== ESTATÍSTICAS DAS NOTAS (só de quem fez cada prova) ===")
    print(estat.to_string())
    print("\n=== MÉDIA GERAL (5 notas) de quem fez os dois dias ===")
    for nome, t in tabelas.items():
        print(f"\n--- {nome} ---")
        print(t.to_string())
    print(f"\nTabelas salvas em {PASTA_SAIDA}")


if __name__ == "__main__":
    main()