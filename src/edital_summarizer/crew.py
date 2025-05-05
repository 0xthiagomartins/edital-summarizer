from crewai import Agent, Crew, Process, Task

# Remover a importação que causou o erro
# from crewai.tools import Tool

# Manter a importação do decorador
from crewai.tools import tool

# Importando apenas ferramentas disponíveis ou implementando nossa própria
from langchain.tools import BaseTool
from typing import List, Dict, Optional, Union, Any
import yaml
from pathlib import Path
import json
from rich import print as rprint
from .types import SummaryType
from .tools.document_processor import DocumentProcessor
from .tools.rag_tools import DocumentSearchTool, TableExtractionTool
import os


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


# Definir funções não decoradas para uso interno
def _read_file(file_path: str) -> str:
    """Versão não decorada da função read_file."""
    try:
        path = Path(file_path)
        # ... resto do código da função ...
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"


class DocumentSummarizerCrew:
    def __init__(self, language: str = "pt-br", verbose: bool = False):
        self.config_dir = Path(__file__).parent / "config"
        self.language = language
        self.verbose = verbose

        # Inicializar processador de documentos que já funciona
        self.document_processor = DocumentProcessor(chunk_size=1500, chunk_overlap=150)

        # Não decoramos novamente - usamos as funções já decoradas como ferramentas
        self.file_reader = read_file
        self.document_search = search_document
        self.table_extractor = extract_tables

        # Carregar configurações de agentes
        self.agents = self._load_agents()

    def _load_agents(self) -> Dict[str, Agent]:
        """Carrega a configuração dos agentes a partir do arquivo YAML."""
        with open(self.config_dir / "agents.yaml") as f:
            agents_config = yaml.safe_load(f)

        agents = {}

        # Processar configurações específicas do idioma
        for name, config in agents_config.items():
            if isinstance(config["goal"], dict):
                config["goal"] = config["goal"][self.language]
            if isinstance(config["backstory"], dict):
                config["backstory"] = config["backstory"][self.language]

            # Substituir nomes de ferramentas por instâncias reais
            if "tools" in config:
                tool_instances = []
                for tool_name in config["tools"]:
                    if tool_name == "SimpleFileReadTool":
                        tool_instances.append(self.file_reader)
                    elif tool_name == "DocumentSearchTool":
                        tool_instances.append(self.document_search)
                    elif tool_name == "TableExtractionTool":
                        tool_instances.append(self.table_extractor)
                    else:
                        if self.verbose:
                            rprint(f"[red]Ferramenta desconhecida: {tool_name}[/red]")

                config["tools"] = tool_instances

            # Configurar o modelo AI com base na tarefa do agente
            # Agentes para metadados e extração de informações estruturadas usam OpenAI
            if name in ["identifier_agent", "organization_agent", "dates_agent"]:
                config["llm"] = "openai"
                config["model_name"] = "gpt-4"  # ou "gpt-4o" se tiver acesso
                config["temperature"] = (
                    0.1  # Temperatura baixa para extração estruturada
                )
                config["max_tokens"] = 800

            # Agentes para resumos e análises usam Gemini
            elif name in [
                "technical_summary_agent",
                "executive_summary_agent",
                "legal_summary_agent",
            ]:
                config["llm"] = "gemini"
                config["model_name"] = "gemini-pro"
                config["temperature"] = (
                    0.3  # Temperatura um pouco mais alta para criatividade nos resumos
                )
                config["max_tokens"] = 1500

            # Para outros agentes genéricos, use Gemini por padrão
            else:
                config["llm"] = "gemini"
                config["model_name"] = "gemini-pro"
                config["temperature"] = 0.2
                config["max_tokens"] = 1000

            if self.verbose:
                rprint(
                    f"[dim]Configurando agente {name} com modelo {config.get('llm')} - {config.get('model_name')}[/dim]"
                )

            agents[name] = self._create_agent_with_model(config)

        return agents

    def _create_agent_with_model(self, config):
        """Cria um agente com o modelo especificado, com fallback para alternativas."""
        primary_llm = config.get("llm", "gemini")
        primary_model = config.get("model_name")

        try:
            # Tentar criar o agente com o modelo primário
            return Agent(**config)
        except Exception as e:
            if self.verbose:
                rprint(
                    f"[yellow]Erro ao criar agente com {primary_llm} - {primary_model}: {str(e)}[/yellow]"
                )
                rprint(f"[yellow]Tentando modelo alternativo...[/yellow]")

            # Configurar modelo alternativo
            if primary_llm == "openai":
                config["llm"] = "gemini"
                config["model_name"] = "gemini-pro"
            else:
                config["llm"] = "openai"
                config["model_name"] = "gpt-3.5-turbo"

            try:
                if self.verbose:
                    rprint(
                        f"[green]Usando modelo alternativo: {config['llm']} - {config['model_name']}[/green]"
                    )

                return Agent(**config)
            except Exception as e2:
                if self.verbose:
                    rprint(f"[red]Falha também no modelo alternativo: {str(e2)}[/red]")

                # Último recurso: criar um agente simples sem especificar o modelo
                basic_config = {
                    "role": config.get("role", "Assistente"),
                    "goal": config.get("goal", "Ajudar com a tarefa"),
                    "backstory": config.get("backstory", "Um assistente útil"),
                    "verbose": config.get("verbose", self.verbose),
                }

                if self.verbose:
                    rprint("[red]Criando agente básico sem modelo específico[/red]")

                return Agent(**basic_config)

    def _load_tasks(self) -> Dict[str, dict]:
        """Carrega a configuração das tarefas a partir do arquivo YAML."""
        with open(self.config_dir / "tasks.yaml") as f:
            tasks_config = yaml.safe_load(f)

        # Processar descrições específicas do idioma
        for task_name, task_config in tasks_config.items():
            if isinstance(task_config.get("description"), dict):
                task_config["description"] = task_config["description"][self.language]

        return tasks_config

    def _load_metadata_json(self, file_path: Path) -> Dict:
        """Carrega metadados do arquivo metadata.json correspondente."""
        try:
            # Verificar diferentes possíveis localizações do metadata.json
            possible_locations = [
                file_path.parent / "metadata.json",  # Mesmo diretório
                Path("samples")
                / file_path.stem
                / "metadata.json",  # Na pasta samples/nome-do-arquivo
                Path("samples")
                / file_path.parent.name
                / "metadata.json",  # Na pasta samples/diretório-pai
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
        metadata_from_file = {}

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

                    # Caso contrário, registramos os campos faltantes para extração
                    missing_fields = [
                        field
                        for field in required_fields
                        if field not in metadata or not metadata[field]
                    ]
                    if self.verbose and missing_fields:
                        rprint(
                            f"[yellow]Campos faltantes que serão extraídos: {', '.join(missing_fields)}[/yellow]"
                        )
            except Exception as e:
                if self.verbose:
                    rprint(
                        f"[red]Erro ao processar arquivo de metadados: {str(e)}[/red]"
                    )

        # 2. Se ainda precisamos de metadados, usar a abordagem multi-agente
        if self.verbose:
            rprint(
                "[yellow]Extraindo metadados faltantes com abordagem multi-agente...[/yellow]"
            )

        # Limite de tamanho para o texto analisado
        max_len = 5000
        if len(text) > max_len:
            truncated_text = text[:max_len]
            if self.verbose:
                rprint(
                    f"[dim]Texto truncado de {len(text)} para {max_len} caracteres[/dim]"
                )
        else:
            truncated_text = text

        try:
            # Usar o DocumentProcessor para extração de metadados (caso não tenhamos agentes configurados)
            if not hasattr(self, "agents") or not self.agents:
                if self.verbose:
                    rprint(
                        "[yellow]Usando DocumentProcessor para extração de metadados (fallback)[/yellow]"
                    )
                from .tools.document_processor import DocumentProcessor

                processor = DocumentProcessor()
                metadata_from_llm = processor.extract_metadata_from_text(truncated_text)
            else:
                # Criar tarefas específicas para cada agente
                metadata_from_llm = {}

                # Define agents específicos para extração de metadados
                try:
                    identifier_agent = self.agents.get("identifier_agent")
                    organization_agent = self.agents.get("organization_agent")
                    dates_agent = self.agents.get("dates_agent")
                    subject_agent = self.agents.get("subject_agent")

                    # Fallback para criação de agentes caso não existam
                    if not identifier_agent:
                        if self.verbose:
                            rprint(
                                "[yellow]Criando agente de identificação (fallback)[/yellow]"
                            )
                        identifier_agent = Agent(
                            role="Identificador de Documentos",
                            goal="Extrair identificadores e números de documentos com precisão",
                            backstory="Especialista em localizar códigos, números de processo, identificadores de licitação e edital",
                            verbose=self.verbose,
                            llm=(
                                "openai"
                                if os.environ.get("OPENAI_API_KEY")
                                else "gemini"
                            ),
                            model_name=(
                                "gpt-3.5-turbo"
                                if os.environ.get("OPENAI_API_KEY")
                                else "gemini-pro"
                            ),
                            temperature=0.1,
                        )

                    # Criar e definir tarefas com a nova função helper
                    identifier_task = create_task_with_timeout(
                        description=f"Extraia do texto a seguir APENAS os identificadores do documento (número do edital, número da licitação, número do processo). "
                        f"Responda SOMENTE em formato JSON com as chaves 'public_notice' (número do edital), 'bid_number' (número da licitação) e 'process_id' (número do processo).\n\n"
                        f"TEXTO: {truncated_text[:1500]}",
                        expected_output="JSON com identificadores",
                        agent=identifier_agent,
                        timeout=30,
                        async_exec=False,
                    )

                    # Executar cada agente individualmente para evitar problemas
                    if identifier_agent:
                        try:
                            identifier_result = self._extract_json_from_text(
                                identifier_task.execute()
                            )
                            metadata_from_llm.update(identifier_result)
                        except Exception as e:
                            if self.verbose:
                                rprint(
                                    f"[red]Erro no agente de identificação: {str(e)}[/red]"
                                )

                    # Executar outros agentes se necessário
                    # ... (código para os outros agentes)

                except Exception as e:
                    if self.verbose:
                        rprint(f"[red]Erro ao configurar agentes: {str(e)}[/red]")
                    metadata_from_llm = {}

            # Mesclar os resultados da extração automática com os metadados do arquivo
            if metadata_from_llm:
                # Priorizar dados do arquivo metadata.json e complementar com LLM
                for key, value in metadata_from_llm.items():
                    if (
                        key not in metadata or not metadata[key]
                    ):  # Só adicionar se não existir ou for vazio
                        metadata[key] = value

            return metadata

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro na extração de metadados: {str(e)}[/red]")
            # Se falhou, retornar o que conseguimos extrair do arquivo
            return metadata or {}

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
                            f"[yellow]Texto encontrado não é um JSON válido, tentando limpeza...[/yellow]"
                        )
                    # Algumas correções comuns
                    json_str = json_str.replace("'", '"')
                    try:
                        return json.loads(json_str)
                    except:
                        pass

            # Se não conseguiu extrair JSON válido, tenta formato chave-valor
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
                rprint(
                    f"[yellow]Erro ao extrair JSON: {str(e)}. Usando formato alternativo...[/yellow]"
                )

            # Fallback para tentativa de extrair manualmente
            result = {}
            try:
                # Tenta extrair campos específicos com base em padrões
                if "edital" in text.lower() or "notice" in text.lower():
                    import re

                    # Buscar padrões comuns de edital
                    edital_patterns = [
                        r"edital\s*(?:n[°º.]?)?\s*:?\s*([A-Za-z0-9-_/]+)",
                        r"notice\s*(?:n[°º.]?)?\s*:?\s*([A-Za-z0-9-_/]+)",
                        r"PE/\d+/\d+",
                    ]
                    for pattern in edital_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            result["public_notice"] = match.group(1)
                            break

                # Extrair linhas com pares chave:valor
                lines = text.split("\n")
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip().strip("\"'")
                        value = parts[1].strip().strip("\"'")
                        if key and value:
                            result[key] = value
            except:
                pass

            return result

    def generate_summary(self, text: str, summary_type: SummaryType) -> str:
        """Gera um resumo do documento do tipo especificado."""
        if self.verbose:
            rprint(f"[yellow]Iniciando geração de resumo {summary_type}...[/yellow]")

        # Reduzir ainda mais o tamanho do texto para melhorar desempenho
        max_length = 5000
        if len(text) > max_length:
            if self.verbose:
                rprint(
                    f"[dim]Texto truncado para geração de resumo (de {len(text)} para {max_length} caracteres)[/dim]"
                )
            text = text[:max_length]

        try:
            tasks_config = self._load_tasks()

            # Ajustando para usar os nomes corretos dos agentes
            if summary_type == SummaryType.EXECUTIVE:
                agent_name = "executive_summary_agent"
                task_name = "executive_summary"
            elif summary_type == SummaryType.TECHNICAL:
                agent_name = "technical_summary_agent"
                task_name = "technical_summary"
            elif summary_type == SummaryType.LEGAL:
                agent_name = "legal_summary_agent"
                task_name = "legal_summary"
            else:
                raise ValueError(f"Tipo de resumo não suportado: {summary_type}")

            # Verificar se o agente existe
            if agent_name not in self.agents:
                if self.verbose:
                    rprint(
                        f"[red]Agente não encontrado: {agent_name}. Agentes disponíveis: {list(self.agents.keys())}[/red]"
                    )
                raise ValueError(
                    f"Agente não encontrado: {agent_name}. Agentes disponíveis: {list(self.agents.keys())}"
                )

            if self.verbose:
                rprint(f"[dim]Criando tarefa para o agente {agent_name}...[/dim]")

            # Criar tarefa com prompt mais direto e menor
            prompt_text = f"{tasks_config[task_name]['description']}\n\nTexto do documento (truncado):\n{text}"

            task = Task(
                description=prompt_text,
                expected_output=tasks_config[task_name]["expected_output"],
                agent=self.agents[agent_name],
                # Adicionar timeout para evitar execuções longas demais
                async_execution=False,
                output_file=None,
            )

            if self.verbose:
                rprint(
                    f"[dim]Iniciando crew de geração de resumo {summary_type}...[/dim]"
                )

            crew = Crew(
                agents=[self.agents[agent_name]],
                tasks=[task],
                verbose=self.verbose,
                process=Process.sequential,
                # Adicionar timeout ao nível da crew
                task_timeout=180,  # 3 minutos
                max_rpm=6,  # Limitar a 6 requisições por minuto
            )

            if self.verbose:
                rprint(f"[dim]Executando o kickoff da crew...[/dim]")

            result = crew.kickoff()

            if self.verbose:
                rprint(f"[green]Resumo {summary_type} gerado com sucesso[/green]")

            return result

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro na geração do resumo {summary_type}: {str(e)}[/red]")
            # Retornar mensagem de erro mais informativa
            if "not found in self.agents" in str(e):
                return f"Erro ao gerar resumo: Agente não encontrado. Agentes disponíveis: {list(self.agents.keys())}"
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

        # Extrai metadados usando o processador de documentos
        metadata = self.extract_metadata(text, file_path=file_path)

        # Gera resumos para cada tipo solicitado
        summaries = {}
        for summary_type in summary_types:
            summaries[str(summary_type)] = self.generate_summary(text, summary_type)

        return {"metadata": metadata, "summaries": summaries}


def create_task_with_timeout(
    description, expected_output, agent, timeout=30, async_exec=True
):
    """Helper para criar tarefas com timeout consistente."""
    try:
        # Tentar criar com context como lista (versão mais recente)
        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            async_execution=async_exec,
            context=[{"key": "timeout", "value": timeout}],
        )
    except:
        try:
            # Tentar sem context (versão estável)
            return Task(
                description=description,
                expected_output=expected_output,
                agent=agent,
                async_execution=async_exec,
            )
        except:
            # Fallback para versões antigas
            return Task(
                description=description,
                expected_output=expected_output,
                agent=agent,
                async_execution=async_exec,
                context={"timeout": timeout},
            )
