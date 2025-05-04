#!/bin/bash

# Demo: Process multiple directories
for dir in samples/edital-*/; do
  echo "Processing $dir..."
  python -m edital_summarizer.main \
    "$dir" \
    --output "reports/$(basename $dir).xlsx" \
    --verbose
done 