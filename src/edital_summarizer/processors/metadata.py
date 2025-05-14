from typing import Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MetadataProcessor:
    """Processador de metadados para editais."""

    def process(self, doc_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa os metadados do edital.
        
        Args:
            doc_result: Resultado do processamento do documento
            
        Returns:
            Dicionário com os metadados extraídos
        """
        try:
            # Extrai o texto do documento
            text = doc_result.get("text", "")
            
            # Inicializa o resultado
            metadata = {
                "identifier": self._extract_identifier(text),
                "organization": self._extract_organization(text),
                "subject": self._extract_subject(text)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao processar metadados: {str(e)}")
            return {"error": str(e)}

    def _extract_identifier(self, text: str) -> Dict[str, str]:
        """Extrai informações de identificação do edital."""
        return {
            "public_notice": self._find_pattern(text, r"EDITAL DE LICITAÇÃO\s*[Nn]º?\s*(\d+)"),
            "process_id": self._find_pattern(text, r"[Pp]rocesso\s*[Nn]º?\s*(\d+)"),
            "bid_number": self._find_pattern(text, r"[Ll]icitação\s*[Nn]º?\s*(\d+)")
        }

    def _extract_organization(self, text: str) -> Dict[str, str]:
        """Extrai informações da organização."""
        return {
            "organization": self._find_pattern(text, r"[Oo]rganização:\s*(.+?)(?:\n|$)"),
            "phone": self._find_pattern(text, r"[Tt]elefone:\s*(.+?)(?:\n|$)"),
            "website": self._find_pattern(text, r"[Ww]ebsite:\s*(.+?)(?:\n|$)"),
            "location": self._find_pattern(text, r"[Ll]ocal:\s*(.+?)(?:\n|$)")
        }

    def _extract_subject(self, text: str) -> Dict[str, str]:
        """Extrai informações do objeto do edital."""
        return {
            "title": self._find_pattern(text, r"[Tt]ítulo:\s*(.+?)(?:\n|$)"),
            "object": self._find_pattern(text, r"[Oo]bjeto:\s*(.+?)(?:\n|$)"),
            "dates": self._find_pattern(text, r"[Dd]ata:\s*(.+?)(?:\n|$)")
        }

    def _find_pattern(self, text: str, pattern: str) -> str:
        """Encontra um padrão no texto usando regex."""
        import re
        match = re.search(pattern, text)
        return match.group(1).strip() if match else "" 