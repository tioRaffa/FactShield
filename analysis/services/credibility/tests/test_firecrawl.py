"""Testes para a função extract_content_firecrawl."""

import os
import sys
from unittest.mock import Mock, patch

import pytest
from decouple import UndefinedValueError
from rest_framework.exceptions import APIException

# Adiciona o diretório raiz do projeto ao path para permitir importações absolutas
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)
from analysis.services.credibility._firecrawl import extract_content_firecrawl


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_success(mock_config, mock_firecrawl_app):
    """Testa a extração de conteúdo bem-sucedida (caminho feliz)."""
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_scrape_result = Mock()
    mock_scrape_result.markdown = "Raw markdown with #extra chars"
    mock_scrape_result.metadata = {
        "title": "Test Title",
        "description": "Test Description",
        "url": "http://example.com",
    }
    mock_scrape_result.metadata = Mock(**mock_scrape_result.metadata)

    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.return_value = mock_scrape_result

    # Act
    result = extract_content_firecrawl("http://example.com")

    # Assert
    assert result["title"] == "Test Title"
    assert result["description"] == "Test Description"
    assert result["url"] == "http://example.com"
    assert result["content"] == "Raw markdown with extra chars"
    mock_firecrawl_instance.scrape.assert_called_once_with(
        "http://example.com", formats=["markdown"], only_main_content=True
    )


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_missing_metadata(mock_config, mock_firecrawl_app):
    """Testa o tratamento de atributos de metadados ausentes."""
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_scrape_result = Mock()
    mock_scrape_result.markdown = "Some content"
    mock_scrape_result.metadata = {"title": "Only Title"}
    mock_scrape_result.metadata = Mock(**mock_scrape_result.metadata)
    mock_scrape_result.metadata.description = None
    mock_scrape_result.metadata.url = None

    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.return_value = mock_scrape_result

    # Act
    result = extract_content_firecrawl("http://example.com")

    # Assert
    assert result["title"] == "Only Title"
    assert result["description"] == ""
    assert result["url"] == ""


@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_no_api_key(mock_config):
    """Testa se uma APIException é levantada se a chave da API não for encontrada."""
    # Arrange
    mock_config.side_effect = UndefinedValueError()

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        extract_content_firecrawl("http://example.com")
    assert "Chave API KEY não encontrada no .env!" in str(excinfo.value)


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_scrape_returns_none(
    mock_config, mock_firecrawl_app
):
    """Testa se uma APIException é retornada se a chamada de scrape retornar None."""
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.return_value = None

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        extract_content_firecrawl("http://example.com")
    assert "Não foi possível obter dados da URL." in str(excinfo.value)


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_scrape_raises_exception(
    mock_config, mock_firecrawl_app
):
    """Testa se uma exceção durante o scraping é capturada e retornada como uma APIException."""
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.side_effect = Exception("External service failed")

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        extract_content_firecrawl("http://example.com")
    assert "Erro ao acessar Firecrawl: External service failed" in str(excinfo.value)