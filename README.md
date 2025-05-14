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

Sistema para processamento e análise de editais de licitação utilizando IA.

## Uso do Processador de Editais

O script `process_edital.bat` permite processar editais de forma automatizada. Ele suporta arquivos individuais, diretórios e arquivos ZIP.

### Sintaxe

```cmd
process_edital.bat [caminho_do_edital] [target] [threshold] [arquivo_saida] [force_match]
```

### Parâmetros

1. `caminho_do_edital` (obrigatório)
   - Caminho para o arquivo ou diretório do edital
   - Pode ser um arquivo individual, diretório ou arquivo ZIP
   - Exemplos:
     - `samples/edital-001`
     - `samples/edital-001.zip`
     - `C:\Users\SDS\Documents\editais\edital-001`

2. `target` (obrigatório)
   - Termo ou descrição para análise
   - Pode incluir descrição entre parênteses
   - Exemplos:
     - `RPA`
     - `RPA (Automação de Processos Robotizados)`
     - `Tablet (Dispositivo móvel)`

3. `threshold` (opcional, padrão: 500)
   - Valor mínimo para contagem de referências
   - Usado principalmente para targets de dispositivos
   - Exemplo: `500`

4. `arquivo_saida` (opcional, padrão: resultado.json)
   - Nome do arquivo JSON de saída
   - Exemplos:
     - `meu_resultado.json`
     - `output/resultado.json`

5. `force_match` (opcional, padrão: false)
   - Força o target_match a ser True
   - Útil para testar o processamento dos metadados
   - Valores: `true` ou `false`

### Exemplos de Uso

1. Uso básico (recomendado):
```cmd
process_edital.bat samples/edital-001 "RPA (Automação de Processos Robotizados)" 500 resultado.json
```

2. Processar arquivo ZIP:
```cmd
process_edital.bat samples/edital-001.zip "RPA (Automação de Processos Robotizados)" 500 resultado.json
```

3. Processar diretório:
```cmd
process_edital.bat samples/editais "Tablet (Dispositivo móvel)" 300 output/resultado.json
```

4. Forçar target_match (para testes):
```cmd
process_edital.bat samples/edital-001 "RPA" 500 resultado.json true
```

5. Uso mínimo (apenas caminho e target):
```cmd
process_edital.bat samples/edital-001 "RPA"
```

6. Uso com caminho absoluto:
```cmd
process_edital.bat C:\Users\SDS\Documents\editais\edital-001 "RPA" 500 resultado.json
```

### Formato de Saída

O arquivo JSON de saída terá o seguinte formato:

```json
{
  "target_match": true/false,
  "threshold_match": true/false,
  "summary": "resumo executivo (se target_match for true)",
  "metadata": {
    "identifier": {
      "public_notice": "...",
      "process_id": "...",
      "bid_number": "..."
    },
    "organization": {
      "organization": "...",
      "phone": "...",
      "website": "...",
      "location": "..."
    },
    "subject": {
      "title": "...",
      "object": "...",
      "dates": "..."
    }
  }
}
```

### Observações

- O script suporta arquivos ZIP aninhados (ZIPs dentro de ZIPs)
- Arquivos ocultos e temporários são ignorados automaticamente
- O processamento é feito no WSL Ubuntu
- Os arquivos temporários são limpos automaticamente após o processamento
- Para testar apenas o processamento de metadados, use o parâmetro `force_match=true`
- O threshold é especialmente importante para targets de dispositivos (tablet, celular, notebook, etc.)
- O script escapa automaticamente caracteres especiais no target (parênteses, espaços, etc.)

C:\Users\SDS\Documents\edital-summarizer\process_edital.bat /mnt/c/Users/SDS/Documents/edital-1747239577377-j5y0mtp8 "RPA (Automação de Processos Robotizados)" 500 llmResponse.json

C:\\Users\\SDS\\Documents\\edital-summarizer\\process_edital.bat //mnt//c//Users//SDS//Documents//edital-1747240054638-ifpkr1k4 "RPA (Automação de Processos Robotizados)" 500 llmResponse.json