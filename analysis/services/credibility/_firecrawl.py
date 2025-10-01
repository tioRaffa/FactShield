import os
import sys

from decouple import UndefinedValueError, config
from firecrawl import FirecrawlApp
from rest_framework.exceptions import APIException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from pprint import pprint


from analysis.util.clean import clean_content


def extract_content_firecrawl(url):
    try:
        api_key = config("KEY_FIRECRAWL")
        if not api_key:
            raise APIException("Chave API KEY não encontrada no .env!")
    except UndefinedValueError:
        raise APIException("Chave API KEY não encontrada no .env!")

    client = FirecrawlApp(api_key=api_key)

    try:
        doc = client.scrape(url, formats=["markdown"], only_main_content=True)
        if doc:
            raw_content = doc.markdown
            cleaned_content = clean_content(raw_content)

            data = {
                "title": getattr(doc.metadata, "title", "") or "",
                "description": getattr(doc.metadata, "description", "") or "",
                "content": cleaned_content,
                "url": getattr(doc.metadata, "url", "") or "",
            }

            return data
        else:
            return APIException('"Não foi possível obter dados da URL."')

    except Exception as e:
        return APIException(f"Erro ao acessar Firecrawl: {e}")


if __name__ == "__main__":
    url = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"
    data = extract_content_firecrawl(url)
    pprint(data)
