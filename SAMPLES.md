# Exemplos de Uso do Processador de Editais

Este documento contém exemplos práticos de como utilizar o script `process_edital.bat` para diferentes casos de negócio da Samsung SDS.

## Estrutura Básica do Comando

```bash
process_edital.bat [caminho_do_documento] [target] [threshold] [arquivo_saida]
```

## Targets Multiline

Para maior precisão na busca, você pode usar targets em múltiplas linhas. Para isso, use aspas triplas (""") no Windows:

```bash
process_edital.bat "caminho/do/documento" """
Solução de Inteligência Artificial
com as seguintes características:
- Processamento de Linguagem Natural
- Análise de Imagens
- Aprendizado de Máquina
- Implementação On-Premise
""" 500 resultado.json
```

## Exemplos por Área de Negócio

### 1. Inteligência Artificial

#### Target Genérico para IA
```bash
process_edital.bat "caminho/do/documento" """
Solução de Inteligência Artificial
com foco em:
- Análise de dados
- Processamento de imagens
- Automação de processos
- Aprendizado de máquina
""" 500 resultado.json
```

#### Target para Projetos de IA
```bash
process_edital.bat "caminho/do/documento" """
Desenvolvimento de Projeto de Inteligência Artificial
com as seguintes características:
- Análise preditiva
- Processamento de dados
- Automação de decisões
- Integração com sistemas existentes
""" 500 resultado.json
```

### 2. RPA (Robot Process Automation)

#### Target Genérico para RPA
```bash
process_edital.bat "caminho/do/documento" """
Automação de Processos
com as seguintes características:
- Robotização de tarefas repetitivas
- Integração com sistemas existentes
- Redução de erros operacionais
- Aumento de produtividade
""" 500 resultado.json
```

#### Target para Automação de Processos
```bash
process_edital.bat "caminho/do/documento" """
Automação de Processos Administrativos
com foco em:
- Processos repetitivos
- Integração de sistemas
- Redução de erros manuais
- Aumento de produtividade
- Monitoramento de processos
""" 500 resultado.json
```

### 3. Dispositivos

#### Target para Equipamentos de Informática
```bash
process_edital.bat "caminho/do/documento" """
Fornecimento de Equipamentos de Informática
com as seguintes especificações:
- Notebooks para uso administrativo
- Processador de última geração
- Memória RAM mínima de 8GB
- Armazenamento SSD
- Sistema operacional Windows
- Garantia de 12 meses
""" 500 resultado.json
```

#### Target para Tablets Educacionais
```bash
process_edital.bat "caminho/do/documento" """
Fornecimento de Tablets para Educação
com as seguintes especificações:
- Tablets para uso educacional
- Sistema operacional Android
- Suporte a caneta digital
- Tela de alta resolução
- Bateria de longa duração
- Capa protetora
- Garantia de 12 meses
""" 500 resultado.json
```

#### Target para Smartphones Corporativos
```bash
process_edital.bat "caminho/do/documento" """
Fornecimento de Smartphones Corporativos
com as seguintes especificações:
- Smartphones para uso corporativo
- Sistema operacional Android
- Câmera de alta resolução
- Bateria de longa duração
- Suporte a 5G
- Garantia de 12 meses
""" 500 resultado.json
```

## Dicas para Targets Mais Efetivos

1. **Pense como o Cliente**: Use termos que o órgão público usaria
   - ❌ "Notebooks Samsung Galaxy Book"
   - ✅ "Notebooks para uso administrativo com processador de última geração"

2. **Evite Marcações Diretas**: Não mencione marcas específicas
   - ❌ "Smartphones Samsung Galaxy"
   - ✅ "Smartphones corporativos com sistema Android"

3. **Foque nas Necessidades**: Especifique o propósito do equipamento
   - ❌ "Tablets Samsung"
   - ✅ "Tablets para uso educacional com suporte a caneta digital"

4. **Use Termos do Mercado**: Utilize termos comuns em editais
   - ❌ "IA"
   - ✅ "Solução de Inteligência Artificial para análise de dados"

5. **Use Targets Multiline**: Para maior precisão, liste características específicas
   - ❌ "Tablet para educação"
   - ✅ """
     Fornecimento de Tablets para Educação
     com as seguintes especificações:
     - Tablets para uso educacional
     - Sistema operacional Android
     - Suporte a caneta digital
     - Tela de alta resolução
     """

## Exemplos de Casos Reais

### Exemplo 1: Licitação para IA em Hospital
```bash
process_edital.bat "editais/hospital_ia.txt" """
Solução de Inteligência Artificial para Análise de Imagens Médicas
com as seguintes características:
- Processamento de imagens DICOM
- Integração com sistemas PACS
- Análise de radiografias
- Detecção de anomalias
- Implementação em infraestrutura local
- Suporte técnico 24/7
""" 500 resultado_hospital.json
```

### Exemplo 2: Licitação para RPA em Banco
```bash
process_edital.bat "editais/banco_rpa.txt" """
Automação de Processos Bancários
com foco em:
- Processamento de transações
- Reconciliação de contas
- Geração de relatórios
- Integração com sistemas bancários
- Conformidade com regulamentações
- Suporte técnico especializado
""" 500 resultado_banco.json
```

### Exemplo 3: Licitação para Equipamentos em Escola
```bash
process_edital.bat "editais/escola_dispositivos.txt" """
Fornecimento de Equipamentos para Laboratório de Informática
com as seguintes especificações:
- Notebooks para uso educacional
- Processador de última geração
- Memória RAM mínima de 8GB
- Armazenamento SSD
- Sistema operacional Windows
- Garantia de 12 meses
- Suporte técnico especializado
- Treinamento para professores
""" 500 resultado_escola.json
```

## Observações Importantes

1. O `threshold` padrão é 500, mas pode ser ajustado conforme necessário
2. O arquivo de saída pode ter qualquer nome, mas deve terminar em `.json`
3. O caminho do documento pode ser um arquivo único ou um diretório
4. Use o parâmetro `--force-match` apenas quando necessário forçar a análise
5. Para targets multiline, use aspas triplas (""") no Windows

## Boas Práticas

1. **Organização de Arquivos**:
   - Mantenha os editais em pastas organizadas por tipo
   - Use nomes descritivos para os arquivos de saída

2. **Nomenclatura de Targets**:
   - Evite abreviações
   - Use termos completos e técnicos
   - Inclua o contexto do negócio
   - Use targets multiline para maior precisão
   - Pense como o órgão público ao criar o target

3. **Análise de Resultados**:
   - Verifique sempre o arquivo JSON gerado
   - Analise as justificativas geradas
   - Ajuste os targets conforme necessário
   - Considere diferentes formas como o edital pode ser escrito 