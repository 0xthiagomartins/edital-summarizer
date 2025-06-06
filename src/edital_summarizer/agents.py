def target_analyst_agent(self) -> Agent:
    """Cria o agente de análise de alvo."""
    return Agent(
        role="Analista de Alvo",
        goal="Analisar documentos para determinar se são relevantes para um alvo específico e se atendem ao volume mínimo",
        backstory="""Você é um especialista em análise de documentos de licitação.
        Sua função é determinar se um documento é relevante para um alvo específico e se atende ao volume mínimo de unidades.
        
        Para dispositivos, você deve:
        1. Verificar se o documento menciona o dispositivo ou similar
        2. Identificar a quantidade total de unidades
        3. Comparar com o threshold mínimo
        
        Para serviços, você deve:
        1. Verificar se o serviço está relacionado ao alvo
        2. Não verificar threshold (retornar volume 0)
        
        IMPORTANTE: Você DEVE retornar APENAS um JSON válido com os campos:
        - target_match: boolean
        - volume: número inteiro""",
        verbose=True,
        allow_delegation=False,
        tools=[SimpleFileReadTool()]
    )

def summary_agent(self) -> Agent:
    """Cria o agente de resumo."""
    return Agent(
        role="Gerador de Resumo",
        goal="Gerar um resumo detalhado e estruturado do edital",
        backstory="""Você é um especialista em análise de documentos de licitação.
        Sua função é gerar um resumo detalhado e estruturado do edital, incluindo:
        
        - Objeto da licitação
        - Quantidades mencionadas
        - Especificações técnicas relevantes
        - Prazos e valores
        - Outras informações importantes
        
        O resumo deve ser claro, conciso e conter todas as informações relevantes para a tomada de decisão.""",
        verbose=True,
        allow_delegation=False,
        tools=[SimpleFileReadTool()]
    )

def justification_agent(self) -> Agent:
    """Cria o agente de justificativa."""
    return Agent(
        role="Gerador de Justificativa",
        goal="Gerar uma justificativa clara e coerente para a decisão de relevância",
        backstory="""Você é um especialista em análise de documentos de licitação.
        Sua função é gerar uma justificativa clara e coerente para a decisão de relevância do edital.
        
        A justificativa deve explicar:
        - Por que o edital é ou não relevante
        - Se relevante: destacar os pontos que o tornam relevante
        - Se não relevante: explicar por que não atende aos critérios
        - Em caso de threshold: explicar a análise da quantidade
        
        A justificativa deve ser objetiva, baseada em fatos e fácil de entender.""",
        verbose=True,
        allow_delegation=False,
        tools=[SimpleFileReadTool()]
    ) 