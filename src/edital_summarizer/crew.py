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
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_retries": 2,
                "retry_delay": 5,
                "timeout": 30,
                "max_tokens": 500,  # Limitar tokens para metadados
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
    def executive_summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["executive_summary_agent"],
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

    @agent
    def technical_summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_summary_agent"],
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

    @agent
    def document_type_agent(self) -> Agent:
        """Agente especializado em identificar o tipo de documento."""
        return Agent(
            role="Especialista em Classificação de Documentos",
            goal="Identificar o tipo e propósito de documentos de licitação",
            backstory="""Você é um especialista em classificação de documentos de licitação.
            Sua função é analisar o conteúdo do documento e identificar seu tipo e propósito.
            Você deve classificar documentos em categorias como:
            - Edital de Licitação
            - Termo de Referência
            - Projeto Básico
            - Projeto Executivo
            - Anexo Técnico
            - Outros documentos relacionados""",
            verbose=True,
            allow_delegation=False,
            tools=[DocumentSearchTool()],
            llm_config={
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.2,
                "max_retries": 2,
                "retry_delay": 5,
                "timeout": 30,
            },
        )

    def process_document(
        self,
        document_path: str,
        output_file: str,
        verbose: bool = False,
        ignore_metadata: bool = False,
        full_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Processa um documento ou diretório de documentos.

        Args:
            document_path: Caminho para o documento ou diretório
            output_file: Arquivo de saída (Excel)
            verbose: Se True, exibe logs detalhados
            ignore_metadata: Se True, ignora os metadados existentes
            full_content: Se True, processa o conteúdo completo do documento

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
                if not full_content:
                    print("Modo de processamento: Conteúdo limitado (otimizado para testes)")
                else:
                    print("Modo de processamento: Conteúdo completo")

            # Primeiro, identificar o tipo do documento
            document_type_task = Task(
                description=f"""
Analise o documento e identifique seu tipo e propósito. O documento deve ser classificado em uma das seguintes categorias:
- Edital de Licitação
- Termo de Referência
- Projeto Básico
- Projeto Executivo
- Anexo Técnico
- Outros documentos relacionados

DOCUMENTO:
{document_content[:5000]}  # Primeiros 5000 caracteres para análise inicial

Forneça sua resposta no seguinte formato:
TIPO: [tipo do documento]
PROPÓSITO: [breve descrição do propósito do documento]
""",
                expected_output="Identificação do tipo e propósito do documento",
                agent=self.document_type_agent(),
            )

            # Criar um crew temporário para identificar o tipo do documento
            type_crew = Crew(
                agents=[self.document_type_agent()],
                tasks=[document_type_task],
                verbose=verbose,
                process=Process.sequential,
            )

            try:
                type_result = type_crew.kickoff()
                document_type = "Não identificado"
                document_purpose = "Não identificado"
                
                # Log detalhado do type_result
                print("\n=== DEBUG: Análise do type_result ===")
                print(f"Tipo do type_result: {type(type_result)}")
                print(f"Conteúdo do type_result: {type_result}")
                
                # Extrair tipo e propósito do resultado
                if isinstance(type_result, str):
                    print("\n=== DEBUG: Processando type_result como string ===")
                    for line in type_result.split('\n'):
                        print(f"Linha processada: {line}")
                        if line.startswith('TIPO:'):
                            document_type = line.replace('TIPO:', '').strip()
                            print(f"Tipo encontrado: {document_type}")
                        elif line.startswith('PROPÓSITO:'):
                            document_purpose = line.replace('PROPÓSITO:', '').strip()
                            print(f"Propósito encontrado: {document_purpose}")
                else:
                    # Se não for string, tentar extrair do objeto CrewOutput
                    print("\n=== DEBUG: Processando type_result como objeto ===")
                    # Primeiro tenta acessar diretamente o conteúdo
                    content = str(type_result)
                    for line in content.split('\n'):
                        print(f"Linha processada: {line}")
                        if line.startswith('TIPO:'):
                            document_type = line.replace('TIPO:', '').strip()
                            print(f"Tipo encontrado: {document_type}")
                        elif line.startswith('PROPÓSITO:'):
                            document_purpose = line.replace('PROPÓSITO:', '').strip()
                            print(f"Propósito encontrado: {document_purpose}")

                if verbose:
                    print(f"\n=== Valores finais ===")
                    print(f"Tipo do documento identificado: {document_type}")
                    print(f"Propósito: {document_purpose}")

                # Garantir que o tipo e propósito não sejam vazios
                if not document_type or document_type == "":
                    document_type = "Não identificado"
                if not document_purpose or document_purpose == "":
                    document_purpose = "Não identificado"

                print("\n=== Valores após validação ===")
                print(f"Tipo do documento final: {document_type}")
                print(f"Propósito final: {document_purpose}")

                # Continuar com o processamento normal, agora com informação do tipo do documento
                if has_metadata:
                    if existing_metadata:
                        if verbose:
                            print("Metadados encontrados no arquivo JSON, pulando extração de metadados")

                        # Preparar inputs simplificados para resumos
                        inputs = {
                            "document_text": document_content,
                            "metadata": json.dumps(existing_metadata),
                            "file_path": file_path,
                            "document_type": document_type,
                            "document_purpose": document_purpose,
                        }

                        # Executar o crew apenas para gerar resumos
                        try:
                            # Limitamos o tamanho do conteúdo para evitar exceder o contexto
                            max_content_length = None if full_content else 4000
                            truncated_content = document_content
                            if not full_content and len(document_content) > max_content_length:
                                truncated_content = document_content[:max_content_length]
                                truncated_content += f"\n\n[Texto truncado em {max_content_length} caracteres]"

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

TIPO DO DOCUMENTO: {document_type}
PROPÓSITO: {document_purpose}

CONTEÚDO DO DOCUMENTO:
{truncated_content}

METADADOS:
{json.dumps(existing_metadata, indent=2)}

IMPORTANTE: 
1. Seu resultado DEVE seguir EXATAMENTE este formato:

# RESUMO EXECUTIVO
(conteúdo do resumo executivo aqui)

# RESUMO TÉCNICO
(conteúdo do resumo técnico aqui)

2. NÃO inclua nenhum texto explicativo antes ou depois dos resumos.
3. NÃO inclua o texto "Given the complexity..." ou qualquer outro texto em inglês.
4. Mantenha os resumos em português.
5. Mantenha os resumos SEPARADOS, não os concatene.
6. NÃO inclua os cabeçalhos "RESUMO EXECUTIVO:" ou "RESUMO TÉCNICO:" no texto dos resumos.
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
                            if "# RESUMO EXECUTIVO" in summary_output and "# RESUMO TÉCNICO" in summary_output:
                                parts = summary_output.split("# RESUMO TÉCNICO", 1)
                                executive_part = parts[0].strip()
                                technical_part = parts[1].strip() if len(parts) > 1 else ""

                                # Remover cabeçalho do resumo executivo e qualquer texto em inglês
                                executive_summary = executive_part.replace("# RESUMO EXECUTIVO", "").strip()
                                # Remover texto em inglês do início
                                if executive_summary.lower().startswith("given the"):
                                    executive_summary = executive_summary.split("\n\n", 1)[-1]
                                technical_summary = technical_part.strip()

                                print(f"RESUMO EXECUTIVO EXTRAÍDO: {executive_summary[:100]}...")
                                print(f"RESUMO TÉCNICO EXTRAÍDO: {technical_summary[:100]}...")
                            else:
                                print("AVISO: Não foi possível separar os resumos executivo e técnico.")

                            # Adicionar resultados
                            result = {
                                "file_name": doc.get("file_name", ""),
                                "file_path": file_path,
                                "metadata": existing_metadata,
                                "document_type": document_type,
                                "document_purpose": document_purpose,
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
                                "document_type": document_type if document_type else "Não identificado",
                                "document_purpose": document_purpose if document_purpose else "Não identificado",
                                "executive_summary": executive_summary,
                                "technical_summary": technical_summary,
                            }

                            # Garantir que o tipo e propósito do documento estejam presentes
                            if not result["document_type"]:
                                result["document_type"] = "Não identificado"
                            if not result["document_purpose"]:
                                result["document_purpose"] = "Não identificado"

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
                else:
                    # Adicionar resultados
                    result = {
                        "file_name": doc.get("file_name", ""),
                        "file_path": file_path,
                        "metadata": existing_metadata,
                        "document_type": document_type if document_type else "Não identificado",
                        "document_purpose": document_purpose if document_purpose else "Não identificado",
                        "executive_summary": "",
                        "technical_summary": "",
                    }

                    # Garantir que o tipo e propósito do documento estejam presentes
                    if not result["document_type"]:
                        result["document_type"] = "Não identificado"
                    if not result["document_purpose"]:
                        result["document_purpose"] = "Não identificado"

                    results.append(result)
            except Exception as e:
                if verbose:
                    print(f"Erro ao identificar o tipo do documento: {str(e)}")
                results.append(
                    {
                        "file_name": doc.get("file_name", ""),
                        "file_path": file_path,
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
