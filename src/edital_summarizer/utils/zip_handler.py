import os
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from .logger import get_logger

logger = get_logger(__name__)

class ZipHandler:
    """Classe para lidar com arquivos ZIP em editais."""

    @staticmethod
    def is_zip_file(file_path: str) -> bool:
        """Verifica se o arquivo é um ZIP."""
        return file_path.lower().endswith('.zip')

    @staticmethod
    def extract_zip(zip_path: str, extract_to: str = None) -> str:
        """
        Extrai um arquivo ZIP para um diretório temporário ou especificado.
        
        Args:
            zip_path: Caminho do arquivo ZIP
            extract_to: Diretório de destino (opcional)
            
        Returns:
            Caminho do diretório onde os arquivos foram extraídos
        """
        try:
            # Se não for especificado um diretório de destino, usa um temporário
            if not extract_to:
                extract_to = tempfile.mkdtemp(prefix='edital_zip_')
            
            # Cria o diretório se não existir
            os.makedirs(extract_to, exist_ok=True)
            
            # Extrai o ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            logger.info(f"Arquivo ZIP extraído para: {extract_to}")
            return extract_to
            
        except Exception as e:
            logger.error(f"Erro ao extrair arquivo ZIP: {str(e)}")
            raise

    @staticmethod
    def get_zip_contents(extract_path: str) -> List[Dict[str, Any]]:
        """
        Lista os conteúdos do diretório extraído.
        
        Args:
            extract_path: Caminho do diretório extraído
            
        Returns:
            Lista de dicionários com informações dos arquivos
        """
        contents = []
        
        try:
            for root, _, files in os.walk(extract_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, extract_path)
                    
                    # Ignora arquivos ocultos e temporários
                    if file.startswith('.') or file.endswith('.tmp'):
                        continue
                    
                    contents.append({
                        'file_name': file,
                        'file_path': file_path,
                        'relative_path': rel_path,
                        'is_zip': file.lower().endswith('.zip')
                    })
            
            return contents
            
        except Exception as e:
            logger.error(f"Erro ao listar conteúdos do ZIP: {str(e)}")
            raise

    @staticmethod
    def cleanup_temp_dir(temp_dir: str) -> None:
        """
        Remove um diretório temporário e seu conteúdo.
        
        Args:
            temp_dir: Caminho do diretório temporário
        """
        try:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Diretório temporário removido: {temp_dir}")
        except Exception as e:
            logger.error(f"Erro ao remover diretório temporário: {str(e)}")
            # Não propaga o erro para não interromper o processamento 