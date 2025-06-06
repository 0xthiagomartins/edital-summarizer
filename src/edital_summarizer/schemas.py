from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator

class EditalResponse(BaseModel):
    """Schema para a resposta do processamento de editais."""
    
    target_match: bool = Field(
        ...,
        description="Indica se o documento é relevante para o target"
    )
    
    threshold_match: Literal["true", "false", "inconclusive"] = Field(
        ...,
        description="Indica se o documento atende ao threshold mínimo"
    )
    
    is_relevant: bool = Field(
        ...,
        description="Indica se o edital é relevante considerando todas as regras"
    )
    
    summary: str = Field(
        default="",
        description="Resumo detalhado do conteúdo do edital"
    )
    
    justification: str = Field(
        default="",
        description="Justificativa clara e coerente da decisão"
    )
    
    @validator('is_relevant')
    def validate_is_relevant(cls, v, values):
        """Valida a lógica de relevância."""
        target_match = values.get('target_match')
        threshold_match = values.get('threshold_match')
        
        if target_match is None or threshold_match is None:
            return v
            
        # Se target_match for false, is_relevant deve ser false
        if not target_match:
            if v:
                raise ValueError("is_relevant deve ser false quando target_match é false")
            return v
            
        # Se target_match for true, verifica threshold_match
        if threshold_match in ["inconclusive", "false"]:
            if v:
                raise ValueError("is_relevant deve ser false quando threshold_match é inconclusive ou false")
            return v
            
        # Se chegou aqui, target_match é true e threshold_match é true
        if not v:
            raise ValueError("is_relevant deve ser true quando target_match e threshold_match são true")
        return v
    