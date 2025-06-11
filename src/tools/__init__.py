"""
Módulo de Ferramentas (tools)

Este módulo contém ferramentas específicas que são usadas pelo CrewAI para interagir
com o mundo externo. São ferramentas que os agents podem usar para realizar tarefas
específicas, como ler arquivos, fazer chamadas de API, etc.

Diferente do módulo utils, as ferramentas aqui são:
1. Específicas para uso com CrewAI
2. Implementam a interface BaseTool do CrewAI
3. São usadas diretamente pelos agents durante a execução

Componentes principais:
- file_tools: Ferramentas para leitura e manipulação de arquivos (PDF, DOCX, etc)
"""

from .file_tools import FileReadTool

__all__ = ['FileReadTool'] 