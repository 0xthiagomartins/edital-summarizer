import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import PyPDF2
import chardet
import io

logger = logging.getLogger(__name__)

class DocumentProcessor:
    @staticmethod
    def read_pdf(file_path: str) -> str:
        """Lê o conteúdo de um arquivo PDF."""
        try:
            # Abre o arquivo em modo binário
            with open(file_path, 'rb') as file:
                # Lê o conteúdo binário
                pdf_content = file.read()
                
                # Cria um buffer de memória com o conteúdo
                pdf_buffer = io.BytesIO(pdf_content)
                
                # Tenta ler o PDF com diferentes codificações
                try:
                    reader = PyPDF2.PdfReader(pdf_buffer)
                    text = ""
                    for page in reader.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        except Exception as e:
                            logger.warning(f"Erro ao extrair texto da página: {str(e)}")
                            continue
                    
                    if not text.strip():
                        logger.warning(f"Nenhum texto extraído do PDF: {file_path}")
                        return ""
                        
                    return text
                except Exception as e:
                    logger.error(f"Erro ao ler PDF {file_path}: {str(e)}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Erro ao abrir arquivo PDF {file_path}: {str(e)}")
            return ""

    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """Lê o conteúdo de um arquivo JSON."""
        try:
            # Primeiro detecta a codificação do arquivo
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'latin1'  # Usa latin1 como fallback

            # Lê o arquivo com a codificação detectada
            with open(file_path, 'r', encoding=encoding) as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Erro ao ler arquivo JSON {file_path}: {str(e)}")
            return {}

    @staticmethod
    def process_document(document_path: str) -> Dict[str, Any]:
        """Processa um documento e retorna seu conteúdo."""
        try:
            document_path = Path(document_path)
            if not document_path.exists():
                logger.error(f"Arquivo não encontrado: {document_path}")
                return {}

            # Processa o arquivo PDF
            pdf_path = document_path / f"{document_path.name}.pdf"
            if not pdf_path.exists():
                # Procura por qualquer arquivo PDF no diretório
                pdf_files = list(document_path.glob("*.pdf"))
                if pdf_files:
                    pdf_path = pdf_files[0]
                else:
                    logger.error(f"Nenhum arquivo PDF encontrado em {document_path}")
                    return {}

            # Lê o conteúdo do PDF
            content = DocumentProcessor.read_pdf(str(pdf_path))
            if not content:
                logger.error(f"Não foi possível extrair conteúdo do PDF: {pdf_path}")
                return {}

            # Processa o arquivo de metadados
            metadata_path = document_path / "metadata.json"
            if metadata_path.exists():
                metadata = DocumentProcessor.read_json(str(metadata_path))
            else:
                metadata = {}

            # Verifica se o conteúdo está vazio
            if not content.strip():
                logger.error(f"Conteúdo vazio para o documento {document_path}")
                return {}

            return {
                "content": content,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Erro ao processar documento {document_path}: {str(e)}")
            return {} 