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
        
        # Extrai apenas os campos relevantes
        output = {
            "bid_number": result.bid_number,
            "city": result.city,
            "metadata": {
                "title": result.metadata.get("title", ""),
                "object": result.metadata.get("object", ""),
                "quantities": result.metadata.get("quantities", ""),
                "specifications": result.metadata.get("specifications", ""),
                "deadlines": result.metadata.get("deadlines", ""),
                "values": result.metadata.get("values", ""),
                "phone": result.metadata.get("phone", ""),
                "website": result.metadata.get("website", ""),
                "email": result.metadata.get("email", "")
            },
            "target_match": result.target_match,
            "threshold_match": result.threshold_match,
            "is_relevant": result.is_relevant,
            "summary": result.summary,
            "justification": result.justification
        }
        
        # Salva o resultado
        logger.info("Salvando resultado...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Resultado salvo em: {output_file}")
        
        # Mostra informações relevantes no log
        logger.info("\n=== Resumo do Processamento ===")
        logger.info(f"Número do Edital: {result.bid_number}")
        logger.info(f"Cidade/UF: {result.city}")
        logger.info(f"Título: {result.metadata.get('title', 'Não informado')}")
        logger.info(f"Objeto: {result.metadata.get('object', 'Não informado')}")
        logger.info(f"Quantidades: {result.metadata.get('quantities', 'Não informado')}")
        logger.info(f"Especificações: {result.metadata.get('specifications', 'Não informado')}")
        logger.info(f"Prazos: {result.metadata.get('deadlines', 'Não informado')}")
        logger.info(f"Valores: {result.metadata.get('values', 'Não informado')}")
        logger.info(f"Contatos:")
        logger.info(f"  - Telefone: {result.metadata.get('phone', 'Não informado')}")
        logger.info(f"  - Website: {result.metadata.get('website', 'Não informado')}")
        logger.info(f"  - Email: {result.metadata.get('email', 'Não informado')}")
        logger.info(f"\nRelevância:")
        logger.info(f"  - Match com Target: {'Sim' if result.target_match else 'Não'}")
        logger.info(f"  - Match com Threshold: {result.threshold_match}")
        logger.info(f"  - Edital Relevante: {'Sim' if result.is_relevant else 'Não'}")
        logger.info(f"\nResumo: {result.summary}")
        logger.info(f"\nJustificativa: {result.justification}")
        
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
    logger.info("\n=== Iniciando Processamento ===")
    logger.info(f"Edital: {args.edital_path_dir}")
    logger.info(f"Target: {args.target}")
    logger.info(f"Threshold: {args.threshold}")
    logger.info(f"Forçar Match: {'Sim' if args.force_match else 'Não'}")
    
    # Mostra nível de verbosidade
    verbosity_levels = {
        0: "Silencioso (WARNING)",
        1: "Básico (INFO)",
        2: "Detalhado (DEBUG)",
        3: "Máximo (TRACE)"
    }
    logger.info(f"Nível de Verbosidade: {verbosity_levels.get(args.verbose, 'Máximo (TRACE)')}")
    logger.info(f"Arquivo de Saída: {args.output}")
    logger.info("=" * 50)
    
    # Executa o processamento
    result = run(
        edital_path_dir=args.edital_path_dir,
        target=args.target,
        threshold=args.threshold,
        output_file=args.output,
        force_match=args.force_match,
    )
    
    if result:
        logger.info("\n=== Processamento Concluído com Sucesso ===")
    else:
        logger.error("\n=== Ocorreu um Erro Durante o Processamento ===")
        sys.exit(1)

if __name__ == "__main__":
    main() 