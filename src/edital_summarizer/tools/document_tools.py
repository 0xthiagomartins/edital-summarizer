from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import re


class DocumentSearchToolInput(BaseModel):
    """Input schema for DocumentSearchTool."""

    document: str = Field(..., description="The document text to search in.")
    query: str = Field(..., description="The query to search for in the document.")
    max_chars_context: int = Field(
        500, description="Maximum characters of context to return around each match."
    )


class DocumentSearchTool(BaseTool):
    name: str = "Document Search Tool"
    description: str = (
        "Searches for specific information in a document. Returns matches with surrounding context."
    )
    args_schema: Type[BaseModel] = DocumentSearchToolInput

    def _run(self, document: str, query: str, max_chars_context: int = 500) -> str:
        """Search for the query in the document and return matches with context."""
        if not document or not query:
            return "Error: Empty document or query."

        try:
            # Create regex pattern for the query (case insensitive)
            pattern = re.compile(query, re.IGNORECASE)

            # Find all matches
            matches = list(pattern.finditer(document))

            if not matches:
                return f"No matches found for query: '{query}'"

            results = []
            for i, match in enumerate(matches, 1):
                start = max(0, match.start() - max_chars_context // 2)
                end = min(len(document), match.end() + max_chars_context // 2)

                # Get context around the match
                context = document[start:end]

                # Add ellipsis if context is truncated
                if start > 0:
                    context = "..." + context
                if end < len(document):
                    context = context + "..."

                results.append(f"Match {i}: {context}")

            return "\n\n".join(results)
        except Exception as e:
            return f"Error searching document: {str(e)}"


class TableExtractionToolInput(BaseModel):
    """Input schema for TableExtractionTool."""

    document: str = Field(..., description="The document text to extract tables from.")
    table_keywords: str = Field(
        ...,
        description="Comma-separated keywords to identify tables (e.g., 'tabela,quadro,valor').",
    )


class TableExtractionTool(BaseTool):
    name: str = "Table Extraction Tool"
    description: str = (
        "Extracts tabular data from text documents based on keywords and formatting patterns."
    )
    args_schema: Type[BaseModel] = TableExtractionToolInput

    def _run(self, document: str, table_keywords: str) -> str:
        """Extract tables from the document based on keywords."""
        if not document:
            return "Error: Empty document."

        try:
            keywords = [k.strip().lower() for k in table_keywords.split(",")]

            # Simple heuristic for table detection
            # Look for sections with table keywords and extract potential tables
            lines = document.split("\n")
            tables = []
            current_table = []
            in_table = False

            for line in lines:
                line_lower = line.lower()

                # Check if line contains any table keyword
                has_keyword = any(keyword in line_lower for keyword in keywords)

                # Check if line has table-like structure (multiple spaces or tabs)
                has_table_structure = bool(re.search(r"\s{2,}|\t", line))

                if has_keyword and not in_table:
                    # Found potential table header
                    in_table = True
                    current_table = [line]
                elif in_table:
                    if has_table_structure or line.strip() == "":
                        # Continue collecting table data
                        current_table.append(line)
                    else:
                        # End of table reached
                        if len(current_table) > 2:  # Ensure it's not just a header
                            tables.append("\n".join(current_table))
                        current_table = []
                        in_table = False

            # Add last table if exists
            if in_table and len(current_table) > 2:
                tables.append("\n".join(current_table))

            if not tables:
                return "No tables found matching the specified keywords."

            return "\n\n--- TABLE SEPARATOR ---\n\n".join(tables)
        except Exception as e:
            return f"Error extracting tables: {str(e)}"
