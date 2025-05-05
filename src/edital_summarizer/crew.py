from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from typing import List, Dict, Optional, Any
import yaml
from pathlib import Path
import json
import os
import re
from rich import print as rprint
from .types import SummaryType
from .tools.document_processor import DocumentProcessor
from .tools.rag_tools import DocumentSearchTool, TableExtractionTool
import crewai


# Definir ferramentas usando o decorador @tool
@tool
def read_file(file_path: str) -> str:
    """Lê o conteúdo de arquivos de texto e PDF."""
    try:
        path = Path(file_path)

        # Tentar encontrar o arquivo se não existir no caminho especificado
        if not path.exists():
            # Verificar se é apenas um nome de arquivo (sem diretório)
            if not path.parent or path.parent == Path("."):
                # Tentar encontrar em diretórios comuns
                possible_locations = [
                    Path("samples") / path.name,
                    Path("samples/edital-001") / path.name,
                    Path().cwd() / path.name,
                ]

                for possible_path in possible_locations:
                    if possible_path.exists():
                        path = possible_path
                        break

        if not path.exists():
            return f"Erro: Arquivo não encontrado: {file_path}. Verifique o caminho."

        if path.suffix.lower() == ".pdf":
            # Para PDFs, usamos PyPDFLoader
            from langchain_community.document_loaders import PyPDFLoader

            loader = PyPDFLoader(str(path))
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        else:
            # Para outros arquivos, lemos como texto
            return path.read_text(errors="replace")
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"


@tool
def search_document(query: str, text: str = None, file_path: str = None) -> str:
    """Busca informações específicas dentro de um documento usando RAG."""
    search_tool = DocumentSearchTool()
    return search_tool._run(query, text, file_path)


@tool
def extract_tables(text: str, table_keyword: str = None) -> str:
    """Extrai tabelas de documentos e as retorna em formato estruturado."""
    table_tool = TableExtractionTool()
    return table_tool._run(text, table_keyword)


class DocumentSummarizerCrew:
    """Classe para processar documentos de editais e gerar resumos."""

    def __init__(self, verbose: bool = False):
        self.config_dir = Path(__file__).parent / "config"
        self.verbose = verbose
        self.document_processor = DocumentProcessor(chunk_size=1500, chunk_overlap=150)

        # Verificar versão do CrewAI
        if hasattr(crewai, "__version__"):
            crewai_version = crewai.__version__
            if self.verbose:
                rprint(f"[dim]Usando CrewAI versão: {crewai_version}[/dim]")

        # Carregar configurações
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()

        # Inicializar agentes
        self.agents = self._load_agents()

    def _load_agents_config(self) -> Dict:
        """Carrega configurações de agentes do arquivo YAML."""
        with open(self.config_dir / "agents.yaml", "r") as f:
            return yaml.safe_load(f)

    def _load_tasks_config(self) -> Dict:
        """Carrega configurações de tarefas do arquivo YAML."""
        with open(self.config_dir / "tasks.yaml", "r") as f:
            return yaml.safe_load(f)

    def _load_agents(self) -> Dict[str, Agent]:
        """Cria instâncias de agentes baseados nas configurações."""
        agents = {}

        for name, config in self.agents_config.items():
            # Configurar ferramentas
            tools_list = []
            if "tools" in config:
                for tool_name in config["tools"]:
                    if tool_name == "SimpleFileReadTool":
                        tools_list.append(read_file)
                    elif tool_name == "DocumentSearchTool":
                        tools_list.append(search_document)
                    elif tool_name == "TableExtractionTool":
                        tools_list.append(extract_tables)

            # Configurar modelo de IA com base na tarefa do agente
            if name in ["identifier_agent", "organization_agent", "dates_agent"]:
                model_config = {
                    "llm": "openai",
                    "model_name": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 800,
                }
            elif name in ["technical_summary_agent", "executive_summary_agent"]:
                model_config = {
                    "llm": "gemini",
                    "model_name": "gemini-pro",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                }
            else:
                model_config = {
                    "llm": "gemini",
                    "model_name": "gemini-pro",
                    "temperature": 0.2,
                    "max_tokens": 1000,
                }

            # Criar o agente
            try:
                agent_config = {
                    "role": config["role"],
                    "goal": config["goal"],
                    "backstory": config["backstory"],
                    "verbose": config.get("verbose", self.verbose),
                    "allow_delegation": config.get("allow_delegation", True),
                    "tools": tools_list,
                    **model_config,
                }

                agents[name] = Agent(**agent_config)

                if self.verbose:
                    rprint(
                        f"[green]Agente {name} criado com modelo {model_config['llm']} - {model_config['model_name']}[/green]"
                    )

            except Exception as e:
                if self.verbose:
                    rprint(f"[red]Erro ao criar agente {name}: {str(e)}[/red]")

        return agents

    def _create_task(self, task_name: str, text: str) -> Task:
        """Cria uma tarefa a partir da configuração."""
        if task_name not in self.tasks_config:
            raise ValueError(f"Tarefa não encontrada: {task_name}")

        task_config = self.tasks_config[task_name]
        agent_name = task_config.get("agent")

        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")

        # Substituir placeholders na descrição
        description = task_config["description"]
        if "{text}" in description:
            description = description.replace("{text}", text)
        else:
            description = f"{description}\n\nTEXTO: {text}"

        # Obter o output esperado
        expected_output = task_config["expected_output"]

        # Na versão 0.118.0, o método de execução é run() em vez de execute()
        try:
            task = Task(
                description=description,
                expected_output=expected_output,
                agent=self.agents[agent_name],
                async_execution=False,
            )
            return task
        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro ao criar tarefa {task_name}: {str(e)}[/red]")

            # Tentativa alternativa - formato mais simples possível
            return Task(
                description=description,
                expected_output=expected_output,
                agent=self.agents[agent_name],
            )

    def _extract_json_from_text(self, text: str) -> Dict:
        """Extrai um objeto JSON de um texto."""
        if not text:
            return {}

        try:
            # Procurar por texto entre chaves
            start_idx = text.find("{")
            end_idx = text.rfind("}")

            if start_idx >= 0 and end_idx >= 0 and start_idx < end_idx:
                json_str = text[start_idx : end_idx + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    if self.verbose:
                        rprint(
                            "[yellow]Texto encontrado não é um JSON válido, tentando limpeza...[/yellow]"
                        )
                    # Algumas correções comuns
                    json_str = json_str.replace("'", '"')
                    try:
                        return json.loads(json_str)
                    except:
                        pass

            # Se não conseguir extrair JSON válido, tentar extrair chave-valor
            result = {}
            lines = text.split("\n")
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().strip("\"'")
                    value = parts[1].strip().strip("\"'")
                    if key and value:
                        result[key] = value

            return result

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro ao extrair JSON do texto: {str(e)}[/red]")
            return {}

    def _load_metadata_json(self, file_path: Path) -> Dict:
        """Carrega metadados do arquivo metadata.json correspondente."""
        try:
            # Verificar diferentes possíveis localizações do metadata.json
            possible_locations = [
                file_path.parent / "metadata.json",  # Mesmo diretório
                Path("samples")
                / file_path.stem
                / "metadata.json",  # samples/nome-do-arquivo
                Path("samples")
                / file_path.parent.name
                / "metadata.json",  # samples/diretório-pai
                Path("samples/edital-001") / "metadata.json",  # Local padrão
            ]

            if self.verbose:
                rprint(
                    f"[dim]Procurando metadata.json em: {[str(p) for p in possible_locations]}[/dim]"
                )

            for metadata_path in possible_locations:
                if metadata_path.exists():
                    if self.verbose:
                        rprint(
                            f"[green]Arquivo de metadados encontrado em: {metadata_path}[/green]"
                        )
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        all_metadata = json.load(f)

                    # Procurar metadados específicos para este arquivo
                    file_name = file_path.name

                    # Se o metadata.json for uma lista de objetos
                    if isinstance(all_metadata, list):
                        for item in all_metadata:
                            # Verificar se este item corresponde ao arquivo atual
                            if (
                                item.get("filename") == file_name
                                or item.get("file") == file_name
                            ):
                                return item
                        # Se não encontrou específico, retornar o primeiro item (se existir)
                        if all_metadata:
                            return all_metadata[0]

                    # Se o metadata.json for um dict simples
                    elif isinstance(all_metadata, dict):
                        return all_metadata

            return {}
        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro ao carregar metadata.json: {str(e)}[/red]")
            return {}

    def extract_metadata(self, text: str, file_path: Optional[Path] = None) -> Dict:
        """Extrai metadados usando uma combinação de arquivo metadata.json e extração por LLM."""
        if self.verbose:
            rprint("[yellow]Iniciando extração de metadados...[/yellow]")

        # Inicializar metadados vazios
        metadata = {}

        # 1. Primeiro, tentar carregar do metadata.json se tiver um arquivo
        if file_path:
            # Verificar se file_path é um objeto Path ou uma string
            if isinstance(file_path, str):
                file_path = Path(file_path)

            try:
                # Tentar encontrar o metadata.json correspondente
                metadata_from_file = self._load_metadata_json(file_path)
                if metadata_from_file:
                    if self.verbose:
                        rprint(
                            f"[green]Metadados encontrados em arquivo existente[/green]"
                        )
                    metadata.update(metadata_from_file)

                    # Se temos todos os metadados necessários, podemos retornar imediatamente
                    required_fields = [
                        "public_notice",
                        "bid_number",
                        "process_id",
                        "agency",
                        "object",
                    ]

                    if all(
                        field in metadata and metadata[field]
                        for field in required_fields
                    ):
                        if self.verbose:
                            rprint(
                                f"[green]Todos os metadados necessários encontrados no arquivo[/green]"
                            )
                        return metadata

                    if self.verbose:
                        missing_fields = [
                            field
                            for field in required_fields
                            if field not in metadata or not metadata[field]
                        ]
                        if missing_fields:
                            rprint(
                                f"[yellow]Campos faltantes que serão extraídos: {', '.join(missing_fields)}[/yellow]"
                            )
            except Exception as e:
                if self.verbose:
                    rprint(
                        f"[red]Erro ao processar arquivo de metadados: {str(e)}[/red]"
                    )

        # 2. Extrair metadados usando agentes
        if self.verbose:
            rprint("[yellow]Extraindo metadados com agentes...[/yellow]")

        try:
            # Limitar o tamanho do texto para extração de metadados
            truncated_text = text[:5000] if len(text) > 5000 else text

            # Criar tarefas para extração de metadados
            tasks = []
            metadata_from_llm = {}

            # Verificar quais agentes estão disponíveis
            if "identifier_agent" in self.agents:
                try:
                    identifier_task = self._create_task(
                        "identifier_task", truncated_text
                    )

                    # Verificar e usar o método correto para executar a tarefa
                    if hasattr(identifier_task, "execute"):
                        identifier_result = identifier_task.execute()
                    elif hasattr(identifier_task, "run"):
                        identifier_result = identifier_task.run()
                    else:
                        # Criar uma crew com apenas esta tarefa e executá-la
                        crew = Crew(
                            agents=[identifier_task.agent],
                            tasks=[identifier_task],
                            verbose=self.verbose,
                            process=Process.sequential,
                        )
                        identifier_result = crew.kickoff()

                    extracted_data = self._extract_json_from_text(identifier_result)
                    metadata_from_llm.update(extracted_data)
                    if self.verbose:
                        rprint(
                            f"[green]Dados extraídos por identifier_agent: {extracted_data}[/green]"
                        )
                except Exception as e:
                    if self.verbose:
                        rprint(
                            f"[red]Erro ao executar identifier_agent: {str(e)}[/red]"
                        )

            if "organization_agent" in self.agents:
                try:
                    org_task = self._create_task("organization_task", truncated_text)
                    org_result = org_task.execute()
                    extracted_data = self._extract_json_from_text(org_result)
                    metadata_from_llm.update(extracted_data)
                    if self.verbose:
                        rprint(
                            f"[green]Dados extraídos por organization_agent: {extracted_data}[/green]"
                        )
                except Exception as e:
                    if self.verbose:
                        rprint(
                            f"[red]Erro ao executar organization_agent: {str(e)}[/red]"
                        )

            if "dates_agent" in self.agents:
                try:
                    dates_task = self._create_task("dates_task", truncated_text)
                    dates_result = dates_task.execute()
                    extracted_data = self._extract_json_from_text(dates_result)
                    metadata_from_llm.update(extracted_data)
                    if self.verbose:
                        rprint(
                            f"[green]Dados extraídos por dates_agent: {extracted_data}[/green]"
                        )
                except Exception as e:
                    if self.verbose:
                        rprint(f"[red]Erro ao executar dates_agent: {str(e)}[/red]")

            if "metadata_agent" in self.agents:
                try:
                    subject_task = self._create_task("subject_task", truncated_text)
                    subject_result = subject_task.execute()
                    extracted_data = self._extract_json_from_text(subject_result)
                    metadata_from_llm.update(extracted_data)
                    if self.verbose:
                        rprint(
                            f"[green]Dados extraídos por metadata_agent: {extracted_data}[/green]"
                        )
                except Exception as e:
                    if self.verbose:
                        rprint(f"[red]Erro ao executar metadata_agent: {str(e)}[/red]")

            # Mesclar os resultados da extração automática com os metadados do arquivo
            for key, value in metadata_from_llm.items():
                if key not in metadata or not metadata[key]:
                    metadata[key] = value

            return metadata

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro na extração de metadados: {str(e)}[/red]")
            return metadata  # Retornar o que conseguimos do arquivo

    def generate_summary(self, text: str, summary_type: SummaryType) -> str:
        """Gera um resumo do documento conforme o tipo solicitado."""
        try:
            if self.verbose:
                rprint(f"[yellow]Gerando resumo {summary_type}...[/yellow]")

            # Limitar o tamanho do texto baseado no tipo de resumo
            max_text_len = 15000 if summary_type == SummaryType.TECHNICAL else 10000
            truncated_text = text[:max_text_len] if len(text) > max_text_len else text

            # Criar a tarefa de resumo apropriada
            if summary_type == SummaryType.EXECUTIVE:
                if "executive_summary_agent" not in self.agents:
                    return "Erro: Agente de resumo executivo não encontrado"

                task = self._create_task("executive_summary", truncated_text)

            elif summary_type == SummaryType.TECHNICAL:
                if "technical_summary_agent" not in self.agents:
                    return "Erro: Agente de resumo técnico não encontrado"

                task = self._create_task("technical_summary", truncated_text)

            else:
                return f"Tipo de resumo não suportado: {summary_type}"

            # Executar a tarefa - verificar se tem execute() ou run()
            if hasattr(task, "execute"):
                result = task.execute()
            elif hasattr(task, "run"):
                result = task.run()
            else:
                # Criar uma crew com apenas esta tarefa e executá-la
                single_task_crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    verbose=self.verbose,
                    process=Process.sequential,
                )
                result = single_task_crew.kickoff()

            if self.verbose:
                rprint(f"[green]Resumo {summary_type} gerado com sucesso[/green]")

            return result

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro na geração do resumo {summary_type}: {str(e)}[/red]")
            return f"Erro ao gerar resumo: {str(e)}"

    def process_document(
        self,
        text: str,
        summary_types: List[SummaryType] = None,
        file_path: Optional[Path] = None,
    ) -> Dict:
        """Processa um documento e gera todos os resumos solicitados."""
        if summary_types is None:
            summary_types = [SummaryType.EXECUTIVE, SummaryType.TECHNICAL]

        # Limitar o tamanho do texto desde o início
        max_text_length = 20000
        if len(text) > max_text_length:
            if self.verbose:
                rprint(
                    f"[dim]Texto completo truncado de {len(text)} para {max_text_length} caracteres[/dim]"
                )
            text = text[:max_text_length]

        # Extrai metadados
        metadata = self.extract_metadata(text, file_path=file_path)

        # Gera resumos para cada tipo solicitado
        summaries = {}
        for summary_type in summary_types:
            summaries[str(summary_type)] = self.generate_summary(text, summary_type)

        return {"metadata": metadata, "summaries": summaries}
