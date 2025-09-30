"""
Este módulo contém testes unitários abrangentes para a função `_scan_url`,
localizada em `analysis.services.virus_total.scan_url`.

Os testes cobrem cenários de sucesso, diversos tipos de erros da API do VirusTotal,
problemas de configuração (chave de API ausente), erros de rede e validação de entrada de URL.
"""

import pytest
import requests
from unittest.mock import MagicMock, patch

from analysis.services.virus_total.scan_url import _scan_url
from rest_framework.exceptions import APIException, ValidationError


@pytest.fixture
def mock_config(mocker):
    """Fixture para mockar a função `config` do `decouple`."""
    return mocker.patch("analysis.services.virus_total.scan_url.config")


@pytest.fixture
def mock_requests_post(mocker):
    """Fixture para mockar a função `requests.post`."""
    return mocker.patch("requests.post")


# --- Testes de Caminho Feliz ---

def test_scan_url_success(mock_config, mock_requests_post):
    """
    Testa o cenário de sucesso onde a API do VirusTotal retorna um ID de análise válido.

    Condição:
        - Chave de API configurada.
        - API do VirusTotal retorna status 200 com um corpo JSON contendo o 'id' da análise.
    Verificação:
        - A função retorna o 'id' extraído corretamente.
        - `requests.post` é chamado uma vez com os parâmetros corretos.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"id": "test_url_id"}}
    mock_requests_post.return_value = mock_response

    url_id = _scan_url("http://example.com")
    assert url_id == "test_url_id"
    mock_requests_post.assert_called_once()


# --- Testes de Erros da API e Resposta ---

@pytest.mark.parametrize(
    "status_code, json_response, expected_exception, expected_message",
    [
        # Teste 2: Erro na API (status diferente de 200)
        (403, {"error": {"message": "Permission denied"}}, APIException, "Permission denied"),
        (500, {"error": {"message": "Internal server error"}}, APIException, "Internal server error"),
        # Teste 3: Resposta válida (200), mas sem o ID esperado
        (200, {"data": {"some_other_key": "value"}}, ValidationError, "ID da url não encontrado"),
        (200, {"data": {}}, ValidationError, "ID da url não encontrado"),
        (200, {}, ValidationError, "ID da url não encontrado"),
    ],
    ids=[
        "api_error_403_permission_denied",
        "api_error_500_internal_server_error",
        "missing_id_in_response_other_key",
        "missing_id_in_response_empty_data",
        "missing_id_in_response_empty_json",
    ],
)
def test_scan_url_api_response_errors(
    mock_config, mock_requests_post, status_code, json_response, expected_exception, expected_message
):
    """
    Testa diversos cenários de erro na resposta da API do VirusTotal.

    Condição:
        - Chave de API configurada.
        - API retorna diferentes status codes ou estruturas JSON inesperadas.
    Verificação:
        - A exceção `expected_exception` é levantada com a `expected_message`.
        - `requests.post` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_response
    mock_requests_post.return_value = mock_response

    with pytest.raises(expected_exception) as excinfo:
        _scan_url("http://example.com")
    assert expected_message in str(excinfo.value)
    mock_requests_post.assert_called_once()


def test_scan_url_invalid_json_response(mock_config, mock_requests_post):
    """
    Testa o cenário onde a API retorna um status 200, mas o corpo da resposta não é um JSON válido.

    Condição:
        - Chave de API configurada.
        - API retorna status 200, mas `response.json()` levanta `JSONDecodeError`.
    Verificação:
        - `APIException` é levantada com uma mensagem indicando erro na requisição.
        - `requests.post` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Erro na requisição: Expecting value" in str(excinfo.value)
    mock_requests_post.assert_called_once()


# --- Testes de Erros de Configuração e Ambiente ---

def test_scan_url_api_key_missing(mock_config, mock_requests_post):
    """
    Testa o cenário onde a chave de API do VirusTotal não está configurada.

    Condição:
        - `config("KEY_VIRUS_TOTAL")` retorna `None`.
    Verificação:
        - `APIException` é levantada com a mensagem de chave não encontrada.
        - Nenhuma chamada de rede (`requests.post`) é feita.
    """
    mock_config.return_value = None

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Chave API KEY não encontrada no .env!" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_VIRUS_TOTAL")
    mock_requests_post.assert_not_called()


@pytest.mark.parametrize(
    "exception_type, exception_message, expected_error_prefix",
    [
        # Teste 6: Erros de Rede (RequestException)
        (requests.exceptions.RequestException, "Network is down", "Erro na requisição:"),
        # Teste 6 (continuação): Erros HTTP (HTTPError)
        (requests.exceptions.HTTPError, "404 Client Error: Not Found", "Erro na api:"),
    ],
    ids=["network_request_exception", "http_error_exception"],
)
def test_scan_url_network_and_http_errors(
    mock_config, mock_requests_post, exception_type, exception_message, expected_error_prefix
):
    """
    Testa cenários de erros de rede e HTTP durante a chamada à API.

    Condição:
        - Chave de API configurada.
        - `requests.post` levanta `RequestException` ou `HTTPError`.
    Verificação:
        - `APIException` é levantada com a mensagem de erro correspondente.
        - `requests.post` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_requests_post.side_effect = exception_type(exception_message)

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert f"{expected_error_prefix} {exception_message}" in str(excinfo.value)
    mock_requests_post.assert_called_once()


# --- Testes de Erros de Entrada de Dados (Validação de URL) ---

@pytest.mark.parametrize(
    "invalid_url, expected_message",
    [
        (None, "URL não pode ser vazia."),
        ("", "URL não pode ser vazia."),
        ("invalid-url", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
        ("ftp://example.com", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
        ("example.com", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
        ("file:///path/to/file", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
    ],
    ids=[
        "url_is_none",
        "url_is_empty_string",
        "url_missing_scheme_and_netloc",
        "url_unsupported_scheme_ftp",
        "url_missing_scheme_only",
        "url_unsupported_scheme_file",
    ],
)
def test_scan_url_invalid_input_url(mock_config, mock_requests_post, invalid_url, expected_message):
    """
    Testa a validação de entrada da URL para a função `_scan_url`.

    Condição:
        - A função recebe uma URL inválida (None, string vazia, formato incorreto, esquema não suportado).
    Verificação:
        - `ValidationError` é levantada com a `expected_message` correspondente.
        - Nenhuma chamada de rede (`requests.post`) é feita.
    """
    mock_config.return_value = "fake_api_key"
    with pytest.raises(ValidationError) as excinfo:
        _scan_url(invalid_url)
    assert expected_message in str(excinfo.value)
    mock_requests_post.assert_not_called() # Garante que nenhuma chamada de rede é feita para URLs inválidas.