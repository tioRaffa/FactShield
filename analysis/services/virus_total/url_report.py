import pprint
import time

import requests
from decouple import config
from rest_framework.exceptions import APIException, ValidationError

from .scan_url import scan_url


def get_report(url_id):
    api_key = config("KEY_VIRUS_TOTAL")
    if not api_key:
        raise APIException("Chave API KEY não encontrada no .env!")

    url = f"https://www.virustotal.com/api/v3/analyses/{url_id}"

    headers = {"accept": "application/json", "x-apikey": api_key}

    try:
        response = requests.get(url=url, headers=headers)
        data = response.json()

        if response.status_code != 200:
            error_message = data.get("error", {}).get("message", "erro desconhecido")
            raise APIException(f"Erro na API: {error_message}")

        return data

    except requests.exceptions.HTTPError as e:
        raise APIException(f"Erro na API: {e}")
    except requests.exceptions.RequestException as e:
        raise APIException(f"Erro na requisição: {e}")


if __name__ == "__main__":
    url_to_scan = "https://github.com/tioRaffa/FactShield"
    print(f"Submetendo URL: {url_to_scan}")

    url_id = scan_url(url_to_scan)
    print(f"ID de Análise obtido: {url_id}")

    print("Aguardando 15 segundos antes de buscar o relatório...")
    time.sleep(15)

    final_report = get_report(url_id)
    print("\n--- Relatório Final ---")
    pprint(final_report)
