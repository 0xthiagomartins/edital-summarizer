# Sprint: Refatoração do Edital Summarizer

## Objetivo
Refatorar o sistema para usar LLM diretamente nos métodos do Flow, mantendo um único agente e melhorando a precisão das análises.

## Tasks

### 1. Implementar Métodos no Flow
- [x] `analyze_target`
  - [x] Implementar método com prompt para análise de target
  - [x] Implementar lógica de matching contextual
  - [x] Status: Concluído

- [ ] `extract_quantities`
  - [ ] Implementar método com prompt para extração de quantidades
  - [ ] Implementar lógica de extração de números e unidades
  - [ ] Status: Não iniciado

- [ ] `extract_specifications`
  - [ ] Implementar método com prompt para extração de especificações
  - [ ] Implementar lógica de extração de características técnicas
  - [ ] Status: Não iniciado

- [ ] `generate_summary`
  - [ ] Implementar método com prompt para geração de resumo
  - [ ] Implementar lógica de estruturação do resumo
  - [ ] Status: Não iniciado

- [ ] `generate_justification`
  - [ ] Implementar método com prompt para geração de justificativa
  - [ ] Implementar lógica de fundamentação da decisão
  - [ ] Status: Não iniciado

### 2. Melhorar Flow
- [x] Refatorar `EditalAnalysisFlow`
  - [x] Implementar métodos diretamente na classe
  - [x] Atualizar gerenciamento de estado
  - [x] Status: Concluído

### 3. Melhorias Gerais
- [ ] Melhorar tratamento de erros
  - [ ] Adicionar logs detalhados
  - [ ] Implementar tratamento de exceções
  - [ ] Status: Não iniciado

- [ ] Otimizar performance
  - [ ] Implementar cache para documentos
  - [ ] Otimizar processamento de PDFs
  - [ ] Status: Não iniciado

## Critérios de Aceitação
1. Cada método deve ter um prompt específico e bem definido
2. O sistema deve manter a mesma interface atual
3. As análises devem ser mais precisas que a versão com regex
4. A performance deve ser mantida ou melhorada

## Métricas de Sucesso
1. Acurácia da análise de target > 90%
2. Precisão na extração de quantidades > 85%
3. Tempo de processamento < 30s por edital

## Próximos Passos
1. ✅ Testar o método `analyze_target` com diferentes tipos de editais
2. Iterar sobre o prompt baseado nos resultados
3. Implementar `extract_quantities`
4. Continuar com os próximos métodos na ordem definida

## Ponto de Teste Atual
Precisamos testar o método `analyze_target` com diferentes tipos de editais para validar:
1. A precisão do matching contextual
2. O comportamento com diferentes tipos de targets (produtos e serviços)
3. O tratamento de casos limite

Por favor, execute o seguinte comando para testar:
```bash
.\process_edital.bat C:\Users\SDS\Documents\edital-summarizer\samples\edital-004 "Fornecimento de Tablets para Educação" 500 llmResponse_edital-004.json -v
```

Após executar, me envie o resultado para que eu possa avaliar se o comportamento está conforme esperado. 