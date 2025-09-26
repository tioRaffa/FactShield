from pprint import pprint

import requests
from decouple import config
from rest_framework.exceptions import APIException, ValidationError


def scan_url(url):
    api_key = config("KEY_VIRUS_TOTAL")
    if not api_key:
        raise APIException("Chave API KEY não encontrada no .env!")

    url_virus_total = "https://www.virustotal.com/api/v3/urls"
    payload = {"url": f"{url}"}
    headers = {
        "accept": "application/json",
        "x-apikey": api_key,
        "content-type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(url=url_virus_total, data=payload, headers=headers)
        data = response.json()

        if response.status_code != 200:
            error_messages = data.get("error", {}).get("message", "erro desconhecido")
            raise APIException(f"Erro na API: {error_messages}")

        url_id = data.get("data", {}).get("id")
        return url_id

    except requests.exceptions.HTTPError as e:
        raise APIException(f"Erro na api: {e}")
    except requests.exceptions.RequestException as e:
        raise APIException(f"Erro na requisição: {e}")


if __name__ == "__main__":
    x = scan_url("https://github.com/tioRaffa/FactShield")
    pprint(x)
