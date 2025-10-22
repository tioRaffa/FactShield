import json
import os
import sys
from pprint import pprint

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
import logging

from decouple import UndefinedValueError, config
from google import genai
from google.genai.errors import APIError
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


def analyze_with_llm(raw_content):
    try:
        api_key = config("KEY_GEMINI_API")
    except UndefinedValueError:
        raise APIException("Chave GEMINI_API não encontrada no arquivo .env!")

    safe_raw_content = raw_content.strip() if raw_content else None

    if not safe_raw_content or len(safe_raw_content) < 100:
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
    safe_content = safe_raw_content[:8000]

    user_prompt = (
        f"Analise o seguinte conteúdo bruto de um artigo:\n\n---\n{safe_content}\n---\n\n"
        "Com base na análise, gere um objeto JSON com três chaves obrigatórias:\n"
        "1. **summary**: Um resumo conciso em no máximo 5 linhas.\n"
        "2. **risk_assessment**: Uma breve avaliação que detalhe sinais de desinformação, linguagem sensacionalista, manipulação, ou outros fatores de risco.\n"
        "3. **recommendation**: Uma recomendação final, sendo uma das três opções: 'CONFIE NO CONTEÚDO', 'PROSSIGA COM CAUTELA', ou 'EVITE ESTE SITE E CONTEÚDO'.\n"
        "\nNão inclua nenhum texto fora do objeto JSON."
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            },
        )
        json_string = response.text.strip()

        try:
            llm_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Alerta: Falha no parsing do JSON. Retorno do LLM:\n{json_string}",
                exc_info=True,
            )
            raise APIException(f"Erro ao analisar o JSON do LLM: {e}")

        recommendation = (llm_data.get("recommendation") or "").upper()
        if "EVITE" in recommendation:
            llm_status = "ALTO RISCO"
        elif "CAUTELA" in recommendation:
            llm_status = "RISCO MODERADO"
        else:
            llm_status = "BAIXO RISCO"

        return {
            "llm_status": llm_status,
            "llm_summary": llm_data.get("summary") or "N/A",
            "llm_risk_assessment": llm_data.get("risk_assessment") or "N/A",
            "llm_recommendation": llm_data.get("recommendation") or "N/A",
        }

    except APIError as e:
        raise APIException(f"Erro na API da LLM: {e}")
    except Exception as e:
        raise APIException(f"Erro inesperado na LLM: {e}")


if __name__ == "__main__":
    from analysis.services.credibility._firecrawl import extract_content_firecrawl

    url = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"
    data = extract_content_firecrawl(url)

    result = analyze_with_llm(data.get("content"))
    pprint(result)
