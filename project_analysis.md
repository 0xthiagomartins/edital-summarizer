# Edital Summarizer - Arquitetura CrewAI

## Contexto do Negócio

O processo atual de análise de editais é realizado por uma única pessoa e consiste em:

1. **Extração do Edital** (Já automatizado via RPA)
   - Download do edital do site
   - Descompactação do arquivo ZIP
   - Organização dos documentos

2. **Análise do Edital** (Objetivo deste projeto)
   - Recebe pasta com documentos extraídos
   - Recebe metadata.json com contexto
   - Recebe target e threshold da empresa
   - Analisa relevância do edital

3. **Decisão de Relevância**
   - Verifica se o edital é relevante para o target
   - Se relevante, verifica se atinge o threshold
   - Gera justificativa da decisão
   - Cria relatório final

## Análise do Caso de Uso

### Complexidade (Score: 5/10)

1. **Número de Passos** (5/10)
   - Análise de target
   - Verificação de threshold
   - Geração de justificativa
   - Criação de relatório

2. **Interdependências** (4/10)
   - Análise depende do target/threshold
   - Justificativa depende da análise
   - Fluxo linear e simples

3. **Lógica Condicional** (5/10)
   - Decisão baseada em threshold
   - Regras de relevância
   - Validação de outputs

4. **Conhecimento de Domínio** (6/10)
   - Análise de editais
   - Regras de licitação
   - Validação de outputs

### Precisão (Score: 8/10)

1. **Estrutura de Output** (9/10)
   - JSON estritamente formatado
   - Campos obrigatórios definidos
   - Validação via Pydantic
   - Tipos de dados específicos

2. **Necessidade de Precisão** (8/10)
   - Decisões de relevância críticas
   - Thresholds precisos
   - Justificativas claras

3. **Reprodutibilidade** (8/10)
   - Mesmo input deve gerar mesmo output
   - Validação consistente
   - Processamento determinístico

4. **Tolerância a Erros** (7/10)
   - Erros podem impactar decisões
   - Validação rigorosa necessária
   - Logs para debug

## Recomendação de Arquitetura

### Abordagem Recomendada: Flow Simples

Baseado na análise acima e no fluxo real do negócio, recomendamos uma arquitetura simples usando **Flow**:

1. **Flow Principal**
   - Gerencia o estado do processamento
   - Controla o fluxo de execução
   - Valida outputs
   - Gera relatório final

2. **Estados do Flow**
   - **Inicial**: Recebe inputs (target, threshold, pasta)
   - **Análise**: Processa documentos e metadata
   - **Decisão**: Avalia relevância e threshold
   - **Final**: Gera relatório com justificativa

### Justificativa

1. **Simplicidade do Processo**
   - Fluxo linear e claro
   - Poucas interdependências
   - Processo único e bem definido
   - Não há necessidade de múltiplos crews

2. **Alta Precisão Necessária**
   - Flow oferece controle sobre o estado
   - Validação robusta de outputs
   - Processamento determinístico
   - Logs detalhados

3. **Manutenibilidade**
   - Código mais simples
   - Menos pontos de falha
   - Mais fácil de debugar
   - Mais fácil de manter

## Plano de Implementação

1. **Fase 1: Estrutura Base do Flow**
   - Criar classe EditalAnalysisFlow
   - Definir estados e transições
   - Implementar validações
   - Configurar logs

2. **Fase 2: Processamento de Documentos**
   - Leitura de documentos
   - Processamento de metadata
   - Extração de informações
   - Validação de inputs

3. **Fase 3: Análise e Decisão**
   - Análise de target
   - Verificação de threshold
   - Geração de justificativa
   - Validação de outputs

4. **Fase 4: Relatório Final**
   - Formatação do resultado
   - Validação do relatório
   - Logs de execução
   - Tratamento de erros

## Benefícios Esperados

1. **Simplicidade**
   - Código mais direto
   - Menos complexidade
   - Mais fácil de entender
   - Mais fácil de manter

2. **Confiabilidade**
   - Validações robustas
   - Tratamento de erros
   - Logs detalhados
   - Processamento consistente

3. **Performance**
   - Processamento otimizado
   - Menos overhead
   - Uso eficiente de recursos
   - Resposta mais rápida

4. **Manutenibilidade**
   - Código organizado
   - Responsabilidades claras
   - Fácil de testar
   - Fácil de estender 