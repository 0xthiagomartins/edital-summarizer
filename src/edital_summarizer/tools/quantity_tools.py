from typing import List, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import re
from decimal import Decimal

class QuantityExtractionToolInput(BaseModel):
    """Input schema for QuantityExtractionTool."""
    text: str = Field(..., description="The text to extract quantities from.")
    target_keywords: List[str] = Field(default=["notebook", "tablet", "celular", "smartphone", "laptop"], description="List of keywords to look for quantities.")
    context_window: int = Field(default=100, description="Number of characters to look around the number.")

class QuantityExtractionTool(BaseTool):
    name: str = "Quantity Extraction Tool"
    description: str = (
        "Extracts quantities and their context from text. "
        "Returns a list of found quantities with their context and units."
    )
    args_schema: type[BaseModel] = QuantityExtractionToolInput

    def _run(self, text: str, target_keywords: List[str] = None, context_window: int = 100) -> str:
        """
        Extract quantities and their context from text.
        
        Args:
            text: The text to analyze
            target_keywords: List of keywords to look for quantities
            context_window: Number of characters to look around the number
            
        Returns:
            JSON string with found quantities and their context
        """
        if target_keywords is None:
            target_keywords = ["notebook", "tablet", "celular", "smartphone", "laptop"]
            
        results = []
        
        # Normalize text and keywords
        text = text.lower()
        target_keywords = [kw.lower() for kw in target_keywords]
        
        # Find all numbers in the text
        number_pattern = r'\b\d{1,3}(?:\.\d{3})*(?:,\d+)?|\b\d+(?:,\d+)?\b'
        numbers = [(m.group(), m.start(), m.end()) for m in re.finditer(number_pattern, text)]
        
        for number, start, end in numbers:
            # Get context around the number
            context_start = max(0, start - context_window)
            context_end = min(len(text), end + context_window)
            context = text[context_start:context_end]
            
            # Check if any target keyword is in the context
            if any(keyword in context for keyword in target_keywords):
                # Try to extract unit if present
                unit = self._extract_unit(context, number)
                
                # Try to normalize the number
                normalized_number = self._normalize_number(number)
                
                result = {
                    "number": float(normalized_number),
                    "original": number,
                    "unit": unit,
                    "context": context.strip(),
                    "confidence": self._calculate_confidence(context, target_keywords)
                }
                results.append(result)
        
        return str(results)

    def _extract_unit(self, context: str, number: str) -> Optional[str]:
        """Extract unit from context if present."""
        # Common units for devices
        units = {
            'unidade': ['unidade', 'unidades', 'un', 'uns'],
            'peça': ['peça', 'peças', 'pc', 'pcs'],
            'kit': ['kit', 'kits'],
            'lote': ['lote', 'lotes'],
            'conjunto': ['conjunto', 'conjuntos']
        }
        
        # Look for units after the number
        words_after = context.split(number)[1].split()[:3]
        for word in words_after:
            for unit, variations in units.items():
                if word in variations:
                    return unit
        
        return None

    def _normalize_number(self, number: str) -> Decimal:
        """Normalize number to decimal format."""
        # Remove dots used as thousand separators
        number = number.replace('.', '')
        # Replace comma with dot for decimal point
        number = number.replace(',', '.')
        try:
            return Decimal(number)
        except:
            return Decimal('0')

    def _calculate_confidence(self, context: str, target_keywords: List[str]) -> float:
        """Calculate confidence score for the quantity match."""
        confidence = 0.0
        
        # Check for quantity indicators
        quantity_indicators = [
            'quantidade', 'total', 'número', 'qtd', 'qtde',
            'quantidade de', 'total de', 'número de'
        ]
        
        for indicator in quantity_indicators:
            if indicator in context:
                confidence += 0.3
                break
        
        # Check for target keywords
        for keyword in target_keywords:
            if keyword in context:
                confidence += 0.4
                break
        
        # Check for unit presence
        if self._extract_unit(context, '') is not None:
            confidence += 0.3
            
        return min(confidence, 1.0) 