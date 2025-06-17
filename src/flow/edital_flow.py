from typing import Dict, Any, Optional, List, Callable
from crewai import Flow, LLM
from crewai.flow.flow import start, listen, or_
from utils import read_metadata
from tools.file_tools import FileReadTool, DocumentTooLargeError
from pydantic import BaseModel, Field
import json
import functools
from utils import get_logger

logger = get_logger(__name__)


def handle_flow_error(func: Callable) -> Callable:
    """Decorator para tratar erros no flow de forma consistente."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        print(f"\n{'='*50}\nExecutando {func.__name__}")
        print(f"Estado atual - has_error: {self.state.has_error}, error_message: {self.state.error_message}")
        
        # Se já houve erro, apenas retorna
        if self.state.has_error:
            print(f"IGNORADO: {func.__name__} - Erro anterior: {self.state.error_message}")
            return

        try:
            result = func(self, *args, **kwargs)
            print(f"✅ {func.__name__} executado com sucesso")
            return result
        except DocumentTooLargeError as e:
            print(f"❌ {func.__name__} - DocumentTooLargeError: {str(e)}")
            self.state.has_error = True
            self.state.error_message = str(e)
            self.state.justification = e.error_message
            self.state.target_match = False
            self.state.threshold_match = "inconclusive"
            self.state.is_relevant = False
            return self.state
        except Exception as e:
            print(f"❌ {func.__name__} - Exception: {str(e)}")
            self.state.has_error = True
            self.state.error_message = f"Erro em {func.__name__}: {str(e)}"
            self.state.justification = self.state.error_message
            return self.state
    return wrapper

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
    summary: str = Field(description="Resumo textual do edital, incluindo informações relevantes encontradas")
    city: str = Field(description="Cidade/UF do edital (ou 'Não foi possível determinar' se não encontrado)")
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
    summary: str = ""
    justification: str = ""

    # Controle de erro
    has_error: bool = False
    error_message: str = ""

    class Config:
        json_encoders = {
            # Exclui campos internos do output JSON
            "content": lambda _: None
        }

class EditalAnalysisFlow(Flow[EditalState]):
    """Flow para análise de editais."""

    def __init__(self, target: str, threshold: int = 0, force_match: bool = False):
        super().__init__()
        self.target = target
        self.threshold = threshold
        self.force_match = force_match
        self.file_tool = FileReadTool()
        logger.info(f"Target: {target}")
        logger.info(f"Threshold: {threshold}")
        logger.info(f"Forçar Match: {force_match}")

    @start()
    @handle_flow_error
    def extract_metadata(self):
        """Extrai metadata do edital."""
        logger.info("Iniciando extração de metadata...")
        metadata = read_metadata(self.state.edital_path_dir)
        self.state.metadata = metadata
        
        # Extrai bid_number do metadata
        if "bid_number" in metadata:
            self.state.bid_number = metadata["bid_number"]
            logger.info(f"Bid number extraído: {self.state.bid_number}")
        
        logger.info("Metadata extraída com sucesso")

    @listen(extract_metadata)
    @handle_flow_error
    def extract_content(self):
        """Extrai conteúdo do edital."""
        print("Iniciando extração de conteúdo...")
        try:
            # Usa o FileReadTool para ler o arquivo
            content = self.file_tool._run(f"{self.state.edital_path_dir}/edital_1.pdf")
            self.state.content = content
            print("Conteúdo extraído com sucesso")
        except DocumentTooLargeError as e:
            print(f"❌ Erro: Documento muito grande - {str(e)}")
            self.state.has_error = True
            self.state.error_message = str(e)
            self.state.justification = e.error_message
            self.state.target_match = False
            self.state.threshold_match = "inconclusive"
            self.state.is_relevant = False
            return self.state
        except FileNotFoundError as e:
            print(f"❌ Erro: Arquivo não encontrado - {str(e)}")
            self.state.has_error = True
            self.state.error_message = str(e)
            self.state.justification = f"Erro ao processar edital: {str(e)}"
            return self.state
        except Exception as e:
            print(f"❌ Erro ao extrair conteúdo: {str(e)}")
            self.state.has_error = True
            self.state.error_message = f"Erro ao extrair conteúdo: {str(e)}"
            self.state.justification = self.state.error_message
            return self.state

    @listen(extract_content)
    @handle_flow_error
    def generate_summary(self):
        """Gera resumo do edital."""
        logger.info("Iniciando geração de resumo...")
        # Inicializa o LLM
        llm = LLM(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            response_format=SummaryAnalysis
        )

        # Faz a chamada ao LLM
        response = llm.call(
            messages=[
                {"role": "system", "content": """Você é um especialista em resumir editais de licitação.
                Sua tarefa é gerar um resumo detalhado e estruturado do edital.
                
                Instruções:
                1. Analise cuidadosamente todo o conteúdo
                2. Extraia TODAS as informações relevantes:
                   - Objeto da licitação
                   - Quantidades e especificações
                   - Prazos e valores
                   - Requisitos técnicos
                   - Condições comerciais
                3. Seja detalhado mas conciso
                4. Organize as informações em seções claras
                5. Máximo 1500 palavras
                
                IMPORTANTE: Identifique também:
                1. A cidade/UF do edital (procure no metadata ou no texto)
                2. Informações de contato:
                   - phone: telefone de contato
                   - website: site oficial
                   - email: email de contato
                3. Outras informações (em formato texto):
                   - title: título do edital
                   - object: objeto da licitação
                   - quantities: quantidades relevantes (ex: "100 unidades de tablets")
                   - specifications: especificações técnicas (ex: "Tablets com tela de 10 polegadas")
                   - deadlines: prazos importantes (ex: "Entrega em 30 dias")
                   - values: valores relevantes (ex: "Valor total de R$ 500.000,00")
                Se não encontrar alguma informação, use string vazia"""},
                {"role": "user", "content": f"""
                Target: {self.target}
                
                Metadata:
                {json.dumps(self.state.metadata, ensure_ascii=False, indent=2)}
                
                Conteúdo do Edital:
                {self.state.content}
                """}
            ]
        )
        
        logger.info(f"Resumo gerado: {response}")
        
        # Converte a string JSON em objeto SummaryAnalysis
        response_dict = json.loads(response)
        response_obj = SummaryAnalysis(**response_dict)
        
        # Limpa campos vazios
        cleaned_data = response_obj.clean_empty_fields()
        
        # Atualiza o state
        self.state.summary = cleaned_data.get("summary", "")
        self.state.city = cleaned_data.get("city", "Não foi possível determinar")
        
        # Atualiza o metadata com as informações de contato e outras informações
        self.state.metadata.update({
            "phone": cleaned_data.get("phone", ""),
            "website": cleaned_data.get("website", ""),
            "email": cleaned_data.get("email", ""),
            "title": cleaned_data.get("title", ""),
            "object": cleaned_data.get("object", ""),
            "quantities": cleaned_data.get("quantities", ""),
            "specifications": cleaned_data.get("specifications", ""),
            "deadlines": cleaned_data.get("deadlines", ""),
            "values": cleaned_data.get("values", "")
        })
        
        logger.info("Resumo salvo com sucesso")

    @listen(generate_summary)
    @handle_flow_error
    def analyze_target(self):
        """Analisa se o edital é relevante para o target."""
        logger.info("Iniciando análise de target...")
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
                
                Resumo do Edital:
                {self.state.summary}
                
                Informações Adicionais:
                - Objeto: {self.state.metadata.get('object', '')}
                - Especificações: {self.state.metadata.get('specifications', '')}
                - Quantidades: {self.state.metadata.get('quantities', '')}
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

    @listen(analyze_target)
    @handle_flow_error
    def check_threshold(self):
        """Verifica se o edital atende ao threshold."""
        logger.info("Iniciando verificação de threshold...")
        
        # Caso 1: Threshold = 0 (serviço)
        if self.threshold == 0:
            self.state.threshold_match = "true"
            logger.info("Threshold = 0, ignorando verificação")
            return

        # Caso 2: Target não match
        if not self.state.target_match:
            self.state.threshold_match = "false"
            logger.info("Target não match, threshold = false")
            return

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
                
                Instruções:
                1. Analise cuidadosamente o resumo do edital
                2. Identifique TODAS as quantidades mencionadas
                3. Some as quantidades relevantes para o target
                4. Especifique a unidade de medida
                5. Explique como chegou na quantidade total
                
                Exemplo de resposta:
                {
                    "total_quantity": 100,
                    "unit": "unidades",
                    "explanation": "Encontrei 100 unidades mencionadas no edital"
                }"""},
                {"role": "user", "content": f"""
                Target: {self.target}
                Threshold: {self.threshold}
                
                Resumo do Edital:
                {self.state.summary}
                """}
            ]
        )
        
        logger.info(f"Conteúdo do QuantitiesAnalysis: {response}")
        
        # Validação 1: Verifica se a resposta é um JSON válido
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            self.state.threshold_match = "inconclusive"
            self.state.metadata["quantities"] = "Erro ao processar quantidades: resposta inválida"
            return
        
        # Validação 2: Verifica se todos os campos obrigatórios estão presentes
        required_fields = ["total_quantity", "unit", "explanation"]
        missing_fields = [field for field in required_fields if field not in response_dict]
        if missing_fields:
            logger.error(f"Campos obrigatórios ausentes: {missing_fields}")
            self.state.threshold_match = "inconclusive"
            self.state.metadata["quantities"] = f"Erro ao processar quantidades: campos ausentes ({', '.join(missing_fields)})"
            return
        
        # Validação 3: Verifica se total_quantity é um número válido
        try:
            total_quantity = int(response_dict["total_quantity"])
            if total_quantity < 0:
                raise ValueError("Quantidade não pode ser negativa")
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao validar quantidade: {str(e)}")
            self.state.threshold_match = "inconclusive"
            self.state.metadata["quantities"] = "Erro ao processar quantidades: valor inválido"
            return
        
        # Validação 4: Verifica se unit é uma string não vazia
        if not response_dict["unit"] or not isinstance(response_dict["unit"], str):
            logger.error("Unidade de medida inválida")
            self.state.threshold_match = "inconclusive"
            self.state.metadata["quantities"] = "Erro ao processar quantidades: unidade inválida"
            return
        
        # Cria o objeto QuantitiesAnalysis com os dados validados
        response_obj = QuantitiesAnalysis(
            total_quantity=total_quantity,
            unit=response_dict["unit"],
            explanation=response_dict["explanation"]
        )
        
        # Verifica se a quantidade total atende ao threshold
        if response_obj.total_quantity >= self.threshold:
            self.state.threshold_match = "true"
            logger.info(f"Quantidade {response_obj.total_quantity} {response_obj.unit} >= threshold {self.threshold}")
        else:
            self.state.threshold_match = "false"
            logger.info(f"Quantidade {response_obj.total_quantity} {response_obj.unit} < threshold {self.threshold}")
        
        # Atualiza o metadata com a explicação
        self.state.metadata["quantities"] = f"{response_obj.total_quantity} {response_obj.unit} - {response_obj.explanation}"

    @listen(check_threshold)
    @handle_flow_error
    def generate_justification(self):
        """Gera justificativa para a decisão."""
        logger.info("Iniciando geração de justificativa...")
        logger.warning(f"Estado atual - has_error: {self.state.has_error}, error_message: {self.state.error_message}")
        
        # Inicializa o LLM
        llm = LLM(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=250,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )

        # Faz a chamada ao LLM
        response = llm.call(
            messages=[
                {"role": "system", "content": """Você é um especialista em justificar decisões sobre editais.
                Sua tarefa é gerar uma justificativa extremamente concisa e direta.
                
                Lógica de Decisão:
                1. Target Match (true/false):
                   - true: O edital menciona o target ou equipamentos/serviços similares
                   - false: O edital não menciona nada relacionado ao target
                
                2. Threshold Match ("true"/"false"/"inconclusive"):
                   - "true": Quantidade >= threshold
                   - "false": Quantidade < threshold
                   - "inconclusive": Não foi possível determinar a quantidade
                
                3. Edital Relevante (is_relevant):
                   - true: target_match=true E (threshold=0 OU threshold_match="true")
                   - false: target_match=false OU threshold_match="false"
                
                Instruções:
                1. Seja direto e objetivo
                2. Use no máximo 2 frases
                3. Se não relevante:
                   - Se target_match=false: Explique por que não encontrou o target
                   - Se threshold_match="false": Explique por que a quantidade é insuficiente
                4. Se relevante:
                   - Se threshold=0: Explique por que o target é relevante
                   - Se threshold>0: Explique por que a quantidade é suficiente
                5. Máximo 50 palavras"""},
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
        
        logger.info(f"Justificativa gerada: {response}")
        self.state.justification = response
        
        # Define se o edital é relevante
        self.state.is_relevant = (
            self.state.target_match and 
            (self.threshold == 0 or self.state.threshold_match == "true")
        )
        
        logger.info("Justificativa salva com sucesso")

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