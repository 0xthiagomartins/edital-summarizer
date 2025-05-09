#!/usr/bin/env python
import os
import sys
import argparse
import warnings
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Carregando variáveis de ambiente diretamente
load_dotenv()

from edital_summarizer.crew import EditalSummarizer
from edital_summarizer.processors.document import DocumentProcessor

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


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
        "-o",
        "--output",
        default="relatorio_editais.xlsx",
        help="Caminho para o arquivo de saída (Excel)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Ativar modo verboso para exibir logs detalhados",
    )

    parser.add_argument(
        "--exec-only",
        action="store_true",
        help="Gerar apenas resumo executivo (mais rápido)",
    )

    parser.add_argument(
        "--tech-only",
        action="store_true",
        help="Gerar apenas resumo técnico (mais rápido)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout para chamadas de API em segundos (padrão: 300)",
    )

    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Apenas escanear os documentos sem processá-los",
    )

    parser.add_argument(
        "--ignore-metadata",
        action="store_true",
        help="Ignorar arquivo metadata.json e sempre extrair metadados usando IA",
    )

    parser.add_argument(
        "--full-content",
        action="store_true",
        help="Processar o conteúdo completo do documento (sem truncamento). Por padrão, o conteúdo é limitado para otimizar custos.",
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
        # Se --scan-only, apenas escaneamos os documentos
        if args.scan_only:
            processor = DocumentProcessor()
            document_data = processor.process_path(document_path)

            print("\n=== DOCUMENTOS ENCONTRADOS ===")

            if "documents" in document_data:
                docs = document_data["documents"]
                print(f"Total de documentos: {len(docs)}")

                if document_data.get("has_metadata_file"):
                    print(f"\nMetadados encontrados no diretório: metadata.json")
                    metadata = document_data.get("metadata", {})
                    if metadata:
                        print(
                            f"  Objeto: {metadata.get('subject', {}).get('object', 'N/A')}"
                        )
                        print(
                            f"  Órgão: {metadata.get('organization', {}).get('organization', 'N/A')}"
                        )
                        print(
                            f"  Edital: {metadata.get('identifier', {}).get('public_notice', 'N/A')}"
                        )

                for i, doc in enumerate(docs, 1):
                    print(f"\nDocumento {i}: {doc['file_name']}")
                    print(f"  Tipo: {doc.get('type', 'desconhecido')}")
                    print(f"  Tamanho: {doc['size']} caracteres")

                    if doc.get("has_metadata_file"):
                        print(f"  Metadados: Encontrados (metadata.json)")
            else:
                # Arquivo único
                print(f"Documento: {document_data['file_name']}")
                print(f"Tipo: {document_data.get('type', 'desconhecido')}")
                print(f"Tamanho: {document_data['size']} caracteres")

                if document_data.get("has_metadata_file"):
                    print(f"Metadados: Encontrados (metadata.json)")
                    metadata = document_data.get("metadata", {})
                    if metadata:
                        print(
                            f"  Objeto: {metadata.get('subject', {}).get('object', 'N/A')}"
                        )
                        print(
                            f"  Órgão: {metadata.get('organization', {}).get('organization', 'N/A')}"
                        )
                        print(
                            f"  Edital: {metadata.get('identifier', {}).get('public_notice', 'N/A')}"
                        )

            sys.exit(0)

        # Caso contrário, verificamos as variáveis de ambiente
        check_environment()

        # Criar e configurar o crew
        edital_summarizer = EditalSummarizer()

        # Processar o documento
        result = edital_summarizer.process_document(
            document_path=document_path,
            output_file=output_file,
            verbose=args.verbose,
            ignore_metadata=args.ignore_metadata,
            full_content=args.full_content,
        )

        print(f"\nProcessamento concluído com sucesso!")
        print(f"Documentos processados: {result['documents_processed']}")
        print(f"Relatório salvo em: {result['output_file']}")

    except Exception as e:
        print(f"ERRO durante o processamento: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run()
