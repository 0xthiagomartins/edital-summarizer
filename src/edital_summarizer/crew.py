from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import json
import yaml

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .processors.document import DocumentProcessor
from .utils.logger import get_logger

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

    @agent
    def target_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["target_analyst_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
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

    def kickoff(self, document_path: str, target: str, threshold: int = 500, force_match: bool = False) -> dict:
        """Inicia o processamento do documento."""
        try:
            print("\n=== Iniciando processamento do documento ===")
            print(f"Documento: {document_path}")
            print(f"Target: {target}")
            print(f"Threshold: {threshold}")
            print(f"Force Match: {force_match}")

            # Processa o documento
            print("\n=== Processando documento ===")
            document_data = self.processor.process_path(document_path)
            print(f"Tipo de document_data: {type(document_data)}")
            print(f"Chaves em document_data: {document_data.keys() if isinstance(document_data, dict) else 'N/A'}")
            
            # Obtém o conteúdo combinado dos documentos
            combined_content = ""
            if document_data.get('documents'):
                print("\n=== Processando documentos ===")
                for doc in document_data['documents']:
                    print(f"\nDocumento encontrado:")
                    print(f"- Tipo: {type(doc)}")
                    print(f"- Chaves: {doc.keys() if isinstance(doc, dict) else 'N/A'}")
                    if doc.get('content'):
                        print(f"- Tamanho do conteúdo: {len(doc['content'])} caracteres")
                        combined_content += f"\n\n=== {doc.get('file_name', 'Unknown')} ===\n\n"
                        combined_content += doc['content']
            
            print(f"\nTamanho total do conteúdo combinado: {len(combined_content)} caracteres")
            
            if not combined_content:
                print("\nNenhum conteúdo encontrado nos documentos")
                return {
                    "target_match": False,
                    "threshold_match": False,
                    "target_summary": "",
                    "document_summary": "",
                    "justification": "Não foi possível encontrar conteúdo nos documentos fornecidos.",
                    "metadata": {}
                }

            # Cria os agentes
            print("\n=== Criando agentes ===")
            target_analyst = Agent(
                role=self.agents_config["target_analyst_agent"]["role"],
                goal=self.agents_config["target_analyst_agent"]["goal"],
                backstory=self.agents_config["target_analyst_agent"]["backstory"],
                verbose=True
            )
            print(f"Agente target_analyst criado: {type(target_analyst)}")

            summary_agent = Agent(
                role=self.agents_config["summary_agent"]["role"],
                goal=self.agents_config["summary_agent"]["goal"],
                backstory=self.agents_config["summary_agent"]["backstory"],
                verbose=True
            )
            print(f"Agente summary_agent criado: {type(summary_agent)}")

            justification_agent = Agent(
                role=self.agents_config["justification_agent"]["role"],
                goal=self.agents_config["justification_agent"]["goal"],
                backstory=self.agents_config["justification_agent"]["backstory"],
                verbose=True
            )
            print(f"Agente justification_agent criado: {type(justification_agent)}")

            # Cria as tarefas
            print("\n=== Criando tarefas ===")
            tasks = []
            
            # Se não for force_match, adiciona a tarefa de análise de target
            if not force_match:
                target_analysis_task = Task(
                    description=self.tasks_config["target_analysis_task"]["description"].format(
                        target=target,
                        document_content=combined_content
                    ),
                    expected_output=self.tasks_config["target_analysis_task"]["expected_output"],
                    agent=target_analyst
                )
                print(f"Tarefa target_analysis_task criada: {type(target_analysis_task)}")
                print(f"Configuração da tarefa:")
                print(f"- Descrição: {target_analysis_task.description[:100]}...")
                print(f"- Expected Output: {target_analysis_task.expected_output}")
                tasks.append(target_analysis_task)

            # Adiciona a tarefa de resumo
            summary_task = Task(
                description=self.tasks_config["summary_task"]["description"].format(
                    target=target,
                    document_content=combined_content
                ),
                expected_output=self.tasks_config["summary_task"]["expected_output"],
                agent=summary_agent
            )
            print(f"Tarefa summary_task criada: {type(summary_task)}")
            print(f"Configuração da tarefa:")
            print(f"- Descrição: {summary_task.description[:100]}...")
            print(f"- Expected Output: {summary_task.expected_output}")
            tasks.append(summary_task)

            # Se não for force_match, adiciona a tarefa de justificativa
            if not force_match:
                justification_task = Task(
                    description=self.tasks_config["justification_task"]["description"].format(
                        target=target,
                        document_content=combined_content
                    ),
                    expected_output=self.tasks_config["justification_task"]["expected_output"],
                    agent=justification_agent
                )
                print(f"Tarefa justification_task criada: {type(justification_task)}")
                print(f"Configuração da tarefa:")
                print(f"- Descrição: {justification_task.description[:100]}...")
                print(f"- Expected Output: {justification_task.expected_output}")
                tasks.append(justification_task)

            # Cria a crew
            print("\n=== Criando crew ===")
            crew = Crew(
                agents=[target_analyst, summary_agent, justification_agent],
                tasks=tasks,
                verbose=True
            )
            print(f"Crew criada: {type(crew)}")

            # Executa a crew
            print("\n=== Executando crew ===")
            result = crew.kickoff()
            print(f"Tipo do resultado: {type(result)}")
            print(f"Conteúdo do resultado: {result}")

            # Processa o resultado
            print("\n=== Processando resultado ===")
            # O resultado vem como uma lista de outputs das tarefas
            task_outputs = result.tasks_output if hasattr(result, 'tasks_output') else []
            print(f"Outputs das tarefas: {task_outputs}")
            
            # Se for force_match, define target_match como True
            target_match = force_match
            summary = ""
            justification = ""

            if force_match:
                # Em modo force_match, apenas pega o resumo
                if len(task_outputs) > 0:
                    summary = str(task_outputs[0])
            else:
                # Processamento normal
                if len(task_outputs) > 0:
                    target_response = str(task_outputs[0]).strip().lower()
                    print(f"Resposta do analista de target: '{target_response}'")
                    
                    # Validação mais rigorosa da resposta
                    if target_response not in ['true', 'false']:
                        print(f"Resposta inválida do analista de target: '{target_response}'")
                        target_match = False
                    else:
                        target_match = target_response == 'true'
                    
                    print(f"Target Match após processamento: {target_match}")
                
                # Segunda tarefa é o resumo
                if len(task_outputs) > 1:
                    summary = str(task_outputs[1])
                
                # Terceira tarefa é a justificativa
                if not target_match and len(task_outputs) > 2:
                    justification = str(task_outputs[2])

            print(f"\nResultado final do processamento:")
            print(f"- Target Match: {target_match}")
            print(f"- Tamanho do resumo: {len(summary)} caracteres")
            print(f"- Tamanho da justificativa: {len(justification)} caracteres")

            # Verifica se o resumo gerado é válido
            if not summary:
                print("\nResumo inválido gerado")
                summary = "Não foi possível gerar um resumo válido para o documento."

            final_result = {
                "target_match": target_match,
                "threshold_match": True,  # Mantido para compatibilidade
                "target_summary": summary,  # Sempre inclui o resumo
                "document_summary": summary,  # Sempre inclui o resumo
                "justification": justification if not target_match else "",
                "metadata": {}
            }
            print("\n=== Resultado final ===")
            print(f"Tipo do resultado final: {type(final_result)}")
            print(f"Chaves no resultado final: {final_result.keys()}")
            return final_result

        except Exception as e:
            logger.error(f"Erro ao processar documento: {str(e)}")
            print(f"\n=== Erro durante o processamento ===")
            print(f"Tipo do erro: {type(e)}")
            print(f"Mensagem do erro: {str(e)}")
            return {
                "target_match": False,
                "threshold_match": False,
                "target_summary": "",
                "document_summary": "",
                "justification": f"Erro ao processar documento: {str(e)}",
                "metadata": {}
            }
