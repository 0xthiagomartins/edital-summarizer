#!/bin/bash

# Demo: Process English bidding documents
python -m edital_summarizer.main \
  samples/edital-001 \
  --output english-report.xlsx \
  --language en \
  --verbose 