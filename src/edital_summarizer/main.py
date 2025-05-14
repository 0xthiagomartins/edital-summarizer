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
from edital_summarizer.processors.metadata import MetadataProcessor
from edital_summarizer.processors.summary import SummaryProcessor
from edital_summarizer.utils.logger import get_logger

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

def process_edital(document_path: str, target: str, threshold: int = 500, force_match: bool = False, verbose: bool = False, output_file: str = "llmResponse.json") -> dict:
    """Processa um edital e retorna o resultado."""
    try:
        # Inicializa o processador
        summarizer = EditalSummarizer()
        
        # Processa o documento
        result = summarizer.kickoff(document_path, target, threshold)
        
        # Se force_match for True, força o target_match e usa o resumo gerado
        if force_match:
            return {
                "target_match": True,  # Força o target_match
                "threshold_match": True,
                "target_summary": result["document_summary"],  # Usa o resumo gerado
                "document_summary": result["document_summary"],  # Usa o resumo gerado
                "justification": "",  # Limpa a justificativa já que forçamos o match
                "metadata": {}
            }
        
        # Se não houver match e não for forçado, retorna a justificativa
        if not result["target_match"]:
            return {
                "target_match": False,
                "threshold_match": True,
                "target_summary": "",
                "document_summary": "",
                "justification": result["justification"],
                "metadata": {}
            }
        
        # Se houver match, retorna o resumo
        return {
            "target_match": result["target_match"],
            "threshold_match": True,
            "target_summary": result["target_summary"],
            "document_summary": result["document_summary"],
            "justification": result["justification"],
            "metadata": {}
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar edital: {str(e)}")
        return {
            "target_match": False,
            "threshold_match": False,
            "target_summary": "",
            "document_summary": "",
            "justification": f"Erro ao processar edital: {str(e)}",
            "metadata": {}
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

    print(f"\n=== Iniciando processamento ===")
    print(f"Documento: {document_path}")
    print(f"Target: {args.target}")
    print(f"Threshold: {args.threshold}")
    print(f"Force Match: {args.force_match}")
    print(f"Modo Verboso: {args.verbose}")
    print(f"Arquivo de saída: {output_file}\n")

    try:
        # Se force_match for True, força o target_match mas ainda usa o crew para gerar o resumo
        if args.force_match:
            print("=== Modo Force Match Ativado ===")
            # Verifica se é um diretório
            if os.path.isdir(document_path):
                print("Processando diretório...")
                # Processa todos os arquivos no diretório
                all_text = ""
                for root, _, files in os.walk(document_path):
                    for file in files:
                        if file.endswith('.txt'):  # Processa apenas arquivos .txt
                            file_path = os.path.join(root, file)
                            print(f"Lendo arquivo: {file_path}")
                            with open(file_path, 'r', encoding='utf-8') as f:
                                all_text += f.read() + "\n\n"
                
                print("Processando metadados...")
                # Processa os metadados do texto combinado
                metadata_processor = MetadataProcessor()
                metadata = metadata_processor.process({"text": all_text})
            else:
                print("Processando arquivo único...")
                # Processa um único arquivo
                with open(document_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                print("Processando metadados...")
                # Processa os metadados
                metadata_processor = MetadataProcessor()
                metadata = metadata_processor.process({"text": text})
            
            print("\n=== Iniciando Crew para geração do resumo ===")
            # Cria a instância do crew
            crew = EditalSummarizer(verbose=True)
            
            # Processa o edital forçando o target_match
            output = crew.kickoff(document_path, args.target)
            
            # Força o target_match e threshold_match para True
            output["target_match"] = True
            output["threshold_match"] = True
            
            result = output
            
        else:
            print("=== Iniciando processamento normal com Crew ===")
            # Processa normalmente usando o crew
            result = process_edital(document_path, args.target, args.threshold)
        
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
