from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import json
import yaml
from pathlib import Path
import PyPDF2
import zipfile
import tempfile
import shutil

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .tools.quantity_tools import QuantityExtractionTool
from .processors.document import DocumentProcessor
from .utils.logger import get_logger
from .utils.device_utils import is_device_target, check_device_threshold
from .utils.zip_handler import ZipHandler

# Função utilitária para carregar arquivos YAML
def load_yaml_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_pdf(file_path: str) -> str:
    """Lê um arquivo PDF e retorna seu conteúdo como texto."""
    text = ""
    try:
        logger.info(f"Tentando ler PDF: {file_path}")
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF tem {total_pages} páginas")
            for i, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                        logger.debug(f"Página {i}/{total_pages} processada com sucesso")
                    else:
                        logger.warning(f"Página {i}/{total_pages} não retornou texto")
                except Exception as e:
                    logger.warning(f"Erro ao extrair texto da página {i}/{total_pages} do PDF {file_path}: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Erro ao ler PDF {file_path}: {str(e)}")
    return text

def read_text_file(file_path: str) -> str:
    """Lê um arquivo de texto com diferentes codificações."""
    logger.info(f"Tentando ler arquivo de texto: {file_path}")
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            logger.debug(f"Tentando codificação: {encoding}")
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                logger.info(f"Arquivo lido com sucesso usando codificação {encoding}")
                return content
        except UnicodeDecodeError:
            logger.debug(f"Falha ao ler com codificação {encoding}")
            continue
    logger.warning(f"Não foi possível ler o arquivo {file_path} com nenhuma codificação conhecida")
    return ""

def process_zip(zip_path: str) -> str:
    """Processa um arquivo ZIP e retorna o conteúdo combinado de todos os arquivos suportados."""
    text = ""
    temp_dir = tempfile.mkdtemp()
    try:
        logger.info(f"Processando arquivo ZIP: {zip_path}")
        # Extrai o ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            logger.info(f"ZIP extraído para diretório temporário: {temp_dir}")
        
        # Processa todos os arquivos extraídos
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                logger.info(f"Processando arquivo extraído: {file}")
                if file.endswith('.pdf'):
                    pdf_text = read_pdf(file_path)
                    if pdf_text:
                        text += f"\n\n=== {file} ===\n\n{pdf_text}"
                        logger.info(f"PDF processado com sucesso: {file}")
                    else:
                        logger.warning(f"PDF não retornou texto: {file}")
                elif file.endswith(('.txt', '.docx', '.doc', '.md')):
                    file_text = read_text_file(file_path)
                    if file_text:
                        text += f"\n\n=== {file} ===\n\n{file_text}"
                        logger.info(f"Arquivo de texto processado com sucesso: {file}")
                    else:
                        logger.warning(f"Arquivo de texto não retornou conteúdo: {file}")
    finally:
        # Limpa o diretório temporário
        shutil.rmtree(temp_dir)
        logger.info(f"Diretório temporário removido: {temp_dir}")
    return text

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
        self.zip_handler = ZipHandler()

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
            logger.info(f"Iniciando processamento do documento: {document_path}")
            logger.info(f"Target: {target}")
            logger.info(f"Threshold: {threshold}")
            logger.info(f"Force Match: {force_match}")

            # Verifica se é um arquivo ZIP
            if self.zip_handler.is_zip_file(document_path):
                logger.info("Documento é um arquivo ZIP")
                text = process_zip(document_path)
            # Verifica se é um diretório
            elif os.path.isdir(document_path):
                logger.info("Documento é um diretório")
                # Processa todos os arquivos no diretório
                all_text = ""
                for root, _, files in os.walk(document_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        logger.info(f"Processando arquivo: {file_path}")
                        if file.endswith('.pdf'):
                            # Lê arquivo PDF
                            pdf_text = read_pdf(file_path)
                            if pdf_text:
                                all_text += f"\n\n=== {file} ===\n\n{pdf_text}"
                                logger.info(f"PDF processado com sucesso: {file}")
                            else:
                                logger.warning(f"PDF não retornou texto: {file}")
                        elif file.endswith(('.txt', '.docx', '.doc', '.md')):
                            file_text = read_text_file(file_path)
                            if file_text:
                                all_text += f"\n\n=== {file} ===\n\n{file_text}"
                                logger.info(f"Arquivo de texto processado com sucesso: {file}")
                            else:
                                logger.warning(f"Arquivo de texto não retornou conteúdo: {file}")
                text = all_text
            else:
                # Lê o documento único
                logger.info("Documento é um arquivo único")
                if document_path.endswith('.pdf'):
                    text = read_pdf(document_path)
                else:
                    text = read_text_file(document_path)

            # Verifica se o texto está vazio
            if not text.strip():
                logger.error("Nenhum texto foi extraído dos documentos")
                raise ValueError("Nenhum texto foi extraído dos documentos")

            logger.info(f"Texto extraído com sucesso. Tamanho: {len(text)} caracteres")
            logger.debug(f"Primeiros 500 caracteres do texto: {text[:500]}")

            # Verifica se é um target de dispositivo
            is_device = is_device_target(target)
            logger.info(f"Target é dispositivo: {is_device}")

            # Se for dispositivo e threshold > 0, verifica o threshold
            threshold_status = "inconclusive"
            threshold_match = False
            if is_device and threshold > 0:
                logger.info("Verificando threshold para dispositivo")
                try:
                    # Extrai quantidades do texto
                    quantities = self.quantity_tool._run(text)
                    logger.info(f"Quantidades extraídas: {quantities}")
                    
                    # Verifica se há quantidades suficientes
                    if quantities and quantities.strip():
                        try:
                            quantities_list = eval(quantities)  # Converte a string JSON para lista
                            if not isinstance(quantities_list, list):
                                logger.warning(f"Quantidades não é uma lista: {type(quantities_list)}")
                                threshold_status = "inconclusive"
                            else:
                                total_quantity = sum(q.get("number", 0) for q in quantities_list)
                                threshold_match = total_quantity >= threshold
                                threshold_status = "true" if threshold_match else "false"
                                logger.info(f"Total de quantidades: {total_quantity}, Threshold: {threshold}, Match: {threshold_match}")
                        except Exception as e:
                            logger.error(f"Erro ao processar quantidades: {str(e)}")
                            threshold_status = "inconclusive"
                    else:
                        logger.warning("Nenhuma quantidade encontrada ou string vazia")
                        threshold_status = "inconclusive"
                except Exception as e:
                    logger.error(f"Erro ao extrair quantidades: {str(e)}")
                    threshold_status = "inconclusive"
            elif is_device and threshold == 0:
                logger.info("Threshold é 0, considerando como true")
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
                agent=target_analyst,
                expected_output="true, false ou inconclusive"
            )

            summary_task = Task(
                description="Gere um resumo conciso do documento, destacando os pontos mais relevantes.",
                agent=summary_agent,
                expected_output="Resumo do documento em português"
            )

            justification_task = Task(
                description="""Forneça uma justificativa clara para a decisão tomada.
                Se o documento não for relevante, explique por quê.
                Se a quantidade não atender ao threshold, explique por quê.""",
                agent=justification_agent,
                expected_output="Justificativa em português"
            )

            # Cria a crew
            crew = Crew(
                agents=[target_analyst, summary_agent, justification_agent],
                tasks=[target_analysis_task, summary_task, justification_task],
                verbose=self.verbose
            )

            # Executa a crew
            result = crew.kickoff()
            logger.info(f"Resultado da crew: {result}")
            logger.info(f"Tipo do resultado: {type(result)}")
            logger.info(f"Atributos do resultado: {dir(result)}")
            logger.info(f"Representação do resultado: {repr(result)}")

            # Processa o resultado
            try:
                # Extrai os resultados das tarefas
                target_response = self._process_target_response(result.tasks_output[0].raw)
                summary = result.tasks_output[1].raw
                justification = result.tasks_output[2].raw

                logger.info(f"Target response: {target_response}")
                logger.info(f"Summary: {summary}")
                logger.info(f"Justification: {justification}")

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
                logger.error(f"Erro ao processar resultado da crew: {str(e)}")
                return {
                    "target_match": False,
                    "threshold_match": False,
                    "threshold_status": "inconclusive",
                    "target_summary": "",
                    "document_summary": "",
                    "justification": f"Erro ao processar resultado da crew: {str(e)}"
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
