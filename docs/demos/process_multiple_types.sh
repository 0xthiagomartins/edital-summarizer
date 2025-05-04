#!/bin/bash

# Demo: Process with custom summary types
python -m edital_summarizer.main \
  samples/edital-001 \
  --output custom-report.xlsx \
  --summary-types "executive,technical,legal" \
  --verbose 