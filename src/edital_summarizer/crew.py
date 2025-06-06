from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent
from typing import Dict, Any
import os, yaml, json, traceback, re, time
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .utils.logger import get_logger

RATE_LIMIT_CONFIG = {
    "requests_per_minute": 450,  # 10% abaixo do limite de 500 RPM
    "tokens_per_minute": 25000,  # 17% abaixo do limite de 30,000 TPM
    "shared": True,  # Indica que o limite é compartilhado entre todos os agentes
    "chunk_size": 15000,  # Tamanho máximo de cada chunk em caracteres
    "chunk_overlap": 1000  # Sobreposição entre chunks para manter contexto
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

def split_text_into_chunks(text: str, chunk_size: int = 15000, overlap: int = 1000) -> list[str]:
    """Divide o texto em chunks menores com sobreposição."""
    try:
        logger.info(f"Iniciando split_text_into_chunks com tamanho do texto: {len(text)}")
        logger.info(f"Parâmetros: chunk_size={chunk_size}, overlap={overlap}")
        
        if not text:
            logger.info("Texto vazio recebido")
            return []
            
        if not isinstance(text, str):
            logger.info(f"Tipo de texto inválido: {type(text)}")
            raise ValueError(f"Texto deve ser string, recebido {type(text)}")
            
        chunks = []
        start = 0
        text_length = len(text)
        
        logger.info(f"Tamanho total do texto: {text_length}")
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Se este for o último chunk, não precisa procurar por quebra natural
            if end == text_length:
                chunk = text[start:end]
                logger.info(f"Último chunk criado: posição {start} até {end}, tamanho {len(chunk)}")
                chunks.append(chunk)
                break
            
            # Tenta encontrar um ponto de quebra natural (fim de parágrafo)
            last_period = text.rfind('.', start, end)
            if last_period != -1 and last_period > start + chunk_size // 2:
                end = last_period + 1
                logger.info(f"Quebra natural encontrada na posição {last_period}")
            
            chunk = text[start:end]
            logger.info(f"Chunk criado: posição {start} até {end}, tamanho {len(chunk)}")
            chunks.append(chunk)
            
            # Calcula a próxima posição de início, garantindo que avance
            next_start = end - overlap
            if next_start <= start:
                next_start = start + 1  # Garante que avance pelo menos 1 caractere
            start = next_start
            logger.info(f"Próximo chunk começará na posição {start}")
        
        logger.info(f"Total de chunks criados: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1}: tamanho {len(chunk)}")
        
        return chunks
        
    except Exception as e:
        logger.info(f"Erro em split_text_into_chunks: {str(e)}")
        logger.info(f"Stack trace:\n{traceback.format_exc()}")
        raise

logger = get_logger(__name__)

@CrewBase
class EditalSummarizer:
    """EditalSummarizer crew otimizado para processamento de editais de licitação"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.agents_config = load_yaml_config(os.path.join(base_dir, 'config', 'agents.yaml'))
        self.tasks_config = load_yaml_config(os.path.join(base_dir, 'config', 'tasks.yaml'))
        
        # Verifica a configuração da API
        if not os.getenv("OPENAI_API_KEY"):
            logger.info("OPENAI_API_KEY não definida no ambiente")
            raise ValueError("OPENAI_API_KEY não definida no ambiente")
        
        logger.info("Configuração da API verificada com sucesso")

    def _create_knowledge_base(self, edital_path_dir: str) -> list:
        """Cria a base de conhecimento a partir dos arquivos do edital."""
        try:
            logger.info(f"Criando base de conhecimento para: {edital_path_dir}")
            knowledge_sources = []
            
            # Lista os arquivos no diretório
            for root, _, filenames in os.walk(edital_path_dir):
                for file in filenames:
                    file_path = os.path.abspath(os.path.join(root, file))
                    
                    if file.lower().endswith('.pdf'):
                        logger.info(f"Adicionando PDF à base de conhecimento: {file_path}")
                        knowledge_sources.append(PDFKnowledgeSource(file_paths=[file_path]))
                    elif file.lower().endswith('.json'):
                        logger.info(f"Adicionando JSON à base de conhecimento: {file_path}")
                        knowledge_sources.append(JSONKnowledgeSource(file_paths=[file_path]))
            
            logger.info(f"Base de conhecimento criada com {len(knowledge_sources)} fontes")
            return knowledge_sources
            
        except Exception as e:
            logger.info(f"Erro ao criar base de conhecimento: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            raise

    @agent
    def knowledge_builder_agent(self) -> Agent:
        """Agente responsável por construir a base de conhecimento."""
        try:
            logger.info("Criando knowledge_builder_agent...")
            llm_config = {
                **BASE_LLM_CONFIG,
                "temperature": 0.1,
                "timeout": 60,
                "max_tokens": 1000,
                "request_timeout": 120
            }
            
            agent = Agent(
                role="Construtor de Base de Conhecimento",
                goal="Construir uma base de conhecimento estruturada a partir dos documentos do edital",
                backstory="""Você é um especialista em processamento de documentos e construção de bases de conhecimento.
                Sua função é analisar os documentos do edital e estruturar as informações de forma que possam ser facilmente consultadas.""",
                verbose=True,
                llm_config=llm_config,
                tools=[SimpleFileReadTool(), DocumentSearchTool()]
            )
            logger.info("knowledge_builder_agent criado com sucesso")
            return agent
        except Exception as e:
            logger.info(f"Erro ao criar knowledge_builder_agent: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            raise

    @agent
    def target_analyst_agent(self) -> Agent:
        """Create target analyst agent."""
        try:
            logger.info("Criando target_analyst_agent...")
            llm_config = {
                **BASE_LLM_CONFIG,
                "temperature": 0.1,
                "timeout": 30,
                "max_tokens": 500,
                "request_timeout": 60
            }
            
            agent = Agent(
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
                tools=[SimpleFileReadTool(), DocumentSearchTool()]
            )
            logger.info("target_analyst_agent criado com sucesso")
            return agent
        except Exception as e:
            logger.info(f"Erro ao criar target_analyst_agent: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            raise

    @agent
    def summary_agent(self) -> Agent:
        try:
            logger.info("Criando summary_agent...")
            llm_config = {
                **BASE_LLM_CONFIG,
                "temperature": 0.3,
                "timeout": 60,
                "max_tokens": 1000,  # Reduzido para economizar tokens
                "request_timeout": 120
            }
            logger.info(f"Configuração LLM para summary_agent: {llm_config}")
            
            agent = Agent(
                config=self.agents_config["summary_agent"],
                tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
                verbose=True,
                llm_config=llm_config
            )
            logger.info("summary_agent criado com sucesso")
            return agent
        except Exception as e:
            logger.info(f"Erro ao criar summary_agent: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            raise

    @agent
    def justification_agent(self) -> Agent:
        try:
            logger.info("Criando justification_agent...")
            llm_config = {
                **BASE_LLM_CONFIG,
                "temperature": 0.3,
                "timeout": 60,
                "max_tokens": 500,  # Reduzido para economizar tokens
                "request_timeout": 60
            }
            logger.info(f"Configuração LLM para justification_agent: {llm_config}")
            
            agent = Agent(
                config=self.agents_config["justification_agent"],
                tools=[SimpleFileReadTool(), DocumentSearchTool()],
                verbose=True,
                llm_config=llm_config
            )
            logger.info("justification_agent criado com sucesso")
            return agent
        except Exception as e:
            logger.info(f"Erro ao criar justification_agent: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            raise

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
                    logger.info(f"Resposta não é um dicionário: {type(data)}")
                    return False
                    
                target_match = data.get("target_match")
                volume = data.get("volume", 0)
                
                if not isinstance(target_match, bool):
                    logger.info(f"target_match não é um booleano: {type(target_match)}")
                    return False
                    
                if not isinstance(volume, (int, float)):
                    logger.info(f"volume não é um número: {type(volume)}")
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
                logger.info(f"Erro ao decodificar JSON: {str(e)}")
                return False
                
        except Exception as e:
            logger.info(f"Erro ao processar resposta do target analyst: {str(e)}")
            logger.info(f"Stack trace: {traceback.format_exc()}")
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
                logger.info(f"Diretório não encontrado: {edital_path_dir}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
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
                logger.info(f"Nenhum arquivo encontrado em: {edital_path_dir}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
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
                        logger.info(f"Erro ao ler arquivo {file_path}: {file_text}")
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
                    logger.info(f"Primeiros 100 caracteres do arquivo: {file_text[:100]}")
                except Exception as e:
                    logger.info(f"Erro ao processar arquivo {file_path}: {str(e)}")
                    logger.info(f"Stack trace:\n{traceback.format_exc()}")
                    continue
            
            if not text.strip():
                logger.info("Nenhum texto extraído dos arquivos")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
                    "summary": "Erro: Não foi possível extrair texto dos arquivos",
                    "justification": "Não foi possível processar o edital pois não foi possível extrair texto dos arquivos."
                }
            
            # Limpa e normaliza o texto final
            text = text.replace('\x00', '')
            text = re.sub(r'\s+', ' ', text)  # Normaliza espaços
            text = text.strip()
            
            logger.info(f"Texto extraído com sucesso. Tamanho: {len(text)} caracteres")
            logger.info(f"Primeiros 500 caracteres do texto: {text[:500]}")
            
            # Divide o texto em chunks
            try:
                logger.info("Iniciando divisão do texto em chunks...")
                chunks = split_text_into_chunks(
                    text,
                    chunk_size=RATE_LIMIT_CONFIG["chunk_size"],
                    overlap=RATE_LIMIT_CONFIG["chunk_overlap"]
                )
                logger.info(f"Texto dividido em {len(chunks)} chunks")
                for i, chunk in enumerate(chunks):
                    logger.info(f"Chunk {i+1} tamanho: {len(chunk)} caracteres")
            except Exception as e:
                logger.info(f"Erro ao dividir texto em chunks: {str(e)}")
                logger.info(f"Stack trace:\n{traceback.format_exc()}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
                    "summary": f"Erro ao dividir texto em chunks: {str(e)}",
                    "justification": "Ocorreu um erro ao dividir o texto em partes menores para análise."
                }
            
            # Cria o agente de análise
            try:
                logger.info("Criando agente de análise...")
                target_analyst = self.target_analyst_agent()
                logger.info("Agente de análise criado com sucesso")
            except Exception as e:
                logger.info(f"Erro ao criar agente de análise: {str(e)}")
                logger.info(f"Stack trace:\n{traceback.format_exc()}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
                    "summary": f"Erro ao criar agente de análise: {str(e)}",
                    "justification": "Ocorreu um erro ao criar o agente responsável pela análise."
                }
            
            # Processa cada chunk
            target_matches = []
            volumes = []
            
            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"\n=== Processando chunk {i+1}/{len(chunks)} ===")
                    logger.info(f"Tamanho do chunk: {len(chunk)} caracteres")
                    logger.info(f"Primeiros 100 caracteres do chunk: {chunk[:100]}")
                    
                    logger.info("Criando task para o chunk...")
                    analysis_task = Task(
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
                        
                        CONTEÚDO DO DOCUMENTO (Parte {i+1} de {len(chunks)}):
                        {chunk}""",
                        agent=target_analyst,
                        expected_output="JSON com target_match e volume"
                    )
                    logger.info("Task criada com sucesso")
                    
                    # Cria a crew para este chunk
                    logger.info("Criando crew para o chunk...")
                    crew = Crew(
                        agents=[target_analyst],
                        tasks=[analysis_task],
                        verbose=True
                    )
                    logger.info("Crew criada com sucesso")
                    
                    # Executa a crew
                    logger.info("Executando crew...")
                    try:
                        result = crew.kickoff()
                        logger.info("Crew executada com sucesso")
                    except Exception as e:
                        logger.error(f"Erro ao executar crew: {str(e)}")
                        logger.error(f"Stack trace:\n{traceback.format_exc()}")
                        continue
                    
                    # Processa os resultados
                    logger.info("Processando resultados...")
                    try:
                        logger.info(f"Resultado bruto: {result.tasks_output[0].raw}")
                        target_response = json.loads(result.tasks_output[0].raw)
                        target_matches.append(target_response["target_match"])
                        volumes.append(target_response["volume"])
                        logger.info(f"Resultados processados: target_match={target_response['target_match']}, volume={target_response['volume']}")
                    except Exception as e:
                        logger.error(f"Erro ao processar resultados: {str(e)}")
                        logger.error(f"Stack trace:\n{traceback.format_exc()}")
                        continue
                    
                    # Aguarda um pouco para evitar rate limit
                    logger.info("Aguardando 1 segundo para evitar rate limit...")
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar chunk {i+1}: {str(e)}")
                    logger.error(f"Stack trace:\n{traceback.format_exc()}")
                    continue
            
            # Consolida os resultados
            try:
                logger.info("Consolidando resultados...")
                final_target_match = any(target_matches)
                final_volume = max(volumes) if volumes else 0
                logger.info(f"Resultados consolidados: target_match={final_target_match}, volume={final_volume}")
                
                # Se force_match for True, força o target_match
                if force_match:
                    final_target_match = True
                    logger.info("Force match ativado: target_match forçado para True")
                
                # Determina o threshold_match
                if not final_target_match:
                    threshold_match = "false"
                elif not self._is_device_target(target):
                    threshold_match = "true"  # Não verifica threshold para não-dispositivos
                elif threshold == 0:
                    threshold_match = "true"  # Não verifica threshold se threshold = 0
                elif final_volume >= threshold:
                    threshold_match = "true"
                elif final_volume == 0:
                    threshold_match = "inconclusive"  # Não foi possível determinar o volume
                else:
                    threshold_match = "false"
                
                # Determina is_relevant
                is_relevant = False
                if final_target_match:
                    if threshold_match == "true":
                        is_relevant = True
                    elif threshold == 0:  # Não verifica threshold
                        is_relevant = True
                
                # Gera o resumo e justificativa
                summary_agent = self.summary_agent()
                justification_agent = self.justification_agent()
                
                # Cria tasks para resumo e justificativa
                summary_task = Task(
                    description=f"""Gere um resumo detalhado do edital, incluindo:
                    - Objeto da licitação
                    - Quantidades mencionadas
                    - Especificações técnicas relevantes
                    - Prazos e valores
                    - Outras informações importantes
                    
                    CONTEÚDO DO DOCUMENTO:
                    {text}""",
                    agent=summary_agent,
                    expected_output="Resumo detalhado do edital"
                )
                
                justification_task = Task(
                    description=f"""Gere uma justificativa clara e coerente para a decisão de relevância.
                    
                    Target: {target}
                    Threshold: {threshold}
                    Target Match: {final_target_match}
                    Threshold Match: {threshold_match}
                    Is Relevant: {is_relevant}
                    
                    A justificativa deve explicar:
                    - Por que o edital é ou não relevante
                    - Se relevante: destacar os pontos que o tornam relevante
                    - Se não relevante: explicar por que não atende aos critérios
                    - Em caso de threshold: explicar a análise da quantidade
                    
                    CONTEÚDO DO DOCUMENTO:
                    {text}""",
                    agent=justification_agent,
                    expected_output="Justificativa clara e coerente"
                )
                
                # Executa as tasks
                crew = Crew(
                    agents=[summary_agent, justification_agent],
                    tasks=[summary_task, justification_task],
                    verbose=True
                )
                
                result = crew.kickoff()
                summary = result.tasks_output[0].raw
                justification = result.tasks_output[1].raw
                
                return {
                    "target_match": final_target_match,
                    "threshold_match": threshold_match,
                    "is_relevant": is_relevant,
                    "summary": summary,
                    "justification": justification
                }
                
            except Exception as e:
                logger.info(f"Erro ao consolidar resultados: {str(e)}")
                logger.info(f"Stack trace:\n{traceback.format_exc()}")
                return {
                    "target_match": False,
                    "threshold_match": "false",
                    "is_relevant": False,
                    "summary": f"Erro ao consolidar resultados: {str(e)}",
                    "justification": "Ocorreu um erro ao consolidar os resultados da análise."
                }
            
        except Exception as e:
            logger.info(f"Erro ao processar edital: {str(e)}")
            logger.info(f"Stack trace:\n{traceback.format_exc()}")
            return {
                "target_match": False,
                "threshold_match": "false",
                "is_relevant": False,
                "summary": f"Erro ao processar edital: {str(e)}",
                "justification": "Ocorreu um erro ao processar o edital."
            }
