"""
Ferramentas de RAG (Retrieval Augmented Generation) para o processamento de documentos.
"""

from langchain.tools import BaseTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, ClassVar
import os
import json
import pandas as pd
from dotenv import load_dotenv
from pydantic import Field, ConfigDict

# Carregar variáveis de ambiente
load_dotenv()


class DocumentSearchTool(BaseTool):
    """Ferramenta para buscar informações específicas em documentos."""

    name: str = "document_search"
    description: str = "Busca informações específicas dentro de um documento usando RAG"

    # Definir os atributos explicitamente como campos
    embeddings: Any = Field(default=None, exclude=True)
    text_splitter: Any = Field(default=None, exclude=True)

    # Configurar para permitir campos extras
    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow", arbitrary_types_allowed=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Usar embeddings da OpenAI se disponível, senão usar os do Google
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.embeddings = OpenAIEmbeddings()
            else:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001"
                )

            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
            )
        except Exception as e:
            # Capturar problemas na inicialização
            print(f"Erro ao inicializar DocumentSearchTool: {str(e)}")
            # Garantir que os atributos existam mesmo em caso de falha
            self.embeddings = None
            self.text_splitter = None

    def _run(self, query: str, text: str = None, file_path: str = None) -> str:
        """
        Busca informações no documento baseado na query.

        Args:
            query: A pergunta ou query de busca
            text: Texto do documento (opcional se file_path for fornecido)
            file_path: Caminho para o arquivo do documento (opcional se text for fornecido)

        Returns:
            Resultado da busca com informações relevantes
        """
        if not self.embeddings or not self.text_splitter:
            return "Erro: Embeddings ou text_splitter não inicializados corretamente."

        if not text and not file_path:
            return "Erro: É necessário fornecer o texto ou o caminho do arquivo."

        # Obter o texto do documento
        if file_path and not text:
            try:
                text = self._load_document(file_path)
            except Exception as e:
                return f"Erro ao carregar o arquivo: {str(e)}"

        # Dividir o texto em chunks e criar base vetorial
        try:
            chunks = self.text_splitter.split_text(text)
            vectorstore = FAISS.from_texts(chunks, self.embeddings)

            # Realizar a busca
            docs = vectorstore.similarity_search(query, k=3)

            # Formatar os resultados
            results = []
            for i, doc in enumerate(docs):
                results.append(f"Trecho {i+1}:\n{doc.page_content}\n")

            return "\n".join(results)
        except Exception as e:
            return f"Erro na busca: {str(e)}"

    def _load_document(self, file_path: str) -> str:
        """Carrega o conteúdo de um documento a partir do caminho do arquivo."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Escolhe o loader adequado baseado na extensão do arquivo
        extension = path.suffix.lower()

        if extension == ".pdf":
            loader = PyPDFLoader(str(path))
        elif extension == ".txt":
            loader = TextLoader(str(path))
        elif extension in [".docx", ".doc"]:
            loader = Docx2txtLoader(str(path))
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extension}")

        documents = loader.load()
        return "\n".join([doc.page_content for doc in documents])

    async def _arun(self, query: str, text: str = None, file_path: str = None) -> str:
        """Implementação assíncrona (necessária pelo CrewAI)"""
        return self._run(query, text, file_path)


class TableExtractionTool(BaseTool):
    """Ferramenta para extrair tabelas de documentos."""

    name: str = "table_extractor"
    description: str = (
        "Extrai tabelas de documentos e as retorna em formato estruturado"
    )

    # Configurar para permitir campos extras
    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow", arbitrary_types_allowed=True
    )

    def _run(self, text: str, table_keyword: str = None) -> str:
        """
        Extrai tabelas de um texto.

        Args:
            text: Texto do documento
            table_keyword: Palavra-chave para identificar a tabela (opcional)

        Returns:
            Tabelas extraídas em formato JSON
        """
        try:
            # Lógica simplificada para extração de tabelas
            # Em um caso real, usaríamos bibliotecas como tabula-py (para PDFs)
            # ou modelos de ML específicos para detecção de tabelas

            if table_keyword:
                # Buscar seções que contêm a palavra-chave
                sections = self._find_table_sections(text, table_keyword)
                if not sections:
                    return "Nenhuma tabela encontrada com a palavra-chave fornecida."

                # Extrair tabelas das seções encontradas
                tables = []
                for section in sections:
                    table_data = self._parse_table_text(section)
                    if table_data:
                        tables.append(table_data)

                return json.dumps(tables, ensure_ascii=False, indent=2)
            else:
                # Tentar extrair todas as possíveis tabelas
                potential_tables = self._find_potential_tables(text)
                tables = []

                for potential_table in potential_tables:
                    table_data = self._parse_table_text(potential_table)
                    if table_data:
                        tables.append(table_data)

                if not tables:
                    return "Nenhuma tabela detectada no documento."

                return json.dumps(tables, ensure_ascii=False, indent=2)

        except Exception as e:
            return f"Erro na extração de tabelas: {str(e)}"

    def _find_table_sections(self, text: str, keyword: str) -> List[str]:
        """Encontra seções de texto que podem conter tabelas baseadas em palavra-chave."""
        lines = text.split("\n")
        sections = []
        current_section = []
        in_section = False

        for line in lines:
            if keyword.lower() in line.lower():
                if current_section:
                    sections.append("\n".join(current_section))
                current_section = [line]
                in_section = True
            elif in_section:
                current_section.append(line)
                # Se encontrarmos uma linha vazia seguida de texto não tabulado,
                # consideramos que a tabela terminou
                if not line.strip() and len(current_section) > 10:
                    in_section = False
                    sections.append("\n".join(current_section))
                    current_section = []

        if current_section:
            sections.append("\n".join(current_section))

        return sections

    def _find_potential_tables(self, text: str) -> List[str]:
        """Identifica possíveis tabelas no texto."""
        lines = text.split("\n")
        potential_tables = []
        current_table = []
        in_table = False
        consecutive_pattern_lines = 0

        for line in lines:
            # Heurística simples: linhas com vários espaços ou tabulações
            # são candidatas a linhas de tabela
            if "  " in line or "\t" in line:
                if not in_table:
                    in_table = True
                current_table.append(line)
                consecutive_pattern_lines += 1

                # Se tivermos pelo menos 3 linhas com padrão tabular, é uma tabela candidata
                if consecutive_pattern_lines >= 3:
                    in_table = True
            else:
                if in_table:
                    # Uma linha não tabular pode ainda ser parte da tabela
                    # (como um título ou nota de rodapé)
                    current_table.append(line)

                    # Se tivermos mais de 2 linhas não tabulares consecutivas,
                    # consideramos que a tabela terminou
                    consecutive_pattern_lines = 0

                    if not line.strip():  # Linha vazia
                        in_table = False
                        if len(current_table) >= 3:  # Tabelas têm pelo menos 3 linhas
                            potential_tables.append("\n".join(current_table))
                        current_table = []

        # Não esquecer a última tabela
        if current_table and len(current_table) >= 3:
            potential_tables.append("\n".join(current_table))

        return potential_tables

    def _parse_table_text(self, table_text: str) -> Dict:
        """Analisa o texto da tabela e converte em estrutura de dados."""
        lines = table_text.strip().split("\n")

        # Remover linhas vazias
        lines = [line for line in lines if line.strip()]

        if len(lines) < 2:  # Precisa de pelo menos título e uma linha de dados
            return {}

        # Tentar identificar o separador (espaços, tabs, etc.)
        if "\t" in lines[0]:
            delimiter = "\t"
        else:
            # Assumir espaços como separador
            delimiter = None  # pandas vai inferir os espaços

        try:
            # Usar pandas para parsing
            df = pd.read_csv(pd.StringIO("\n".join(lines)), sep=delimiter, header=0)
            return {"headers": df.columns.tolist(), "data": df.values.tolist()}
        except:
            # Fallback para parsing manual simples
            headers = [h.strip() for h in lines[0].split(delimiter) if h.strip()]
            data = []

            for line in lines[1:]:
                values = [v.strip() for v in line.split(delimiter) if v.strip()]
                if values:
                    data.append(values)

            return {"headers": headers, "data": data}

    async def _arun(self, text: str, table_keyword: str = None) -> str:
        """Implementação assíncrona (necessária pelo CrewAI)"""
        return self._run(text, table_keyword)
