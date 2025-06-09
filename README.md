# Edital Summarizer

Uma ferramenta inteligente para análise e resumo de editais de licitação, utilizando CrewAI e GPT-4 para identificar oportunidades de negócio relevantes.

## 🚀 Funcionalidades

- **Análise Inteligente**: Identifica automaticamente editais relevantes para seu negócio
- **Resumo Estruturado**: Gera resumos claros e objetivos dos editais
- **Suporte a Múltiplos Formatos**: Processa PDFs, Word, PowerPoint, Excel, TXT, MD e mais
- **Metadados Automáticos**: Extrai informações como número do edital, cidade/UF e datas
- **Threshold Configurável**: Define quantidade mínima para produtos
- **Justificativa Clara**: Explica por que um edital é ou não relevante

## 📋 Pré-requisitos

- Python 3.10 ou superior
- OpenAI API Key
- Dependências listadas em `pyproject.toml`

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/0xthiagomartins/edital-summarizer.git
cd edital-summarizer
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -e .
```

4. Configure a API Key:
```bash
# Windows
set OPENAI_API_KEY=sua-api-key
# Linux/Mac
export OPENAI_API_KEY=sua-api-key
```

## 🎯 Uso

### Comando Básico

```bash
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "Fornecimento de Notebooks para Uso Administrativo" \
  --threshold 500 \
  -o resultado.json \
  -v
```

### Parâmetros

- `edital_path_dir`: Caminho para o diretório do edital
- `--target`: Target para análise (ex: "Fornecimento de Notebooks")
- `--threshold`: Quantidade mínima para dispositivos (use 0 para serviços)
- `-o/--output`: Arquivo de saída (JSON)
- `--force-match`: Força o target_match a ser True
- `-v/--verbose`: Ativa modo verboso para logs detalhados

### Exemplos

#### 1. Análise de Notebooks
```bash
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "Fornecimento de Notebooks para Uso Administrativo" \
  --threshold 500 \
  -o resultado.json \
  -v
```

#### 2. Serviço de RPA
```bash
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "Automação de Processos com RPA" \
  --threshold 0 \
  -o resultado.json \
  -v
```

#### 3. Forçar Match
```bash
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "Fornecimento de Tablets para Educação" \
  --threshold 1000 \
  --force-match \
  -o resultado.json \
  -v
```

## 📊 Saída

O sistema retorna um JSON com:

```json
{
    "bid_number": "string",           // Número do edital/licitação
    "city": "string",                 // Cidade/UF do edital
    "target_match": true/false,       // O edital é relevante para seu target?
    "threshold_match": "true/false/inconclusive",  // Atingiu a quantidade mínima?
    "is_relevant": true/false,        // O edital é relevante considerando todas as regras?
    "summary": "...",                 // Resumo detalhado do conteúdo do edital
    "justification": "..."            // Justificativa clara e coerente da decisão
}
```

## 📁 Estrutura do Projeto

```
edital-summarizer/
├── src/
│   └── edital_summarizer/
│       ├── __init__.py
│       ├── crew.py          # Lógica principal do processamento
│       ├── main.py          # Ponto de entrada CLI
│       ├── schemas.py       # Schemas de dados
│       ├── agents.py        # Definição dos agentes
│       ├── config/          # Configurações
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       ├── tools/          # Ferramentas de processamento
│       │   ├── file_tools.py
│       │   ├── document_tools.py
│       │   └── format_extractor.py
│       └── utils/          # Utilitários
│           └── logger.py
├── samples/                # Exemplos de editais
├── docs.md                # Documentação detalhada
├── README.md              # Este arquivo
├── LICENSE
└── pyproject.toml         # Configuração do projeto
```

## 🔍 Dicas de Uso

1. **Targets Efetivos**
   - Seja específico: "Fornecimento de Notebooks para Uso Administrativo"
   - Inclua contexto: "Automação de Processos com RPA para Área Financeira"
   - Use termos do mercado: "Solução de Inteligência Artificial para Análise de Dados"

2. **Threshold Realista**
   - Notebooks: 500-1000
   - Tablets: 1000-2000
   - Smartphones: 500-1000

3. **Modo Verboso**
   - Use `-v` para debug e entendimento do processamento
   - Mostra informações detalhadas sobre cada etapa

## 📚 Documentação

Para mais detalhes sobre o uso e configuração, consulte:
- [Documentação Detalhada](docs.md)
- [Exemplos de Uso](docs.md#exemplos-práticos)

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
