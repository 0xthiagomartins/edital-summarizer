import os
from pathlib import Path
import pandas as pd
from typing import List, Optional
import json
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pipeline.extractor import process_directory
from pipeline.summarizer import DocumentSummarizer

app = typer.Typer(help="Process bidding documents and generate summaries.")
console = Console()

def process_editais(
    input_path: Path,
    output_file: Path,
    summary_types: List[str],
    verbose: bool = False
) -> None:
    """Process bidding documents and generate summaries."""
    if not input_path.exists():
        console.print(f"[red]Error: Input path does not exist: {input_path}[/red]")
        raise typer.Exit(1)

    # Initialize the summarizer
    summarizer = DocumentSummarizer()

    # Process all documents
    results = []
    extracted_texts = process_directory(input_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(extracted_texts))
        
        for file_path, text in extracted_texts.items():
            if verbose:
                console.print(f"Processing: {file_path}")
                
            try:
                # Process document and generate summaries
                result = summarizer.process_document(text, summary_types)
                
                # Add the result to our list
                results.append({
                    "Origem": str(file_path),
                    "Metadados": json.dumps(result["metadata"], ensure_ascii=False),
                    **{f"Resumo {t.capitalize()}": result["summaries"][t] for t in summary_types}
                })
                
                if verbose:
                    console.print(f"[green]Completed processing: {file_path}[/green]")
                    
            except Exception as e:
                console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
                if verbose:
                    raise
                
            progress.advance(task)

    # Create DataFrame and save to Excel
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    console.print(f"[green]Report saved to: {output_file}[/green]")

@app.command()
def main(
    input_path: Path = typer.Argument(
        ...,
        help="Path to the directory containing bidding documents",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "report.xlsx",
        "--output",
        "-o",
        help="Output Excel file",
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
    ),
    summary_types: str = typer.Option(
        "executivo,técnico",
        "--summary-types",
        "-s",
        help="Comma-separated list of summary types",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Process bidding documents and generate summaries.
    
    The application will process all documents in the specified directory (including ZIP files),
    extract text from all supported file types, use CrewAI agents to analyze the content,
    generate metadata and summaries, and save the results to an Excel file.
    """
    # Split summary types
    summary_types_list = [t.strip() for t in summary_types.split(',')]
    
    # Process documents
    process_editais(input_path, output, summary_types_list, verbose)

if __name__ == '__main__':
    app() 