import os
import sys
import argparse
import warnings
import json
import traceback
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

from edital_summarizer.crew import EditalSummarizer
from edital_summarizer.utils.logger import get_logger

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Processador de Editais de Licitação utilizando CrewAI"
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
        default=500,
        help="Threshold mínimo para dispositivos (use 0 para serviços)"
    )

    parser.add_argument(
        "--output",
        default="resultado.json",
        help="Caminho para o arquivo de saída (JSON)"
    )

    parser.add_argument(
        "--force-match",
        action="store_true",
        help="Força o target_match a ser True"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Ativar modo verboso para exibir logs detalhados",
    )

    return parser.parse_args()

def check_environment():
    """Verifica se as variáveis de ambiente necessárias estão definidas."""
    required_vars = {
        "OPENAI_API_KEY": "Necessária para os modelos OpenAI GPT-4",
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

def validate_result(result: Dict[str, Any]) -> bool:
    """Valida se o resultado contém todos os campos necessários."""
    required_fields = ["bid_number", "city", "target_match", "threshold_match", "is_relevant", "summary", "justification"]
    
    for field in required_fields:
        if field not in result:
            logger.error(f"Campo obrigatório ausente no resultado: {field}")
            return False
    
    # Valida tipos dos campos
    if not isinstance(result["bid_number"], str):
        logger.error("bid_number deve ser uma string")
        return False
        
    if not isinstance(result["city"], str):
        logger.error("city deve ser uma string")
        return False
        
    if not isinstance(result["target_match"], bool):
        logger.error("target_match deve ser um booleano")
        return False
        
    if result["threshold_match"] not in ["true", "false", "inconclusive"]:
        logger.error("threshold_match deve ser 'true', 'false' ou 'inconclusive'")
        return False
        
    if not isinstance(result["is_relevant"], bool):
        logger.error("is_relevant deve ser um booleano")
        return False
        
    if not isinstance(result["summary"], str):
        logger.error("summary deve ser uma string")
        return False
        
    if not isinstance(result["justification"], str):
        logger.error("justification deve ser uma string")
        return False
    
    return True

def run():
    """
    Função principal para execução da CLI.
    """
    try:
        args = parse_args()

        # Validar caminho do edital
        edital_path_dir = args.edital_path_dir
        if not os.path.exists(edital_path_dir):
            logger.error(f"Caminho não encontrado: {edital_path_dir}")
            sys.exit(1)

        # Criar diretório de saída se necessário
        output_file = args.output
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logger.info(f"\n=== Iniciando processamento ===")
        logger.info(f"Diretório do Edital: {edital_path_dir}")
        logger.info(f"Target: {args.target}")
        logger.info(f"Threshold: {args.threshold}")
        logger.info(f"Force Match: {args.force_match}")
        logger.info(f"Modo Verboso: {args.verbose}")
        logger.info(f"Arquivo de saída: {output_file}\n")

        try:
            logger.info("=== Iniciando processamento com Crew ===")
            # Cria a instância do summarizer
            summarizer = EditalSummarizer(verbose=args.verbose)
            
            # Cria e executa a crew
            crew = summarizer.crew(
                edital_path_dir=edital_path_dir,
                target=args.target,
                threshold=args.threshold,
                force_match=args.force_match
            )
            
            # Executa o processamento
            result = crew.kickoff(inputs={
                "edital_path_dir": edital_path_dir,
                "target": args.target,
                "threshold": args.threshold,
                "force_match": args.force_match
            })
            
            # Processa o resultado
            processed_result = summarizer.process_output(result)
            
            # Valida o resultado
            if not validate_result(processed_result):
                logger.error("Resultado inválido gerado pelo processamento")
                sys.exit(1)
            
            logger.info("\n=== Salvando resultado ===")
            # Salva o resultado em JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultado salvo em: {output_file}")
            logger.info("\n=== Processamento concluído ===")

        except Exception as e:
            logger.error(f"\nERRO durante o processamento: {str(e)}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\nERRO FATAL: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    run()