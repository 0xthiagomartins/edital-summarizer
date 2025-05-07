
## Sumário de Editais - Regras de Negócio e Especificações

Este documento contém as regras de negócio e especificações para a criação de um sistema de processamento e resumo de editais de licitação utilizando a biblioteca CrewAI.

### 1. Objetivo do Sistema

Criar um sistema que processe documentos de editais de licitação para:
1. Extrair metadados relevantes (título, órgão, número do processo, etc.)
2. Gerar resumos executivos e técnicos do conteúdo
3. Produzir um relatório estruturado com as informações extraídas

### 2. Componentes Principais

#### 2.1 Processador de Documentos
- Deve ser capaz de ler documentos em formato PDF e texto
- Deve extrair o conteúdo textual para processamento
- Deve lidar com tamanhos de documentos variados, limitando conforme necessário

#### 2.2 Extrator de Metadados
- Deve identificar e extrair os seguintes campos:
  - Título do edital
  - Órgão responsável
  - Objeto da licitação
  - Número do edital (public_notice)
  - Número do processo (process_id)
  - Número da licitação (bid_number)
  - Datas importantes
  - Telefone de contato
  - Website
  - Cidade/Local

#### 2.3 Gerador de Resumos
- Deve criar dois tipos de resumo:
  - **Resumo Executivo**: Visão geral concisa do edital
  - **Resumo Técnico**: Detalhamento técnico das especificações e requisitos

#### 2.4 Sistema de Relatórios
- Deve combinar os metadados e resumos em um relatório estruturado
- Deve salvar o relatório em formato Excel

### 3. Arquitetura com CrewAI

#### 3.1 Agentes
Implementar os seguintes agentes especializados:

1. **metadata_agent**: Especialista em metadados gerais
2. **identifier_agent**: Especialista em identificar números e códigos (processo, edital, licitação)
3. **organization_agent**: Especialista em identificar organizações, contatos e localizações
4. **executive_summary_agent**: Especialista em criar resumos executivos
5. **technical_summary_agent**: Especialista em criar resumos técnicos detalhados

#### 3.2 Tarefas
Definir as seguintes tarefas:

1. **identifier_task**: Extrair números de editais, processos e licitações
2. **organization_task**: Extrair informações sobre organizações
3. **subject_task**: Extrair objeto e título do edital
4. **executive_summary**: Gerar um resumo executivo
5. **technical_summary**: Gerar um resumo técnico

#### 3.3 Ferramentas
Implementar as seguintes ferramentas para uso dos agentes:

1. **SimpleFileReadTool**: Para ler arquivos
2. **DocumentSearchTool**: Para buscar informações específicas dentro dos documentos
3. **TableExtractionTool**: Para extrair tabelas de documentos

### 4. Configurações e Parâmetros

#### 4.1 Modelos LLM a serem usados
- Para tarefas de identificação, organização e datas: OpenAI GPT-4
- Para resumos executivos e técnicos: Google Gemini Pro

#### 4.2 Limitações de Texto
- Texto completo: máximo 20.000 caracteres
- Para extração de metadados: máximo 5.000 caracteres
- Para resumo executivo: máximo 10.000 caracteres
- Para resumo técnico: máximo 15.000 caracteres

#### 4.3 Parâmetros de LLM
- Para tarefas de identificação: temperatura 0.1
- Para resumos: temperatura 0.3
- Para outras tarefas: temperatura 0.2

### 5. Interface de Linha de Comando

Criar uma CLI que permita:

1. Processar um único documento ou diretório de documentos
2. Especificar tipos de resumo a gerar
3. Definir arquivo de saída
4. Ativar modo verboso para depuração

### 6. Tratamento de Erros e Resiliência

1. Implementar timeout nas chamadas de API (máximo 300 segundos)
2. Tratar erros de API graciosamente
3. Fornecer fallbacks para quando metadados não puderem ser extraídos
4. Verificar compatibilidade com a versão do CrewAI sendo usada

### 7. Requisitos Técnicos

#### 7.1 CrewAI
- Verificar compatibilidade com versão 0.118.0 ou superior
- Adaptar a configuração de agentes e tarefas para as mudanças de API

#### 7.2 Modelos de Linguagem
- OpenAI GPT-4 para extração de metadados precisos
- Google Gemini Pro para resumos e outras tarefas

#### 7.3 Estrutura de Arquivos
- Organizar o código em módulos para:
  - Configuração
  - Processamento de documentos
  - Extração de metadados
  - Geração de resumos
  - CLI

### 8. Exemplos de Uso

```bash
# Processar um único documento
python -m src.edital_summarizer.main samples/edital-001/documento.pdf -o resultado.xlsx -v

# Processar um diretório inteiro
python -m src.edital_summarizer.main samples/edital-001/ -o relatorio-completo.xlsx
```

### 9. Variáveis de Ambiente Necessárias

- `OPENAI_API_KEY`: Chave de API para acessar modelos da OpenAI
- `GOOGLE_API_KEY`: Chave de API para acessar modelos Gemini da Google

### 10. Notas de Implementação

1. **Compatibilidade com CrewAI**: A implementação deve ser flexível para lidar com diferentes versões da API CrewAI.
2. **Reutilização de Código**: Evitar duplicação, utilizar abstrações quando apropriado.
3. **Saídas Verbosas**: Em modo verboso, imprimir informações detalhadas sobre o progresso.
4. **Tratamento de Documentos Grandes**: Implementar estratégias para lidar com documentos que excedam os limites de tokens dos modelos.
5. **Fallbacks**: Implementar mecanismos de fallback quando os modelos primários falharem. 

## Sumário de Editais - Regras de Negócio e Especificações

Este documento contém as regras de negócio e especificações para a criação de um sistema de processamento e resumo de editais de licitação utilizando a biblioteca CrewAI.

### 1. Objetivo do Sistema

Criar um sistema que processe documentos de editais de licitação para:
1. Extrair metadados relevantes (título, órgão, número do processo, etc.)
2. Gerar resumos executivos e técnicos do conteúdo
3. Produzir um relatório estruturado com as informações extraídas

### 2. Componentes Principais

#### 2.1 Processador de Documentos
- Deve ser capaz de ler documentos em formato PDF e texto
- Deve extrair o conteúdo textual para processamento
- Deve lidar com tamanhos de documentos variados, limitando conforme necessário

#### 2.2 Extrator de Metadados
- Deve identificar e extrair os seguintes campos:
  - Título do edital
  - Órgão responsável
  - Objeto da licitação
  - Número do edital (public_notice)
  - Número do processo (process_id)
  - Número da licitação (bid_number)
  - Datas importantes
  - Telefone de contato
  - Website
  - Cidade/Local

#### 2.3 Gerador de Resumos
- Deve criar dois tipos de resumo:
  - **Resumo Executivo**: Visão geral concisa do edital
  - **Resumo Técnico**: Detalhamento técnico das especificações e requisitos

#### 2.4 Sistema de Relatórios
- Deve combinar os metadados e resumos em um relatório estruturado
- Deve salvar o relatório em formato Excel

### 3. Arquitetura com CrewAI

#### 3.1 Agentes
Implementar os seguintes agentes especializados:

1. **metadata_agent**: Especialista em metadados gerais
2. **identifier_agent**: Especialista em identificar números e códigos (processo, edital, licitação)
3. **organization_agent**: Especialista em identificar organizações, contatos e localizações
4. **executive_summary_agent**: Especialista em criar resumos executivos
5. **technical_summary_agent**: Especialista em criar resumos técnicos detalhados

#### 3.2 Tarefas
Definir as seguintes tarefas:

1. **identifier_task**: Extrair números de editais, processos e licitações
2. **organization_task**: Extrair informações sobre organizações
3. **subject_task**: Extrair objeto e título do edital
4. **executive_summary**: Gerar um resumo executivo
5. **technical_summary**: Gerar um resumo técnico

#### 3.3 Ferramentas
Implementar as seguintes ferramentas para uso dos agentes:

1. **SimpleFileReadTool**: Para ler arquivos
2. **DocumentSearchTool**: Para buscar informações específicas dentro dos documentos
3. **TableExtractionTool**: Para extrair tabelas de documentos

### 4. Configurações e Parâmetros

#### 4.1 Modelos LLM a serem usados
- Para tarefas de identificação, organização e datas: OpenAI GPT-4
- Para resumos executivos e técnicos: Google Gemini Pro

#### 4.2 Limitações de Texto
- Texto completo: máximo 20.000 caracteres
- Para extração de metadados: máximo 5.000 caracteres
- Para resumo executivo: máximo 10.000 caracteres
- Para resumo técnico: máximo 15.000 caracteres

#### 4.3 Parâmetros de LLM
- Para tarefas de identificação: temperatura 0.1
- Para resumos: temperatura 0.3
- Para outras tarefas: temperatura 0.2

### 5. Interface de Linha de Comando

Criar uma CLI que permita:

1. Processar um único documento ou diretório de documentos
2. Especificar tipos de resumo a gerar
3. Definir arquivo de saída
4. Ativar modo verboso para depuração

### 6. Tratamento de Erros e Resiliência

1. Implementar timeout nas chamadas de API (máximo 300 segundos)
2. Tratar erros de API graciosamente
3. Fornecer fallbacks para quando metadados não puderem ser extraídos
4. Verificar compatibilidade com a versão do CrewAI sendo usada

### 7. Requisitos Técnicos

#### 7.1 CrewAI
- Verificar compatibilidade com versão 0.118.0 ou superior
- Adaptar a configuração de agentes e tarefas para as mudanças de API

#### 7.2 Modelos de Linguagem
- OpenAI GPT-4 para extração de metadados precisos
- Google Gemini Pro para resumos e outras tarefas

#### 7.3 Estrutura de Arquivos
- Organizar o código em módulos para:
  - Configuração
  - Processamento de documentos
  - Extração de metadados
  - Geração de resumos
  - CLI

### 8. Exemplos de Uso

```bash
# Processar um único documento
python -m src.edital_summarizer.main samples/edital-001/documento.pdf -o resultado.xlsx -v

# Processar um diretório inteiro
python -m src.edital_summarizer.main samples/edital-001/ -o relatorio-completo.xlsx
```

### 9. Variáveis de Ambiente Necessárias

- `OPENAI_API_KEY`: Chave de API para acessar modelos da OpenAI
- `GOOGLE_API_KEY`: Chave de API para acessar modelos Gemini da Google

### 10. Notas de Implementação

1. **Compatibilidade com CrewAI**: A implementação deve ser flexível para lidar com diferentes versões da API CrewAI.
2. **Reutilização de Código**: Evitar duplicação, utilizar abstrações quando apropriado.
3. **Saídas Verbosas**: Em modo verboso, imprimir informações detalhadas sobre o progresso.
4. **Tratamento de Documentos Grandes**: Implementar estratégias para lidar com documentos que excedam os limites de tokens dos modelos.
5. **Fallbacks**: Implementar mecanismos de fallback quando os modelos primários falharem. 
