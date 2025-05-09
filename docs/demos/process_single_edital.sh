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