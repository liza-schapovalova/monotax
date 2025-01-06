from datetime import datetime
from pathlib import Path
import openpyxl
import tqdm

from mono import ClientInfo, Transaction, fetch_client_info, fetch_statement
from nbu import fetch_exchange_rate
from util import MonotaxConfig, add_dict, get_month_epoch_bounds, load_conf, sum_dict

TEMPLATE_PATH = Path("templates", "ladger-book-template.xlsx")
OUTPUT_PATH = Path("output")

CURRENCY_CODES = {
    980: "UAH",
    978: "EUR",
    840: "USD",
}

def calculate_total_in_uah(statements: list[Transaction], exchange_rates: dict[str, float], client_info: ClientInfo) -> dict[str, float]:
    total = {}
    for transaction in statements:
        if transaction.amount > 0 and transaction.counterIban not in client_info.ibans:
            amount = transaction.amount / 100
            currency_code = CURRENCY_CODES.get(transaction.currencyCode)

            if currency_code not in total:
                total[currency_code] = 0

            if currency_code == "UAH":
                total[currency_code] += amount
            elif currency_code in exchange_rates:
                total[currency_code] += amount * exchange_rates[currency_code]

    return total

def get_mono_statement(interval: tuple[int, int], client_info: ClientInfo, conf: MonotaxConfig) -> dict[str, float]:
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

    total_in_uah = {}
    for date, transactions in grouped_by_date.items():
        exchange_rates = fetch_exchange_rate(date)
        add_dict(total_in_uah, calculate_total_in_uah(transactions, exchange_rates, client_info))

    return total_in_uah

def get_mounth_earning(year: int, month: int) -> dict[str, float]:
        current_month = datetime.now().month
        current_year = datetime.now().year

        conf = load_conf()
        client_info = fetch_client_info(conf.api_token)

        if month < current_month or year < current_year:
            return get_mono_statement(get_month_epoch_bounds(year, month), client_info, conf)
        else:
            return {"UAH": 0}


def generate_report(year: int) -> Path:
    current_month = datetime.now().month
    current_year = datetime.now().year

    conf = load_conf()
    client_info = fetch_client_info(conf.api_token)

    def get_total_by_mounth(month: int):
        if month < current_month or year < current_year:
            return get_mono_statement(get_month_epoch_bounds(year, month), client_info, conf)
        else:
            return {"UAH": 0}

    wb_obj = openpyxl.load_workbook(TEMPLATE_PATH)
    book_sheet = wb_obj['book']
    transcript_sheet = wb_obj['transcript']

    book_cells = ['D9', 'D10', 'D11', 'D13', 'D14', 'D15', 'D18', 'D19', 'D20', 'D23', 'D24', 'D25']
    transcript_cells = [
        ['C3', 'D3', 'E3'],
        ['C4', 'D4', 'E4'],
        ['C5', 'D5', 'E5'],
        ['C6', 'D6', 'E6'],
        ['C7', 'D7', 'E7'],
        ['C8', 'D8', 'E8'],
        ['C9', 'D9', 'E9'],
        ['C10', 'D10', 'E10'],
        ['C11', 'D11', 'E11'],
        ['C12', 'D12', 'E12'],
        ['C13', 'D13', 'E13'],
        ['C14', 'D14', 'E14'],
    ]

    print("Fetching transactions")
    
    for i in tqdm.tqdm(range(12)):
        total = get_total_by_mounth(i + 1)
        book_sheet[book_cells[i]] = sum_dict(total)
        transcript_sheet[transcript_cells[i][0]] = total.get('UAH', 0)
        transcript_sheet[transcript_cells[i][1]] = total.get('EUR', 0)
        transcript_sheet[transcript_cells[i][2]] = total.get('USD', 0)

    report_path = OUTPUT_PATH / f"report-{year}-{current_month}.xlsx"

    wb_obj.save(report_path)

    print(f"Saved to: {report_path}")

    return report_path


if __name__ == "__main__":
    generate_report(datetime.now().year)
