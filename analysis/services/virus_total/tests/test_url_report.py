"""
Este módulo contém testes unitários abrangentes para a função `get_report`,
localizada em `analysis.services.virus_total.url_report`.

Os testes cobrem cenários de sucesso, diversos tipos de erros da API do VirusTotal,
problemas de configuração (chave de API ausente) e erros de rede.
"""

import pytest
import requests
from unittest.mock import MagicMock, patch

from analysis.services.virus_total.url_report import get_report
from rest_framework.exceptions import APIException, ValidationError


@pytest.fixture
def mock_config(mocker):
    """Fixture para mockar a função `config` do `decouple`."""
    return mocker.patch("analysis.services.virus_total.url_report.config")


@pytest.fixture
def mock_requests_get(mocker):
    """Fixture para mockar a função `requests.get`."""
    return mocker.patch("requests.get")


# --- Testes de Caminho Feliz ---

@pytest.mark.parametrize(
    "json_response, expected_report",
    [
        # Teste 1: Relatório de Sucesso com Detecções Maliciosas/Suspeitas
        ({
            "data": {
                "attributes": {
                    "stats": {"malicious": 5, "suspicious": 2, "harmless": 10, "undetected": 83},
                    "status": "completed",
                },
                "type": "analysis",
                "id": "analysis_id_123",
            },
            "meta": {"url_info": {"url": "http://malicious.com"}},
        },
        {
            "url_scanned": "http://malicious.com",
            "malicious_count": 5,
            "suspicious_count": 2,
            "total_scans": 100,
            "status": "completed",
        }),
        # Teste 2: Relatório de Sucesso sem Detecções (Inofensivo)
        ({
            "data": {
                "attributes": {
                    "stats": {"malicious": 0, "suspicious": 0, "harmless": 90, "undetected": 10},
                    "status": "completed",
                },
                "type": "analysis",
                "id": "analysis_id_456",
            },
            "meta": {"url_info": {"url": "http://harmless.com"}},
        },
        {
            "url_scanned": "http://harmless.com",
            "malicious_count": 0,
            "suspicious_count": 0,
            "total_scans": 100,
            "status": "completed",
        }),
        # Teste 6: Missing 'stats' in Response (deve defaultar para 0)
        ({
            "data": {
                "attributes": {"status": "completed"}, # Missing 'stats'
                "type": "analysis",
                "id": "analysis_id_123",
            },
            "meta": {"url_info": {"url": "http://example.com"}},
        },
        {
            "url_scanned": "http://example.com",
            "malicious_count": 0,
            "suspicious_count": 0,
            "total_scans": 0,
            "status": "completed",
        }),
    ],
    ids=[
        "success_with_detections",
        "success_no_detections",
        "success_missing_stats_default_to_zero",
    ],
)
def test_get_report_success_scenarios(mock_config, mock_requests_get, json_response, expected_report):
    """
    Testa cenários de sucesso na recuperação de relatórios da API do VirusTotal.

    Condição:
        - Chave de API configurada.
        - API do VirusTotal retorna status 200 com diferentes estruturas JSON válidas.
    Verificação:
        - A função retorna o dicionário de relatório esperado.
        - `requests.get` é chamado uma vez com os parâmetros corretos.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = json_response
    mock_requests_get.return_value = mock_response

    report = get_report("analysis_id_123")

    assert report == expected_report
    mock_requests_get.assert_called_once_with(
        url="https://www.virustotal.com/api/v3/analyses/analysis_id_123",
        headers={
            "accept": "application/json",
            "x-apikey": "fake_api_key",
        },
    )


# --- Testes de Erros de Configuração e Ambiente ---

def test_get_report_api_key_missing(mock_config, mock_requests_get):
    """
    Testa o cenário onde a chave de API do VirusTotal não está configurada.

    Condição:
        - `config("KEY_VIRUS_TOTAL")` retorna `None`.
    Verificação:
        - `APIException` é levantada com a mensagem de chave não encontrada.
        - Nenhuma chamada de rede (`requests.get`) é feita.
    """
    mock_config.return_value = None  # Simula chave de API ausente

    with pytest.raises(APIException) as excinfo:
        get_report("analysis_id_123")
    assert "Chave API KEY não encontrada no .env!" in str(excinfo.value)
    mock_config.assert_called_once_with("KEY_VIRUS_TOTAL")
    mock_requests_get.assert_not_called()  # Nenhuma chamada de rede deve ser feita


# --- Testes de Erros da API e Resposta ---

@pytest.mark.parametrize(
    "status_code, json_response, expected_exception, expected_message",
    [
        # Teste 4: API Retorna Status de Erro
        (403, {"error": {"message": "Permission denied"}}, APIException, "Permission denied"),
        (404, {"error": {"message": "Analysis not found"}}, APIException, "Analysis not found"),
        (500, {"error": {"message": "Internal server error"}}, APIException, "Internal server error"),
        # Teste 5: Atributos Ausentes na Resposta
        (200, {"data": {"type": "analysis", "id": "analysis_id_123"}}, ValidationError, "Attributes não encontrados!"),
        (200, {}, ValidationError, "Attributes não encontrados!"),
    ],
    ids=[
        "api_error_403_permission_denied",
        "api_error_404_analysis_not_found",
        "api_error_500_internal_server_error",
        "missing_attributes_in_response",
        "empty_json_missing_attributes",
    ],
)
def test_get_report_api_response_errors(
    mock_config, mock_requests_get, status_code, json_response, expected_exception, expected_message
):
    """
    Testa diversos cenários de erro na resposta da API do VirusTotal.

    Condição:
        - Chave de API configurada.
        - API retorna diferentes status codes ou estruturas JSON inesperadas.
    Verificação:
        - A exceção `expected_exception` é levantada com a `expected_message`.
        - `requests.get` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_response
    mock_requests_get.return_value = mock_response

    with pytest.raises(expected_exception) as excinfo:
        get_report("analysis_id_123")
    assert expected_message in str(excinfo.value)
    mock_requests_get.assert_called_once()


def test_get_report_invalid_json_response(mock_config, mock_requests_get):
    """
    Testa o cenário onde a API retorna um status 200, mas o corpo da resposta não é um JSON válido.

    Condição:
        - Chave de API configurada.
        - API retorna status 200, mas `response.json()` levanta `JSONDecodeError`.
    Verificação:
        - `APIException` é levantada com uma mensagem indicando erro na requisição.
        - `requests.get` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
    mock_requests_get.return_value = mock_response

    with pytest.raises(APIException) as excinfo:
        get_report("analysis_id_123")
    assert "Erro na requisição: Expecting value" in str(excinfo.value)
    mock_requests_get.assert_called_once()


# --- Testes de Erros de Rede e Requisição ---

@pytest.mark.parametrize(
    "exception_type, exception_message, expected_error_prefix",
    [
        # Teste 8: Erro de Conexão de Rede
        (requests.exceptions.RequestException, "Connection refused", "Erro na requisição:"),
        # Teste 9: Erro HTTP (e.g., 4xx/5xx client/server error)
        (requests.exceptions.HTTPError, "500 Server Error: Internal Server Error", "Erro na API:"),
    ],
    ids=["network_request_exception", "http_error_exception"],
)
def test_get_report_network_and_http_errors(
    mock_config, mock_requests_get, exception_type, exception_message, expected_error_prefix
):
    """
    Testa cenários de erros de rede e HTTP durante a chamada à API.

    Condição:
        - Chave de API configurada.
        - `requests.get` levanta `RequestException` ou `HTTPError`.
    Verificação:
        - `APIException` é levantada com a mensagem de erro correspondente.
        - `requests.get` é chamado uma vez.
    """
    mock_config.return_value = "fake_api_key"
    mock_requests_get.side_effect = exception_type(exception_message)

    with pytest.raises(APIException) as excinfo:
        get_report("analysis_id_123")
    assert f"{expected_error_prefix} {exception_message}" in str(excinfo.value)
    mock_requests_get.assert_called_once()