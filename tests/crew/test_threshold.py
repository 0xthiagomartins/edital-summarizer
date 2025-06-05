import pytest
from edital_summarizer.crew import EditalSummarizer

@pytest.fixture
def summarizer():
    return EditalSummarizer()

def test_is_device_target(summarizer):
    assert summarizer._is_device_target("notebook") == True
    assert summarizer._is_device_target("tablet") == True
    assert summarizer._is_device_target("smartphone") == True
    assert summarizer._is_device_target("RPA") == False
    assert summarizer._is_device_target("Automação") == False

def test_process_target_response_true(summarizer):
    result = summarizer._process_target_response("true")
    assert result["target_match"] == True
    assert result["threshold_match"] == True
    assert result["threshold_status"] == "true"

def test_process_target_response_false(summarizer):
    result = summarizer._process_target_response("false")
    assert result["target_match"] == False
    assert result["threshold_match"] == False
    assert result["threshold_status"] == "false"

def test_process_target_response_inconclusive(summarizer):
    result = summarizer._process_target_response("inconclusive")
    assert result["target_match"] == False
    assert result["threshold_match"] == False
    assert result["threshold_status"] == "inconclusive"

def test_process_target_response_invalid(summarizer):
    result = summarizer._process_target_response("invalid")
    assert result["target_match"] == False
    assert result["threshold_match"] == False
    assert result["threshold_status"] == "inconclusive"

def test_process_target_response_case_insensitive(summarizer):
    result = summarizer._process_target_response("TRUE")
    assert result["target_match"] == True
    assert result["threshold_match"] == True
    assert result["threshold_status"] == "true"

    result = summarizer._process_target_response("FALSE")
    assert result["target_match"] == False
    assert result["threshold_match"] == False
    assert result["threshold_status"] == "false"

    result = summarizer._process_target_response("INCONCLUSIVE")
    assert result["target_match"] == False
    assert result["threshold_match"] == False
    assert result["threshold_status"] == "inconclusive" 