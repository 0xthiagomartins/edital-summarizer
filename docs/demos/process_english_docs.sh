#!/bin/bash

# Demo: Process English bidding documents
python -m edital_summarizer.main \
  samples/edital-xxx \
  --output english-report.xlsx \
  --language en \
  --verbose 