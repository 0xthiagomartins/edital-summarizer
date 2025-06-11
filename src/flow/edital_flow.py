from typing import Dict, Any, Optional, List
from crewai import Flow, LLM
from crewai.flow.flow import start, listen
from utils import read_metadata, InformationExtractor
from tools.file_tools import FileReadTool
from pydantic import BaseModel, Field
import logging
import json

logger = logging.getLogger(__name__)

class TargetAnalysis(BaseModel):
    """Análise de target do edital."""
    is_relevant: bool = Field(description="Se o edital é relevante para o target")
    confidence: float = Field(description="Nível de confiança da análise (0-1)")
    matching_terms: List[str] = Field(description="Termos que indicam match com o target")
    explanation: str = Field(description="Explicação breve da decisão")

class QuantitiesAnalysis(BaseModel):
    """Análise de quantidades do edital."""
    quantities: List[Dict[str, Any]] = Field(
        description="Lista de quantidades encontradas",
        default_factory=list
    )
    total_quantity: int = Field(description="Quantidade total relevante")
    unit: str = Field(description="Unidade de medida (unidade, peça, etc)")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "quantities": [{"value": 100, "context": "Exemplo de contexto"}],
                "total_quantity": 100,
                "unit": "unidades"
            }]
        }
    }

class SummaryAnalysis(BaseModel):
    """Resumo do edital."""
    summary: str = Field(description="Resumo textual do edital, incluindo informações relevantes encontradas")
    title: Optional[str] = Field(default=None, description="Título do edital (opcional)")
    object: Optional[str] = Field(default=None, description="Objeto da licitação (opcional)")
    quantities: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Quantidades relevantes encontradas (opcional)"
    )
    specifications: Optional[List[str]] = Field(
        default_factory=list,
        description="Especificações técnicas relevantes encontradas (opcional)"
    )
    deadlines: Optional[List[str]] = Field(
        default_factory=list,
        description="Prazos importantes encontrados (opcional)"
    )
    values: Optional[List[str]] = Field(
        default_factory=list,
        description="Valores relevantes encontrados (opcional)"
    )


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
    edital_path_dir: str = ""  # Adiciona o caminho do edital ao state
    
    # Metadata e conteúdo
    metadata: Dict[str, Any] = {}
    content: str = ""
    structured_info: Dict[str, Any] = {}
    
    # Resultados da análise
    target_match: bool = False
    threshold_match: str = "inconclusive"  # "true", "false", "inconclusive"
    is_relevant: bool = False
    
    # Saídas
    summary: str = ""
    justification: str = ""

class EditalAnalysisFlow(Flow[EditalState]):
    """Flow para análise de editais."""

    def __init__(self, target: str, threshold: int = 0, force_match: bool = False):
        super().__init__()
        self.target = target
        self.threshold = threshold
        self.force_match = force_match
        self.extractor = InformationExtractor()
        self.file_tool = FileReadTool()
        logger.info(f"Target: {target}")
        logger.info(f"Threshold: {threshold}")
        logger.info(f"Forçar Match: {force_match}")

    @start()
    def extract_metadata(self) -> Dict[str, Any]:
        """Extrai metadata do edital."""
        logger.info("Iniciando extração de metadata...")
        try:
            metadata = read_metadata(self.state.edital_path_dir)
            self.state.metadata = metadata
            logger.info("Metadata extraída com sucesso")
            return metadata
        except Exception as e:
            logger.error(f"Erro ao extrair metadata: {str(e)}")
            raise

    @listen(extract_metadata)
    def extract_content(self) -> str:
        """Extrai conteúdo do edital."""
        logger.info("Iniciando extração de conteúdo...")
        try:
            # Usa o FileReadTool para ler o arquivo
            content = self.file_tool._run(f"{self.state.edital_path_dir}/edital_1.pdf")
            self.state.content = content
            logger.info("Conteúdo extraído com sucesso")
            return content
        except Exception as e:
            logger.error(f"Erro ao extrair conteúdo: {str(e)}")
            raise

    @listen(extract_content)
    def extract_structured_info(self) -> Dict[str, Any]:
        """Extrai informações estruturadas do conteúdo."""
        logger.info("Iniciando extração de informações estruturadas...")
        try:
            info = self.extractor.extract_all(self.state.content)
            self.state.structured_info = info
            logger.info("Informações estruturadas extraídas com sucesso")
            return info
        except Exception as e:
            logger.error(f"Erro ao extrair informações estruturadas: {str(e)}")
            raise

    @listen(extract_structured_info)
    def analyze_target(self) -> EditalState:
        """Analisa se o edital é relevante para o target."""
        logger.info("Iniciando análise de target...")
        try:
            # Inicializa o LLM
            logger.info("Inicializando LLM com response_format=TargetAnalysis")
            llm = LLM(
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                response_format=TargetAnalysis
            )

            # Faz a chamada ao LLM
            logger.info("Fazendo chamada ao LLM...")
            response = llm.call(
                messages=[
                    {"role": "system", "content": """Você é um especialista em análise de editais de licitação.
                    Sua tarefa é analisar se o edital é relevante para o target especificado.
                    
                    Considere:
                    1. Sinônimos e termos relacionados
                    2. Especificações técnicas que indiquem o tipo de equipamento
                    3. Contexto do uso do equipamento/serviço"""},
                    {"role": "user", "content": f"""
                    Target: {self.target}
                    
                    Conteúdo do Edital:
                    {self.state.content}
                    """}
                ]
            )
            
            logger.info(f"Conteúdo do TargetAnalysis: {response}")
            
            # Converte a string JSON em objeto TargetAnalysis
            response_dict = json.loads(response)
            response_obj = TargetAnalysis(**response_dict)
            
            # Define o target_match baseado na resposta
            self.state.target_match = response_obj.is_relevant
            
            # Se force_match, força o target_match
            if self.force_match:
                self.state.target_match = True
            
            logger.info(f"Análise de target concluída: {response_obj.explanation}")
            return self.state
        except Exception as e:
            logger.error(f"Erro ao analisar target: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            raise

    @listen(analyze_target)
    def check_threshold(self) -> EditalState:
        """Verifica se o edital atende ao threshold."""
        logger.info("Iniciando verificação de threshold...")
        try:
            if self.threshold == 0:
                self.state.threshold_match = "true"
                logger.info("Threshold = 0, ignorando verificação")
                return self.state

            if not self.state.target_match:
                self.state.threshold_match = "false"
                logger.info("Target não match, threshold = false")
                return self.state

            # Inicializa o LLM
            llm = LLM(
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                response_format=QuantitiesAnalysis
            )

            # Faz a chamada ao LLM
            response = llm.call(
                messages=[
                    {"role": "system", "content": """Você é um especialista em análise de quantidades em editais.
                    Sua tarefa é identificar e somar todas as quantidades relevantes para o target.
                    
                    Considere:
                    1. Diferentes unidades de medida
                    2. Quantidades em tabelas e listas
                    3. Quantidades em texto corrido"""},
                    {"role": "user", "content": f"""
                    Target: {self.target}
                    Threshold: {self.threshold}
                    
                    Conteúdo do Edital:
                    {self.state.content}
                    """}
                ]
            )
            
            logger.info(f"Conteúdo do QuantitiesAnalysis: {response}")
            
            # Converte a string JSON em objeto QuantitiesAnalysis
            response_dict = json.loads(response)
            response_obj = QuantitiesAnalysis(**response_dict)
            
            # Verifica se a quantidade total atende ao threshold
            if response_obj.total_quantity >= self.threshold:
                self.state.threshold_match = "true"
                logger.info(f"Quantidade {response_obj.total_quantity} >= threshold {self.threshold}")
            else:
                self.state.threshold_match = "false"
                logger.info(f"Quantidade {response_obj.total_quantity} < threshold {self.threshold}")
            
            return self.state
        except Exception as e:
            logger.error(f"Erro ao verificar threshold: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            raise

    @listen(check_threshold)
    def generate_summary(self) -> EditalState:
        """Gera resumo do edital."""
        logger.info("Iniciando geração de resumo...")
        try:
            # Inicializa o LLM
            llm = LLM(
                model="gpt-4o",
                temperature=0.7,
                max_tokens=500,  # Reduzido para garantir resumo conciso
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )

            # Faz a chamada ao LLM
            response = llm.call(
                messages=[
                    {"role": "system", "content": """Você é um especialista em resumir editais de licitação.
                    Sua tarefa é gerar um resumo conciso e direto do edital.
                    
                    Instruções:
                    1. Resuma em 2-3 parágrafos curtos
                    2. Foque em informações relevantes para o target
                    3. Inclua apenas se encontrar:
                       - Objeto da licitação
                       - Quantidades relevantes
                       - Especificações técnicas importantes
                       - Prazos críticos
                       - Valores significativos
                    4. Se não encontrar alguma informação, não mencione
                    5. Seja direto e objetivo
                    6. Máximo 300 palavras"""},
                    {"role": "user", "content": f"""
                    Target: {self.target}
                    
                    Conteúdo do Edital:
                    {self.state.content}
                    """}
                ]
            )
            
            logger.info(f"Resumo gerado: {response}")
            self.state.summary = response
            logger.info("Resumo salvo com sucesso")
            return self.state
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            raise

    @listen(generate_summary)
    def generate_justification(self) -> EditalState:
        """Gera justificativa para a decisão."""
        logger.info("Iniciando geração de justificativa...")
        try:
            # Inicializa o LLM
            llm = LLM(
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                response_format=JustificationAnalysis
            )

            # Faz a chamada ao LLM
            response = llm.call(
                messages=[
                    {"role": "system", "content": """Você é um especialista em justificar decisões sobre editais.
                    Sua tarefa é gerar uma justificativa clara e objetiva.
                    
                    Considere:
                    1. Match com o target
                    2. Verificação de threshold
                    3. Contexto do edital"""},
                    {"role": "user", "content": f"""
                    Target: {self.target}
                    Target Match: {self.state.target_match}
                    Threshold Match: {self.state.threshold_match}
                    Threshold: {self.threshold}
                    
                    Resumo do Edital:
                    {self.state.summary}
                    """}
                ]
            )
            
            logger.info(f"Conteúdo do JustificationAnalysis: {response}")
            
            # Converte a string JSON em objeto JustificationAnalysis
            response_dict = json.loads(response)
            response_obj = JustificationAnalysis(**response_dict)
            
            self.state.justification = response_obj.model_dump_json(indent=2)
            
            # Define se o edital é relevante
            self.state.is_relevant = (
                self.state.target_match and 
                (self.threshold == 0 or self.state.threshold_match == "true")
            )
            
            logger.info("Justificativa gerada com sucesso")
            return self.state
        except Exception as e:
            logger.error(f"Erro ao gerar justificativa: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            raise

def kickoff(edital_path_dir: str, target: str, threshold: int = 0, force_match: bool = False) -> EditalState:
    """Executa o fluxo de análise de edital."""
    flow = EditalAnalysisFlow(target=target, threshold=threshold, force_match=force_match)
    # Executa o flow
    flow.kickoff({"edital_path_dir": edital_path_dir})
    logger.info("=== Flow Concluído ===")
    return flow.state

def plot():
    """Gera uma visualização do fluxo."""
    flow = EditalAnalysisFlow(target="exemplo", threshold=0)
    flow.plot("edital_analysis_flow")
    logger.info("Visualização do fluxo salva em edital_analysis_flow.html") 