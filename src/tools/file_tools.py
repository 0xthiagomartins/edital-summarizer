import os
import pypdf
import zipfile
import tempfile
import shutil
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import PyPDF2
import re
import docx
from utils import get_logger

logger = get_logger(__name__)

def clean_text(text: str) -> str:
    """Limpa e otimiza o texto removendo espaços desnecessários e caracteres especiais."""
    if not text:
        return text
        
    # Remove caracteres nulos e outros caracteres especiais
    text = text.replace('\x00', '')
    text = text.replace('\r', ' ')
    
    # Remove múltiplos espaços em branco
    text = re.sub(r'\s+', ' ', text)
    
    # Remove espaços antes e depois de pontuação
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Remove quebras de linha desnecessárias
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove espaços no início e fim de cada linha
    text = '\n'.join(line.strip() for line in text.split('\n'))
    
    # Remove linhas vazias no início e fim do texto
    text = text.strip()
    
    return text

class DocumentTooLargeError(Exception):
    """Exceção lançada quando o documento excede o limite de caracteres."""
    def __init__(self, max_chars: int, actual_chars: int):
        self.max_chars = max_chars
        self.actual_chars = actual_chars
        self.error_message = (
            f"Não foi possível processar a análise por completo pois o documento é muito grande "
            f"(tamanho atual: {actual_chars} caracteres, limite: {max_chars} caracteres). "
            f"Por segurança, o edital foi marcado como não relevante."
        )
        super().__init__(self.error_message)

class FileReadToolInput(BaseModel):
    """Input schema for FileReadTool."""
    file_path: str = Field(..., description="Path to the file to be read.")
    max_chars: int = Field(100000, description="Maximum number of characters to return.")

class FileReadTool(BaseTool):
    """Tool for reading different file formats."""
    
    name: str = "File Reader"
    description: str = (
        "Reads the content of a file and returns it as text. "
        "Supports TXT, PDF, DOCX, MD files and ZIP archives."
    )
    args_schema: Type[BaseModel] = FileReadToolInput

    def _run(self, file_path: str, max_chars: int = 100000) -> str:
        """Read file content and return it as text."""
        try:
            print(f"\n{'='*50}")
            print(f"FileReadTool: Iniciando leitura do arquivo: {file_path}")
            print(f"FileReadTool: Limite de caracteres: {max_chars}")
            
            # Valida caminho
            if not os.path.exists(file_path):
                print(f"❌ FileReadTool: Arquivo não encontrado: {file_path}")
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            print(f"✅ FileReadTool: Arquivo encontrado")

            # Determina tipo de arquivo
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            print(f"FileReadTool: Tipo de arquivo: {file_extension}")

            # Extrai texto baseado no tipo
            try:
                if file_extension == ".pdf":
                    print("FileReadTool: Extraindo texto do PDF...")
                    text = self._extract_text_from_pdf(file_path)
                elif file_extension in [".docx", ".doc"]:
                    print("FileReadTool: Extraindo texto do DOCX...")
                    text = self._extract_text_from_docx(file_path)
                elif file_extension in [".md", ".markdown"]:
                    print("FileReadTool: Extraindo texto do Markdown...")
                    text = self._extract_text_from_markdown(file_path)
                elif file_extension == ".zip":
                    print("FileReadTool: Extraindo texto do ZIP...")
                    text = self._extract_text_from_zip(file_path, max_chars)
                else:  # Assume it's a text file
                    print("FileReadTool: Lendo arquivo de texto...")
                    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                        text = file.read()

                # Limpa e otimiza o texto
                print("FileReadTool: Limpando e otimizando texto...")
                original_size = len(text)
                text = clean_text(text)
                cleaned_size = len(text)
                print(f"FileReadTool: Tamanho original: {original_size} caracteres")
                print(f"FileReadTool: Tamanho após limpeza: {cleaned_size} caracteres")
                print(f"FileReadTool: Redução: {original_size - cleaned_size} caracteres ({(original_size - cleaned_size)/original_size*100:.1f}%)")

                # Verifica limite de caracteres
                if len(text) > max_chars:
                    print(f"❌ FileReadTool: Documento excede limite de caracteres")
                    print(f"FileReadTool: Tamanho atual: {len(text)}")
                    print(f"FileReadTool: Limite: {max_chars}")
                    error_msg = (
                        f"Não foi possível processar a análise por completo pois o documento é muito grande "
                        f"(tamanho atual: {len(text)} caracteres, limite: {max_chars} caracteres). "
                        f"Por segurança, o edital foi marcado como não relevante."
                    )
                    raise DocumentTooLargeError(max_chars, len(text))

                print(f"✅ FileReadTool: Arquivo processado com sucesso")
                print(f"{'='*50}\n")
                return text
                
            except DocumentTooLargeError as e:
                print(f"❌ FileReadTool: Erro - Documento muito grande")
                print(f"FileReadTool: {str(e)}")
                raise
            except Exception as e:
                print(f"❌ FileReadTool: Erro ao ler arquivo")
                print(f"FileReadTool: {str(e)}")
                raise Exception(f"Erro ao ler arquivo: {str(e)}")
                
        except Exception as e:
            print(f"❌ FileReadTool: Erro ao processar arquivo")
            print(f"FileReadTool: {str(e)}")
            raise Exception(f"Erro ao processar arquivo: {str(e)}")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            print(f"FileReadTool: Extraindo texto do PDF: {file_path}")
            text = ""
            
            with open(file_path, "rb") as file:
                # Tenta ler o PDF com PyPDF2
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    num_pages = len(pdf_reader.pages)
                    print(f"FileReadTool: PDF tem {num_pages} páginas")
                    
                    # Processa apenas as primeiras 20 páginas
                    max_pages = min(20, num_pages)
                    print(f"FileReadTool: Processando {max_pages} páginas do PDF")
                    
                    for page_num in range(max_pages):
                        try:
                            page = pdf_reader.pages[page_num]
                            page_text = page.extract_text()
                            if page_text:
                                # Limpa o texto da página
                                page_text = clean_text(page_text)
                                
                                # Adiciona apenas se houver conteúdo significativo
                                if len(page_text) > 50:
                                    text += f"\n\n=== Página {page_num + 1} ===\n\n{page_text}"
                                    print(f"FileReadTool: Texto extraído da página {page_num + 1}: {len(page_text)} caracteres")
                                else:
                                    print(f"FileReadTool: Página {page_num + 1} ignorada por ter pouco conteúdo")
                            else:
                                print(f"FileReadTool: Nenhum texto extraído da página {page_num + 1}")
                        except Exception as e:
                            print(f"FileReadTool: Erro ao extrair texto da página {page_num + 1}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"FileReadTool: Erro ao ler PDF com PyPDF2: {str(e)}")
                    # Se falhar com PyPDF2, tenta com pypdf
                    try:
                        file.seek(0)
                        pdf_reader = pypdf.PdfReader(file)
                        num_pages = len(pdf_reader.pages)
                        print(f"FileReadTool: PDF tem {num_pages} páginas (usando pypdf)")
                        
                        max_pages = min(20, num_pages)
                        print(f"FileReadTool: Processando {max_pages} páginas do PDF")
                        
                        for page_num in range(max_pages):
                            try:
                                page = pdf_reader.pages[page_num]
                                page_text = page.extract_text()
                                if page_text:
                                    # Limpa o texto da página
                                    page_text = clean_text(page_text)
                                    
                                    if len(page_text) > 50:
                                        text += f"\n\n=== Página {page_num + 1} ===\n\n{page_text}"
                                        print(f"FileReadTool: Texto extraído da página {page_num + 1}: {len(page_text)} caracteres")
                                    else:
                                        print(f"FileReadTool: Página {page_num + 1} ignorada por ter pouco conteúdo")
                                else:
                                    print(f"FileReadTool: Nenhum texto extraído da página {page_num + 1}")
                            except Exception as e:
                                print(f"FileReadTool: Erro ao extrair texto da página {page_num + 1}: {str(e)}")
                                continue
                    except Exception as e:
                        print(f"FileReadTool: Erro ao ler PDF com pypdf: {str(e)}")
                        raise
            
            if not text.strip():
                print("FileReadTool: Nenhum texto extraído do PDF")
                return "Error: No text extracted from PDF"
            
            # Limpa o texto final
            text = clean_text(text)
            
            print(f"FileReadTool: Texto extraído com sucesso do PDF. Tamanho: {len(text)} caracteres")
            return text
            
        except Exception as e:
            print(f"FileReadTool: Erro ao extrair texto do PDF: {str(e)}")
            return f"Error: Failed to extract text from PDF: {str(e)}"

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            logger.info(f"Extraindo texto do DOCX: {file_path}")
            text = ""
            
            doc = docx.Document(file_path)
            
            # Extrai texto dos parágrafos
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            
            # Extrai texto das tabelas
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text += " | ".join(row_text) + "\n"
            
            if not text.strip():
                logger.error("Nenhum texto extraído do DOCX")
                return "Error: No text extracted from DOCX"
            
            logger.info(f"Texto extraído com sucesso do DOCX. Tamanho: {len(text)} caracteres")
            return text
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX: {str(e)}")
            return f"Error: Failed to extract text from DOCX: {str(e)}"

    def _extract_text_from_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file."""
        try:
            logger.info(f"Extraindo texto do Markdown: {file_path}")
            
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                text = file.read()
            
            if not text.strip():
                logger.error("Nenhum texto extraído do Markdown")
                return "Error: No text extracted from Markdown"
            
            logger.info(f"Texto extraído com sucesso do Markdown. Tamanho: {len(text)} caracteres")
            return text
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do Markdown: {str(e)}")
            return f"Error: Failed to extract text from Markdown: {str(e)}"

    def _extract_text_from_zip(self, file_path: str, max_chars: int) -> str:
        """Extract text from ZIP file."""
        try:
            logger.info(f"Extraindo texto do ZIP: {file_path}")
            text = ""
            temp_dir = None
            
            try:
                # Cria diretório temporário
                temp_dir = tempfile.mkdtemp()
                logger.info(f"Diretório temporário criado: {temp_dir}")
                
                # Extrai arquivo ZIP
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                logger.info("Arquivo ZIP extraído com sucesso")
                
                # Processa arquivos extraídos
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        logger.info(f"Processando arquivo extraído: {file_path}")
                        
                        try:
                            # Tenta extrair texto
                            file_text = self._run(file_path)
                            
                            if not file_text.startswith("Error:"):
                                text += f"\n\n=== {file} ===\n\n{file_text}"
                                logger.debug(f"Texto extraído do arquivo {file}: {file_text[:100]}")
                            else:
                                logger.warning(f"Erro ao extrair texto do arquivo {file}: {file_text}")
                                
                        except Exception as e:
                            logger.error(f"Erro ao processar arquivo {file}: {str(e)}")
                            continue
                
                if not text.strip():
                    logger.error("Nenhum texto extraído do ZIP")
                    return "Error: No text extracted from ZIP"
                
                # Limita tamanho do texto
                if len(text) > max_chars:
                    text = text[:max_chars] + f"\n\n[Texto truncado em {max_chars} caracteres]"
                
                logger.info(f"Texto extraído com sucesso do ZIP. Tamanho: {len(text)} caracteres")
                return text
                
            finally:
                # Limpa diretório temporário
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Diretório temporário removido: {temp_dir}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto do ZIP: {str(e)}")
            return f"Error: Failed to extract text from ZIP: {str(e)}" 