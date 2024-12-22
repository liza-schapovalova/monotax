from dataclasses import dataclass
from typing import Optional
import requests

from util import fetch_with_retries

# Constants
BASE_MONOBANK_URL = "https://api.monobank.ua/personal/statement/{account}/{from_epoch}/{to_epoch}"
BASE_MONOBANK_CLIENT_INFO_URL = "https://api.monobank.ua/personal/client-info"

@dataclass
class Transaction:
    id: str
    time: int
    description: str
    mcc: int
    originalMcc: int
    hold: bool
    amount: int
    operationAmount: int
    currencyCode: int
    commissionRate: int
    cashbackAmount: int
    balance: int
    comment: Optional[str] = None
    receiptId: Optional[str] = None
    invoiceId: Optional[str] = None
    counterEdrpou: Optional[str] = None
    counterIban: Optional[str] = None
    counterName: Optional[str] = None

@dataclass
class ClientInfo:
    accounts: dict[int, list[str]]
    ibans: list[str]

def fetch_client_info(api_token: str) -> ClientInfo:
    headers = {"X-Token": api_token}
    response = requests.get(BASE_MONOBANK_CLIENT_INFO_URL, headers=headers)
    response.raise_for_status()

    client_info = response.json()
    accounts = client_info.get("accounts", [])

    currency_to_fop_accounts = {}
    ibans = []

    for account in accounts:
        if account.get("type") == "fop":
            currency_code = account.get("currencyCode")
            account_id = account.get("id")
            iban = account.get("iban")
            if currency_code not in currency_to_fop_accounts:
                currency_to_fop_accounts[currency_code] = []
            currency_to_fop_accounts[currency_code].append(account_id)
            ibans.append(iban)

    return ClientInfo(currency_to_fop_accounts, ibans)

def fetch_statement(api_token: str, account: dict[int, str], from_timestamp: int, to_timestamp: int) -> Transaction:
    url = BASE_MONOBANK_URL.format(account=account, from_epoch=from_timestamp, to_epoch=to_timestamp)
    headers = {"X-Token": api_token}
    response = fetch_with_retries(url, headers=headers, delay=[10, 20, 30, 60])
    response.raise_for_status()

    json_array = response.json()

    return [Transaction(**json) for json in json_array]
