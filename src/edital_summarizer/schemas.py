from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator

class EditalResponse(BaseModel):
    """Schema para a resposta do processamento de editais."""
    
    target_match: bool = Field(
        ...,
        description="Indica se o documento é relevante para o target"
    )
    
    threshold_match: bool = Field(
        ...,
        description="Indica se o documento atende ao threshold mínimo"
    )
    
    summary: str = Field(
        default="",
        description="Resumo geral do edital ou diretório"
    )
    
    justification: str = Field(
        default="",
        description="Justificativa para não geração do resumo"
    )
    