# Edital Summarizer

## Visão Geral
O Edital Summarizer é um sistema especializado em processamento e análise de editais de licitação utilizando Inteligência Artificial. O sistema utiliza uma arquitetura baseada em agentes (CrewAI) para analisar documentos, determinar sua relevância para um target específico e gerar resumos executivos.

## Arquitetura

### Componentes Principais

1. **EditalSummarizer (Crew Principal)**
   - Classe principal que coordena todo o processamento
   - Gerencia os agentes e suas tarefas
   - Processa documentos e gera resultados

2. **Agentes**
   - **Target Analyst Agent**: Analisa se o documento é relevante para o target especificado
   - **Summary Agent**: Gera resumos executivos dos documentos
   - **Justification Agent**: Gera justificativas quando um documento não é relevante

3. **Processadores**
   - **DocumentProcessor**: Processa diferentes tipos de documentos (PDF, DOCX, TXT, etc.)
   - **MetadataProcessor**: Extrai metadados dos documentos
   - **SummaryProcessor**: Processa e gera resumos
   - **CrewProcessor**: Gerencia o processamento usando a arquitetura de agentes

4. **Ferramentas**
   - **SimpleFileReadTool**: Lê conteúdo de arquivos
   - **DocumentSearchTool**: Busca informações específicas em documentos
   - **TableExtractionTool**: Extrai tabelas de documentos

## Fluxo de Processamento

1. **Entrada**
   - Documento ou diretório de documentos
   - Target para análise
   - Threshold (opcional)
   - Force Match (opcional)

2. **Processamento**
   - Leitura e extração do conteúdo do documento
   - Análise de relevância para o target
   - Geração de resumo (se relevante)
   - Geração de justificativa (se não relevante)

3. **Saída**
   - JSON com resultados do processamento
   - Campos: target_match, threshold_match, target_summary, document_summary, justification, metadata

## Configuração

### Arquivos de Configuração
- `agents.yaml`: Configuração dos agentes (papéis, objetivos, backstories)
- `tasks.yaml`: Configuração das tarefas (descrições, outputs esperados)

### Variáveis de Ambiente
- `OPENAI_API_KEY`: Chave da API OpenAI para os modelos GPT-4
- `GOOGLE_API_KEY`: Chave da API Google para modelos Gemini Pro

## Uso

### Via CLI
```bash
process_edital.bat [caminho_do_edital] [target] [threshold] [arquivo_saida] [force_match]
```

### Parâmetros
1. `caminho_do_edital` (obrigatório)
   - Caminho para arquivo ou diretório
   - Suporta arquivos individuais, diretórios e ZIPs

2. `target` (obrigatório)
   - Termo ou descrição para análise
   - Pode incluir descrição entre parênteses
   - Exemplo: "RPA (Automação de Processos Robotizados)"

3. `threshold` (opcional, padrão: 500)
   - Valor mínimo para contagem de referências
   - Usado principalmente para targets de dispositivos

4. `arquivo_saida` (opcional, padrão: resultado.json)
   - Nome do arquivo JSON de saída

5. `force_match` (opcional, padrão: false)
   - Força o target_match a ser True
   - Útil para testes e processamento forçado

## Estrutura do Projeto

```
src/edital_summarizer/
├── __init__.py
├── crew.py                 # Implementação principal do Crew
├── main.py                 # Ponto de entrada CLI
├── config/
│   ├── agents.yaml        # Configuração dos agentes
│   └── tasks.yaml         # Configuração das tarefas
├── processors/
│   ├── document.py        # Processamento de documentos
│   ├── metadata.py        # Processamento de metadados
│   ├── summary.py         # Processamento de resumos
│   └── crew_processor.py  # Processamento via Crew
├── tools/
│   ├── document_tools.py  # Ferramentas de documento
│   ├── file_tools.py      # Ferramentas de arquivo
│   └── custom_tool.py     # Ferramentas personalizadas
└── utils/
    ├── logger.py          # Configuração de logging
    └── zip_handler.py     # Manipulação de arquivos ZIP
```

## Funcionalidades Principais

### 1. Processamento de Documentos
- Suporte a múltiplos formatos (PDF, DOCX, TXT, MD)
- Processamento de arquivos ZIP
- Extração de texto e metadados
- Limite configurável de caracteres

### 2. Análise de Relevância
- Verificação de relevância para target específico
- Suporte a descrições detalhadas
- Threshold configurável
- Modo force_match para testes

### 3. Geração de Resumos
- Resumos executivos em português
- Foco em aspectos relevantes para o target
- Extração de tabelas e dados estruturados
- Limpeza e formatação de texto

### 4. Tratamento de Erros
- Logging detalhado
- Tratamento de exceções
- Mensagens de erro informativas
- Fallbacks para casos de erro

## Boas Práticas

### 1. Organização de Arquivos
- Manter editais em pastas organizadas
- Usar nomes descritivos
- Evitar caracteres especiais

### 2. Nomenclatura de Targets
- Usar termos completos
- Incluir contexto do negócio
- Evitar abreviações
- Considerar diferentes formas de escrita

### 3. Análise de Resultados
- Verificar arquivo JSON gerado
- Analisar justificativas
- Ajustar targets conforme necessário
- Considerar diferentes contextos

## Dependências Principais
- crewai: Framework para agentes de IA
- PyPDF2: Processamento de PDFs
- python-docx: Processamento de DOCX
- PyYAML: Processamento de arquivos YAML
- OpenAI: Modelos de linguagem GPT-4

## Limitações e Considerações

1. **Performance**
   - Processamento de documentos grandes pode ser lento
   - Limite de caracteres para evitar sobrecarga
   - Cache de resultados não implementado

2. **Precisão**
   - Dependência da qualidade do OCR
   - Variação na formatação dos documentos
   - Necessidade de ajuste fino dos prompts

3. **Segurança**
   - Tratamento de dados sensíveis
   - Validação de inputs
   - Proteção de chaves de API

## Próximos Passos Sugeridos

1. **Melhorias Técnicas**
   - Implementar cache de resultados
   - Otimizar processamento de documentos grandes
   - Adicionar suporte a mais formatos

2. **Funcionalidades**
   - Interface web
   - Processamento em lote
   - Exportação para outros formatos

3. **Documentação**
   - Documentação de API
   - Guias de contribuição
   - Exemplos de uso

## Suporte e Contribuição

Para contribuir com o projeto:
1. Seguir as boas práticas de código
2. Adicionar testes para novas funcionalidades
3. Documentar alterações
4. Manter compatibilidade com versões anteriores

## Contato e Suporte
[Adicionar informações de contato e suporte] 