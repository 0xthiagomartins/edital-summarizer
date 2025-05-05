from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
import os
from google.generativeai import configure
import json


class DocumentProcessor:
    """Processador de documentos usando LangChain com Gemini."""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """Inicializa o processador de documentos."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

        # Configura a API do Google
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables"
            )

        # Configura o modelo Gemini
        configure(api_key=api_key)

        # Inicializa modelo LLM com timeout menor
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            timeout=30,  # Timeout reduzido para 30 segundos
            max_output_tokens=1024,  # Limitar saída para resposta mais rápida
        )

    def load_document(self, file_path: Union[str, Path]) -> List[Document]:
        """Carrega um documento a partir do caminho do arquivo."""
        file_path = Path(file_path) if isinstance(file_path, str) else file_path

        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Escolhe o loader adequado baseado na extensão do arquivo
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif extension == ".txt":
            loader = TextLoader(str(file_path))
        elif extension in [".docx", ".doc"]:
            loader = Docx2txtLoader(str(file_path))
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extension}")

        return loader.load()

    def extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """Extrai metadados diretamente do texto."""
        # Dividir em chunks menores para processamento
        chunks = self.text_splitter.split_text(text)

        # Criar um índice vetorial para consulta semântica
        docs = [Document(page_content=chunk) for chunk in chunks]
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(docs, embeddings)

        # Criar um chain para responder perguntas sobre o documento
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(),
        )

        return self._extract_metadata_with_qa(qa_chain)

    def extract_metadata_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extrai metadados de um documento."""
        # Garantir que file_path é um objeto Path
        file_path = Path(file_path) if isinstance(file_path, str) else file_path

        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        documents = self.load_document(file_path)

        # Combinar o texto de todas as páginas
        all_text = "\n".join([doc.page_content for doc in documents])

        return self.extract_metadata_from_text(all_text)

    def _extract_metadata_with_qa(self, qa_chain) -> Dict[str, Any]:
        """Extrai metadados usando um QA chain."""
        # Extrair metadados através de consultas específicas
        metadata = {}

        # Consultas mais curtas e diretas para resultados mais rápidos
        queries = {
            "object": "Qual o objeto principal deste documento?",
            "agency": "Qual o órgão responsável por este documento?",
            "public_notice": "Qual o número do edital?",
            "bid_number": "Qual o número da licitação?",
            "status": "Qual o status do processo?",
            "dates": "Quais as datas importantes?",
            "city": "Em qual cidade está ocorrendo?",
            "process_id": "Qual o número do processo?",
            "notes": "Informações sobre modalidade ou tipo de julgamento?",
            "phone": "Qual o telefone para contato?",
            "website": "Há algum site mencionado?",
        }

        # Executar consultas com timeout
        for field, query in queries.items():
            try:
                # Adicionar log para depuração
                print(f"Extraindo '{field}'...")

                # Invocar o modelo e processar o resultado corretamente
                result = qa_chain.invoke(query)

                # Verificar o tipo de resultado e extrair o texto
                if isinstance(result, dict) and "result" in result:
                    text_result = result["result"]
                elif isinstance(result, dict) and "answer" in result:
                    text_result = result["answer"]
                elif isinstance(result, str):
                    text_result = result
                else:
                    print(f"Formato inesperado para {field}: {type(result)}")
                    text_result = str(result)

                metadata[field] = (
                    text_result.strip()
                    if hasattr(text_result, "strip")
                    else str(text_result)
                )

            except Exception as e:
                print(f"Erro ao extrair {field}: {str(e)}")
                metadata[field] = ""

        return metadata
