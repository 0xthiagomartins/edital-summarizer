#!/bin/bash

# Demo: Process a single bidding document in Portuguese
python -m edital_summarizer.main \
  samples/edital-001 \
  --output resultado-edital.xlsx \
  --verbose 