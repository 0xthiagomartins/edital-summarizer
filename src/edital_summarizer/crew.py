from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import yaml
import PyPDF2
import zipfile
import tempfile
import shutil

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .tools.quantity_tools import QuantityExtractionTool
from .utils.logger import get_logger

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

    def kickoff(self, edital_path_dir: str, target: str, threshold: int = 500, force_match: bool = False) -> Dict[str, Any]:
        """Inicia o processamento do edital."""
        try:
            logger.warning(f"Processando: {edital_path_dir}")

            # Processa todos os arquivos no diretório
            all_text = ""
            for root, _, files in os.walk(edital_path_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith('.pdf'):
                        # Lê arquivo PDF
                        pdf_text = read_pdf(file_path)
                        if pdf_text:
                            all_text += f"\n\n=== {file} ===\n\n{pdf_text}"
                    elif file.endswith(('.txt', '.docx', '.doc', '.md')):
                        file_text = read_text_file(file_path)
                        if file_text:
                            all_text += f"\n\n=== {file} ===\n\n{file_text}"
                text = all_text

            # Verifica se o texto está vazio
            if not text.strip():
                logger.error("Nenhum texto foi extraído dos documentos")
                raise ValueError("Nenhum texto foi extraído dos documentos")

            # Verifica se é um target de dispositivo
            is_device = self._is_device_target(target)
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
                                threshold_match = False
                            else:
                                total_quantity = sum(q.get("number", 0) for q in quantities_list)
                                threshold_match = total_quantity >= threshold
                                threshold_status = "true" if threshold_match else "false"
                                logger.info(f"Total de quantidades: {total_quantity}, Threshold: {threshold}, Match: {threshold_match}")
                        except Exception as e:
                            logger.error(f"Erro ao processar quantidades: {str(e)}")
                            threshold_status = "inconclusive"
                            threshold_match = False
                    else:
                        logger.warning("Nenhuma quantidade encontrada ou string vazia")
                        threshold_status = "inconclusive"
                        threshold_match = False
                except Exception as e:
                    logger.error(f"Erro ao extrair quantidades: {str(e)}")
                    threshold_status = "inconclusive"
                    threshold_match = False
            elif is_device and threshold == 0:
                logger.info("Threshold é 0, considerando como true")
                threshold_match = True
                threshold_status = "true"

            # Limite de texto para o LLM (ex: 4.000 caracteres)
            max_summary_chars = 4000
            text_for_summary = text[:max_summary_chars]
            logger.info(f"Primeiros 500 caracteres enviados ao agente de resumo: {text_for_summary[:500]}")

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
                description=(
                    f"Gere um resumo executivo do documento fornecido, focando no target '{target}'.\n"
                    "IMPORTANTE:\n"
                    "1. O resumo DEVE ser baseado APENAS no conteúdo do documento fornecido.\n"
                    "2. O resumo DEVE ser em português.\n"
                    "3. O resumo DEVE ser informativo e útil.\n"
                    "4. NÃO inclua nenhum texto em inglês.\n"
                    "5. NÃO inclua nenhum texto explicativo antes ou depois do resumo.\n"
                    "6. NÃO retorne 'Thought:', 'Final Answer:', 'Não há contexto', 'Preciso de mais informações', ou qualquer justificativa.\n"
                    "7. O resumo DEVE ser um texto completo e coerente em português.\n"
                    "8. NÃO gere um resumo genérico sobre o target.\n"
                    "9. NÃO retorne um JSON ou qualquer outro formato.\n"
                    "10. Se o documento não contiver informações suficientes, retorne: 'Edital de licitação para {target}'.\n"
                    "11. A resposta DEVE ser APENAS o resumo em português, sem nenhum texto adicional.\n"
                    "12. NÃO inclua palavras como 'Thought:', 'Final Answer:' ou qualquer outro prefixo.\n"
                    "13. O resumo DEVE conter:\n"
                    "    - Objeto da licitação\n"
                    "    - Quantidade de itens (se mencionada)\n"
                    "    - Principais especificações técnicas\n"
                    "    - Prazo de entrega (se mencionado)\n"
                    "    - Valor estimado (se mencionado)\n\n"
                    f"DOCUMENTO:\n{text_for_summary}"
                ),
                agent=summary_agent,
                expected_output="Resumo do documento em português",
                input=text_for_summary
            )

            justification_task = Task(
                description=f"""Forneça uma justificativa clara para a decisão tomada.
                Se o documento não for relevante, explique por quê.
                Se a quantidade não atender ao threshold de {threshold}, explique por quê.
                A justificativa DEVE ser baseada APENAS no conteúdo do documento fornecido.
                NÃO gere uma justificativa genérica ou teórica.
                NÃO inclua nenhum texto em inglês.
                NÃO inclua nenhum texto explicativo antes ou depois da justificativa.
                NÃO retorne 'Thought:', 'Final Answer:' ou qualquer outro prefixo.
                A resposta DEVE ser APENAS a justificativa em português, sem nenhum texto adicional.

                DOCUMENTO:
                {text_for_summary}""",
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
                    threshold_status = "true"
                    threshold_match = True

                # threshold_match deve ser sempre 'true', 'false' ou 'inconclusive' (string)
                threshold_match_str = threshold_status if is_device else "true"
                # target_match deve ser booleano
                target_match_bool = bool(target_response["match"])

                # Corrigir threshold_match para 'false' se threshold não for atingido
                if not threshold_match and is_device:
                    threshold_match_str = "false"

                # Justificativa só se não houver match ou threshold_match não for 'true'
                justification_out = ""
                if not target_match_bool or threshold_match_str in ["false", "inconclusive"]:
                    justification_out = justification

                return {
                    "target_match": target_match_bool,
                    "threshold_match": threshold_match_str,
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
