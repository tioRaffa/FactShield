import json
import os
import sys
from pprint import pprint

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

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
            print(f"Alerta: Falha no parsing do JSON. Retorno do LLM:\n{json_string}")
            raise APIException(f"Erro ao analisar o JSON do LLM: {e}")

        return llm_data

    except:  # noqa: E722
        return


if __name__ == "__main__":
    from analysis.services.credibility._firecrawl import extract_content_firecrawl

    url = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"
    data = extract_content_firecrawl(url)

    result = analyze_with_llm(data.get("content"))
    print(result)
