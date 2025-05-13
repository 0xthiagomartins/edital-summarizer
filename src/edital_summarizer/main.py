#!/usr/bin/env python
import os
import sys
import argparse
import warnings
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Carregando variáveis de ambiente diretamente
load_dotenv()

from edital_summarizer.crew import EditalSummarizer
from edital_summarizer.processors.document import DocumentProcessor
from .utils.logger import get_logger

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

logger = get_logger(__name__)

def is_device_target(target: str) -> bool:
    """Verifica se o target é relacionado a dispositivos."""
    device_keywords = ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']
    return any(keyword in target.lower() for keyword in device_keywords)

def check_device_threshold(text: str, threshold: int) -> bool:
    """Verifica se o texto contém referências suficientes a dispositivos."""
    device_keywords = ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']
    count = sum(text.lower().count(keyword) for keyword in device_keywords)
    return count >= threshold

def process_edital(edital_path: str, target: str, threshold: int = 500) -> Dict[str, Any]:
    """Processa um edital e retorna um dicionário com os resultados."""
    try:
        # Inicializa o resultado
        result = {
            "target_match": False,
            "threshold_match": True,  # Assume True por padrão se não for dispositivo
            "summary": "",
            "metadata": {}
        }

        # Cria a instância do crew
        crew = EditalSummarizer(verbose=True)
        
        # Verifica se é target de dispositivo
        if is_device_target(target):
            # Verifica o threshold
            with open(edital_path, 'r', encoding='utf-8') as f:
                text = f.read()
            if not check_device_threshold(text, threshold):
                result["threshold_match"] = False
                return result

        # Processa o edital
        output = crew.kickoff(edital_path, target)
        
        # Atualiza o resultado
        result["target_match"] = output.get("target_match", False)
        result["metadata"] = output.get("metadata", {})
        
        # Só gera resumo se o target der match
        if result["target_match"]:
            result["summary"] = output.get("summary", "")
        
        return result

    except Exception as e:
        logger.error(f"Erro ao processar edital: {str(e)}")
        return {
            "target_match": False,
            "threshold_match": False,
            "summary": "",
            "metadata": {},
            "error": str(e)
        }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Processador de Editais de Licitação utilizando CrewAI"
    )

    parser.add_argument(
        "document_path",
        help="Caminho para o documento ou diretório de documentos a serem processados",
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

    # Validar caminho do documento
    document_path = args.document_path
    if not os.path.exists(document_path):
        print(f"ERRO: Caminho não encontrado: {document_path}")
        sys.exit(1)

    # Criar diretório de saída se necessário
    output_file = args.output
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.verbose:
        print(f"Processando: {document_path}")
        print(f"Arquivo de saída: {output_file}")

    try:
        # Processa o edital
        edital_result = process_edital(document_path, args.target, args.threshold)
        
        # Salva o resultado em JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edital_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultado salvo em: {output_file}")

    except Exception as e:
        print(f"ERRO durante o processamento: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run()
