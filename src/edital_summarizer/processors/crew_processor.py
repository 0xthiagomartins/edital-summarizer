import logging
from pathlib import Path
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from .base_processor import BaseProcessor
from ..utils.text_utils import clean_text
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class CrewProcessor(BaseProcessor):
    def __init__(self, target: str, threshold: int = 500, force_match: bool = False, verbose: bool = False):
        super().__init__(target, threshold, force_match, verbose)
        self.agents = {}
        self.tasks = {}
        self.crew = None
        self.document_processor = DocumentProcessor()

    def _create_agents(self) -> None:
        """Cria os agentes necessários para o processamento."""
        try:
            # Agente para análise de target
            self.agents['target_analyst'] = Agent(
                role='Analista de Target',
                goal='Analisar se o documento é relevante para o target especificado',
                backstory='Especialista em análise de documentos e identificação de relevância temática',
                verbose=self.verbose,
                allow_delegation=False
            )

            # Agente para geração de resumo
            self.agents['summary_generator'] = Agent(
                role='Gerador de Resumo',
                goal='Gerar resumos executivos de documentos',
                backstory='Especialista em síntese e resumo de documentos técnicos',
                verbose=self.verbose,
                allow_delegation=False
            )

            # Agente para geração de justificativas
            self.agents['justification_generator'] = Agent(
                role='Gerador de Justificativas',
                goal='Gerar justificativas para não geração de resumos',
                backstory='Especialista em análise documental e justificativas técnicas',
                verbose=self.verbose,
                allow_delegation=False
            )

            logger.info("Agentes criados com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar agentes: {str(e)}")
            raise

    def _create_tasks(self, document_content: str, metadata: Dict[str, Any]) -> None:
        """Cria as tarefas para o processamento do documento."""
        try:
            # Tarefa de análise de target
            self.tasks['target_analysis'] = Task(
                description=f"""
                Analise o documento e determine se ele é relevante para o target: {self.target}

                O target pode incluir uma descrição entre parênteses. Por exemplo:
                - Se o target for "RPA (Automação de Processos Robotizados)", você deve verificar se o documento
                  menciona RPA, automação de processos, processos robotizados ou termos relacionados.
                - Se o target for "Tablet (Dispositivo móvel)", você deve verificar se o documento
                  menciona tablets, dispositivos móveis ou termos relacionados.

                Considere tanto o termo principal quanto a descrição entre parênteses ao fazer a análise.

                DOCUMENTO:
                {document_content}

                METADADOS:
                {metadata}

                IMPORTANTE: 
                1. Retorne APENAS 'True' se o documento for relevante para o target ou 'False' se não for.
                2. NÃO inclua nenhum outro texto na resposta.
                3. NÃO retorne "I now can give a great answer" ou qualquer outro texto.
                4. NÃO retorne um JSON ou qualquer outro formato.
                5. A resposta DEVE ser exatamente 'True' ou 'False'.
                """,
                agent=self.agents['target_analyst'],
                expected_output="True ou False"
            )

            # Tarefa de geração de resumo do target
            self.tasks['target_summary'] = Task(
                description=f"""
                Gere um resumo executivo sobre o target: {self.target}

                IMPORTANTE:
                1. O resumo DEVE ser em português
                2. O resumo DEVE ser informativo e útil
                3. NÃO inclua nenhum texto em inglês
                4. NÃO inclua nenhum texto explicativo antes ou depois do resumo
                5. NÃO retorne "I now can give a great answer" ou qualquer outro texto em inglês
                6. O resumo DEVE ser um texto completo e coerente em português
                7. NÃO retorne um JSON ou qualquer outro formato
                """,
                agent=self.agents['summary_generator']
            )

            # Tarefa de geração de resumo do documento
            self.tasks['document_summary'] = Task(
                description=f"""
                Gere um resumo executivo do documento fornecido.

                IMPORTANTE:
                1. O resumo DEVE ser baseado APENAS no conteúdo do documento fornecido
                2. O resumo DEVE ser em português
                3. O resumo DEVE ser informativo e útil
                4. NÃO inclua nenhum texto em inglês
                5. NÃO inclua nenhum texto explicativo antes ou depois do resumo
                6. NÃO retorne "I now can give a great answer" ou qualquer outro texto em inglês
                7. O resumo DEVE ser um texto completo e coerente em português
                8. NÃO gere um resumo genérico sobre o target
                9. NÃO retorne um JSON ou qualquer outro formato
                10. Se o documento não contiver informações suficientes, retorne uma justificativa clara

                DOCUMENTO:
                {document_content}

                METADADOS:
                {metadata}
                """,
                agent=self.agents['summary_generator']
            )

            # Tarefa de geração de justificativa
            self.tasks['justification_generation'] = Task(
                description=f"""
                Gere uma justificativa clara e objetiva para a não geração do resumo.

                Considere os seguintes cenários:
                1. Se o documento não for relevante para o target '{self.target}'
                2. Se o número de referências ao target for menor que o threshold
                3. Se houver problemas na leitura do documento
                4. Se o documento estiver vazio ou não contiver informações suficientes

                DOCUMENTO:
                {document_content}

                METADADOS:
                {metadata}

                A justificativa deve ser profissional e técnica, explicando o motivo da não geração do resumo.

                IMPORTANTE:
                1. A justificativa DEVE ser em português
                2. A justificativa DEVE ser clara e objetiva
                3. NÃO inclua nenhum texto em inglês
                4. NÃO inclua nenhum texto explicativo antes ou depois da justificativa
                5. NÃO retorne o mesmo texto do resumo
                6. A justificativa DEVE explicar POR QUE o documento não é relevante ou não atende ao threshold
                7. A justificativa DEVE ser baseada APENAS no conteúdo do documento fornecido
                8. NÃO gere uma justificativa genérica, mas sim baseada no conteúdo específico do documento
                9. NÃO retorne um JSON ou qualquer outro formato
                10. NÃO retorne "I now can give a great answer" ou qualquer outro texto em inglês
                """,
                agent=self.agents['justification_generator']
            )

            logger.info("Tarefas criadas com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar tarefas: {str(e)}")
            raise

    def _create_crew(self) -> None:
        """Cria o crew para execução das tarefas."""
        try:
            self.crew = Crew(
                agents=list(self.agents.values()),
                tasks=list(self.tasks.values()),
                verbose=self.verbose,
                process=Process.sequential
            )
            logger.info("Crew criado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar crew: {str(e)}")
            raise

    def _process_with_crew(self, document_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o documento usando o crew."""
        try:
            logger.info("Iniciando Crew")
            result = self.crew.kickoff()

            target_match = False
            target_summary = ""
            document_summary = ""
            justification = ""

            for i, task_output in enumerate(result.tasks_output, 1):
                if i == 1:  # Análise de target
                    response = task_output.raw.strip().lower()
                    if response == "true":
                        target_match = True
                    elif response == "false":
                        target_match = False
                    else:
                        logger.error(f"Resposta inválida do Analista de Target: {response}")
                        target_match = False
                elif i == 2:  # Geração de resumo do target
                    target_summary = task_output.raw
                elif i == 3:  # Geração de resumo do documento
                    document_summary = task_output.raw
                elif i == 4:  # Geração de justificativa
                    justification = task_output.raw

            if not target_match or not document_content:
                return {
                    "target_match": False,
                    "threshold_match": False,
                    "target_summary": target_summary,
                    "document_summary": "",
                    "justification": justification if justification else "Não foi possível ler o conteúdo do documento devido a problemas de codificação.",
                    "metadata": metadata
                }

            return {
                "target_match": True,
                "threshold_match": True,
                "target_summary": target_summary,
                "document_summary": document_summary,
                "justification": "",
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Erro ao processar com crew: {str(e)}")
            return {
                "target_match": False,
                "threshold_match": False,
                "target_summary": "",
                "document_summary": "",
                "justification": f"Erro ao processar documento: {str(e)}",
                "metadata": {}
            }

    def process(self, document_path: str) -> Dict[str, Any]:
        """Processa o documento usando o crew."""
        try:
            # Processa o documento
            result = self.document_processor.process_document(document_path)
            if not result:
                return {
                    "target_match": False,
                    "threshold_match": False,
                    "target_summary": "",
                    "document_summary": "",
                    "justification": "Não foi possível ler o conteúdo do documento devido a problemas de codificação.",
                    "metadata": {}
                }

            document_content = result.get("content", "")
            metadata = result.get("metadata", {})

            if not document_content:
                return {
                    "target_match": False,
                    "threshold_match": False,
                    "target_summary": "",
                    "document_summary": "",
                    "justification": "O documento está vazio ou não foi possível extrair seu conteúdo.",
                    "metadata": metadata
                }

            # Cria os agentes
            self._create_agents()

            # Cria as tarefas
            self._create_tasks(document_content, metadata)

            # Cria o crew
            self._create_crew()

            # Processa o documento
            return self._process_with_crew(document_content, metadata)

        except Exception as e:
            logger.error(f"Erro ao processar documento: {str(e)}")
            return {
                "target_match": False,
                "threshold_match": False,
                "target_summary": "",
                "document_summary": "",
                "justification": f"Erro ao processar documento: {str(e)}",
                "metadata": {}
            } 