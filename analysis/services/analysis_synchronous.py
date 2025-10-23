import concurrent.futures
import time

from rest_framework.exceptions import APIException

from analysis.services import (
    analyze_with_llm,
    extract_content_firecrawl,
    search_fact_check,
)


def run_full_analysis_synchronous(url):
    start_time = time.time()
    try:
        firecrawl_data = extract_content_firecrawl(url=url)
        title = firecrawl_data.get("title", "")
        content = firecrawl_data.get("content", "")

    except Exception as e:
        raise APIException(f"Falha na extração de conteudo 'firecrawl': {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # A - Virus Total
        future_vt = executor.submit()

        # B - Google Fact Check
        future_fact_check = executor.submit(search_fact_check, title)

        # C - LLM Gemini
        future_llm = executor.submit(analyze_with_llm, content)
