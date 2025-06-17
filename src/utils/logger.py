import logging
from typing import Optional
import sys

# Cores ANSI
class Colors:
    """Cores ANSI para os logs."""
    RED = '\033[91m'      # Erro
    YELLOW = '\033[93m'   # Aviso
    GREEN = '\033[92m'    # Info
    BLUE = '\033[94m'     # Debug
    RESET = '\033[0m'     # Reset

class ColoredFormatter(logging.Formatter):
    """Formatador de logs com cores."""
    
    FORMATS = {
        logging.DEBUG: f"{Colors.BLUE}%(levelname)s: %(message)s{Colors.RESET}",
        logging.INFO: f"{Colors.GREEN}%(levelname)s: %(message)s{Colors.RESET}",
        logging.WARNING: f"{Colors.YELLOW}%(levelname)s: %(message)s{Colors.RESET}",
        logging.ERROR: f"{Colors.RED}%(levelname)s: %(message)s{Colors.RESET}",
        logging.CRITICAL: f"{Colors.RED}%(levelname)s: %(message)s{Colors.RESET}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Configura e retorna um logger."""
    logger = logging.getLogger(name or __name__)
    
    if not logger.handlers:
        # Configura o handler para stdout com cores
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(ColoredFormatter())
        logger.addHandler(stdout_handler)
        
        # Configura o handler para stderr (erros) com cores
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_formatter = logging.Formatter(
            f'{Colors.RED}ERROR: %(message)s\nFile "%(pathname)s", line %(lineno)d{Colors.RESET}'
        )
        stderr_handler.setFormatter(stderr_formatter)
        stderr_handler.setLevel(logging.ERROR)
        logger.addHandler(stderr_handler)
        
        # Define o nível de log
        logger.setLevel(logging.INFO)
    
    return logger 