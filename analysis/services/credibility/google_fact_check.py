import requests
from decouple import UndefinedValueError, config
from rest_framework.exceptions import APIException


def search_fact_check(query):
    try:
        api_key = config("KEY_FACT_CHECK")
        if not api_key:
            raise APIException("Chave API GOOGLE_FACTCHECK não encontrada no .env!")
    except UndefinedValueError:
        raise APIException("Chave API GOOGLE_FACTCHECK não encontrada no .env!")

    url_google = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    params = {"key": api_key, "query": query, "languageCode": "pt-BR", "pageSize": 5}

    try:
        response = requests.post(url=url_google, params=params)
        data = response.json()
        if response.status_code != 200:
            error_message = data.get("error", {}).get(
                "message", "Erro desconhecido ou falha ao ler o JSON"
            )
            raise APIException(f"Erro na API: {error_message}")

        return data

    except requests.exceptions.HTTPError as e:
        raise APIException(f"Erro na API: {e}")
    except requests.exceptions.RequestException as e:
        raise APIException(f"Erro na requisição da API: {e}")
    except Exception as e:
        raise APIException(f"Erro inesperado: {e}")
