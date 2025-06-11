import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractedInfo(BaseModel):
    """Informações extraídas do edital."""
    quantities: List[int] = []
    specifications: List[str] = []
    deadlines: List[str] = []
    values: List[str] = []

class InformationExtractor:
    """Classe para extrair informações estruturadas do texto do edital."""

    def __init__(self):
        # Padrões para quantidades
        self.quantity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:unidades?|und\.?|pç\.?|peças?)',
            r'quantidade:\s*(\d+(?:\.\d+)?)',
            r'qtd\.?:\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:tablets?|notebooks?|computadores?)',
        ]

        # Padrões para especificações técnicas
        self.spec_patterns = [
            r'(?:especificações?|especificação técnica):\s*([^.]*\.)',
            r'(?:características?|característica):\s*([^.]*\.)',
            r'(?:requisitos?|requisito):\s*([^.]*\.)',
            r'(?:configurações?|configuração):\s*([^.]*\.)',
        ]

        # Padrões para prazos
        self.deadline_patterns = [
            r'prazo de (?:entrega|execução):\s*(\d+)\s*(?:dias?|meses?)',
            r'entrega em:\s*(\d+)\s*(?:dias?|meses?)',
            r'execução em:\s*(\d+)\s*(?:dias?|meses?)',
            r'vigência:\s*(\d+)\s*(?:dias?|meses?)',
        ]

        # Padrões para valores
        self.value_patterns = [
            r'R\$\s*(\d+(?:\.\d+)?(?:,\d+)?)',
            r'valor:\s*R\$\s*(\d+(?:\.\d+)?(?:,\d+)?)',
            r'preço:\s*R\$\s*(\d+(?:\.\d+)?(?:,\d+)?)',
            r'custo:\s*R\$\s*(\d+(?:\.\d+)?(?:,\d+)?)',
        ]

    def extract_quantities(self, text: str) -> List[Dict[str, Any]]:
        """Extrai quantidades do texto."""
        logger.info("Extraindo quantidades...")
        quantities = []
        
        for pattern in self.quantity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                quantity = match.group(1)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                logger.debug(f"Quantidade encontrada: {quantity} no contexto: {context}")
                quantities.append({
                    "value": float(quantity.replace('.', '').replace(',', '.')),
                    "context": context.strip()
                })
        
        logger.info(f"Quantidades encontradas: {len(quantities)}")
        return quantities

    def extract_specifications(self, text: str) -> List[str]:
        """Extrai especificações técnicas do texto."""
        logger.info("Extraindo especificações...")
        specs = []
        
        for pattern in self.spec_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                spec = match.group(1)
                logger.debug(f"Especificação encontrada: {spec}")
                specs.append(spec.strip())
        
        logger.info(f"Especificações encontradas: {len(specs)}")
        return specs

    def extract_deadlines(self, text: str) -> List[Dict[str, Any]]:
        """Extrai prazos do texto."""
        logger.info("Extraindo prazos...")
        deadlines = []
        
        for pattern in self.deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                logger.debug(f"Prazo encontrado: {value} no contexto: {context}")
                deadlines.append({
                    "value": int(value),
                    "context": context.strip()
                })
        
        logger.info(f"Prazos encontrados: {len(deadlines)}")
        return deadlines

    def extract_values(self, text: str) -> List[Dict[str, Any]]:
        """Extrai valores monetários do texto."""
        logger.info("Extraindo valores...")
        values = []
        
        for pattern in self.value_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                logger.debug(f"Valor encontrado: {value} no contexto: {context}")
                values.append({
                    "value": float(value.replace('.', '').replace(',', '.')),
                    "context": context.strip()
                })
        
        logger.info(f"Valores encontrados: {len(values)}")
        return values

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extrai todas as informações do texto."""
        logger.info("\n=== Extraindo informações do texto ===")
        
        quantities = self.extract_quantities(text)
        specs = self.extract_specifications(text)
        deadlines = self.extract_deadlines(text)
        values = self.extract_values(text)
        
        return {
            "quantities": quantities,
            "specifications": specs,
            "deadlines": deadlines,
            "values": values
        }

def extract_info(content: str) -> ExtractedInfo:
    """Extrai informações estruturadas do conteúdo do edital."""
    logger.info("\n=== Extraindo informações do texto ===")

    # Extrai quantidades
    quantities = []
    quantity_patterns = [
        r'(\d+)\s*(?:unidades?|pcs|peças?|itens?)',
        r'quantidade:\s*(\d+)',
        r'qtd:\s*(\d+)',
        r'(\d+)\s*(?:tablets?|notebooks?|computadores?)'
    ]
    for pattern in quantity_patterns:
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            try:
                quantities.append(int(match.group(1)))
            except ValueError:
                continue
    logger.info(f"Quantidades encontradas: {len(quantities)}")

    # Extrai especificações
    specifications = []
    spec_patterns = [
        r'especificações?:\s*([^\n]+)',
        r'características?:\s*([^\n]+)',
        r'requisitos?:\s*([^\n]+)'
    ]
    for pattern in spec_patterns:
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            specs = [s.strip() for s in match.group(1).split(',')]
            specifications.extend(specs)
    logger.info(f"Especificações encontradas: {len(specifications)}")

    # Extrai prazos
    deadlines = []
    deadline_patterns = [
        r'prazo:\s*([^\n]+)',
        r'entrega:\s*([^\n]+)',
        r'data:\s*([^\n]+)'
    ]
    for pattern in deadline_patterns:
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            deadlines.append(match.group(1).strip())
    logger.info(f"Prazos encontrados: {len(deadlines)}")

    # Extrai valores
    values = []
    value_patterns = [
        r'valor:\s*([^\n]+)',
        r'preço:\s*([^\n]+)',
        r'custo:\s*([^\n]+)'
    ]
    for pattern in value_patterns:
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            values.append(match.group(1).strip())
    logger.info(f"Valores encontrados: {len(values)}")

    return ExtractedInfo(
        quantities=quantities,
        specifications=specifications,
        deadlines=deadlines,
        values=values
    ) 