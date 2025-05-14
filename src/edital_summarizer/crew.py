from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
import json

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .processors.document import DocumentProcessor
from .reports.excel import ExcelReportGenerator
from .config.agents import get_agents
from .config.tasks import get_tasks
from .utils.logger import get_logger

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

logger = get_logger(__name__)

@CrewBase
class EditalSummarizer:
    """EditalSummarizer crew otimizado para processamento de editais de licitação"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.agents_config = get_agents()
        self.tasks_config = get_tasks()
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

    def kickoff(self, document_path: str, target: str, threshold: int = 500) -> dict:
        """Inicia o processamento do documento."""
        try:
            print("\n=== Iniciando processamento do documento ===")
            print(f"Documento: {document_path}")
            print(f"Target: {target}")
            print(f"Threshold: {threshold}")

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

            # Cria a crew
            print("\n=== Criando crew ===")
            crew = Crew(
                agents=[target_analyst, summary_agent, justification_agent],
                tasks=[target_analysis_task, summary_task, justification_task],
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
            
            # Primeira tarefa é a análise de target
            target_match = False
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
            summary = ""
            if len(task_outputs) > 1:  # Removida a condição de target_match
                summary = str(task_outputs[1])
                print(f"Resumo gerado: {summary[:200]}...")
            
            # Terceira tarefa é a justificativa
            justification = ""
            if not target_match and len(task_outputs) > 2:
                justification = str(task_outputs[2])
                print(f"Justificativa gerada: {justification[:200]}...")

            print(f"\nResultado final do processamento:")
            print(f"- Target Match: {target_match}")
            print(f"- Tamanho do resumo: {len(summary)} caracteres")
            print(f"- Tamanho da justificativa: {len(justification)} caracteres")

            # Verifica se o resumo gerado é válido
            if not summary:
                print("\nResumo inválido gerado")
                summary = "Não foi possível gerar um resumo válido para o documento."

            # Verifica se o documento realmente é relevante
            if target_match and not any(keyword in combined_content.lower() for keyword in ['rpa', 'automação', 'processo', 'robotizado', 'automatizado']):
                print("\nDocumento não contém palavras-chave relevantes")
                target_match = False
                justification = "O documento não contém referências a RPA, automação de processos ou termos relacionados."

            # Se o documento for uma cotação ou formulário administrativo, não é relevante
            if any(keyword in combined_content.lower() for keyword in ['cotação', 'solicitação', 'formulário', 'processo de compra']):
                print("\nDocumento é uma cotação ou formulário administrativo")
                target_match = False
                justification = "O documento é uma solicitação de cotação ou formulário administrativo, não contendo conteúdo relevante sobre RPA ou automação de processos."

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
