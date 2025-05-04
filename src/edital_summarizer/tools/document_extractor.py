import os
import zipfile
from pathlib import Path
from typing import List, Dict, Union
import PyPDF2
import io


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
    def process_directory(directory_path: Union[str, Path]) -> Dict[str, str]:
        """Process a directory and extract text from all supported files."""
        extracted_texts = {}
        directory_path = Path(directory_path)

        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() == ".pdf":
                    extracted_texts[str(file_path.relative_to(directory_path))] = (
                        DocumentExtractor.extract_text_from_pdf(file_path)
                    )
                elif file_path.suffix.lower() == ".txt":
                    extracted_texts[str(file_path.relative_to(directory_path))] = (
                        DocumentExtractor.extract_text_from_txt(file_path)
                    )
                elif file_path.suffix.lower() == ".md":
                    extracted_texts[str(file_path.relative_to(directory_path))] = (
                        DocumentExtractor.extract_text_from_md(file_path)
                    )
                elif file_path.suffix.lower() == ".zip":
                    zip_texts = DocumentExtractor.process_zip_file(file_path)
                    for filename, text in zip_texts.items():
                        extracted_texts[
                            f"{file_path.relative_to(directory_path)}/{filename}"
                        ] = text

        return extracted_texts
