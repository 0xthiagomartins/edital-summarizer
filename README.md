# RPA de Processamento e Resumo de Editais

## Visão Geral

Este projeto é um aplicativo Python que monitora uma pasta contendo editais (descompactados ou em ZIP), extrai texto (PDF, MD, TXT, ZIPs aninhados), aplica agentes CrewAI para:

1. Extrair metadados estruturados
2. Gerar diferentes tipos de resumo (executivo, técnico, etc.)
3. Referenciar o diretório de origem de cada edital

Como saída, gera um relatório Excel com colunas para:

* **Origem**: caminho do ZIP ou diretório onde está o edital
* **Metadados**: JSON com título, órgão, datas, objeto, etc.
* **Resumo Executivo**
* **Resumo Técnico**

Uma flag `--verbose` permite exibir logs de execução (incluindo chamadas ao CrewAI).

## Funcionalidades Principais

* Processamento recursivo de arquivos ZIP e diretórios
* Extração de texto de PDFs (e OCR, se configurado) e arquivos `.md`/`.txt`
* Agentes CrewAI pré-configurados para:

  * Extração de metadados
  * Geração de resumos customizados
* Geração de relatório em Excel (`.xlsx`) com todas as colunas necessárias
* Modo silencioso ou verboso via CLI

## Requisitos

* Python 3.10+
* API Key do CrewAI disponível em variável de ambiente `CREWAI_API_KEY`
* Bibliotecas:

  ```bash
  # Instale o uv se ainda não tiver
  pip install uv

  # Instale as dependências usando uv
  uv pip install -r requirements.txt
  ```

## Estrutura do Projeto

```
├── main.py                # Script principal (entry point)
├── pipeline/              # Módulos de extração e resumo
│   ├── extractor.py       # Funções de leitura de ZIPs e PDFs
│   └── summarizer.py      # Configuração de agentes CrewAI
├── requirements.txt       # Dependências do projeto
└── README.md              # Este arquivo de documentação
```

## Configuração

1. Defina sua chave de API CrewAI:

   ```bash
   export CREWAI_API_KEY="<sua_chave_aqui>"
   ```
2. Ajuste, se necessário, os `agent_id` e `prompt_templates` em `pipeline/summarizer.py`.

## Uso

```bash
python main.py /caminho/para/edital_descompactado \
  --output relatório.xlsx \
  [--summary-types executivo,técnico] \
  [--verbose]
```

* `--output`: arquivo Excel de saída (padrão `report.xlsx`)
* `--summary-types`: lista de tipos de resumo separados por vírgula
* `--verbose`: exibe logs detalhados

## Exemplo

```bash
python main.py ./downloads/descompactados \
  --output resumos_editais.xlsx \
  --summary-types executivo,técnico \
  --verbose
```
