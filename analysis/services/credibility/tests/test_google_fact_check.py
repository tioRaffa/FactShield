"""Testes para a função search_fact_check."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from decouple import UndefinedValueError
from rest_framework.exceptions import APIException

from analysis.services.credibility.google_fact_check import search_fact_check


@patch("analysis.services.credibility.google_fact_check.config")
@patch("analysis.services.credibility.google_fact_check.requests.get")
def test_search_fact_check_success(mock_requests_get, mock_config):
    """
    Testa o sucesso da busca de checagem de fatos.

    Verifica se a função retorna os dados esperados quando a API do Google
    Fact Check retorna uma resposta bem-sucedida com alegações.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "claims": [
            {
                "text": "Claim text",
                "claimant": "Claimant",
                "claimDate": "2023-01-01T00:00:00Z",
                "claimReview": [
                    {
                        "publisher": {"name": "Fact Checker"},
                        "url": "http://example.com/factcheck",
                        "textualRating": "False",
                    }
                ],
            }
        ]
    }
    mock_requests_get.return_value = mock_response

    # Act
    result = search_fact_check("some query")

    # Assert
    expected = {
        "fact_check_status": "Human Vefiried",
        "veredict": "False",
        "fact_checker": "Fact Checker",
        "fact_check_url": "http://example.com/factcheck",
        "claim_text": "Claim text",
        "claim_date": "2023-01-01T00:00:00Z",
        "claimant": "Claimant",
    }
    assert result == expected


@patch("analysis.services.credibility.google_fact_check.config")
@patch("analysis.services.credibility.google_fact_check.requests.get")
def test_search_fact_check_no_claims(mock_requests_get, mock_config):
    """
    Testa a busca de checagem de fatos sem alegações retornadas.

    Verifica se a função retorna um dicionário vazio quando a API do Google
    Fact Check não retorna nenhuma alegação para a consulta.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"claims": []}
    mock_requests_get.return_value = mock_response

    # Act
    result = search_fact_check("some query")

    # Assert
    assert result == {}


@patch("analysis.services.credibility.google_fact_check.config")
@patch("analysis.services.credibility.google_fact_check.requests.get")
def test_search_fact_check_api_error(mock_requests_get, mock_config):
    """
    Testa o tratamento de erro da API na busca de checagem de fatos.

    Verifica se a função lança uma APIException quando a API do Google
    Fact Check retorna um erro (status code 400).
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
    mock_requests_get.return_value = mock_response

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        search_fact_check("some query")
    assert str(excinfo.value) == "Erro na API: Invalid API key"


@patch(
    "analysis.services.credibility.google_fact_check.config",
    side_effect=UndefinedValueError(),
)
def test_search_fact_check_no_api_key(mock_config):
    """
    Testa a ausência da chave de API.

    Verifica se a função lança uma APIException quando a chave da API
    GOOGLE_FACTCHECK não está configurada no ambiente.
    """
    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        search_fact_check("some query")
    assert str(excinfo.value) == "Chave API GOOGLE_FACTCHECK não encontrada no .env!"


@patch("analysis.services.credibility.google_fact_check.config")
@patch(
    "analysis.services.credibility.google_fact_check.requests.get",
    side_effect=requests.exceptions.RequestException("Connection error"),
)
def test_search_fact_check_request_exception(mock_requests_get, mock_config):
    """
    Testa o tratamento de exceção de requisição.

    Verifica se a função lança uma APIException quando ocorre um erro
    de conexão durante a chamada para a API.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        search_fact_check("some query")
    assert str(excinfo.value) == "Erro na requisição da API: Connection error"