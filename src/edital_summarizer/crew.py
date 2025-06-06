from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent
from typing import Dict, Any
import os, yaml, PyPDF2, zipfile, tempfile, shutil, json

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .utils.logger import get_logger

# Configuração global de rate limit
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 450,  # 10% abaixo do limite de 500 RPM
    "tokens_per_minute": 25000,  # 17% abaixo do limite de 30,000 TPM
    "shared": True  # Indica que o limite é compartilhado entre todos os agentes
}

# Configuração base do LLM
BASE_LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "api_key": os.getenv("OPENAI_API_KEY"),
    "max_retries": 2,
    "retry_delay": 5,
    "rate_limit": RATE_LIMIT_CONFIG
}

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

    @agent
    def target_analyst_agent(self) -> Agent:
        llm_config = {
            **BASE_LLM_CONFIG,
            "temperature": 0.1,
            "timeout": 30,
            "max_tokens": 1000,
            "request_timeout": 60
        }
        
        return Agent(
            config=self.agents_config["target_analyst_agent"],
            tools=[
                SimpleFileReadTool(),
                DocumentSearchTool()
            ],
            verbose=True,
            llm_config=llm_config
        )

    @agent
    def summary_agent(self) -> Agent:
        llm_config = {
            **BASE_LLM_CONFIG,
            "temperature": 0.3,
            "timeout": 60,
            "max_tokens": 2000,
            "request_timeout": 120
        }
        
        return Agent(
            config=self.agents_config["summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
            verbose=True,
            llm_config=llm_config
        )

    @agent
    def justification_agent(self) -> Agent:
        llm_config = {
            **BASE_LLM_CONFIG,
            "temperature": 0.3,
            "timeout": 60,
            "max_tokens": 1000,
            "request_timeout": 60
        }
        
        return Agent(
            config=self.agents_config["justification_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=True,
            llm_config=llm_config
        )

    def _is_device_target(self, target: str) -> bool:
        """Verifica se o target é relacionado a dispositivos."""
        device_keywords = ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']
        return any(keyword in target.lower() for keyword in device_keywords)

    def _process_target_response(self, response: str) -> Dict[str, str]:
        """Processa a resposta do target analyst e retorna o status do threshold."""
        try:
            logger.info(f"Processando resposta do target analyst: {response}")
            logger.info(f"Tipo da resposta: {type(response)}")
            
            # Tenta primeiro processar como JSON
            try:
                logger.info("Tentando processar como JSON...")
                response_data = json.loads(response)
                logger.info(f"Dados JSON processados: {response_data}")
                target_match = response_data.get("target_match", False)
                volume = response_data.get("volume", 0)
            except json.JSONDecodeError as e:
                logger.info(f"Não é JSON, tentando processar como string: {str(e)}")
                # Se não for JSON, processa como string booleana
                response = response.strip().lower()
                logger.info(f"Resposta após strip e lower: {response}")
                if response in ['true', 'false', 'inconclusive']:
                    target_match = response == 'true'
                    volume = 0
                    logger.info(f"Processado como string booleana. target_match: {target_match}, volume: {volume}")
                else:
                    logger.error(f"Resposta inválida do target analyst: {response}")
                    return {"status": "inconclusive", "match": False}
            
            # Se não for match, retorna imediatamente
            if not target_match:
                logger.info("Documento não é relevante para o target")
                return {"status": "false", "match": False}
            
            # Se for match e for dispositivo, verifica o threshold
            if self._is_device_target(self.target):
                logger.info(f"Target é dispositivo. Volume: {volume}, Threshold: {self.threshold}")
                if volume >= self.threshold:
                    logger.info("Volume atende ao threshold")
                    return {"status": "true", "match": True}
                else:
                    logger.info("Volume não atende ao threshold")
                    return {"status": "false", "match": False}
            
            # Se for match mas não for dispositivo, retorna true
            logger.info("Documento é relevante e não é dispositivo")
            return {"status": "true", "match": True}
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta do target analyst: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            logger.error(f"Stack trace:", exc_info=True)
            return {"status": "inconclusive", "match": False}

    def kickoff(self, edital_path_dir: str, target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """Inicia o processamento do edital."""
        try:
            logger.warning(f"Processando: {edital_path_dir}")
            self.target = target
            self.threshold = threshold

            # Processa todos os arquivos no diretório
            all_text = ""
            for root, _, files in os.walk(edital_path_dir):
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

            # Verifica se o texto está vazio
            if not text.strip():
                logger.error("Nenhum texto foi extraído dos documentos")
                raise ValueError("Nenhum texto foi extraído dos documentos")

            # Verifica se é um target de dispositivo
            is_device = self._is_device_target(target)
            logger.info(f"Target é dispositivo: {is_device}")

            # Cria os agentes
            target_analyst = self.target_analyst_agent()
            summary_agent = self.summary_agent()
            justification_agent = self.justification_agent()

            # Cria as tarefas
            target_analysis_task = Task(
                description=self.tasks_config["target_analysis_task"]["description"].format(
                    target=target,
                    threshold=threshold,
                    document_content=text[:500]
                ),
                agent=target_analyst,
                expected_output=self.tasks_config["target_analysis_task"]["expected_output"]
            )

            summary_task = Task(
                description=self.tasks_config["summary_task"]["description"].format(
                    target=target,
                    document_content=text[:500]
                ),
                agent=summary_agent,
                expected_output=self.tasks_config["summary_task"]["expected_output"]
            )

            justification_task = Task(
                description=self.tasks_config["justification_task"]["description"].format(
                    target=target,
                    threshold=threshold,
                    threshold_status="inconclusive",
                    document_content=text[:500]
                ),
                agent=justification_agent,
                expected_output=self.tasks_config["justification_task"]["expected_output"]
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

                # Pós-processamento do resumo para evitar lixo em inglês
                summary_lower = summary.lower()
                if (
                    'i now can give a great answer' in summary_lower or
                    'thought:' in summary_lower or
                    'final answer:' in summary_lower or
                    'não há contexto' in summary_lower or
                    'preciso de mais informações' in summary_lower or
                    any(word in summary for word in ['context', 'information', 'answer', 'english'])
                ):
                    # Se o resumo for inválido, verifica se temos informações suficientes
                    if not text.strip() or len(text.strip()) < 100:
                        target_response["match"] = False
                        summary = f'Edital de licitação para {target}.'
                        justification = f"O documento está vazio ou contém muito pouco conteúdo para análise."
                    else:
                        # Se temos conteúdo mas o resumo falhou, tenta gerar um resumo básico
                        summary = f'Edital de licitação para {target}. Conteúdo disponível para análise, mas não foi possível gerar um resumo detalhado.'

                # Pós-processamento da justificativa
                justification_lower = justification.lower()
                if (
                    'thought:' in justification_lower or
                    'final answer:' in justification_lower or
                    'não há contexto' in justification_lower or
                    'preciso de mais informações' in justification_lower or
                    any(word in justification for word in ['context', 'information', 'answer', 'english'])
                ):
                    if not text.strip() or len(text.strip()) < 100:
                        justification = f"O documento está vazio ou contém muito pouco conteúdo para análise."
                    else:
                        justification = f"O documento contém conteúdo, mas não foi possível determinar com certeza sua relevância para o target '{target}'."

                # Se force_match for True, força o target_match e threshold_match
                if force_match:
                    target_response["match"] = True
                    target_response["status"] = "true"

                # Corrigir threshold_match para 'false' se threshold não for atingido
                if not target_response["match"] and is_device:
                    target_response["status"] = "false"

                # Justificativa só se não houver match ou threshold_match não for 'true'
                justification_out = ""
                if not target_response["match"] or target_response["status"] in ["false", "inconclusive"]:
                    justification_out = justification

                return {
                    "target_match": target_response["match"],
                    "threshold_match": target_response["status"],
                    "summary": summary,
                    "justification": justification_out
                }
            except Exception as e:
                logger.error(f"Erro ao processar resultado da crew: {str(e)}")
                return {
                    "target_match": False,
                    "threshold_match": "inconclusive",
                    "summary": f"Edital de licitação para {target}.",
                    "justification": f"Erro ao processar resultado da crew: {str(e)}"
                }

        except Exception as e:
            logger.error(f"Erro ao processar edital: {str(e)}")
            return {
                "target_match": False,
                "threshold_match": "inconclusive",
                "summary": f"Edital de licitação para {target}.",
                "justification": f"Erro ao processar edital: {str(e)}"
            }
