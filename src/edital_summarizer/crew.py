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

            if self.verbose:
                rprint(
                    f"[green]Usando modelo alternativo: {config['llm']} - {config['model_name']}[/green]"
                )

            return Agent(**config)

    def _load_tasks(self) -> Dict[str, dict]:
        """Carrega a configuração das tarefas a partir do arquivo YAML."""
        with open(self.config_dir / "tasks.yaml") as f:
            tasks_config = yaml.safe_load(f)

        # Processar descrições específicas do idioma
        for task_name, task_config in tasks_config.items():
            if isinstance(task_config.get("description"), dict):
                task_config["description"] = task_config["description"][self.language]

        return tasks_config

    def extract_metadata(self, text: str, file_path: Optional[Path] = None) -> Dict:
        """Extrai metadados usando uma crew de agentes especializados."""
        if self.verbose:
            rprint(
                "[yellow]Iniciando extração de metadados com abordagem multi-agente...[/yellow]"
            )

        # Se temos um arquivo, primeiro carregamos o conteúdo
        if file_path:
            path_str = str(file_path)
            if self.verbose:
                rprint(f"[dim]Lendo arquivo: {path_str}[/dim]")

            # Verificar se o arquivo existe e tentar encontrá-lo se necessário
            if not Path(path_str).exists():
                rprint(f"[red]Arquivo não encontrado: {path_str}[/red]")
                rprint(f"[dim]Tentando encontrar o arquivo...[/dim]")

                # Tentar encontrar o arquivo nas pastas samples
                samples_dir = Path("samples")
                if samples_dir.exists():
                    possible_files = list(samples_dir.glob(f"**/{Path(path_str).name}"))
                    if possible_files:
                        path_str = str(possible_files[0])
                        rprint(f"[green]Arquivo encontrado em: {path_str}[/green]")

            # Usar read_file (que é uma função e não um objeto Tool)
            # Importante: Como read_file é decorada com @tool, precisamos acessar a função original
            try:
                # Tentar acessar método _run da ferramenta
                file_content = read_file._run(path_str)
            except:
                # Fallback para caso a estrutura da ferramenta tenha mudado
                try:
                    file_content = read_file(path_str)
                except:
                    file_content = f"Erro: Não foi possível ler {path_str}"

            if file_content.startswith("Erro:"):
                return {"error": file_content}

            # Usar o conteúdo do arquivo
            text = file_content

        # Limitar o texto para processamento
        max_len = 5000
        if len(text) > max_len:
            truncated_text = text[:max_len]
            if self.verbose:
                rprint(
                    f"[dim]Texto truncado de {len(text)} para {max_len} caracteres[/dim]"
                )
        else:
            truncated_text = text

        # Criar agentes especializados
        identifier_agent = Agent(
            role="Identificador de Documentos",
            goal="Extrair identificadores e números de documentos com precisão",
            backstory="Especialista em localizar códigos, números de processo, identificadores de licitação e edital",
            verbose=self.verbose,
            tools=[self.file_reader],
            temperature=0.2,
        )

        organization_agent = Agent(
            role="Analista Organizacional",
            goal="Identificar organizações, departamentos e contatos",
            backstory="Especialista em encontrar nomes de órgãos, departamentos, contatos e localidades",
            verbose=self.verbose,
            tools=[self.file_reader],
            temperature=0.3,
        )

        dates_agent = Agent(
            role="Analista de Cronograma",
            goal="Extrair todas as datas e prazos relevantes",
            backstory="Especialista em identificar datas, prazos e períodos em documentos oficiais",
            verbose=self.verbose,
            tools=[self.file_reader],
            temperature=0.2,
        )

        subject_agent = Agent(
            role="Analista de Objeto",
            goal="Compreender o objeto central do documento",
            backstory="Especialista em extrair e resumir o objeto principal da licitação ou contrato",
            verbose=self.verbose,
            tools=[self.file_reader],
            temperature=0.4,
        )

        # Criar tarefas - apenas a primeira é assíncrona
        identifier_task = Task(
            description=f"Examine o documento e extraia APENAS os seguintes campos em formato JSON:\n- public_notice: número do edital\n- bid_number: número da licitação\n- process_id: número do processo\n\nTexto do documento:\n{truncated_text[:2000]}",
            expected_output="JSON contendo apenas os campos solicitados",
            agent=identifier_agent,
            # Todas as tarefas são síncronas quando usando Process.sequential
            async_execution=False,
        )

        organization_task = Task(
            description=f"Examine o documento e extraia APENAS os seguintes campos em formato JSON:\n- agency: órgão responsável\n- city: cidade\n- phone: telefone\n- website: site/email de contato\n\nTexto do documento:\n{truncated_text[:2000]}",
            expected_output="JSON contendo apenas os campos solicitados",
            agent=organization_agent,
            async_execution=False,
        )

        dates_task = Task(
            description=f"Examine o documento e extraia APENAS os seguintes campos em formato JSON:\n- dates: datas importantes (abertura, encerramento, etc)\n- status: status atual (OPEN, CLOSED, etc)\n\nTexto do documento:\n{truncated_text[:2000]}",
            expected_output="JSON contendo apenas os campos solicitados",
            agent=dates_agent,
            async_execution=False,
        )

        subject_task = Task(
            description=f"Examine o documento e extraia APENAS os seguintes campos em formato JSON:\n- object: objeto da licitação (max 150 caracteres)\n- notes: observações sobre modalidade e tipo (max 200 caracteres)\n\nTexto do documento:\n{truncated_text}",
            expected_output="JSON contendo apenas os campos solicitados",
            agent=subject_agent,
            async_execution=False,
        )

        # Criar e executar a crew
        metadata_crew = Crew(
            agents=[identifier_agent, organization_agent, dates_agent, subject_agent],
            tasks=[identifier_task, organization_task, dates_task, subject_task],
            verbose=self.verbose,
            process=Process.sequential,
            task_timeout=30,
            max_rpm=10,
        )

        try:
            # Executar a crew e obter os resultados
            result = metadata_crew.kickoff()

            if self.verbose:
                rprint(f"[green]Processamento de metadados concluído![/green]")

            # Tentar parsear cada resultado como JSON
            metadata = {}

            # Juntar os campos de todos os agentes
            for task_output in result.split("---"):
                try:
                    # Limpar e remover texto extra
                    json_data = self._extract_json_from_text(task_output)
                    if json_data:
                        metadata.update(json_data)
                except Exception as e:
                    if self.verbose:
                        rprint(f"[red]Erro ao processar resultado: {str(e)}[/red]")

            return metadata

        except Exception as e:
            if self.verbose:
                rprint(f"[red]Erro na execução da crew: {str(e)}[/red]")
            return {"error": f"Erro ao processar metadados: {str(e)}"}

    def _extract_json_from_text(self, text: str) -> Dict:
        """Extrai um objeto JSON de texto que pode conter outros elementos."""
        try:
            # Procurar por texto entre chaves
            start_idx = text.find("{")
            end_idx = text.rfind("}")

            if start_idx >= 0 and end_idx >= 0:
                json_str = text[start_idx : end_idx + 1]
                return json.loads(json_str)

            # Se não encontrar chaves, procurar por formato de valor-chave
            result = {}
            lines = text.split("\n")

            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().strip("\"'")
                    value = parts[1].strip().strip("\"'")
                    if key and value:
                        result[key] = value

            return result if result else {}

        except json.JSONDecodeError:
            # Fallback para tentativa de extrair manualmente
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
