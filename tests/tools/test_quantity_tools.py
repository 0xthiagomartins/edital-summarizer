import pytest
from decimal import Decimal
from edital_summarizer.tools.quantity_tools import QuantityExtractionTool

@pytest.fixture
def tool():
    return QuantityExtractionTool()

def test_extract_quantities_basic(tool):
    text = "Fornecimento de 500 notebooks para uso administrativo"
    keywords = ["notebook"]
    result = tool._run(text, keywords)
    assert "500" in result
    assert "notebook" in result.lower()

def test_extract_quantities_with_units(tool):
    text = "Quantidade total: 1.000 unidades de tablets"
    keywords = ["tablet"]
    result = tool._run(text, keywords)
    assert "1000" in result
    assert "unidade" in result.lower()

def test_extract_quantities_multiple(tool):
    text = """
    Fornecimento de:
    - 500 notebooks
    - 1.000 tablets
    - 200 smartphones
    """
    keywords = ["notebook", "tablet", "smartphone"]
    result = tool._run(text, keywords)
    assert "500" in result
    assert "1000" in result
    assert "200" in result

def test_extract_quantities_with_context(tool):
    text = "O edital solicita a quantidade de 750 notebooks para uso administrativo"
    keywords = ["notebook"]
    result = tool._run(text, keywords)
    assert "750" in result
    assert "quantidade" in result.lower()

def test_extract_quantities_no_match(tool):
    text = "Fornecimento de equipamentos de informática"
    keywords = ["notebook"]
    result = tool._run(text, keywords)
    assert result == "[]"

def test_normalize_number(tool):
    assert tool._normalize_number("1.000") == Decimal("1000")
    assert tool._normalize_number("1,5") == Decimal("1.5")
    assert tool._normalize_number("1.000,50") == Decimal("1000.50")
    assert tool._normalize_number("1000") == Decimal("1000")

def test_extract_unit(tool):
    assert tool._extract_unit("500 unidades de notebook", "500") == "unidade"
    assert tool._extract_unit("100 pcs de tablet", "100") == "peça"
    assert tool._extract_unit("50 kits de smartphone", "50") == "kit"
    assert tool._extract_unit("10 lotes de equipamentos", "10") == "lote"
    assert tool._extract_unit("5 conjuntos de notebooks", "5") == "conjunto"

def test_calculate_confidence(tool):
    text = "quantidade total de 500 notebooks"
    keywords = ["notebook"]
    confidence = tool._calculate_confidence(text, keywords)
    assert 0.9 <= confidence <= 1.0

    text = "500 notebooks"
    confidence = tool._calculate_confidence(text, keywords)
    assert 0.4 <= confidence <= 0.7

    text = "quantidade de equipamentos"
    confidence = tool._calculate_confidence(text, keywords)
    assert 0.3 <= confidence <= 0.4 