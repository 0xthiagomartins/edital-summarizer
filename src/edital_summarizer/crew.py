from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import os, yaml, json, traceback, re, time
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .utils.logger import get_logger

logger = get_logger(__name__)

# Configurações globais
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 450,
    "tokens_per_minute": 25000,
    "shared": True,
    "chunk_size": 15000,
    "chunk_overlap": 1000
}

BASE_LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "api_key": os.getenv("OPENAI_API_KEY"),
    "max_retries": 2,
    "retry_delay": 5,
    "rate_limit": RATE_LIMIT_CONFIG
}

def load_yaml_config(path: str) -> Dict[str, Any]:
    """Carrega configuração YAML."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def split_text_into_chunks(text: str, chunk_size: int = 15000, overlap: int = 1000) -> List[str]:
    """Divide o texto em chunks menores com sobreposição."""
    if not text or not isinstance(text, str):
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        if end == text_length:
            chunks.append(text[start:end])
            break
        
        last_period = text.rfind('.', start, end)
        if last_period != -1 and last_period > start + chunk_size // 2:
            end = last_period + 1
        
        chunks.append(text[start:end])
        next_start = end - overlap
        start = next_start if next_start > start else start + 1
    
    return chunks

@CrewBase
class EditalSummarizer:
    """Crew para processamento de editais de licitação."""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = load_yaml_config(os.path.join(base_dir, 'config', 'agents.yaml'))
        self.tasks_config = load_yaml_config(os.path.join(base_dir, 'config', 'tasks.yaml'))
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY não definida no ambiente")

    @agent
    def knowledge_builder_agent(self) -> Agent:
        """Agente responsável por construir a base de conhecimento."""
        return Agent(
            role="Construtor de Base de Conhecimento",
            goal="Construir uma base de conhecimento estruturada a partir dos documentos do edital",
            backstory="""Você é um especialista em processamento de documentos e construção de bases de conhecimento.
            Sua função é analisar os documentos do edital e estruturar as informações de forma que possam ser facilmente consultadas.""",
            verbose=self.verbose,
            llm_config={**BASE_LLM_CONFIG, "temperature": 0.1},
            tools=[SimpleFileReadTool(), DocumentSearchTool()]
        )

    @agent
    def target_analyst_agent(self) -> Agent:
        """Agente responsável por analisar a relevância do target."""
        return Agent(
            role="Analista de Alvo",
            goal="Analisar se o documento é relevante para o alvo especificado e identificar o volume total de operações",
            backstory="""Você é um especialista em análise de editais e documentos de licitação.
            Sua função é determinar se o documento é relevante para o alvo especificado e, se for relacionado a dispositivos,
            identificar o volume total de operações.""",
            verbose=self.verbose,
            llm_config={**BASE_LLM_CONFIG, "temperature": 0.1},
            tools=[SimpleFileReadTool(), DocumentSearchTool()]
        )

    @agent
    def summary_agent(self) -> Agent:
        """Agente responsável por gerar resumos."""
        return Agent(
            config=self.agents_config["summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
            verbose=self.verbose,
            llm_config={**BASE_LLM_CONFIG, "temperature": 0.3}
        )

    @agent
    def justification_agent(self) -> Agent:
        """Agente responsável por gerar justificativas."""
        return Agent(
            config=self.agents_config["justification_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=self.verbose,
            llm_config={**BASE_LLM_CONFIG, "temperature": 0.3}
        )

    @agent
    def city_inference_agent(self) -> Agent:
        """Agente responsável por inferir a cidade."""
        return Agent(
            config=self.agents_config["city_inference_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=self.verbose,
            llm_config={**BASE_LLM_CONFIG, "temperature": 0.1}
        )

    @task
    def target_analysis_task(self, chunk: str, target: str, threshold: int) -> Task:
        """Task para análise do target em um chunk específico."""
        return Task(
            description=self.tasks_config["target_analysis_task"]["description"].format(
                target=target,
                threshold=threshold,
                document_content=chunk
            ),
            agent=self.target_analyst_agent(),
            expected_output="JSON com target_match e volume"
        )

    @task
    def summary_task(self, text: str) -> Task:
        """Task para geração do resumo."""
        return Task(
            description=self.tasks_config["summary_task"]["description"].format(
                document_content=text
            ),
            agent=self.summary_agent(),
            expected_output="Resumo conciso e estruturado do edital incluindo cidade/UF"
        )

    @task
    def justification_task(self, target: str, threshold: int) -> Task:
        """Task para geração da justificativa."""
        return Task(
            description=self.tasks_config["justification_task"]["description"].format(
                target=target,
                threshold=threshold
            ),
            agent=self.justification_agent(),
            expected_output="Justificativa clara e coerente"
        )

    def _create_knowledge_base(self, edital_path_dir: str) -> List[Any]:
        """Cria a base de conhecimento a partir dos arquivos do edital."""
        knowledge_sources = []
        for root, _, filenames in os.walk(edital_path_dir):
            for file in filenames:
                file_path = os.path.abspath(os.path.join(root, file))
                if file.lower().endswith('.pdf'):
                    knowledge_sources.append(PDFKnowledgeSource(file_paths=[file_path]))
                elif file.lower().endswith('.json'):
                    knowledge_sources.append(JSONKnowledgeSource(file_paths=[file_path]))
        return knowledge_sources

    def _read_metadata(self, edital_path_dir: str) -> Dict[str, Any]:
        """Lê o arquivo metadata.json do edital."""
        metadata_path = os.path.join(edital_path_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            return {"bid_number": "N/A"}

        for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(metadata_path, 'r', encoding=encoding) as f:
                    metadata = json.load(f)
                    bid_number = (
                        metadata.get("bid_number") or 
                        metadata.get("bidNumber") or 
                        metadata.get("numero_licitacao") or 
                        metadata.get("numeroLicitacao") or 
                        "N/A"
                    )
                    return {"bid_number": bid_number}
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return {"bid_number": "N/A"}

    def _extract_text_from_files(self, edital_path_dir: str) -> str:
        """Extrai texto dos arquivos do edital."""
        text = ""
        file_tool = SimpleFileReadTool()
        
        for root, _, filenames in os.walk(edital_path_dir):
            for file in filenames:
                if file.lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.md', '.zip', '.json')):
                    file_path = os.path.abspath(os.path.join(root, file))
                    try:
                        file_text = file_tool._run(file_path)
                        if not file_text.startswith("Error:"):
                            file_text = file_text.replace('\x00', '')
                            file_text = re.sub(r'\s+', ' ', file_text).strip()
                            if file_text:
                                text += f"\n\n=== {os.path.basename(file_path)} ===\n\n{file_text}"
                    except Exception as e:
                        logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
                        continue
        
        return text.strip()

    def _is_device_target(self, target: str) -> bool:
        """Verifica se o target é relacionado a dispositivos."""
        device_keywords = [
            'tablet', 'notebook', 'laptop', 'desktop', 'computador', 'pc',
            'smartphone', 'celular', 'telefone', 'impressora', 'scanner',
            'monitor', 'teclado', 'mouse', 'headset', 'câmera', 'camera',
            'projetor', 'tv', 'televisão', 'televisao', 'equipamento',
            'hardware', 'dispositivo', 'aparelho', 'máquina', 'maquina'
        ]
        return any(keyword in target.lower() for keyword in device_keywords)

    @before_kickoff
    def prepare_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara os inputs antes do kickoff."""
        edital_path_dir = inputs.get("edital_path_dir")
        if not os.path.exists(edital_path_dir):
            raise ValueError(f"Diretório não encontrado: {edital_path_dir}")
        
        metadata = self._read_metadata(edital_path_dir)
        text = self._extract_text_from_files(edital_path_dir)
        
        if not text:
            raise ValueError(f"Nenhum texto extraído dos arquivos em: {edital_path_dir}")
        
        # Cria as tasks para cada chunk
        self.tasks = []
        chunks = split_text_into_chunks(
            text,
            chunk_size=RATE_LIMIT_CONFIG["chunk_size"],
            overlap=RATE_LIMIT_CONFIG["chunk_overlap"]
        )
        
        for chunk in chunks:
            self.tasks.append(self.target_analysis_task(
                chunk=chunk,
                target=inputs["target"],
                threshold=inputs["threshold"]
            ))
        
        # Adiciona as tasks de resumo e justificativa
        self.tasks.append(self.summary_task(text=text))
        self.tasks.append(self.justification_task(
            target=inputs["target"],
            threshold=inputs["threshold"]
        ))
        
        return {
            **inputs,
            "metadata": metadata,
            "text": text,
            "chunks": chunks
        }

    @after_kickoff
    def process_output(self, output: Any) -> Dict[str, Any]:
        """Processa o output após o kickoff."""
        try:
            # Processa os resultados das tasks
            target_results = []
            for task_output in output.tasks_output:
                if task_output.agent.role == "Analista de Alvo":
                    target_results.append(json.loads(task_output.raw))
            
            # Consolida os resultados do target
            final_target_match = any(result["target_match"] for result in target_results)
            final_volume = max(result["volume"] for result in target_results) if target_results else 0
            
            # Determina o threshold_match
            if not final_target_match:
                threshold_match = "false"
            elif not self._is_device_target(output.target):
                threshold_match = "true"
            elif output.threshold == 0:
                threshold_match = "true"
            elif final_volume >= output.threshold:
                threshold_match = "true"
            elif final_volume == 0:
                threshold_match = "inconclusive"
            else:
                threshold_match = "false"
            
            # Determina is_relevant
            is_relevant = False
            if final_target_match:
                if threshold_match == "true":
                    is_relevant = True
                elif output.threshold == 0:
                    is_relevant = True
            
            # Extrai o resumo e justificativa
            summary = next((task_output.raw for task_output in output.tasks_output if task_output.agent.role == "Gerador de Resumos"), "")
            justification = next((task_output.raw for task_output in output.tasks_output if task_output.agent.role == "Gerador de Justificativas"), "")
            
            # Extrai a cidade do resumo
            city = "N/A"
            city_match = re.search(r'\*\*Cidade/UF\*\*\s*-\s*([^\n]+)', summary)
            if city_match:
                city = city_match.group(1).strip()
            
            return {
                "bid_number": output.metadata.get("bid_number", "N/A"),
                "city": city,
                "target_match": final_target_match,
                "threshold_match": threshold_match,
                "is_relevant": is_relevant,
                "summary": summary,
                "justification": justification
            }
        except Exception as e:
            logger.error(f"Erro ao processar output: {str(e)}")
            return {
                "bid_number": output.metadata.get("bid_number", "N/A"),
                "city": "N/A",
                "target_match": False,
                "threshold_match": "false",
                "is_relevant": False,
                "summary": f"Erro ao processar output: {str(e)}",
                "justification": "Ocorreu um erro ao processar o resultado da análise."
            }

    @crew
    def crew(self) -> Crew:
        """Cria a crew para processamento do edital."""
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator
            process=Process.sequential,
            verbose=self.verbose
        )

    def kickoff(self, edital_path_dir: str, target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """Inicia o processamento do edital."""
        try:
            crew = self.crew()
            result = crew.kickoff(inputs={
                "edital_path_dir": edital_path_dir,
                "target": target,
                "threshold": threshold,
                "force_match": force_match
            })
            return self.process_output(result)
        except Exception as e:
            logger.error(f"Erro ao processar edital: {str(e)}")
            return {
                "bid_number": "N/A",
                "city": "N/A",
                "target_match": False,
                "threshold_match": "false",
                "is_relevant": False,
                "summary": f"Erro ao processar edital: {str(e)}",
                "justification": "Ocorreu um erro ao processar o edital."
            }
