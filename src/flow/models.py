from typing import Dict, Any, List
from pydantic import BaseModel, Field


class TargetAnalysis(BaseModel):
    """Análise de target do edital."""
    is_relevant: bool = Field(description="Se o edital é relevante para o target")
    confidence: float = Field(description="Nível de confiança da análise (0-1)")
    matching_terms: List[str] = Field(description="Termos que indicam match com o target")
    explanation: str = Field(description="Explicação breve da decisão")

class QuantitiesAnalysis(BaseModel):
    """Análise de quantidades do edital."""
    total_quantity: int = Field(description="Quantidade total relevante")
    unit: str = Field(description="Unidade de medida (unidade, peça, etc)")
    explanation: str = Field(description="Explicação de como chegou na quantidade total")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_quantity": 100,
                "unit": "unidades",
                "explanation": "Encontrei 100 unidades mencionadas no edital"
            }]
        }
    }

class SummaryAnalysis(BaseModel):
    """Resumo do edital."""
    executive_summary: str = Field(description="Resumo executivo comercial, conciso e direto, focado em informações comerciais essenciais")
    technical_summary: str = Field(description="Resumo técnico detalhado com especificações, prazos e condições técnicas")
    city: str = Field(description="Cidade/UF do edital (ou 'Não foi possível determinar' se não encontrado)")
    opening_date: str = Field(default="", description="Data de abertura no formato DD/MM/YYYY (apenas data, sem hora)")
    phone: str = Field(default="", description="Telefone de contato (ou string vazia se não encontrado)")
    website: str = Field(default="", description="Website (ou string vazia se não encontrado)")
    email: str = Field(default="", description="Email de contato (ou string vazia se não encontrado)")
    title: str = Field(default="", description="Título do edital")
    object: str = Field(default="", description="Objeto da licitação")
    quantities: str = Field(default="", description="Quantidades relevantes encontradas (em formato texto)")
    specifications: str = Field(default="", description="Especificações técnicas relevantes encontradas (em formato texto)")
    deadlines: str = Field(default="", description="Prazos importantes encontrados (em formato texto)")
    values: str = Field(default="", description="Valores relevantes encontrados (em formato texto)")

    def clean_empty_fields(self) -> Dict[str, Any]:
        """Remove campos vazios do modelo."""
        data = self.model_dump()
        return {k: v for k, v in data.items() if v and v != ""}

class JustificationAnalysis(BaseModel):
    """Justificativa da decisão."""
    decision: str = Field(description="Decisão final (relevante/não relevante)")
    target_match: bool = Field(description="Se o target foi encontrado")
    threshold_match: str = Field(description="Status do threshold (true/false/inconclusive)")
    explanation: str = Field(description="Explicação detalhada da decisão")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "decision": "relevante",
                "target_match": True,
                "threshold_match": "true",
                "explanation": "Exemplo de explicação"
            }]
        }
    }

class EditalState(BaseModel):
    """Estado do processamento do edital."""
    
    # Informações básicas
    bid_number: str = ""
    city: str = ""
    opening_date: str = ""  # Data de abertura no formato DD/MM/YYYY
    edital_path_dir: str = ""  # Adiciona o caminho do edital ao state
    
    # Metadata e conteúdo
    metadata: Dict[str, Any] = {}
    content: str = ""  # Campo interno, não será incluído no output
    structured_info: Dict[str, Any] = {}
    
    # Resultados da análise
    target_match: bool = False
    threshold_match: str = "inconclusive"  # "true", "false", "inconclusive"
    is_relevant: bool = False
    
    # Saídas
    executive_summary: str = ""
    technical_summary: str = ""
    justification: str = ""

    # Controle de erro
    has_error: bool = False
    error_message: str = ""

    class Config:
        json_encoders = {
            # Exclui campos internos do output JSON
            "content": lambda _: None
        }