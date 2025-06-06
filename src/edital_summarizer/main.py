import os
import sys
import argparse
import warnings
import json
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
        help="Target para análise (ex: RPA)"
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=500,
        help="Threshold mínimo para dispositivos"
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
        "GOOGLE_API_KEY": "Necessária para os modelos Google Gemini Pro",
    }

    missing = []
    for var, desc in required_vars.items():
        if not os.environ.get(var):
            missing.append(f"{var}: {desc}")

    if missing:
        print("ERRO: Variáveis de ambiente necessárias não definidas:")
        for msg in missing:
            print(f"  - {msg}")
        print(
            "\nDefina essas variáveis no arquivo .env ou no ambiente antes de executar."
        )
        sys.exit(1)

def run():
    """
    Função principal para execução da CLI.
    """
    args = parse_args()

    # Validar caminho do edital
    edital_path_dir = args.edital_path_dir
    if not os.path.exists(edital_path_dir):
        print(f"ERRO: Caminho não encontrado: {edital_path_dir}")
        sys.exit(1)

    # Criar diretório de saída se necessário
    output_file = args.output
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"\n=== Iniciando processamento ===")
    print(f"Diretório do Edital: {edital_path_dir}")
    print(f"Target: {args.target}")
    print(f"Threshold: {args.threshold}")
    print(f"Force Match: {args.force_match}")
    print(f"Modo Verboso: {args.verbose}")
    print(f"Arquivo de saída: {output_file}\n")

    try:
        print("=== Iniciando processamento com Crew ===")
        # Cria a instância do crew
        crew = EditalSummarizer(verbose=args.verbose)
        
        # Processa o edital
        result = crew.kickoff(
            edital_path_dir=edital_path_dir,
            target=args.target,
            threshold=args.threshold,
            force_match=args.force_match
        )
        
        print("\n=== Salvando resultado ===")
        # Salva o resultado em JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Resultado salvo em: {output_file}")
        print("\n=== Processamento concluído ===")

    except Exception as e:
        print(f"\nERRO durante o processamento: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()