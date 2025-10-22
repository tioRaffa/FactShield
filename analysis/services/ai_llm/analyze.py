from pprint import pprint

from decouple import UndefinedValueError, config
from google import genai
from google.genai.errors import APIError
from rest_framework.exceptions import APIException


def analyze_with_llm(raw_content):
    try:
        api_key = config("KEY_GEMINI_API")
    except UndefinedValueError:
        raise APIException("Chave GEMINI_API não encontrada no arquivo .env!")

    if not raw_content or len(raw_content) < 100:
        return {
            "llm_full_analysis": "Conteudo insuficiente para analise.",
            "llm_status": "CAUTELA",
            "llm_recommendation": "Cautela: O texto extraido é muito curto ou invalido.",
        }

    system_prompt = (
        "Você é um verificador de conteúdo online imparcial e um assistente de segurança. "
        "Sua análise deve ser objetiva e focada na detecção de risco. "
        "Sua resposta final deve ser estritamente formatada em JSON, seguindo as chaves: 'summary', 'risk_assessment', e 'recommendation'."
    )
    safe_content = raw_content[:8000]

    user_prompt = (
        f"Analise o seguinte conteúdo bruto de um artigo:\n\n---\n{safe_content}\n---\n\n"
        "Com base na análise, gere um objeto JSON com três chaves obrigatórias:\n"
        "1. **summary**: Um resumo conciso em no máximo 5 linhas.\n"
        "2. **risk_assessment**: Uma breve avaliação que detalhe sinais de desinformação, linguagem sensacionalista, manipulação, ou outros fatores de risco.\n"
        "3. **recommendation**: Uma recomendação final, sendo uma das três opções: 'CONFIE NO CONTEÚDO', 'PROSSIGA COM CAUTELA', ou 'EVITE ESTE SITE E CONTEÚDO'.\n"
        "\nNão inclua nenhum texto fora do objeto JSON."
    )
