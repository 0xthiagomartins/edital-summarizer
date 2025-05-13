from typing import Dict, Any

def get_agents() -> Dict[str, Any]:
    """Retorna a configuração dos agentes."""
    return {
        "metadata_agent": {
            "role": "Especialista em Metadados",
            "goal": "Extrair metadados relevantes de documentos de licitação",
            "backstory": """Você é um especialista em análise de documentos de licitação.
            Sua função é extrair metadados importantes como identificadores, organização e objeto."""
        },
        "summary_agent": {
            "role": "Especialista em Resumos",
            "goal": "Criar resumos executivos e técnicos de documentos de licitação",
            "backstory": """Você é um especialista em criar resumos de documentos técnicos.
            Sua função é extrair os pontos mais importantes e criar resumos claros e concisos."""
        }
    } 