from typing import Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SummaryProcessor:
    def process(self, doc_result: Dict[str, Any], target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """
        Processa o resumo do edital.
        
        Args:
            doc_result: Resultado do processamento do documento
            target: Termo ou descrição para análise
            threshold: Valor mínimo para contagem de referências
            force_match: Se True, força o target_match a ser True
            
        Returns:
            Dicionário com os resultados do processamento
        """
        try:
            # Se force_match for True, força o target_match a ser True
            if force_match:
                return {
                    "target_match": True,
                    "threshold_match": True,
                    "summary": "Resumo forçado para teste"
                }
            
            # Processamento normal
            text = doc_result.get("text", "")
            target_count = text.lower().count(target.lower())
            
            return {
                "target_match": target_count > 0,
                "threshold_match": target_count >= threshold,
                "summary": f"O termo '{target}' foi encontrado {target_count} vezes no documento."
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resumo: {str(e)}")
            return {"error": str(e)} 