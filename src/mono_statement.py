import requests
import json
import datetime
from pathlib import Path

# Load API token from configuration file
CONFIG_FILE = Path("conf", "config.json")

def load_api_token():
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found.")

    with open(config_path, "r") as file:
        config = json.load(file)
    
    return config.get("api_token")

# Constants
BASE_MONOBANK_URL = "https://api.monobank.ua/personal/statement/{account}/{from_epoch}/{to_epoch}"
BASE_NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?json&date={date}"

ACCOUNTS = {
    "UAH": "kVYWIN-Ewz1kH-RN3Sm6NA",
    "EUR": "Oloc2gnjYkXQh5NQsQDr_A",
    "USD": "TfUZpzEI_ffVNEf4n1rSPw",
}

CURRENCY_CODES = {
    980: "UAH",
    978: "EUR",
    840: "USD",
}

def get_timestamp_offset(months=0):
    """Get Unix timestamps for the current date and a given offset in months."""
    # today = datetime.date.today()
    # start_date = today.replace(day=1) - datetime.timedelta(days=1)
    # start_of_month = start_date.replace(day=1)
    
    # from_timestamp = int(start_of_month.strftime("%s"))
    # to_timestamp = int(today.strftime("%s"))

    # return from_timestamp, to_timestamp
    return 1732131471, 1734723474

def fetch_statement(api_token, account, from_timestamp, to_timestamp):
    url = BASE_MONOBANK_URL.format(account=account, from_epoch=from_timestamp, to_epoch=to_timestamp)
    headers = {"X-Token": api_token}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_exchange_rate(date):
    url = BASE_NBU_URL.format(date=date)
    response = requests.get(url)
    response.raise_for_status()
    exchange_rates = response.json()
    
    return {rate["cc"]: rate["rate"] for rate in exchange_rates}

def calculate_total_in_uah(statements, exchange_rates):
    total = 0
    for transaction in statements:
        if transaction["amount"] > 0:  # Incoming transactions only
            amount = transaction["amount"] / 100  # Convert to base currency units
            currency_code = CURRENCY_CODES.get(transaction["currencyCode"])

            if currency_code == "UAH":
                total += amount
            elif currency_code in exchange_rates:
                total += amount * exchange_rates[currency_code]

    return total

def main():
    try:
        api_token = load_api_token()
    except Exception as e:
        print(f"Error loading API token: {e}")
        return

    from_timestamp, to_timestamp = get_timestamp_offset()
    all_statements = []

    for currency, account_id in ACCOUNTS.items():
        try:
            statements = fetch_statement(api_token, account_id, from_timestamp, to_timestamp)
            all_statements.extend(statements)
        except Exception as e:
            print(f"Error fetching statements for {currency}: {e}")

    # Group statements by date and fetch exchange rates
    grouped_by_date = {}
    for transaction in all_statements:
        date = datetime.datetime.fromtimestamp(transaction["time"]).strftime("%Y%m%d")
        if date not in grouped_by_date:
            grouped_by_date[date] = []
        grouped_by_date[date].append(transaction)

    total_in_uah = 0
    for date, transactions in grouped_by_date.items():
        try:
            exchange_rates = fetch_exchange_rate(date)
            total_in_uah += calculate_total_in_uah(transactions, exchange_rates)
        except Exception as e:
            print(f"Error fetching exchange rates for date {date}: {e}")

    print(f"Total incoming transactions in UAH: {total_in_uah:.2f}")

if __name__ == "__main__":
    main()
