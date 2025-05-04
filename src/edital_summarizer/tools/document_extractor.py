import os
import zipfile
from pathlib import Path
from typing import List, Dict, Union, Tuple
import PyPDF2
import io
import json
from ..models import BidMetadata


class DocumentExtractor:
    @staticmethod
    def extract_text_from_pdf(pdf_path: Union[str, Path]) -> str:
        """Extract text from a PDF file."""
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return text

    @staticmethod
    def extract_text_from_txt(txt_path: Union[str, Path]) -> str:
        """Extract text from a TXT file."""
        try:
            with open(txt_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"Error reading TXT file {txt_path}: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_md(md_path: Union[str, Path]) -> str:
        """Extract text from a Markdown file."""
        return DocumentExtractor.extract_text_from_txt(md_path)

    @staticmethod
    def process_zip_file(zip_path: Union[str, Path]) -> Dict[str, str]:
        """Process a ZIP file and extract text from all supported files."""
        extracted_texts = {}
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith((".pdf", ".txt", ".md")):
                        with zip_ref.open(file_info) as file:
                            content = file.read()
                            if file_info.filename.endswith(".pdf"):
                                pdf_file = io.BytesIO(content)
                                reader = PyPDF2.PdfReader(pdf_file)
                                text = ""
                                for page in reader.pages:
                                    text += page.extract_text() + "\n"
                            else:
                                text = content.decode("utf-8")
                            extracted_texts[file_info.filename] = text
        except Exception as e:
            print(f"Error processing ZIP file {zip_path}: {str(e)}")
        return extracted_texts

    @staticmethod
    def process_directory(directory_path: Path) -> Dict[str, Tuple[str, BidMetadata]]:
        """
        Process all documents in a directory.
        Returns a dictionary with file paths as keys and tuples of (text content, metadata) as values.
        """
        results = {}

        # First, try to load metadata.json
        metadata_file = directory_path / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"metadata.json not found in {directory_path}")

        try:
            with open(metadata_file) as f:
                metadata = BidMetadata.model_validate(json.load(f))
        except Exception as e:
            raise ValueError(f"Error parsing metadata.json: {str(e)}")

        # Then process all other files
        for file_path in directory_path.glob("*"):
            if file_path.name == "metadata.json":
                continue

            if file_path.suffix.lower() == ".pdf":
                text = DocumentExtractor._extract_from_pdf(file_path)
            elif file_path.suffix.lower() in [".txt", ".md"]:
                text = DocumentExtractor._extract_from_text(file_path)
            else:
                continue

            results[str(file_path.name)] = (text, metadata)

        return results

    @staticmethod
    def _extract_from_pdf(file_path: Path) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    @staticmethod
    def _extract_from_text(file_path: Path) -> str:
        """Extract text from text file."""
        return file_path.read_text()
