import pytest
from edital_summarizer.schemas import EditalResponse

def test_edital_response_creation():
    """Testa a criação de uma resposta válida."""
    response = EditalResponse(
        target_match=True,
        threshold_match=True,
        threshold_status="true",
        target_summary="Resumo do target",
        document_summary="Resumo do documento",
        justification="",
        metadata={}
    )
    
    assert response.target_match == True
    assert response.threshold_match == True
    assert response.threshold_status == "true"
    assert response.target_summary == "Resumo do target"
    assert response.document_summary == "Resumo do documento"
    assert response.justification == ""
    assert response.metadata == {}
    assert response.error is None

def test_edital_response_with_error():
    """Testa a criação de uma resposta com erro."""
    response = EditalResponse(
        target_match=False,
        threshold_match=False,
        threshold_status="inconclusive",
        target_summary="",
        document_summary="",
        justification="Erro ao processar",
        metadata={},
        error="Erro de processamento"
    )
    
    assert response.target_match == False
    assert response.threshold_match == False
    assert response.threshold_status == "inconclusive"
    assert response.target_summary == ""
    assert response.document_summary == ""
    assert response.justification == "Erro ao processar"
    assert response.metadata == {}
    assert response.error == "Erro de processamento"

def test_edital_response_invalid_threshold_status():
    """Testa a criação de uma resposta com status de threshold inválido."""
    with pytest.raises(ValueError):
        EditalResponse(
            target_match=True,
            threshold_match=True,
            threshold_status="invalid",  # Status inválido
            target_summary="",
            document_summary="",
            justification="",
            metadata={}
        )

def test_edital_response_default_values():
    """Testa a criação de uma resposta com valores padrão."""
    response = EditalResponse(
        target_match=False,
        threshold_match=False,
        threshold_status="false"
    )
    
    assert response.target_match == False
    assert response.threshold_match == False
    assert response.threshold_status == "false"
    assert response.target_summary == ""
    assert response.document_summary == ""
    assert response.justification == ""
    assert response.metadata == {}
    assert response.error is None

def test_edital_response_with_metadata():
    """Testa a criação de uma resposta com metadados."""
    metadata = {
        "identifier": {
            "public_notice": "123",
            "process_id": "456",
            "bid_number": "789"
        },
        "organization": {
            "name": "Test Org",
            "location": "Test City"
        }
    }
    
    response = EditalResponse(
        target_match=True,
        threshold_match=True,
        threshold_status="true",
        metadata=metadata
    )
    
    assert response.metadata == metadata
    assert response.metadata["identifier"]["public_notice"] == "123"
    assert response.metadata["organization"]["name"] == "Test Org" 