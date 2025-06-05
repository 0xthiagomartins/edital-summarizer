# EditalSummarizer Crew

Welcome to the EditalSummarizer Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/edital_summarizer/config/agents.yaml` to define your agents
- Modify `src/edital_summarizer/config/tasks.yaml` to define your tasks
- Modify `src/edital_summarizer/crew.py` to add your own logic, tools and specific args
- Modify `src/edital_summarizer/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the edital-summarizer Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The edital-summarizer Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the EditalSummarizer Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.

## Processamento Rápido via CMD

Para facilitar o processamento dos editais via linha de comando do Windows, foi criado um script batch que automatiza a execução no WSL Ubuntu.

### Pré-requisitos
- Windows 10 ou superior
- WSL Ubuntu instalado
- Python e dependências instaladas no WSL Ubuntu

### Como Usar

1. Abra o CMD (Prompt de Comando)
2. Navegue até o diretório do projeto
3. Execute o comando:

```bash
# Uso básico (arquivo de saída padrão: rel.xlsx)
process_edital.bat samples/edital-001

# Especificando arquivo de saída personalizado
process_edital.bat samples/edital-001 meu_relatorio.xlsx
```

### Parâmetros
- Primeiro parâmetro: Caminho do edital a ser processado
- Segundo parâmetro (opcional): Nome do arquivo de saída (padrão: rel.xlsx)

### Exemplos

```bash
# Processar edital com nome de saída padrão
process_edital.bat samples/edital-001

# Processar edital com nome de saída personalizado
process_edital.bat samples/edital-001 relatorio_final.xlsx

# Processar edital em subdiretório
process_edital.bat samples/outros/editais/edital-002
```

O script irá:
1. Verificar os parâmetros fornecidos
2. Executar o processamento no WSL Ubuntu
3. Gerar o arquivo Excel com os resultados
4. Mostrar mensagem de sucesso ou erro

# Edital Summarizer

Processador de editais de licitação utilizando a CrewAI para análise e resumo de documentos.

## Funcionalidades

- Análise de relevância de documentos para targets específicos
- Validação de threshold mínimo para dispositivos
- Geração de resumos executivos
- Extração de metadados
- Suporte a múltiplos formatos de documento (PDF, DOCX, TXT, etc.)

## Instalação

```bash
pip install edital-summarizer
```

## Uso

### Via Linha de Comando

```bash
edital-summarizer <caminho_do_documento> --target "notebook" --threshold 500
```

Parâmetros:
- `caminho_do_documento`: Caminho para o documento ou diretório de documentos
- `--target`: Target para análise (ex: "notebook", "tablet", "RPA")
- `--threshold`: Threshold mínimo para dispositivos (padrão: 500)
- `--force-match`: Força o target_match a ser True
- `--output`: Caminho para o arquivo de saída (padrão: "resultado.json")
- `-v, --verbose`: Ativa modo verboso para exibir logs detalhados

### Via Python

```python
from edital_summarizer import process_edital

result = process_edital(
    document_path="caminho/do/documento.pdf",
    target="notebook",
    threshold=500,
    force_match=False,
    verbose=True
)
```

## Formato da Resposta

A resposta é um objeto JSON com os seguintes campos:

```json
{
    "target_match": true,           // Indica se o documento é relevante para o target
    "threshold_match": true,        // Indica se o documento atende ao threshold mínimo
    "threshold_status": "true",     // Status do threshold: "true", "false" ou "inconclusive"
    "target_summary": "...",        // Resumo específico sobre o target no documento
    "document_summary": "...",      // Resumo geral do documento
    "justification": "...",         // Justificativa para não geração do resumo
    "metadata": {                   // Metadados do documento
        "identifier": {
            "public_notice": "...",
            "process_id": "...",
            "bid_number": "..."
        },
        "organization": {
            "name": "...",
            "location": "..."
        }
    },
    "error": null                   // Mensagem de erro, se houver
}
```

## Threshold

O threshold é uma funcionalidade que permite validar a quantidade mínima de dispositivos mencionada no documento. Por exemplo, se o target for "notebook" e o threshold for 500, o documento só será considerado relevante se mencionar uma quantidade de notebooks maior ou igual a 500.

O status do threshold pode ser:
- `"true"`: A quantidade mencionada é maior ou igual ao threshold
- `"false"`: A quantidade mencionada é menor que o threshold
- `"inconclusive"`: Não foi possível determinar a quantidade com certeza

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.