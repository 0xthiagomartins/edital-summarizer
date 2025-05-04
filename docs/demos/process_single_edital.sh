#!/bin/bash

# Demo: Process a single bidding document in Portuguese
python -m edital_summarizer.main \
  samples/edital-xxx \
  --output resultado-edital.xlsx \
  --verbose 