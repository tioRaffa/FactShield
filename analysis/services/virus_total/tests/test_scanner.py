import pytest
import requests
from unittest.mock import MagicMock, patch

from analysis.services.virus_total.scan_url import _scan_url
from rest_framework.exceptions import APIException, ValidationError

# Mock the config function from decouple
@pytest.fixture
def mock_config(mocker):
    return mocker.patch("analysis.services.virus_total.scan_url.config")

# Mock requests.post
@pytest.fixture
def mock_requests_post(mocker):
    return mocker.patch("requests.post")

# A. Caminho Feliz (Happy Path)
def test_scan_url_success(mock_config, mock_requests_post):
    """
    Teste 1: Resposta de Sucesso
    Condição: A API do VirusTotal retorna status_code 200 e um corpo JSON válido contendo o id da análise.
    Verificação: A função deve retornar o id extraído corretamente.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"id": "test_url_id"}}
    mock_requests_post.return_value = mock_response

    url_id = _scan_url("http://example.com")
    assert url_id == "test_url_id"
    mock_requests_post.assert_called_once()

# B. Erros de API e Resposta
def test_scan_url_api_error(mock_config, mock_requests_post):
    """
    Teste 2: Erro na API
    Condição: A API retorna um status de erro (ex: 401, 403, 500) com uma mensagem de erro no corpo JSON.
    Verificação: A função deve levantar APIException contendo a mensagem de erro da API.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"error": {"message": "Permission denied"}}
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Permission denied" in str(excinfo.value)
    mock_requests_post.assert_called_once()

def test_scan_url_missing_id_in_response(mock_config, mock_requests_post):
    """
    Teste 3: Resposta Válida, mas sem o Dado Esperado
    Condição: A API retorna status_code 200, mas o JSON não contém a chave id ou data.
    Verificação: A função deve levantar ValidationError.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"some_other_key": "value"}} # Missing 'id'
    mock_requests_post.return_value = mock_response

    with pytest.raises(ValidationError) as excinfo:
        _scan_url("http://example.com")
    assert "ID da url não encontrado" in str(excinfo.value)
    mock_requests_post.assert_called_once()

def test_scan_url_invalid_json_response(mock_config, mock_requests_post):
    """
    Teste 4: Resposta Válida, mas com Formato Inesperado
    Condição: A API retorna status_code 200, mas o corpo da resposta não é um JSON válido (ex: HTML de uma página de erro).
    Verificação: A função deve capturar a exceção JSONDecodeError e levantar uma APIException informativa.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
    mock_requests_post.return_value = mock_response

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Erro na requisição: Expecting value" in str(excinfo.value) # The original function catches RequestException, which JSONDecodeError inherits from.
    mock_requests_post.assert_called_once()

# C. Erros de Configuração e Ambiente
def test_scan_url_api_key_missing(mock_config):
    """
    Teste 5: Chave de API Ausente
    Condição: A variável de ambiente KEY_VIRUS_TOTAL não está configurada.
    Verificação: A função deve levantar APIException antes de tentar fazer a chamada de rede.
    """
    mock_config.return_value = None # Simulate missing API key

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Chave API KEY não encontrada no .env!" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_VIRUS_TOTAL")

def test_scan_url_network_error(mock_config, mock_requests_post):
    """
    Teste 6: Erros de Rede (RequestException)
    Condição: A biblioteca requests levanta uma exceção de rede (ex: requests.exceptions.RequestException).
    Verificação: A função deve capturar a exceção e levantar uma APIException correspondente.
    """
    mock_config.return_value = "fake_api_key"
    mock_requests_post.side_effect = requests.exceptions.RequestException("Network is down")

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Erro na requisição: Network is down" in str(excinfo.value)
    mock_requests_post.assert_called_once()

def test_scan_url_http_error(mock_config, mock_requests_post):
    """
    Teste 6 (continuação): Erros de Rede (HTTPError)
    Condição: A biblioteca requests levanta uma exceção HTTPError.
    Verificação: A função deve capturar a exceção e levantar uma APIException correspondente.
    """
    mock_config.return_value = "fake_api_key"
    # Make requests.post directly raise HTTPError
    mock_requests_post.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found for url: http://example.com")

    with pytest.raises(APIException) as excinfo:
        _scan_url("http://example.com")
    assert "Erro na api: 404 Client Error: Not Found for url: http://example.com" in str(excinfo.value)
    mock_requests_post.assert_called_once()

# D. Erros de Entrada de Dados (Input)
@pytest.mark.parametrize("invalid_url, expected_message", [
    (None, "URL não pode ser vazia."),
    ("", "URL não pode ser vazia."),
    ("invalid-url", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
    ("ftp://example.com", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
    ("example.com", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
    ("file:///path/to/file", "URL inválida. A URL deve começar com 'http://' ou 'https://'."),
])
def test_scan_url_invalid_input_url(mock_config, invalid_url, expected_message):
    """
    Teste 7: Validação da URL de Entrada
    Condição: A função recebe uma entrada inválida como None, string vazia (""), ou um texto que não é uma URL.
    Verificação: A função deve levantar uma exceção apropriada (ex: ValidationError) imediatamente, sem fazer chamadas de rede.
    """
    mock_config.return_value = "fake_api_key"
    with pytest.raises(ValidationError) as excinfo:
        _scan_url(invalid_url)
    assert expected_message in str(excinfo.value)
