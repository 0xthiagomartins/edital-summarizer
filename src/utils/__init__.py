"""
Módulo de Utilitários (utils)

Este módulo contém funções e classes utilitárias que são usadas em todo o projeto.
São funções genéricas que podem ser reutilizadas em diferentes partes do sistema.

Componentes principais:
- logger: Configuração de logging para o projeto
- metadata: Funções para leitura e manipulação de metadata de editais
- extractor: Classes e funções para extrair informações estruturadas de texto
"""

from typing import Dict, Any
import yaml
import argparse
import os
import sys
import logging

def load_yaml_config(path: str) -> Dict[str, Any]:
    """Carrega configuração YAML."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

from .logger import get_logger
from .metadata import read_metadata
from .extractor import extract_info, ExtractedInfo, InformationExtractor

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Processador de Editais de Licitação utilizando Flow"
    )

    parser.add_argument(
        "edital_path_dir",
        help="Caminho para o diretório do edital contendo os documentos a serem processados",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target para análise (ex: RPA, Notebooks, etc.)"
    )

    parser.add_argument(
        "--threshold",
        type=int,
        required=True,
        help="Threshold mínimo para dispositivos (use 0 para serviços)"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Caminho para o arquivo de saída (JSON)"
    )

    # Configuração de verbosidade
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Nível de verbosidade (-v: INFO, -vv: DEBUG, -vvv: TRACE)"
    )

    parser.add_argument(
        "--force-match",
        action="store_true",
        help="Forçar match do target (ignora threshold)",
    )

    args = parser.parse_args()
    
    # Configura o nível de log baseado no modo verboso
    if args.verbose == 0:
        # Modo silencioso
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger('crewai').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    elif args.verbose == 1:
        # Verboso básico
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('crewai').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    elif args.verbose == 2:
        # Verboso detalhado
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('crewai').setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.INFO)
    else:
        # Verboso máximo
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('crewai').setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.DEBUG)
        # Adiciona mais loggers se necessário
    
    return args

def check_environment():
    """Verifica se as variáveis de ambiente necessárias estão definidas."""
    required_vars = {
        "MODEL": "Modelo LLM a ser utilizado (ex: openai/gpt-4-turbo-preview)",
        "OPENAI_API_KEY": "Chave de API da OpenAI",
    }

    missing = []
    for var, desc in required_vars.items():
        if not os.environ.get(var):
            missing.append(f"{var}: {desc}")

    if missing:
        logger.error("Variáveis de ambiente necessárias não definidas:")
        for msg in missing:
            logger.error(f"  - {msg}")
        logger.error("\nDefina essas variáveis no arquivo .env ou no ambiente antes de executar.")
        sys.exit(1)

    # Valida o formato do MODEL
    model = os.environ.get("MODEL", "")
    if not model or "/" not in model:
        logger.error("MODEL deve estar no formato 'provedor/modelo' (ex: openai/gpt-4-turbo-preview)")
        sys.exit(1)

__all__ = [
    'get_logger',
    'load_yaml_config',
    'read_metadata',
    'extract_info',
    'ExtractedInfo',
    'parse_args',
    'check_environment',
    'InformationExtractor'
] 