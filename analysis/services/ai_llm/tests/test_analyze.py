import json
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Importe as exceções que serão usadas ou esperadas
from decouple import UndefinedValueError
from google.genai.errors import APIError as GoogleAPIError
from rest_framework.exceptions import APIException

# --- IMPORTANTE: Ajuste este import para o caminho real da sua função ---
from analysis.services.ai_llm.analyze import analyze_with_llm

# --- Fixtures ---


@pytest.fixture
def valid_content():
    """Fixture que fornece um conteúdo de texto válido (passa na verificação de 100 caracteres)."""
    return (
        "Este é um texto de exemplo com mais de 100 caracteres, usado para testar a análise principal."
        * 2
    )


@pytest.fixture(autouse=True)
def mock_config_success():
    """
    Fixture (com autouse=True) que aplica um patch automático na função `config`
    para retornar uma chave de API falsa em todos os testes, exceto onde for
    explicitamente sobrescrita.
    """
    # O patch deve apontar para onde `config` é USADO
    with patch("analysis.services.ai_llm.analyze.config") as mock_conf:
        mock_conf.return_value = "fake-api-key-12345"
        yield mock_conf


@pytest.fixture
def mock_genai_client():
    """
    Fixture principal para mockar a cadeia de chamadas da API do Google.
    O mock é configurado para simular a estrutura response.text.strip()
    """
    # 1. Mock do objeto de resposta final (o que tem o .text)
    mock_api_response = Mock()
    # 2. Mock do atributo .text
    mock_api_response.text = Mock()
    # 3. Define um retorno padrão para .text.strip()
    mock_api_response.text.strip.return_value = "{}"  # Default to an empty JSON string

    # 4. Mock da instância do cliente
    mock_client_instance = Mock()
    mock_client_instance.models.generate_content.return_value = mock_api_response

    # 5. Patch na classe 'Client'
    with patch("analysis.services.ai_llm.analyze.genai.Client") as mock_client_class:
        mock_client_class.return_value = mock_client_instance
        # 6. Yield o mock da resposta para que os testes possam configurá-lo
        yield mock_api_response


# --- Testes de Casos de Erro e Exceção ---


def test_analise_llm_falha_chave_api_ausente():
    """
    ⚠️ Testa o caso de erro onde a variável de ambiente KEY_GEMINI_API não está definida.
    """
    with patch(
        "analysis.services.ai_llm.analyze.config",
        side_effect=UndefinedValueError("Chave não encontrada"),
    ):
        with pytest.raises(APIException) as exc_info:
            analyze_with_llm("qualquer conteudo")
        assert "Chave GEMINI_API não encontrada" in str(exc_info.value)


@pytest.mark.parametrize(
    "conteudo_insuficiente",
    [
        None,
        "",
        " " * 101,  # Este teste agora passa, graças à correção .strip() no código
        "a" * 99,
    ],
)
def test_analise_llm_conteudo_insuficiente(conteudo_insuficiente):
    """
    🧩 Testa os casos de "guarda" (guard clause) onde o conteúdo é muito curto,
    nulo ou inválido (menor que 100 caracteres).
    """
    resultado = analyze_with_llm(conteudo_insuficiente)
    assert resultado["llm_status"] == "CAUTELA"
    assert "texto extraido é muito curto ou invalido" in resultado["llm_recommendation"]


def test_analise_llm_falha_api_google(valid_content):
    """
    ⚠️ Testa o caso de erro onde a API do Google (genai) levanta um GoogleAPIError.
    """
    with patch("analysis.services.ai_llm.analyze.genai.Client") as mock_client_class:
        mock_client_instance = Mock()

        # Adicione o argumento obrigatório `response_json`
        mock_client_instance.models.generate_content.side_effect = GoogleAPIError(
            "Erro de servidor 500", response_json={}
        )

        mock_client_class.return_value = mock_client_instance

        # Act & Assert
        with pytest.raises(APIException) as exc_info:
            analyze_with_llm(valid_content)

        assert "Erro na API da LLM: Erro de servidor 500" in str(exc_info.value)


def test_analise_llm_falha_parsing_json(valid_content, mock_genai_client):
    """
    ⚠️ Testa o caso de erro onde o LLM retorna uma string que *não* é um JSON válido.
    """
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = "Isto não é um JSON { quebrado"

    with pytest.raises(APIException) as exc_info:
        analyze_with_llm(valid_content)
    assert "Erro ao analisar o JSON do LLM" in str(exc_info.value)


def test_analise_llm_falha_inesperada(valid_content):
    """
    ⚠️ Testa o caso de erro genérico (Exception) para qualquer falha não prevista.
    """
    with patch("analysis.services.ai_llm.analyze.genai.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_client_instance.models.generate_content.side_effect = ValueError(
            "Erro inesperado no cliente"
        )
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(APIException) as exc_info:
            analyze_with_llm(valid_content)
        assert "Erro inesperado na LLM: Erro inesperado no cliente" in str(
            exc_info.value
        )


def test_analise_llm_bug_recommendation_nula(valid_content, mock_genai_client):
    """
    🧩 Testa o caso onde o LLM retorna {"recommendation": null}.
    Com a nova lógica de `... or "N/A"`, este teste agora passa como estava escrito.
    """
    llm_json_response = {
        "summary": "Resumo",
        "risk_assessment": "Risco",
        "recommendation": None,
    }
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "BAIXO RISCO"
    assert resultado["llm_summary"] == "Resumo"
    assert resultado["llm_risk_assessment"] == "Risco"
    # Esta asserção agora está CORRETA, pois (None or "N/A") é "N/A"
    assert resultado["llm_recommendation"] == "N/A"


# --- Testes de Casos de Sucesso ---


def test_analise_llm_sucesso_alto_risco(valid_content, mock_genai_client):
    """
    ✅ Testa o caminho feliz para uma recomendação de "ALTO RISCO" (contendo "EVITE").
    """
    llm_json_response = {
        "summary": "Resumo do conteúdo.",
        "risk_assessment": "Detectamos vários sinais de manipulação.",
        "recommendation": "EVITE ESTE SITE E CONTEÚDO",
    }
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "ALTO RISCO"
    assert resultado["llm_summary"] == "Resumo do conteúdo."
    assert resultado["llm_recommendation"] == "EVITE ESTE SITE E CONTEÚDO"


def test_analise_llm_sucesso_risco_moderado(valid_content, mock_genai_client):
    """
    ✅ Testa o caminho feliz para uma recomendação de "RISCO MODERADO" (contendo "CAUTELA").
    """
    llm_json_response = {
        "summary": "Resumo.",
        "risk_assessment": "Linguagem sensacionalista.",
        "recommendation": "PROSSIGA COM CAUTELA",
    }
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "RISCO MODERADO"


def test_analise_llm_sucesso_baixo_risco(valid_content, mock_genai_client):
    """
    ✅ Testa o caminho feliz para uma recomendação de "BAIXO RISCO" (qualquer outra).
    """
    llm_json_response = {
        "summary": "Resumo.",
        "risk_assessment": "Parece fatual.",
        "recommendation": "CONFIE NO CONTEÚDO",
    }
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "BAIXO RISCO"


def test_analise_llm_sucesso_recomendacao_lowercase(valid_content, mock_genai_client):
    """
    🧩 Testa o edge case do .upper(): A recomendação vem em minúsculas.
    """
    llm_json_response = {"recommendation": "prossiga com cautela"}
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "RISCO MODERADO"


# --- Testes de Edge Cases e Lógica Interna ---


def test_analise_llm_truncamento_de_conteudo():
    """
    🧩 Testa se o conteúdo enviado ao LLM é corretamente truncado em 8000 caracteres.
    """
    conteudo_longo = ("a" * 8000) + ("b" * 500)
    conteudo_esperado_no_prompt = "a" * 8000

    with patch("analysis.services.ai_llm.analyze.genai.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_api_response = Mock()

        # CORREÇÃO: Simular a estrutura .text.strip()
        mock_api_response.text = Mock()
        mock_api_response.text.strip.return_value = json.dumps({"recommendation": "OK"})

        mock_client_instance.models.generate_content.return_value = mock_api_response
        mock_client_class.return_value = mock_client_instance

        analyze_with_llm(conteudo_longo)

        mock_client_instance.models.generate_content.assert_called_once()
        kwargs_da_chamada = mock_client_instance.models.generate_content.call_args[1]
        prompt_enviado_ao_llm = kwargs_da_chamada.get("contents", "")

        assert f"\n{conteudo_esperado_no_prompt}\n" in prompt_enviado_ao_llm
        assert "bbbbb" not in prompt_enviado_ao_llm


def test_analise_llm_chaves_json_ausentes(valid_content, mock_genai_client):
    """
    🧩 Testa o que acontece se o LLM retornar um JSON válido, mas vazio ({}).
    """
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = "{}"  # JSON vazio

    resultado = analyze_with_llm(valid_content)

    # Com a nova lógica `... or "N/A"`, todos os campos ausentes devem ser "N/A"
    # e o status (baseado em "" or "N/A") será "BAIXO RISCO".
    assert resultado["llm_status"] == "BAIXO RISCO"
    assert resultado["llm_summary"] == "N/A"
    assert resultado["llm_risk_assessment"] == "N/A"
    assert resultado["llm_recommendation"] == "N/A"


def test_analise_llm_valores_json_nulos_ou_vazios(valid_content, mock_genai_client):
    """
    🧩 Testa a lógica de retorno para valores `None` ou `""`.
    """
    llm_json_response = {
        "summary": None,  # Deve se tornar "N/A"
        "risk_assessment": "",  # Deve se tornar "N/A"
        "recommendation": "OK",
    }
    # CORREÇÃO: Usar .text.strip.return_value
    mock_genai_client.text.strip.return_value = json.dumps(llm_json_response)

    resultado = analyze_with_llm(valid_content)

    assert resultado["llm_status"] == "BAIXO RISCO"
    # CORREÇÃO: Asserções atualizadas para a nova lógica `... or "N/A"`
    assert resultado["llm_summary"] == "N/A"  # (None or "N/A") -> "N/A"
    assert resultado["llm_risk_assessment"] == "N/A"  # ("" or "N/A") -> "N/A"
    assert resultado["llm_recommendation"] == "OK"  # ("OK" or "N/A") -> "OK"
