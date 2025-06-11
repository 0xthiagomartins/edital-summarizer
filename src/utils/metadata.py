import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class EditalMetadata(BaseModel):
    """Modelo para o metadata do edital."""
    object: Optional[str] = Field(None, description="Objeto da licitação")
    dates: Optional[str] = Field(None, description="Datas importantes")
    public_notice: Optional[str] = Field(None, description="Número do aviso público")
    status: Optional[str] = Field(None, description="Status do edital")
    agency: Optional[str] = Field(None, description="Órgão responsável")
    bid_number: str = Field(..., description="Número do edital/licitação")
    notes: Optional[str] = Field(None, description="Notas adicionais")
    process_id: Optional[str] = Field(None, description="ID do processo")
    phone: Optional[str] = Field(None, description="Telefone de contato")
    website: Optional[str] = Field(None, description="Website")
    email: Optional[str] = Field(None, description="Email de contato")
    manager: Optional[str] = Field(None, description="Gerente responsável")

def read_metadata(edital_path_dir: str) -> Dict[str, Any]:
    """Lê e processa o arquivo metadata.json do edital."""
    logger.info(f"\n=== Lendo metadata.json ===")
    
    metadata_path = os.path.join(edital_path_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        logger.warning(f"metadata.json não encontrado em: {metadata_path}")
        return {"bid_number": "N/A"}

    # Lista de encodings para tentar
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(metadata_path, 'r', encoding=encoding) as f:
                content = f.read()
                # Tenta decodificar o conteúdo
                metadata = json.loads(content)
                
                # Valida usando o modelo Pydantic
                try:
                    output = EditalMetadata(**metadata)
                    logger.info(f"metadata.json lido com sucesso usando encoding {encoding}")
                    return output.dict()
                except Exception as e:
                    logger.warning(f"Erro ao validar metadata com encoding {encoding}: {str(e)}")
                    # Se falhar na validação, retorna os dados brutos
                    return metadata
                    
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.warning(f"Erro ao ler com encoding {encoding}: {str(e)}")
            continue
            
    logger.warning("Não foi possível ler o metadata.json com nenhum encoding")
    return {"bid_number": "N/A"}

def extract_city(metadata: Dict[str, Any]) -> str:
    """Extrai a cidade/UF do metadata."""
    try:
        # Tenta extrair do campo agency
        if "agency" in metadata:
            agency = metadata["agency"]
            # Procura por padrões como "Cidade/UF" ou "Cidade - UF"
            import re
            patterns = [
                r"([A-Za-z\s]+)/([A-Z]{2})",  # Cidade/UF
                r"([A-Za-z\s]+)\s*-\s*([A-Z]{2})",  # Cidade - UF
                r"([A-Za-z\s]+),\s*([A-Z]{2})"  # Cidade, UF
            ]
            
            for pattern in patterns:
                match = re.search(pattern, agency)
                if match:
                    city = match.group(1).strip()
                    uf = match.group(2)
                    return f"{city}/{uf}"
                    
        # Se não encontrou, retorna N/A
        return "N/A"
        
    except Exception as e:
        logger.error(f"Erro ao extrair cidade do metadata: {str(e)}")
        return "N/A"

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """Valida se o metadata contém os campos necessários."""
    try:
        # Valida campos obrigatórios
        if "bid_number" not in metadata:
            logger.error("Campo obrigatório ausente: bid_number")
            return False
            
        # Valida tipos dos campos
        if not isinstance(metadata["bid_number"], str):
            logger.error("bid_number deve ser uma string")
            return False
            
        # Valida campos opcionais
        optional_fields = ["object", "dates", "public_notice", "status", "agency"]
        for field in optional_fields:
            if field in metadata and not isinstance(metadata[field], (str, type(None))):
                logger.error(f"{field} deve ser uma string ou None")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Erro ao validar metadata: {str(e)}")
        return False 