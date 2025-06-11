"""
Módulo de Flow (flow)

Este módulo contém a implementação do fluxo principal do processamento de editais
usando CrewAI Flow. O flow define a sequência de etapas que um edital passa durante
seu processamento, desde a extração de metadata até a geração do resumo final.

Componentes principais:
- edital_flow: Implementação do EditalAnalysisFlow que coordena todo o processamento
"""

from .edital_flow import EditalAnalysisFlow

__all__ = ['EditalAnalysisFlow'] 