from typing import List

def is_device_target(target: str) -> bool:
    """
    Verifica se o target é relacionado a dispositivos.
    
    Args:
        target: Termo ou descrição para análise
        
    Returns:
        True se o target for relacionado a dispositivos, False caso contrário
    """
    device_keywords = ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']
    return any(keyword in target.lower() for keyword in device_keywords)

def get_device_keywords() -> List[str]:
    """
    Retorna a lista de palavras-chave para dispositivos.
    
    Returns:
        Lista de palavras-chave para dispositivos
    """
    return ['tablet', 'celular', 'notebook', 'smartphone', 'laptop']

def check_device_threshold(text: str, threshold: int) -> bool:
    """
    Verifica se o texto contém referências suficientes a dispositivos.
    
    Args:
        text: Texto a ser analisado
        threshold: Valor mínimo para contagem de referências
        
    Returns:
        True se o número de referências for maior ou igual ao threshold, False caso contrário
    """
    device_keywords = get_device_keywords()
    count = sum(text.lower().count(keyword) for keyword in device_keywords)
    return count >= threshold 