#!/bin/bash

# Demo: Process with custom summary types
python -m edital_summarizer.main \
  samples/edital-xxx \
  --output custom-report.xlsx \
  --summary-types "executivo,técnico,legal" \
  --verbose 