from pprint import pprint

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
        response = requests.get(url=url_google, params=params)
        data = response.json()
        if response.status_code != 200:
            error_message = data.get("error", {}).get(
                "message", "Erro desconhecido ou falha ao ler o JSON"
            )
            raise APIException(f"Erro na API: {error_message}")

        claims = data.get("claims", [])
        if not claims:
            return {}

        first_claim = claims[0]
        first_review = first_claim.get("claimReview", [{}])[0]
        publisher = first_review.get("publisher", {})

        return {
            "fact_check_status": "Human Vefiried",
            "veredict": first_review.get("textualRating", "N/A"),
            "fact_checker": publisher.get("name", "Desconhecido"),
            "fact_check_url": first_review.get("url", ""),
            "claim_text": first_claim.get("text", ""),
            "claim_date": first_claim.get("claimDate", ""),
            "claimant": first_claim.get("claimant", ""),
        }

    except APIException as e:
        raise e
    except requests.exceptions.HTTPError as e:
        raise APIException(f"Erro na API: {e}")
    except requests.exceptions.RequestException as e:
        raise APIException(f"Erro na requisição da API: {e}")
    except Exception as e:
        raise APIException(f"Erro inesperado: {e}")


if __name__ == "__main__":
    query = "Vacinas causam autismo"

    try:
        results = search_fact_check(query=query)
        if results:
            pprint(results)
        else:
            print("nada encontrado. chamar a IA para dar veredito final")
    except APIException as e:
        print(f"{e}")
