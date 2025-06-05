import pytest
import os
import json
from edital_summarizer import process_edital

@pytest.fixture
def sample_document():
    """Cria um documento de exemplo para testes."""
    content = """
    EDITAL DE LICITAÇÃO Nº 123
    
    OBJETO: Aquisição de notebooks para a Secretaria de Educação
    
    QUANTIDADE: 750 notebooks
    
    ESPECIFICAÇÕES:
    - Notebook com processador Intel Core i5 ou superior
    - Memória RAM de 8GB ou superior
    - Disco SSD de 256GB ou superior
    - Tela de 14" ou superior
    """
    
    # Cria um arquivo temporário
    temp_file = "temp_edital.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    yield temp_file
    
    # Limpa o arquivo temporário
    if os.path.exists(temp_file):
        os.remove(temp_file)

def test_threshold_above_minimum(sample_document):
    """Testa quando a quantidade está acima do threshold."""
    result = process_edital(
        document_path=sample_document,
        target="notebook",
        threshold=500
    )
    
    assert result.target_match == True
    assert result.threshold_match == True
    assert result.threshold_status == "true"
    assert "750 notebooks" in result.document_summary.lower()

def test_threshold_below_minimum(sample_document):
    """Testa quando a quantidade está abaixo do threshold."""
    result = process_edital(
        document_path=sample_document,
        target="notebook",
        threshold=1000
    )
    
    assert result.target_match == True
    assert result.threshold_match == False
    assert result.threshold_status == "false"
    assert "threshold" in result.justification.lower()

def test_threshold_inconclusive():
    """Testa quando a quantidade não pode ser determinada."""
    # Cria um documento sem quantidade específica
    content = """
    EDITAL DE LICITAÇÃO Nº 123
    
    OBJETO: Aquisição de notebooks para a Secretaria de Educação
    
    ESPECIFICAÇÕES:
    - Notebook com processador Intel Core i5 ou superior
    - Memória RAM de 8GB ou superior
    - Disco SSD de 256GB ou superior
    - Tela de 14" ou superior
    """
    
    temp_file = "temp_edital_inconclusive.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        result = process_edital(
            document_path=temp_file,
            target="notebook",
            threshold=500
        )
        
        assert result.target_match == True
        assert result.threshold_match == False
        assert result.threshold_status == "inconclusive"
        assert "quantidade" in result.justification.lower()
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_non_device_target(sample_document):
    """Testa quando o target não é um dispositivo."""
    result = process_edital(
        document_path=sample_document,
        target="RPA",
        threshold=500
    )
    
    assert result.target_match == False
    assert result.threshold_match == False
    assert result.threshold_status == "inconclusive"
    assert "RPA" in result.justification.lower()

def test_force_match(sample_document):
    """Testa o modo force_match."""
    result = process_edital(
        document_path=sample_document,
        target="notebook",
        threshold=1000,
        force_match=True
    )
    
    assert result.target_match == True
    assert result.threshold_match == True
    assert result.threshold_status == "true"
    assert result.justification == ""

def test_multiple_quantities():
    """Testa quando há múltiplas quantidades no documento."""
    content = """
    EDITAL DE LICITAÇÃO Nº 123
    
    OBJETO: Aquisição de equipamentos para a Secretaria de Educação
    
    QUANTIDADE:
    - 300 notebooks
    - 200 tablets
    - 100 smartphones
    
    ESPECIFICAÇÕES:
    - Notebook com processador Intel Core i5 ou superior
    - Tablet com tela de 10" ou superior
    - Smartphone com Android 10 ou superior
    """
    
    temp_file = "temp_edital_multiple.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        # Testa com threshold para notebooks
        result = process_edital(
            document_path=temp_file,
            target="notebook",
            threshold=500
        )
        
        assert result.target_match == True
        assert result.threshold_match == False
        assert result.threshold_status == "false"
        assert "300 notebooks" in result.justification.lower()
        
        # Testa com threshold para tablets
        result = process_edital(
            document_path=temp_file,
            target="tablet",
            threshold=150
        )
        
        assert result.target_match == True
        assert result.threshold_match == True
        assert result.threshold_status == "true"
        assert "200 tablets" in result.document_summary.lower()
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file) 