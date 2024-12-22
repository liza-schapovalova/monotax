# import openpyxl module
import time as t
from datetime import datetime
from pathlib import Path
import openpyxl
import tqdm

from mono import ClientInfo, Transaction, fetch_client_info, fetch_statement
from nbu import fetch_exchange_rate
from util import MonotaxConfig, get_month_epoch_bounds, load_conf

# Give the location of the file
TEMPLATE_PATH = Path("templates", "report.xlsx")
OUTPUT_PATH = Path("output")

CURRENCY_CODES = {
    980: "UAH",
    978: "EUR",
    840: "USD",
}

def calculate_total_in_uah(statements: list[Transaction], exchange_rates: dict[str, float], client_info: ClientInfo):
    total = 0
    for transaction in statements:
        if transaction.amount > 0 and transaction.counterIban not in client_info.ibans:  # Incoming transactions only
            amount = transaction.amount / 100  # Convert to base currency units
            currency_code = CURRENCY_CODES.get(transaction.currencyCode)

            if currency_code == "UAH":
                total += amount
            elif currency_code in exchange_rates:
                total += amount * exchange_rates[currency_code]

    return total

def get_mono_statement(interval: tuple[int, int], client_info: ClientInfo, conf: MonotaxConfig) -> float:
    from_timestamp, to_timestamp = interval
    all_statements = []

    for _, account_ids in client_info.accounts.items():
        for account_id in account_ids:            
            statements = fetch_statement(conf.api_token, account_id, from_timestamp, to_timestamp)
            all_statements.extend(statements)

    # Group statements by date and fetch exchange rates
    grouped_by_date = {}
    for transaction in all_statements:
        date = datetime.fromtimestamp(transaction.time).strftime("%Y%m%d")
        if date not in grouped_by_date:
            grouped_by_date[date] = []
        grouped_by_date[date].append(transaction)

    total_in_uah = 0
    for date, transactions in grouped_by_date.items():
        exchange_rates = fetch_exchange_rate(date)
        total_in_uah += calculate_total_in_uah(transactions, exchange_rates, client_info)

    return total_in_uah

def get_mounth_earning(year: int, month: int) -> float:
        current_month = datetime.now().month
        current_year = datetime.now().year

        conf = load_conf()
        client_info = fetch_client_info(conf.api_token)

        if month < current_month or year < current_year:
            return get_mono_statement(get_month_epoch_bounds(year, month), client_info, conf)
        else:
            return 0


def generate_report(year: int) -> Path:
    current_month = datetime.now().month
    current_year = datetime.now().year

    conf = load_conf()
    client_info = fetch_client_info(conf.api_token)

    def get_statement_by_mounth(month: int):
        if month < current_month or year < current_year:
            return get_mono_statement(get_month_epoch_bounds(year, month), client_info, conf)
        else:
            return 0

    wb_obj = openpyxl.load_workbook(TEMPLATE_PATH)
    sheet_obj = wb_obj.active

    cells = ['D9', 'D10', 'D11', 'D13', 'D14', 'D15', 'D18', 'D19', 'D20', 'D23', 'D24', 'D25']

    print("Fetching transactions")
    
    for i in tqdm.tqdm(range(len(cells))):
        sheet_obj[cells[i]] = get_statement_by_mounth(i + 1)

    report_path = OUTPUT_PATH / f"report-{year}-{current_month}.xlsx"

    wb_obj.save(report_path)

    print(f"Saved to: {report_path}")

    return report_path


if __name__ == "__main__":
    print(get_mounth_earning(2024, 6))
