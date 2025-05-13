import os
import glob
import json
import zipfile
from typing import Union, List, Dict, Any
from ..tools.file_tools import SimpleFileReadTool
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.zip_handler import ZipHandler

logger = get_logger(__name__)

class DocumentProcessor:
    """
    Processa documentos de editais, extraindo texto e preparando para análise.
    """

    def __init__(self, max_chars: int = 20000):
        """
        Inicializa o processador de documentos.

        Args:
            max_chars: Número máximo de caracteres a serem processados
        """
        self.max_chars = max_chars
        self.file_reader = SimpleFileReadTool()
        self.supported_extensions = [
            ".txt",
            ".pdf",
            ".docx",
            ".doc",
            ".md",
            ".markdown",
            ".zip",
        ]
        self.zip_handler = ZipHandler()

    def process_path(self, path: str) -> Dict[str, Any]:
        """
        Processa um caminho que pode ser um arquivo ou diretório.
        
        Args:
            path: Caminho do arquivo ou diretório
            
        Returns:
            Dicionário com informações do processamento
        """
        try:
            # Verifica se é um arquivo ZIP
            if self.zip_handler.is_zip_file(path):
                return self._process_zip(path)
            
            # Verifica se é um arquivo
            if os.path.isfile(path):
                return self._process_file(path)
            
            # Verifica se é um diretório
            if os.path.isdir(path):
                return self._process_directory(path)
            
            raise ValueError(f"Caminho inválido: {path}")
            
        except Exception as e:
            logger.error(f"Erro ao processar caminho {path}: {str(e)}")
            return {
                "error": str(e),
                "file_path": path
            }

    def _process_zip(self, zip_path: str) -> Dict[str, Any]:
        """
        Processa um arquivo ZIP.
        
        Args:
            zip_path: Caminho do arquivo ZIP
            
        Returns:
            Dicionário com informações do processamento
        """
        try:
            # Extrai o ZIP para um diretório temporário
            extract_path = self.zip_handler.extract_zip(zip_path)
            
            # Lista os conteúdos
            contents = self.zip_handler.get_zip_contents(extract_path)
            
            # Processa cada arquivo
            documents = []
            for item in contents:
                if item['is_zip']:
                    # Se encontrar outro ZIP dentro, processa recursivamente
                    nested_result = self._process_zip(item['file_path'])
                    if 'documents' in nested_result:
                        documents.extend(nested_result['documents'])
                else:
                    # Processa arquivo normal
                    doc_result = self._process_file(item['file_path'])
                    if 'content' in doc_result:
                        documents.append(doc_result)
            
            # Limpa o diretório temporário
            self.zip_handler.cleanup_temp_dir(extract_path)
            
            return {
                "file_path": zip_path,
                "file_name": os.path.basename(zip_path),
                "is_zip": True,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar ZIP {zip_path}: {str(e)}")
            return {
                "error": str(e),
                "file_path": zip_path
            }

    def _process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Processa um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dicionário com informações do processamento
        """
        try:
            # Lê o conteúdo do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "content": content,
                "has_metadata_file": False
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
            return {
                "error": str(e),
                "file_path": file_path
            }

    def _process_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Processa um diretório.
        
        Args:
            dir_path: Caminho do diretório
            
        Returns:
            Dicionário com informações do processamento
        """
        try:
            documents = []
            
            # Processa cada item no diretório
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                
                # Ignora arquivos ocultos e temporários
                if item.startswith('.') or item.endswith('.tmp'):
                    continue
                
                # Processa o item
                result = self.process_path(item_path)
                if 'documents' in result:
                    documents.extend(result['documents'])
                elif 'content' in result:
                    documents.append(result)
            
            return {
                "file_path": dir_path,
                "file_name": os.path.basename(dir_path),
                "is_directory": True,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar diretório {dir_path}: {str(e)}")
            return {
                "error": str(e),
                "file_path": dir_path
            }

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Processa um único arquivo.

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Dicionário com metadados e conteúdo do documento
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)

        # Verificar se é um arquivo suportado
        if ext.lower() not in self.supported_extensions and ext.lower() != ".zip":
            print(
                f"Aviso: Tipo de arquivo não suportado: {ext}. Tentando processar como texto."
            )

        content = self.file_reader._run(file_path, self.max_chars)

        # Verificar se existe um arquivo metadata.json no mesmo diretório
        dir_path = os.path.dirname(file_path)
        metadata_path = os.path.join(dir_path, "metadata.json")
        metadata = (
            self.load_metadata(metadata_path) if os.path.exists(metadata_path) else {}
        )

        return {
            "file_path": file_path,
            "file_name": file_name,
            "content": content,
            "size": len(content),
            "type": ext.lower()[1:],  # Remove o ponto do início
            "has_metadata_file": bool(metadata),
            "metadata": metadata,
        }

    def process_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Processa todos os arquivos em um diretório.

        Args:
            dir_path: Caminho para o diretório

        Returns:
            Dicionário com metadados e conteúdo de todos os documentos
        """
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")

        # Verificar se existe um arquivo metadata.json no diretório
        metadata_path = os.path.join(dir_path, "metadata.json")
        directory_metadata = (
            self.load_metadata(metadata_path) if os.path.exists(metadata_path) else {}
        )

        # Encontrar todos os arquivos suportados no diretório
        all_files = []
        for ext in self.supported_extensions:
            pattern = os.path.join(dir_path, f"*{ext}")
            all_files.extend(glob.glob(pattern))

            # Também buscar com extensão maiúscula
            pattern = os.path.join(dir_path, f"*{ext.upper()}")
            all_files.extend(glob.glob(pattern))

        all_files = sorted(all_files)

        # Remover metadata.json da lista de arquivos a processar
        all_files = [
            f for f in all_files if os.path.basename(f).lower() != "metadata.json"
        ]

        if not all_files:
            raise ValueError(f"Nenhum arquivo suportado encontrado em: {dir_path}")

        # Processar todos os arquivos
        documents = []
        for file_path in all_files:
            try:
                doc = self.process_file(file_path)

                # Adicionar os metadados do diretório se o documento não tiver metadados próprios
                if directory_metadata and not doc.get("metadata"):
                    doc["metadata"] = directory_metadata
                    doc["has_metadata_file"] = True

                documents.append(doc)
            except Exception as e:
                print(f"Erro ao processar arquivo {file_path}: {str(e)}")

        return {
            "directory": dir_path,
            "documents": documents,
            "file_count": len(documents),
            "has_metadata_file": bool(directory_metadata),
            "metadata": directory_metadata if directory_metadata else {},
        }

    def load_metadata(self, metadata_path: str) -> Dict[str, Any]:
        """
        Carrega metadados de um arquivo JSON.

        Args:
            metadata_path: Caminho para o arquivo JSON de metadados

        Returns:
            Dicionário com os metadados ou dicionário vazio em caso de erro
        """
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Mapear campos do metadata.json para o formato esperado pelo sistema
            mapped_metadata = {
                "identifier": {
                    "public_notice": metadata.get("public_notice", ""),
                    "process_id": metadata.get("process_id", ""),
                    "bid_number": metadata.get("bid_number", ""),
                },
                "organization": {
                    "organization": metadata.get("agency", ""),
                    "phone": metadata.get("phone", ""),
                    "website": metadata.get("website", ""),
                    "location": metadata.get("city", ""),
                },
                "subject": {
                    "title": metadata.get(
                        "public_notice", ""
                    ),  # Usando o número do edital como título
                    "object": metadata.get("object", ""),
                    "dates": metadata.get("dates", ""),
                },
            }

            return mapped_metadata
        except Exception as e:
            print(f"Erro ao carregar metadados de {metadata_path}: {str(e)}")
            return {}

    def trim_content(self, content: str, max_length: int) -> str:
        """
        Limita o tamanho do conteúdo.

        Args:
            content: Texto a ser limitado
            max_length: Tamanho máximo em caracteres

        Returns:
            Texto limitado ao tamanho máximo
        """
        if len(content) <= max_length:
            return content

        return content[:max_length] + f"\n\n[Texto truncado em {max_length} caracteres]"
