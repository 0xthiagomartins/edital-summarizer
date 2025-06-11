import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from flow.edital_flow import kickoff
from utils import parse_args

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'  # Formato mais conciso
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Configura o ambiente."""
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Configura o CrewAI
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    os.environ["OPENAI_MODEL_NAME"] = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo-preview")

def run(
    edital_path_dir: str,
    target: str,
    threshold: int = 0,
    output_file: str = "llmResponse.json",
    force_match: bool = False,
) -> Optional[dict]:
    """Executa o processamento do edital."""
    try:
        # Executa o processamento
        result = kickoff(
            edital_path_dir=edital_path_dir,
            target=target,
            threshold=threshold,
            force_match=force_match,
        )
        
        # Salva o resultado
        logger.info("Salvando resultado...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info(f"Resultado salvo em: {output_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        return None

def main():
    """Função principal."""
    # Parse arguments
    args = parse_args()
    
    # Configura o ambiente
    setup_environment()
    
    # Log inicial
    logger.info("=== Iniciando processamento ===")
    logger.info(f"Edital: {args.edital_path_dir}")
    logger.info(f"Target: {args.target}")
    logger.info(f"Threshold: {args.threshold}")
    
    # Mostra nível de verbosidade
    verbosity_levels = {
        0: "Silencioso (WARNING)",
        1: "Básico (INFO)",
        2: "Detalhado (DEBUG)",
        3: "Máximo (TRACE)"
    }
    logger.info(f"Nível de Verbosidade: {verbosity_levels.get(args.verbose, 'Máximo (TRACE)')}")
    
    # Executa o processamento
    result = run(
        edital_path_dir=args.edital_path_dir,
        target=args.target,
        threshold=args.threshold,
        output_file=args.output,
        force_match=args.force_match,
    )
    
    if result:
        logger.info("=== Processamento concluído ===")
    else:
        logger.error("Ocorreu um erro durante o processamento.")
        sys.exit(1)

if __name__ == "__main__":
    main() 