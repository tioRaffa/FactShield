import os
import sys
import time
from pprint import pprint

import requests
from decouple import config
from rest_framework.exceptions import APIException, ValidationError

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, project_root)

from analysis.services.virus_total.scan_url import _scan_url  # noqa: E402


def get_report(analysis_id):
    api_key = config("KEY_VIRUS_TOTAL")
    if not api_key:
        raise APIException("Chave API KEY não encontrada no .env!")

    url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"

    headers = {"accept": "application/json", "x-apikey": api_key}

    try:
        response = requests.get(url=url, headers=headers)
        data = response.json()

        if response.status_code != 200:
            error_message = data.get("error", {}).get("message", "erro desconhecido")
            raise APIException(f"Erro na API: {error_message}")

        attributes = data.get("data", {}).get("attributes", {})
        if not attributes:
            raise ValidationError("Attributes não encontrados!")

        stats = attributes.get("stats", {})
        malicious_count = stats.get("malicious", 0)
        suspicious_count = stats.get("suspicious", 0)
        total_scans = (
            stats.get("harmless", 0)
            + malicious_count
            + suspicious_count
            + stats.get("undetected", 0)
        )

        url_scanned = data.get("meta", {}).get("url_info", {}).get("url", "N/A")
        status = attributes.get("status", "N/A")

        report = {
            "url_scanned": url_scanned,
            "malicious_count": malicious_count,
            "suspicious_count": suspicious_count,
            "total_scans": total_scans,
            "status": status,
        }
        return report

    except requests.exceptions.HTTPError as e:
        raise APIException(f"Erro na API: {e}")
    except requests.exceptions.RequestException as e:
        raise APIException(f"Erro na requisição: {e}")


if __name__ == "__main__":
    url_to_scan = "https://g1.globo.com/pr/parana/concursos-e-emprego/noticia/2025/10/01/concurso-adapar-concurso-parana.ghtml"
    print(f"Submetendo URL: {url_to_scan}")

    url_id = _scan_url(url_to_scan)
    print(f"ID de Análise obtido: {url_id}")

    print("Aguardando 15 segundos antes de buscar o relatório...")
    time.sleep(15)

    final_report = get_report(url_id)
    print("\n--- Relatório Final ---")
    print(final_report)
