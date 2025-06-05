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
    
    threshold_status: Literal["true", "false", "inconclusive"] = Field(
        ...,
        description="Status do threshold: 'true', 'false' ou 'inconclusive'"
    )
    
    target_summary: str = Field(
        default="",
        description="Resumo específico sobre o target no documento"
    )
    
    document_summary: str = Field(
        default="",
        description="Resumo geral do documento"
    )
    
    justification: str = Field(
        default="",
        description="Justificativa para não geração do resumo"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados do documento"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Mensagem de erro, se houver"
    )
    
    @validator('threshold_status')
    def validate_threshold_status(cls, v):
        """Valida se o status do threshold é um dos valores permitidos."""
        allowed_values = ["true", "false", "inconclusive"]
        if v not in allowed_values:
            raise ValueError(f"threshold_status deve ser um dos valores: {', '.join(allowed_values)}")
        return v 