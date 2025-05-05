"""
Este arquivo pode ser significativamente simplificado para conter apenas ferramentas específicas
que não são cobertas pelo DocumentProcessor.
"""

from langchain.tools import BaseTool
from typing import Optional, List, Dict, Any


class DocumentChunkTool(BaseTool):
    """Ferramenta para dividir documentos em chunks."""

    name = "document_chunker"
    description = "Divide documentos longos em pedaços menores para processamento."

    def __init__(self, chunk_size: int = 4000, chunk_overlap: int = 200):
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _run(self, text: str) -> List[str]:
        """Divide o texto em chunks."""
        # Implementação simplificada - usa RecursiveCharacterTextSplitter diretamente
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

        return splitter.split_text(text)


# Remover MetadataExtractionTool e ResultsMergeTool se não forem utilizados
