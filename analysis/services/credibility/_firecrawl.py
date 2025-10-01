import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from pprint import pprint

from decouple import config
from firecrawl import FirecrawlApp
from rest_framework.exceptions import APIException, ValidationError

from analysis.util.clean import clean_content


def extract_content_firecrawl(url):
    api_key = config("KEY_FIRECRAWL")
    if not api_key:
        raise APIException("Chave API KEY não encontrada no .env!")

    client = FirecrawlApp(api_key=api_key)

    try:
        doc = client.scrape(url, formats=["markdown"], only_main_content=True)

        raw_content = doc.markdown
        cleaned_content = clean_content(raw_content)

        data = {
            "title": doc.metadata.title,
            "description": doc.metadata.description,
            "content": cleaned_content,
            "url": doc.metadata.url,
        }

        return data

    except APIException:
        return


if __name__ == "__main__":
    url = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"
    data = extract_content_firecrawl(url)
    pprint(data)
