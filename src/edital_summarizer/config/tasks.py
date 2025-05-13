from typing import Dict, Any

def get_tasks() -> Dict[str, Any]:
    """Retorna a configuração das tasks."""
    return {
        "metadata_task": {
            "description": """Analise o documento e extraia os seguintes metadados:
            1. Identificadores (número do edital, processo, licitação)
            2. Organização (nome, telefone, website, local)
            3. Objeto da licitação
            
            Retorne os metadados em formato JSON.""",
            "expected_output": "JSON com metadados extraídos"
        },
        "summary_task": {
            "description": """Crie um resumo executivo do documento, destacando:
            1. Objeto principal
            2. Prazos importantes
            3. Valores relevantes
            4. Requisitos principais
            
            O resumo deve ser conciso e informativo.""",
            "expected_output": "Resumo executivo em português"
        }
    } 