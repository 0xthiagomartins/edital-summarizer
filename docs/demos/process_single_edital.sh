#!/bin/bash

# Demo: Process a single bidding document in Portuguese
python -m src.edital_summarizer.main \
  samples/edital-001 \
  -o rel.xlsx \
  -v 