import concurrent.futures
import os
import sys
import time
from pprint import pprint

from rest_framework.exceptions import APIException

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from analysis.services import (
    _scan_url,
    analyze_with_llm,
    extract_content_firecrawl,
    get_report,
    search_fact_check,
)


def run_full_analysis_synchronous(url):
    start_time = time.time()

    # Extração de conteúdo
    try:
        firecrawl_data = extract_content_firecrawl(url=url)
        title = firecrawl_data.get("title", "")
        content = firecrawl_data.get("content", "")
    except Exception as e:
        raise APIException(f"Falha na extração de conteudo 'firecrawl': {e}")

    # Scan da URL
    try:
        url_id = _scan_url(url=url)
    except Exception as e:
        raise APIException(f"Falha no scan da URL: {e} ")

    # Execução paralela das análises
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # A - Virus Total
        future_vt = executor.submit(get_report, url_id)

        # B - Google Fact Check
        future_fact_check = executor.submit(search_fact_check, title)

        # C - LLM Gemini
        future_llm = executor.submit(analyze_with_llm, content)

        vt_result = future_vt.result(timeout=60)
        fact_check_result = future_fact_check.result(timeout=20)
        llm_result = future_llm.result(timeout=120)

    end_time = time.time()

    # Determinação do veredicto final
    if fact_check_result:
        final_verdict_source = "HUMANO (Fact-Check)"
        final_veredict = fact_check_result.get("veredict", "N/A")
    else:
        final_verdict_source = "INTELIGÊNCIA ARTIFICIAL (LLM)"
        final_veredict = llm_result.get("llm_recommendation", "INCONCLUSIVO")

    return {
        "analysis_time_seconds": round(end_time - start_time, 2),
        "final_verdict_source": final_verdict_source,
        "final_veredict": final_veredict,
        "virustotal_report": vt_result,
        "fact_check_report": fact_check_result,
        "llm_analysis": llm_result,
        "firecrawl_data": firecrawl_data,
    }


if __name__ == "__main__":
    url = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"

    reusltado = run_full_analysis_synchronous(url=url)
    pprint(reusltado)
