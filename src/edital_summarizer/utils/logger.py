import logging
from typing import Optional
import sys

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Configura e retorna um logger."""
    logger = logging.getLogger(name or __name__)
    
    if not logger.handlers:
        # Configura o handler para stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        stdout_handler.setFormatter(stdout_formatter)
        logger.addHandler(stdout_handler)
        
        # Configura o handler para stderr (erros)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File "%(pathname)s", line %(lineno)d\n'
            '%(message)s'
        )
        stderr_handler.setFormatter(stderr_formatter)
        stderr_handler.setLevel(logging.ERROR)
        logger.addHandler(stderr_handler)
        
        # Define o nível de log
        logger.setLevel(logging.INFO)
    
    return logger 