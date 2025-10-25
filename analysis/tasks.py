import concurrent.futures
import os
import sys
import time

from celery import shared_task
from django.core.cache import cache
from rest_framework.exceptions import APIException

from analysis.services import (
    _scan_url,
    analyze_with_llm,
    extract_content_firecrawl,
    get_report,
    search_fact_check,
)

CACHE_5MIN_TTL = 300


@shared_task()
def run_full_analysis_task(url, cache_key):
    start_time = time.time()

    # ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # TAREFAS 1 e 2
        future_firecrawl = executor.submit(extract_content_firecrawl, url)
        future_vt_id = executor.submit(_scan_url, url)

        # Espera a Extração e o ID do VirusTotal
        try:
            firecrawl_data = future_firecrawl.result(timeout=30)
            url_id = future_vt_id.result(timeout=30)
        except Exception as e:
            raise APIException(f"Falha na obtenção de dados iniciais: {e}")

        # TAREFAS 3, 4 e 5
        title = firecrawl_data.get("title", "")
        content = firecrawl_data.get("content", "")

        # 3 - Virus Total
        future_vt = executor.submit(get_report, url_id)

        # 4 - Google Fact Check
        future_fact_check = executor.submit(search_fact_check, title)

        # 5 - LLM Gemini
        future_llm = executor.submit(analyze_with_llm, content)

        # SINCRONIZAÇÃO FINAL
        vt_result = future_vt.result(timeout=120)
        fact_check_result = future_fact_check.result(timeout=60)
        llm_result = future_llm.result(timeout=120)

    end_time = time.time()

    # Determinação do veredicto final
    if fact_check_result:
        final_verdict_source = "HUMANO (Fact-Check)"
        final_veredict = fact_check_result.get("veredict", "N/A")
    else:
        final_verdict_source = "INTELIGÊNCIA ARTIFICIAL (LLM)"
        final_veredict = llm_result.get("llm_recommendation", "INCONCLUSIVO")

    final_report = {
        "analysis_time_seconds": round(end_time - start_time, 2),
        "final_verdict_source": final_verdict_source,
        "final_veredict": final_veredict,
        "virustotal_report": vt_result,
        "fact_check_report": fact_check_result,
        "llm_analysis": llm_result,
        "firecrawl_data": firecrawl_data,
    }
    cache.set(cache_key, final_report, timeout=CACHE_5MIN_TTL)

    return final_report
