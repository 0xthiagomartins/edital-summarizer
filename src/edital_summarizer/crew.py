from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent
from typing import Dict, Any
import os, yaml, PyPDF2, zipfile, tempfile, shutil, json
import traceback
import re

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .utils.logger import get_logger

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
        """Create target analyst agent."""
        llm_config = {
            **BASE_LLM_CONFIG,
            "temperature": 0.1,
            "timeout": 30,
            "max_tokens": 1000,
            "request_timeout": 60
        }
        return Agent(
            role="Analista de Alvo",
            goal="Analisar se o documento é relevante para o alvo especificado e identificar o volume total de operações",
            backstory="""Você é um especialista em análise de editais e documentos de licitação.
            Sua função é determinar se o documento é relevante para o alvo especificado e, se for relacionado a dispositivos,
            identificar o volume total de operações.
            
            IMPORTANTE: Você DEVE retornar APENAS um JSON válido com os seguintes campos:
            - target_match: boolean indicando se o documento é relevante para o alvo
            - volume: número inteiro indicando o volume total de operações (0 se não for relacionado a dispositivos)
            
            Exemplo de resposta válida:
            {
                "target_match": true,
                "volume": 1000
            }
            
            NÃO inclua nenhum texto adicional ou explicações. Apenas o JSON.""",
            verbose=True,
            llm_config=llm_config,
            tools=[SimpleFileReadTool()],
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
        device_keywords = [
            'tablet', 'notebook', 'laptop', 'desktop', 'computador', 'pc',
            'smartphone', 'celular', 'telefone', 'impressora', 'scanner',
            'monitor', 'teclado', 'mouse', 'headset', 'câmera', 'camera',
            'projetor', 'tv', 'televisão', 'televisao', 'equipamento',
            'hardware', 'dispositivo', 'aparelho', 'máquina', 'maquina'
        ]
        
        target_lower = target.lower()
        return any(keyword in target_lower for keyword in device_keywords)

    def _process_target_response(self, response: str, threshold: int) -> bool:
        """Process target analyst response."""
        try:
            logger.info(f"Processando resposta do target analyst: {response}")
            
            # Tenta processar como JSON
            try:
                data = json.loads(response)
                logger.info(f"Resposta processada como JSON: {data}")
                
                if not isinstance(data, dict):
                    logger.error(f"Resposta não é um dicionário: {type(data)}")
                    return False
                    
                target_match = data.get("target_match")
                volume = data.get("volume", 0)
                
                if not isinstance(target_match, bool):
                    logger.error(f"target_match não é um booleano: {type(target_match)}")
                    return False
                    
                if not isinstance(volume, (int, float)):
                    logger.error(f"volume não é um número: {type(volume)}")
                    return False
                
                # Se não for um dispositivo, não precisa verificar o volume
                if not target_match:
                    logger.info("Documento não é relevante para o alvo")
                    return False
                
                # Se for um dispositivo, verifica o volume
                if volume >= threshold:
                    logger.info(f"Volume ({volume}) atende ao threshold ({threshold})")
                    return True
                else:
                    logger.info(f"Volume ({volume}) não atende ao threshold ({threshold})")
                    return False
                    
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar resposta do target analyst: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def kickoff(self, edital_path_dir: str, target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """Processa um edital e retorna um resumo."""
        try:
            logger.info(f"Iniciando processamento do edital em: {edital_path_dir}")
            logger.info(f"Target: {target}")
            logger.info(f"Threshold: {threshold}")
            logger.info(f"Force match: {force_match}")
            
            # Verifica se o diretório existe
            if not os.path.exists(edital_path_dir):
                logger.error(f"Diretório não encontrado: {edital_path_dir}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "summary": f"Erro: Diretório não encontrado: {edital_path_dir}",
                    "justification": "Não foi possível processar o edital pois o diretório não foi encontrado."
                }
            
            # Lista os arquivos no diretório
            files = []
            for root, _, filenames in os.walk(edital_path_dir):
                for file in filenames:
                    if file.lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.md', '.zip', '.json')):
                        files.append(os.path.abspath(os.path.join(root, file)))
            
            if not files:
                logger.error(f"Nenhum arquivo encontrado em: {edital_path_dir}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "summary": f"Erro: Nenhum arquivo encontrado em: {edital_path_dir}",
                    "justification": "Não foi possível processar o edital pois nenhum arquivo foi encontrado."
                }
            
            logger.info(f"Arquivos encontrados: {files}")
            
            # Extrai o texto dos arquivos
            text = ""
            for file_path in files:
                try:
                    logger.info(f"Processando arquivo: {file_path}")
                    file_tool = SimpleFileReadTool()
                    file_text = file_tool._run(file_path)
                    
                    if file_text.startswith("Error:"):
                        logger.error(f"Erro ao ler arquivo {file_path}: {file_text}")
                        continue
                        
                    # Limpa e normaliza o texto
                    file_text = file_text.replace('\x00', '')  # Remove caracteres nulos
                    file_text = re.sub(r'\s+', ' ', file_text)  # Normaliza espaços
                    file_text = file_text.strip()
                    
                    if not file_text:
                        logger.warning(f"Arquivo {file_path} não retornou texto")
                        continue
                        
                    text += f"\n\n=== {os.path.basename(file_path)} ===\n\n{file_text}"
                    logger.info(f"Arquivo processado com sucesso: {file_path}")
                    logger.debug(f"Primeiros 100 caracteres do arquivo: {file_text[:100]}")
                except Exception as e:
                    logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
                    continue
            
            if not text.strip():
                logger.error("Nenhum texto extraído dos arquivos")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "summary": "Erro: Não foi possível extrair texto dos arquivos",
                    "justification": "Não foi possível processar o edital pois não foi possível extrair texto dos arquivos."
                }
            
            # Limpa e normaliza o texto final
            text = text.replace('\x00', '')  # Remove caracteres nulos
            text = re.sub(r'\s+', ' ', text)  # Normaliza espaços
            text = text.strip()
            
            logger.info(f"Texto extraído com sucesso. Tamanho: {len(text)} caracteres")
            logger.debug(f"Primeiros 500 caracteres do texto: {text[:500]}")
            
            # Cria os agentes
            target_analyst = self.target_analyst_agent()
            summary_agent = self.summary_agent()
            justification_agent = self.justification_agent()
            
            # Cria as tarefas
            logger.info("Criando tarefa de análise de target...")
            logger.debug(f"Target: {target}")
            logger.debug(f"Threshold: {threshold}")
            logger.debug(f"Arquivos: {files}")
            
            try:
                target_analysis_task = Task(
                    description=f"""Analise o documento para determinar se é relevante para o alvo '{target}' e se atende ao volume mínimo de {threshold} unidades.
                    
                    IMPORTANTE: Você DEVE retornar APENAS um JSON válido com os seguintes campos:
                    - target_match: boolean indicando se o documento é relevante para o alvo
                    - volume: número inteiro indicando o volume total de operações (0 se não for relacionado a dispositivos)
                    
                    Exemplo de resposta válida:
                    {{
                        "target_match": true,
                        "volume": 1000
                    }}
                    
                    NÃO inclua nenhum texto adicional ou explicações. Apenas o JSON.
                    
                    CONTEÚDO DO DOCUMENTO:
                    {text}""",
                    agent=target_analyst,
                    expected_output="JSON com target_match e volume"
                )
                logger.info("Tarefa de análise de target criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar tarefa de análise de target: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                raise
            
            try:
                logger.info("Criando tarefa de resumo...")
                summary_task = Task(
                    description=f"""Gere um resumo executivo do documento, focando nos pontos mais relevantes.
                    O resumo deve ser conciso e informativo, destacando os aspectos mais importantes do edital.
                    
                    CONTEÚDO DO DOCUMENTO:
                    {text}""",
                    agent=summary_agent,
                    expected_output="Resumo executivo do documento"
                )
                logger.info("Tarefa de resumo criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar tarefa de resumo: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                raise
            
            try:
                logger.info("Criando tarefa de justificativa...")
                justification_task = Task(
                    description=f"""Forneça uma justificativa clara e objetiva para a decisão tomada sobre a relevância do documento.
                    A justificativa deve explicar por que o documento foi considerado relevante ou não para o alvo especificado.
                    
                    CONTEÚDO DO DOCUMENTO:
                    {text}""",
                    agent=justification_agent,
                    expected_output="Justificativa da decisão"
                )
                logger.info("Tarefa de justificativa criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar tarefa de justificativa: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                raise

            # Cria a crew
            try:
                logger.info("Criando crew...")
                logger.debug(f"Agentes: {[type(agent) for agent in [target_analyst, summary_agent, justification_agent]]}")
                logger.debug(f"Tarefas: {[type(task) for task in [target_analysis_task, summary_task, justification_task]]}")
                
                crew = Crew(
                    agents=[target_analyst, summary_agent, justification_agent],
                    tasks=[target_analysis_task, summary_task, justification_task],
                    verbose=True
                )
                logger.info("Crew criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar crew: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                raise
            
            # Executa a crew
            result = crew.kickoff()
            
            try:
                # Extrai os resultados das tarefas
                target_response = self._process_target_response(result.tasks_output[0].raw, threshold)
                summary = result.tasks_output[1].raw
                justification = result.tasks_output[2].raw
                
                # Verifica se o resumo é válido
                if not summary or len(summary.strip()) < 50:
                    logger.warning("Resumo inválido, usando texto alternativo")
                    summary = f'Edital de licitação para {target}.'
                
                # Verifica se a justificativa é válida
                if not justification or len(justification.strip()) < 50:
                    logger.warning("Justificativa inválida, usando texto alternativo")
                    justification = f"O documento foi analisado em relação ao alvo '{target}'."
                
                # Verifica se é um dispositivo
                is_device = self._is_device_target(target)
                
                # Se force_match for True, força o target_match e threshold_match
                if force_match:
                    target_response = True
                
                # Corrigir threshold_match para 'false' se threshold não for atingido
                if not target_response and is_device:
                    target_response = False
                
                # Justificativa só se não houver match ou threshold_match não for 'true'
                justification_out = ""
                if not target_response or target_response == "false":
                    justification_out = justification
                
                return {
                    "target_match": target_response,
                    "threshold_match": "true" if target_response else "false",
                    "summary": summary,
                    "justification": justification_out
                }
                
            except Exception as e:
                logger.error(f"Erro ao processar resultados: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "summary": f"Erro ao processar resultados: {str(e)}",
                    "justification": "Ocorreu um erro ao processar os resultados da análise."
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar edital: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {
                "target_match": False,
                "threshold_match": "false",
                "summary": f"Erro ao processar edital: {str(e)}",
                "justification": "Ocorreu um erro ao processar o edital."
            }
