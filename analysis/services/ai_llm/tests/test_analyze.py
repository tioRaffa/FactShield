import pytest
import json
from unittest.mock import patch, MagicMock
from decouple import UndefinedValueError
from rest_framework.exceptions import APIException
from google.genai.errors import APIError

from analysis.services.ai_llm.analyze import analyze_with_llm

# Test case 1: Test when the API key is missing.
@patch('analysis.services.ai_llm.analyze.config')
def test_analyze_with_llm_missing_api_key(mock_config):
    """
    Tests if analyze_with_llm raises APIException when the GEMINI_API key is not set.
    """
    mock_config.side_effect = UndefinedValueError()
    with pytest.raises(APIException) as excinfo:
        analyze_with_llm("Some content")
    assert "Chave GEMINI_API não encontrada no arquivo .env!" in str(excinfo.value)

# Test case 2: Test with insufficient content.
def test_analyze_with_llm_insufficient_content():
    """
    Tests if analyze_with_llm returns a specific dictionary for short or empty content.
    """
    expected_response = {
        "llm_full_analysis": "Conteudo insuficiente para analise.",
        "llm_status": "CAUTELA",
        "llm_recommendation": "Cautela: O texto extraido é muito curto ou invalido.",
    }
    assert analyze_with_llm(None) == expected_response
    assert analyze_with_llm("") == expected_response
    assert analyze_with_llm("short") == expected_response

# Test case 3: Test a successful analysis.
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_successful_analysis(mock_genai_client, mock_config):
    """
    Tests a successful call to the LLM, ensuring mocks are called and data is returned.
    """
    mock_config.return_value = "fake_api_key"

    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "Test summary",
        "risk_assessment": "Low risk",
        "recommendation": "CONFIE NO CONTEÚDO"
    })
    
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    content = "This is a long and valid content for analysis."
    
    result = analyze_with_llm(content)

    mock_config.assert_called_once_with("KEY_GEMINI_API")
    mock_genai_client.assert_called_once_with(api_key="fake_api_key")
    mock_client_instance.models.generate_content.assert_called_once()
    assert result == {
        "llm_status": "BAIXO RISCO",
        "llm_summary": "Test summary",
        "llm_risk_assessment": "Low risk",
        "llm_recommendation": "CONFIE NO CONTEÚDO",
    }

# Test case 4: Test when the genai API call fails with APIError.
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_api_error(mock_genai_client, mock_config):
    """
    Tests the behavior of analyze_with_llm when the genai API call fails with APIError.
    """
    mock_config.return_value = "fake_api_key"

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = APIError("API Error from GenAI", response_json={})
    mock_genai_client.return_value = mock_client_instance

    content = "This is a valid content that will cause an API error."

    with pytest.raises(APIException) as excinfo:
        analyze_with_llm(content)
    assert "Erro na API da LLM: API Error from GenAI" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_GEMINI_API")
    mock_genai_client.assert_called_once_with(api_key="fake_api_key")
    mock_client_instance.models.generate_content.assert_called_once()

# Test case 5: Test when the genai API call fails with a generic Exception.
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_generic_exception(mock_genai_client, mock_config):
    """
    Tests the behavior of analyze_with_llm when the genai API call fails with a generic Exception.
    """
    mock_config.return_value = "fake_api_key"

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("Generic error")
    mock_genai_client.return_value = mock_client_instance

    content = "This is a valid content that will cause a generic error."

    with pytest.raises(APIException) as excinfo:
        analyze_with_llm(content)
    assert "Erro inesperado na LLM: Generic error" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_GEMINI_API")
    mock_genai_client.assert_called_once_with(api_key="fake_api_key")
    mock_client_instance.models.generate_content.assert_called_once()

# Test case 6: Test when the LLM returns invalid JSON.
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_invalid_json_response(mock_genai_client, mock_config):
    """
    Tests if analyze_with_llm raises APIException when the LLM returns invalid JSON.
    """
    mock_config.return_value = "fake_api_key"

    mock_response = MagicMock()
    mock_response.text.strip.return_value = "this is not valid json"
    
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    content = "Content for invalid JSON test."
    
    with pytest.raises(APIException) as excinfo:
        analyze_with_llm(content)
    assert "Erro ao analisar o JSON do LLM:" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_GEMINI_API")
    mock_genai_client.assert_called_once_with(api_key="fake_api_key")
    mock_client_instance.models.generate_content.assert_called_once()

# Test case 7: Test with very long content to ensure it's truncated.
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_long_content_truncation(mock_genai_client, mock_config):
    """
    Tests if very long content is correctly truncated before being sent to the LLM.
    """
    mock_config.return_value = "fake_api_key"
    
    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "Truncated content summary",
        "risk_assessment": "Low risk",
        "recommendation": "CONFIE NO CONTEÚDO"
    })
    
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    long_content = "a" * 10000
    
    analyze_with_llm(long_content)

    args, kwargs = mock_client_instance.models.generate_content.call_args
    passed_contents = kwargs.get('contents', '')
    
    assert long_content[:8000] in passed_contents
    assert len(long_content[:8000]) == 8000
    assert long_content[8000:] not in passed_contents

# Test case 8: Test recommendation "EVITE ESTE SITE E CONTEÚDO"
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_recommendation_evite(mock_genai_client, mock_config):
    """
    Tests if the llm_status is "ALTO RISCO" for "EVITE ESTE SITE E CONTEÚDO" recommendation.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "Summary",
        "risk_assessment": "High risk",
        "recommendation": "EVITE ESTE SITE E CONTEÚDO"
    })
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    result = analyze_with_llm("Some content")
    assert result["llm_status"] == "ALTO RISCO"

# Test case 9: Test recommendation "PROSSIGA COM CAUTELA"
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_recommendation_cautela(mock_genai_client, mock_config):
    """
    Tests if the llm_status is "RISCO MODERADO" for "PROSSIGA COM CAUTELA" recommendation.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "Summary",
        "risk_assessment": "Moderate risk",
        "recommendation": "PROSSIGA COM CAUTELA"
    })
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    result = analyze_with_llm("Some content")
    assert result["llm_status"] == "RISCO MODERADO"

# Test case 10: Test recommendation with other values (default to BAIXO RISCO)
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_recommendation_other(mock_genai_client, mock_config):
    """
    Tests if the llm_status is "BAIXO RISCO" for other recommendations.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "Summary",
        "risk_assessment": "Low risk",
        "recommendation": "Some other recommendation"
    })
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    result = analyze_with_llm("Some content")
    assert result["llm_status"] == "BAIXO RISCO"

# Test case 11: Test empty summary, risk_assessment, recommendation from LLM
@patch('analysis.services.ai_llm.analyze.config')
@patch('analysis.services.ai_llm.analyze.genai.Client')
def test_analyze_with_llm_empty_llm_fields(mock_genai_client, mock_config):
    """
    Tests if empty summary, risk_assessment, recommendation from LLM are handled correctly.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.text.strip.return_value = json.dumps({
        "summary": "",
        "risk_assessment": "",
        "recommendation": ""
    })
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    result = analyze_with_llm("Some content")
    assert result["llm_summary"] == ""
    assert result["llm_risk_assessment"] == ""
    assert result["llm_recommendation"] == ""
    assert result["llm_status"] == "BAIXO RISCO" # Default for empty recommendation
