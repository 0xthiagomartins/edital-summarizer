import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Configura e retorna um logger."""
    logger = logging.getLogger(name or __name__)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    
    return logger 