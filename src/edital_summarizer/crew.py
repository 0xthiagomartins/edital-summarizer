from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any, Optional, Union
import os
import json

from .tools.file_tools import SimpleFileReadTool
from .tools.document_tools import DocumentSearchTool, TableExtractionTool
from .processors.document import DocumentProcessor
from .reports.excel import ExcelReportGenerator

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class EditalSummarizer:
    """EditalSummarizer crew otimizado para processamento de editais de licitação"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def metadata_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["metadata_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=True,
            llm_config={
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.1,
            },  # Usar Gemini Pro para metadados
        )

    @agent
    def summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
            verbose=True,
            llm_config={
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.3,
            },  # Usar Gemini Pro para resumos
        )

    @agent
    def executive_summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool()],
            verbose=True,
            llm_config={
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.3,
            },
        )

    @agent
    def technical_summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_summary_agent"],
            tools=[SimpleFileReadTool(), DocumentSearchTool(), TableExtractionTool()],
            verbose=True,
            llm_config={
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.3,
            },
        )

    @task
    def metadata_task(self) -> Task:
        return Task(
            config=self.tasks_config["metadata_task"],  # type: ignore[index]
        )

    @task
    def summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["summary_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Define the crew for processing editais."""
        return Crew(
            agents=[
                self.metadata_agent(),
                self.summary_agent(),
            ],
            tasks=[
                self.metadata_task(),
                self.summary_task(),
            ],
            verbose=True,
            process=Process.sequential,  # Sequencial para controle
        )

    def process_document(
        self,
        document_path: str,
        output_file: str,
        verbose: bool = False,
        ignore_metadata: bool = False,
    ) -> Dict[str, Any]:
        """
        Processa um documento ou diretório de documentos.

        Args:
            document_path: Caminho para o documento ou diretório
            output_file: Arquivo de saída (Excel)
            verbose: Se True, exibe logs detalhados
            ignore_metadata: Se True, ignora os metadados existentes

        Returns:
            Dicionário com resultados do processamento
        """
        # Processar o documento/diretório
        processor = DocumentProcessor()
        document_data = processor.process_path(document_path)

        results = []

        # Para cada documento encontrado
        documents = document_data.get("documents", [document_data])
        for doc in documents:
            document_content = doc.get("content", "")
            has_metadata = doc.get("has_metadata_file", False) and not ignore_metadata
            existing_metadata = doc.get("metadata", {})
            file_path = doc.get("file_path", "")

            if verbose:
                print(f"Processando documento: {doc.get('file_name', 'unknown')}")
                print(f"Tamanho do conteúdo: {len(document_content)} caracteres")
                if has_metadata:
                    print(f"Usando metadados do arquivo metadata.json")

            # Se já temos os metadados, só precisamos dos resumos
            if has_metadata and existing_metadata:
                if verbose:
                    print(
                        "Metadados encontrados no arquivo JSON, pulando extração de metadados"
                    )

                # Preparar inputs simplificados para resumos
                inputs = {
                    "document_text": document_content,
                    "metadata": json.dumps(existing_metadata),
                    "file_path": file_path,
                }

                # Executar o crew apenas para gerar resumos
                try:
                    # Limitamos o tamanho do conteúdo para evitar exceder o contexto
                    max_content_length = 4000
                    truncated_content = document_content[:max_content_length]
                    if len(document_content) > max_content_length:
                        truncated_content += (
                            f"\n\n[Texto truncado em {max_content_length} caracteres]"
                        )

                    # Usar o summary_agent em vez de executive_summary_agent e technical_summary_agent
                    summary_task = Task(
                        description=f"""
Com base no documento do edital e nos metadados fornecidos, crie:

1. Um RESUMO EXECUTIVO conciso (máximo 10.000 caracteres) destacando os 
   pontos-chave para tomadores de decisão, incluindo objeto, prazos, valores 
   e requisitos principais.
   
2. Um RESUMO TÉCNICO detalhado (máximo 15.000 caracteres) com as especificações
   técnicas relevantes, requisitos, condições de entrega/execução e outras
   informações técnicas importantes.

CONTEÚDO DO DOCUMENTO:
{truncated_content}

METADADOS:
{json.dumps(existing_metadata, indent=2)}

IMPORTANTE: Seu resultado DEVE seguir EXATAMENTE este formato:

# RESUMO EXECUTIVO
(conteúdo do resumo executivo aqui)

# RESUMO TÉCNICO
(conteúdo do resumo técnico aqui)
""",
                        expected_output="Um documento markdown com as duas seções de resumo claramente separadas.",
                        agent=self.summary_agent(),
                    )

                    # Criamos um crew menor apenas com o agente de resumo
                    crew = Crew(
                        agents=[self.summary_agent()],
                        tasks=[summary_task],
                        verbose=verbose,
                        process=Process.sequential,
                    )

                    crew_result = crew.kickoff(inputs=inputs)

                    # Processar o resultado para extrair os resumos
                    summary_output = ""

                    # Adicionar log para entender o tipo e a estrutura do crew_result
                    print(f"Tipo do crew_result: {type(crew_result)}")
                    print(f"Atributos disponíveis: {dir(crew_result)}")

                    # Tentar diferentes formas de acessar o output
                    try:
                        # Tentar acessar através do atributo tasks_output
                        if hasattr(crew_result, "tasks_output"):
                            print("Acessando via tasks_output")
                            task_output = crew_result.tasks_output[0]
                            print(f"Tipo do task_output: {type(task_output)}")
                            print(f"Atributos do task_output: {dir(task_output)}")

                            # Tentar vários atributos possíveis
                            if hasattr(task_output, "result"):
                                summary_output = task_output.result
                            elif hasattr(task_output, "content"):
                                summary_output = task_output.content
                            elif hasattr(task_output, "task_output"):
                                summary_output = task_output.task_output
                            elif hasattr(task_output, "final_answer"):
                                summary_output = task_output.final_answer
                            elif hasattr(task_output, "value"):
                                summary_output = task_output.value
                            else:
                                # Último recurso - converter para string
                                summary_output = str(task_output)
                    except Exception as e:
                        print(f"Erro ao acessar o output: {str(e)}")
                        summary_output = ""

                    print(f"RESUMO EXTRAÍDO: {summary_output[:100]}...")

                    # Separar os resumos
                    executive_summary = ""
                    technical_summary = ""
                    if (
                        "# RESUMO EXECUTIVO" in summary_output
                        and "# RESUMO TÉCNICO" in summary_output
                    ):
                        parts = summary_output.split("# RESUMO TÉCNICO", 1)
                        executive_part = parts[0].strip()
                        technical_part = parts[1].strip() if len(parts) > 1 else ""

                        # Remover cabeçalho do resumo executivo
                        executive_summary = executive_part.replace(
                            "# RESUMO EXECUTIVO", ""
                        ).strip()
                        technical_summary = technical_part.strip()

                        print(
                            f"RESUMO EXECUTIVO EXTRAÍDO: {executive_summary[:100]}..."
                        )
                        print(f"RESUMO TÉCNICO EXTRAÍDO: {technical_summary[:100]}...")
                    else:
                        print(
                            "AVISO: Não foi possível separar os resumos executivo e técnico."
                        )

                    # Adicionar resultados
                    result = {
                        "file_name": doc.get("file_name", ""),
                        "file_path": file_path,
                        "metadata": existing_metadata,
                        "executive_summary": executive_summary,
                        "technical_summary": technical_summary,
                    }

                    results.append(result)

                except Exception as e:
                    if verbose:
                        print(f"Erro ao processar resumos: {str(e)}")
                    results.append(
                        {
                            "file_name": doc.get("file_name", ""),
                            "file_path": file_path,
                            "metadata": existing_metadata,
                            "error": str(e),
                        }
                    )
            else:
                # Processamento completo com extração de metadados
                if verbose:
                    print(
                        "Nenhum arquivo de metadados encontrado, extraindo metadados via IA"
                    )

                # Preparar inputs para o processamento completo
                inputs = {
                    "document_content": document_content,
                    "identifier_task": {"document_text": document_content},
                    "organization_task": {"document_text": document_content},
                    "subject_task": {"document_text": document_content},
                    "executive_summary": {"document_text": document_content},
                    "technical_summary": {"document_text": document_content},
                }

                # Executar o crew completo
                try:
                    crew_result = self.crew().kickoff(inputs=inputs)

                    # Consolidar metadados
                    metadata = {}
                    for task_result in crew_result:
                        if task_result.task_id == "metadata_task":
                            metadata = task_result.output

                    # Extrair resumos do resultado da tarefa de resumo
                    summary_output = ""
                    for task_result in crew_result:
                        if task_result.task_id == "summary_task":
                            summary_output = task_result.output

                    # Separar os resumos
                    executive_summary = ""
                    technical_summary = ""
                    if (
                        "# RESUMO EXECUTIVO" in summary_output
                        and "# RESUMO TÉCNICO" in summary_output
                    ):
                        parts = summary_output.split("# RESUMO TÉCNICO", 1)
                        executive_part = parts[0].strip()
                        technical_part = parts[1].strip() if len(parts) > 1 else ""

                        # Remover cabeçalho do resumo executivo
                        executive_summary = executive_part.replace(
                            "# RESUMO EXECUTIVO", ""
                        ).strip()
                        technical_summary = technical_part.strip()

                    # Adicionar resultados
                    result = {
                        "file_name": doc.get("file_name", ""),
                        "file_path": doc.get("file_path", ""),
                        "metadata": metadata,
                        "executive_summary": executive_summary,
                        "technical_summary": technical_summary,
                    }

                    results.append(result)

                except Exception as e:
                    if verbose:
                        print(f"Erro ao processar documento: {str(e)}")
                    results.append(
                        {
                            "file_name": doc.get("file_name", ""),
                            "file_path": doc.get("file_path", ""),
                            "error": str(e),
                        }
                    )

        # Gerar relatório Excel
        report_generator = ExcelReportGenerator()
        report_generator.generate_report(results, output_file)

        if verbose:
            print(f"Relatório gerado em: {output_file}")

        return {
            "document_path": document_path,
            "output_file": output_file,
            "documents_processed": len(results),
            "results": results,
        }
