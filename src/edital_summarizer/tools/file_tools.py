import os
import pypdf
import zipfile
import tempfile
import shutil
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class SimpleFileReadToolInput(BaseModel):
    """Input schema for SimpleFileReadTool."""

    file_path: str = Field(..., description="Path to the file to be read.")
    max_chars: int = Field(20000, description="Maximum number of characters to return.")


class SimpleFileReadTool(BaseTool):
    name: str = "Simple File Reader"
    description: str = (
        "Reads the content of a file and returns it as text. "
        "Supports TXT, PDF, DOCX, MD files and ZIP archives."
    )
    args_schema: Type[BaseModel] = SimpleFileReadToolInput

    def _run(self, file_path: str, max_chars: int = 20000) -> str:
        """Read file content and return it as text."""
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        try:
            if file_extension == ".pdf":
                text = self._extract_text_from_pdf(file_path)
            elif file_extension in [".docx", ".doc"]:
                text = self._extract_text_from_docx(file_path)
            elif file_extension in [".md", ".markdown"]:
                text = self._extract_text_from_markdown(file_path)
            elif file_extension == ".zip":
                text = self._extract_text_from_zip(file_path, max_chars)
            else:  # Assume it's a text file
                with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                    text = file.read()

            # Limit text size
            if len(text) > max_chars:
                text = (
                    text[:max_chars] + f"\n\n[Texto truncado em {max_chars} caracteres]"
                )

            return text
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            return text
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"

    def _extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document

            document = Document(docx_path)
            text = "\n\n".join([paragraph.text for paragraph in document.paragraphs])
            return text
        except ImportError:
            return "Error: python-docx library not installed. Please install it with pip install python-docx."
        except Exception as e:
            return f"Error extracting text from DOCX: {str(e)}"

    def _extract_text_from_markdown(self, md_path: str) -> str:
        """Simply read markdown file as text"""
        try:
            with open(md_path, "r", encoding="utf-8", errors="replace") as file:
                return file.read()
        except Exception as e:
            return f"Error reading Markdown file: {str(e)}"

    def _extract_text_from_zip(self, zip_path: str, max_chars: int) -> str:
        """Extract text from all supported files in a ZIP archive."""
        try:
            # Create a temporary directory to extract files
            temp_dir = tempfile.mkdtemp()

            try:
                # Extract all files from the ZIP archive
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Process all files in the temporary directory
                text_parts = []

                # Define supported file extensions
                supported_extensions = [
                    ".txt",
                    ".pdf",
                    ".docx",
                    ".doc",
                    ".md",
                    ".markdown",
                ]

                # Walk through all files in the extracted directory
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        _, ext = os.path.splitext(file_path)

                        if ext.lower() in supported_extensions:
                            # Skip reading the file if we've already exceeded max_chars
                            current_total = sum(len(part) for part in text_parts)
                            if current_total >= max_chars:
                                break

                            # Determine how many characters we can still add
                            remaining_chars = max(0, max_chars - current_total)

                            # Process the file but with a reduced character limit
                            if ext.lower() == ".pdf":
                                file_text = self._extract_text_from_pdf(file_path)
                            elif ext.lower() in [".docx", ".doc"]:
                                file_text = self._extract_text_from_docx(file_path)
                            elif ext.lower() in [".md", ".markdown"]:
                                file_text = self._extract_text_from_markdown(file_path)
                            else:  # text file
                                with open(
                                    file_path, "r", encoding="utf-8", errors="replace"
                                ) as f:
                                    file_text = f.read()

                            # Truncate if necessary and add a header indicating the file
                            if len(file_text) > remaining_chars:
                                file_text = file_text[:remaining_chars]

                            text_parts.append(
                                f"\n\n=== ARQUIVO: {file} ===\n\n{file_text}"
                            )

                # Combine all text parts
                combined_text = "".join(text_parts)

                # Add a message if we truncated the content
                if sum(len(part) for part in text_parts) >= max_chars:
                    combined_text += (
                        f"\n\n[Conteúdo truncado em {max_chars} caracteres]"
                    )

                return combined_text

            finally:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir)

        except Exception as e:
            return f"Error processing ZIP archive: {str(e)}"
