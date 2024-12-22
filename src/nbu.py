import requests


BASE_NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?json&date={date}"


def fetch_exchange_rate(date) -> dict[str, float]:
    url = BASE_NBU_URL.format(date=date)
    response = requests.get(url)
    response.raise_for_status()
    exchange_rates = response.json()
    
    return {rate["cc"]: rate["rate"] for rate in exchange_rates}

