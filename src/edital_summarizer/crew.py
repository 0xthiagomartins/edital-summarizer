from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import json
import yaml
from pathlib import Path

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .tools.quantity_tools import QuantityExtractionTool
from .processors.document import DocumentProcessor
from .utils.logger import get_logger
from .utils.device_utils import is_device_target, check_device_threshold

# Função utilitária para carregar arquivos YAML
def load_yaml_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

logger = get_logger(__name__)

@CrewBase
class EditalSummarizer:
    """EditalSummarizer crew otimizado para processamento de editais de licitação"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = load_yaml_config(os.path.join(base_dir, 'config', 'agents.yaml'))
        self.tasks_config = load_yaml_config(os.path.join(base_dir, 'config', 'tasks.yaml'))
        self.processor = DocumentProcessor()
        self.quantity_tool = QuantityExtractionTool()

    @agent
    def target_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["target_analyst_agent"],
            tools=[
                SimpleFileReadTool(),
                DocumentSearchTool(),
                QuantityExtractionTool()
            ],
            verbose=True,
            llm_config={
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_retries": 2,
                "retry_delay": 5,
                "timeout": 30,
            },
        )

    @agent
    def summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
            verbose=True,
            llm_config={
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.3,
                "max_retries": 2,
                "retry_delay": 5,
                "timeout": 60,
            },
        )

    @agent
    def justification_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["justification_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=True,
            llm_config={
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.3,
                "max_retries": 2,
                "retry_delay": 5,
                "timeout": 60,
            },
        )

    def _is_device_target(self, target: str) -> bool:
        """Verifica se o target é relacionado a dispositivos."""
        device_keywords = ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']
        return any(keyword in target.lower() for keyword in device_keywords)

    def _process_target_response(self, response: str) -> Dict[str, str]:
        """Processa a resposta do target analyst e retorna o status do threshold."""
        response = response.lower().strip()
        if response == "true":
            return {"status": "true", "match": True}
        elif response == "false":
            return {"status": "false", "match": False}
        else:
            return {"status": "inconclusive", "match": False}

    def kickoff(self, document_path: str, target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """Inicia o processamento do edital."""
        try:
            # Lê o documento
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Verifica se é um target de dispositivo
            is_device = is_device_target(target)

            # Se for dispositivo e threshold > 0, verifica o threshold
            threshold_status = "inconclusive"
            threshold_match = False
            if is_device and threshold > 0:
                # Extrai quantidades do texto
                quantities = self.quantity_tool.extract(text)
                
                # Verifica se há quantidades suficientes
                if quantities:
                    total_quantity = sum(q["quantity"] for q in quantities)
                    threshold_match = total_quantity >= threshold
                    threshold_status = "true" if threshold_match else "false"
                else:
                    threshold_status = "inconclusive"
            elif is_device and threshold == 0:
                # Se threshold é 0, considera que não há verificação de quantidade
                threshold_status = "true"
                threshold_match = True

            # Cria os agentes
            target_analyst = Agent(
                role="Target Analyst",
                goal="Analisar se o documento é relevante para o target e validar a quantidade mínima de dispositivos",
                backstory="""Você é um especialista em análise de documentos.
                Sua função é determinar se o documento é relevante para o target especificado.
                Se o target for relacionado a dispositivos e o threshold for maior que zero, você também deve verificar se a quantidade mencionada atende ao threshold mínimo.
                Se não for possível determinar a quantidade, responda com 'Inconclusive'.""",
                verbose=self.verbose
            )

            summary_agent = Agent(
                role="Summary Agent",
                goal="Gerar um resumo conciso do documento",
                backstory="""Você é um especialista em resumir documentos.
                Sua função é gerar um resumo claro e conciso do documento, destacando os pontos mais relevantes.""",
                verbose=self.verbose
            )

            justification_agent = Agent(
                role="Justification Agent",
                goal="Fornecer uma justificativa clara para a decisão tomada",
                backstory="""Você é um especialista em justificar decisões.
                Sua função é fornecer uma justificativa clara e objetiva para a decisão tomada pelo Target Analyst.
                Se o documento não for relevante, explique por quê.
                Se a quantidade não atender ao threshold, explique por quê.""",
                verbose=self.verbose
            )

            # Cria as tarefas
            target_analysis_task = Task(
                description=f"""Analise o documento e determine se ele é relevante para o target '{target}'.
                Se o target for relacionado a dispositivos e o threshold for maior que zero, verifique se a quantidade mencionada atende ao threshold de {threshold}.
                Responda apenas com 'true', 'false' ou 'inconclusive'.""",
                agent=target_analyst
            )

            summary_task = Task(
                description="Gere um resumo conciso do documento, destacando os pontos mais relevantes.",
                agent=summary_agent
            )

            justification_task = Task(
                description="""Forneça uma justificativa clara para a decisão tomada.
                Se o documento não for relevante, explique por quê.
                Se a quantidade não atender ao threshold, explique por quê.""",
                agent=justification_agent
            )

            # Cria a crew
            crew = Crew(
                agents=[target_analyst, summary_agent, justification_agent],
                tasks=[target_analysis_task, summary_task, justification_task],
                verbose=self.verbose
            )

            # Executa a crew
            result = crew.kickoff()

            # Processa o resultado
            target_response = self._process_target_response(result[0])
            summary = result[1]
            justification = result[2]

            # Se force_match for True, força o target_match
            if force_match:
                target_response["match"] = True
                target_response["status"] = "true"

            return {
                "target_match": target_response["match"],
                "threshold_match": threshold_match,
                "threshold_status": threshold_status,
                "target_summary": summary,
                "document_summary": summary,
                "justification": justification
            }

        except Exception as e:
            logger.error(f"Erro ao processar edital: {str(e)}")
            return {
                "target_match": False,
                "threshold_match": False,
                "threshold_status": "inconclusive",
                "target_summary": "",
                "document_summary": "",
                "justification": f"Erro ao processar edital: {str(e)}"
            }
