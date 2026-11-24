# Projeto Final — Análise e Dashboard dos Resultados do ENEM 2025

Projeto da disciplina de **Programação Orientada a Objetos** (Ciência de Dados e Inteligência Artificial).

Sistema em Python que lê os **resultados do ENEM 2025** (INEP — Dados Abertos), trata e analisa os dados com
**Pandas**, gera gráficos interativos com **Plotly** e apresenta tudo em um **dashboard Streamlit**.

## Perguntas que a análise responde

1. Quantos inscritos realmente fizeram as provas, e quantos faltaram a um ou aos dois dias?
2. Como a média geral varia entre regiões e UFs do país?
3. Existe diferença de desempenho entre os tipos de escola (federal, estadual, municipal, privada) e entre escolas urbanas e rurais?

## Estrutura do projeto

```
analise_resultados/
    fonte.py          # FonteDados (abstrata), FonteParquet, FonteCSV
    tratador.py       # TratadorDados: duplicidades, ausentes, colunas derivadas
    analisador.py     # AnalisadorDados: filtros, agrupamentos, estatísticas, indicadores
    indicador.py      # Indicador e subclasses (Numerico, Percentual, Nota, IndicadorPontos)
    interpretador.py  # InterpretadorResultados: texto de análise gerado a partir dos dados
    visualizador.py   # Visualizador (abstrata), gráficos Plotly e Dashboard
app.py                # Dashboard Streamlit
etapa4_demo.py        # Demonstração do tratamento e dos indicadores no terminal
etapa5_graficos.py    # Gera os gráficos em HTML
scripts/              # Exploração dos dados (Etapa 2)
saidas/etapa2/        # Resultados da exploração
tests/                # Testes automatizados (unittest)
docs/                 # Documentação publicada no GitHub Pages
```

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. Baixe `RESULTADOS_2025.csv` no portal do INEP e coloque em `data/`.
2. Gere o arquivo reduzido: `python scripts/item7_arquivo_reduzido.py` (cria `data/resultados_reduzido.parquet`).
3. Abra o dashboard: `streamlit run app.py`.

Os arquivos de dados são grandes e ficam fora do Git (ver `.gitignore`).

## Testes

```bash
python -m unittest discover -s tests -v
```

## Documentação

Publicada no GitHub Pages (branch `gh-pages`, gerada a partir da pasta `docs/`).

## Dados Necessários 

https://drive.google.com/file/d/1oPxkaJAr86BBlveYQbIwBvLx7SXmR3PF/view?usp=sharing
(Coloque na pasta data dentro da pasta do projeto)

