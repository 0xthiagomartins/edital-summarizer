import pandas as pd
from typing import List, Dict, Any
import os
import json


class ExcelReportGenerator:
    """
    Gera relatórios em formato Excel a partir dos dados processados dos editais.
    """

    def generate_report(self, results: List[Dict[str, Any]], output_file: str) -> str:
        """
        Gera um relatório Excel com os resultados do processamento de editais.

        Args:
            results: Lista de resultados do processamento
            output_file: Caminho para o arquivo de saída

        Returns:
            Caminho para o arquivo gerado
        """
        # Criar diretório de saída se não existir
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Preparar dados para o DataFrame
        data = []
        for result in results:
            # Extrair metadados (se existirem)
            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {"error": "Formato de metadados inválido"}

            # Extrair informações de identificação
            identifier_info = metadata.get("identifier", {})
            if isinstance(identifier_info, str):
                try:
                    identifier_info = json.loads(identifier_info)
                except:
                    identifier_info = {}

            # Extrair informações da organização
            org_info = metadata.get("organization", {})
            if isinstance(org_info, str):
                try:
                    org_info = json.loads(org_info)
                except:
                    org_info = {}

            # Extrair informações do assunto
            subject_info = metadata.get("subject", {})
            if isinstance(subject_info, str):
                try:
                    subject_info = json.loads(subject_info)
                except:
                    subject_info = {}

            # Extrair resumos
            executive_summary = result.get("executive_summary", "")
            technical_summary = result.get("technical_summary", "")

            # Criar entrada para o DataFrame
            entry = {
                "Arquivo": result.get("file_name", ""),
                "Caminho": result.get("file_path", ""),
                "Título": subject_info.get("title", ""),
                "Objeto": subject_info.get("object", ""),
                "Órgão": org_info.get("organization", ""),
                "Número do Edital": identifier_info.get("public_notice", ""),
                "Número do Processo": identifier_info.get("process_id", ""),
                "Número da Licitação": identifier_info.get("bid_number", ""),
                "Telefone": org_info.get("phone", ""),
                "Website": org_info.get("website", ""),
                "Localização": org_info.get("location", ""),
                "Datas": str(subject_info.get("dates", "")),
                "Resumo Executivo": executive_summary,
                "Resumo Técnico": technical_summary,
                "Erro": result.get("error", ""),
            }
            data.append(entry)

        # Criar DataFrame e salvar como Excel
        df = pd.DataFrame(data)

        # Salvar como Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Planilha principal com todos os dados
            df.to_excel(writer, sheet_name="Relatório Completo", index=False)

            # Planilha separada só com metadados
            metadata_cols = [
                "Arquivo",
                "Título",
                "Objeto",
                "Órgão",
                "Número do Edital",
                "Número do Processo",
                "Número da Licitação",
                "Telefone",
                "Website",
                "Localização",
                "Datas",
            ]
            df[metadata_cols].to_excel(writer, sheet_name="Metadados", index=False)

            # Planilha para cada documento com seu resumo
            for i, row in df.iterrows():
                sheet_name = f"Doc_{i+1}"
                pd.DataFrame(
                    {
                        "Atributo": [
                            "Arquivo",
                            "Título",
                            "Objeto",
                            "Resumo Executivo",
                            "Resumo Técnico",
                        ],
                        "Valor": [
                            row["Arquivo"],
                            row["Título"],
                            row["Objeto"],
                            row["Resumo Executivo"],
                            row["Resumo Técnico"],
                        ],
                    }
                ).to_excel(writer, sheet_name=sheet_name, index=False)

        return output_file
