#!/usr/bin/env python
import sys
import warnings
from pathlib import Path
import pandas as pd
from typing import List
import json
import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    BarColumn,
)
from .tools.document_extractor import DocumentExtractor
from .crew import DocumentSummarizerCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

app = typer.Typer(help="Process bidding documents and generate summaries.")
console = Console()


def process_editais(
    input_path: Path,
    output_file: Path,
    summary_types: List[str],
    language: str = "pt-br",
    verbose: bool = False,
) -> None:
    """Process bidding documents and generate summaries."""
    if not input_path.exists():
        console.print(f"[red]Error: Input path does not exist: {input_path}[/red]")
        raise typer.Exit(1)

    # Initialize the crew with language and verbose
    crew = DocumentSummarizerCrew(language=language, verbose=verbose)

    # Process all documents
    results = []
    extracted_texts = DocumentExtractor.process_directory(input_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        BarColumn(),
        console=console,
        transient=False if verbose else True,
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(extracted_texts))

        for file_path, text in extracted_texts.items():
            if verbose:
                console.print(f"\n[bold blue]Processing: {file_path}[/bold blue]")
                console.print(f"Text length: {len(text)} characters")

            try:
                # Process document and generate summaries
                result = crew.process_document(text, summary_types)

                # Add the result to our list
                results.append(
                    {
                        "Origem": str(file_path),
                        "Metadados": json.dumps(result["metadata"], ensure_ascii=False),
                        **{
                            f"Resumo {t.capitalize()}": result["summaries"][t]
                            for t in summary_types
                        },
                    }
                )

                if verbose:
                    console.print(f"[green]✓ Completed processing: {file_path}[/green]")

            except Exception as e:
                console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
                if verbose:
                    console.print_exception()

            progress.advance(task)

    # Create DataFrame and save to Excel
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False, engine="openpyxl")

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
    language: str = typer.Option(
        "pt-br",
        "--language",
        "-l",
        help="Language to use (pt-br or en). Default: pt-br",
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
    """
    # Validate language
    if language not in ["pt-br", "en"]:
        console.print(
            f"[red]Error: Invalid language: {language}. Use 'pt-br' or 'en'.[/red]"
        )
        raise typer.Exit(1)

    # Split summary types
    summary_types_list = [t.strip() for t in summary_types.split(",")]

    # Process documents
    process_editais(input_path, output, summary_types_list, language, verbose)


if __name__ == "__main__":
    app()
