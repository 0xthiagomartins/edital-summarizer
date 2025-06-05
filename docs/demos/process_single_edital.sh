#!/bin/bash

# Demo: Process a single bidding document in Portuguese
python -m src.edital_summarizer.main \
  samples/edital-001 \
  -o rel.xlsx \
  -v 


# Modo otimizado (padrão) - bom para testes:
python -m src.edital_summarizer.main samples/edital-001 -o rel.xlsx -v
# Modo completo - para produção
python -m src.edital_summarizer.main samples/edital-001 -o rel.xlsx -v --full-content

# Exemplos com threshold:

# 1. Processar edital verificando quantidade mínima de notebooks (threshold padrão: 500)
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "notebook" \
  --threshold 500 \
  -o rel_notebooks.json \
  -v

# 2. Processar edital verificando quantidade mínima de tablets (threshold personalizado: 1000)
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "tablet" \
  --threshold 1000 \
  -o rel_tablets.json \
  -v

# 3. Processar edital com force_match (ignora threshold)
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target "notebook" \
  --threshold 500 \
  --force-match \
  -o rel_force.json \
  -v

# 4. Processar edital com target multiline (mais preciso)
python -m src.edital_summarizer.main \
  samples/edital-001 \
  --target """
  Fornecimento de Notebooks para Uso Administrativo
  com as seguintes especificações:
  - Notebooks para uso administrativo
  - Processador de última geração
  - Memória RAM mínima de 8GB
  - Armazenamento SSD
  - Sistema operacional Windows
  - Garantia de 12 meses
  """ \
  --threshold 500 \
  -o rel_detalhado.json \
  -v
