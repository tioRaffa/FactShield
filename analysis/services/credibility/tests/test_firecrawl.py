
import os
import sys
from unittest.mock import Mock, patch

import pytest
from decouple import UndefinedValueError
from rest_framework.exceptions import APIException

# Add project root to path to allow absolute imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)
from analysis.services.credibility._firecrawl import extract_content_firecrawl
from analysis.util.clean import clean_content


# Green Path Tests
@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_success(mock_config, mock_firecrawl_app):
    """
    Tests successful content extraction (happy path).
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_scrape_result = Mock()
    mock_scrape_result.markdown = "Raw markdown with #extra chars"
    mock_scrape_result.metadata = {
        "title": "Test Title",
        "description": "Test Description",
        "url": "http://example.com",
    }
    # Convert dict to object for attribute access
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
    """
    Tests graceful handling of missing metadata attributes.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_scrape_result = Mock()
    mock_scrape_result.markdown = "Some content"
    mock_scrape_result.metadata = {"title": "Only Title"}  # Missing description and url
    mock_scrape_result.metadata = Mock(**mock_scrape_result.metadata)
    # Make sure accessing missing attributes returns None or default
    mock_scrape_result.metadata.description = None
    mock_scrape_result.metadata.url = None


    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.return_value = mock_scrape_result

    # Act
    result = extract_content_firecrawl("http://example.com")

    # Assert
    assert result["title"] == "Only Title"
    assert result["description"] == ""  # Should default to empty string
    assert result["url"] == ""      # Should default to empty string


# Red Path Tests
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_no_api_key(mock_config):
    """
    Tests that an APIException is raised if the API key is not found.
    """
    # Arrange
    mock_config.side_effect = UndefinedValueError()

    # Act & Assert
    with pytest.raises(APIException) as excinfo:
        extract_content_firecrawl("http://example.com")
    assert "Chave API KEY não encontrada no .env!" in str(excinfo.value)


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_scrape_returns_none(mock_config, mock_firecrawl_app):
    """
    Tests that an APIException is returned if the scrape call returns None.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.return_value = None

    # Act
    result = extract_content_firecrawl("http://example.com")

    # Assert
    assert isinstance(result, APIException)
    assert "Não foi possível obter dados da URL." in str(result.detail)


@patch("analysis.services.credibility._firecrawl.FirecrawlApp")
@patch("analysis.services.credibility._firecrawl.config")
def test_extract_content_firecrawl_scrape_raises_exception(
    mock_config, mock_firecrawl_app
):
    """
    Tests that an exception during scraping is caught and returned as an APIException.
    This also serves as a security test.
    """
    # Arrange
    mock_config.return_value = "fake_api_key"
    mock_firecrawl_instance = mock_firecrawl_app.return_value
    mock_firecrawl_instance.scrape.side_effect = Exception("External service failed")

    # Act
    result = extract_content_firecrawl("http://example.com")

    # Assert
    assert isinstance(result, APIException)
    assert "Erro ao acessar Firecrawl: External service failed" in str(result.detail)
