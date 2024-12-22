import calendar
from dataclasses import dataclass
import datetime
import json
import time as t
from pathlib import Path

import requests


# Load API token from configuration file
CONFIG_FILE = Path("conf", "config.json")

@dataclass
class MonotaxConfig:
    api_token: str
    

def load_conf() -> MonotaxConfig:
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found.")

    with open(config_path, "r") as file:
        config = json.load(file)
    
    return MonotaxConfig(**config)

def fetch_with_retries(url, headers, delay):
    for attempt in range(1, len(delay) + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)  # Add timeout to avoid indefinite hangs
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return response  # Successful response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < len(delay):
                t.sleep(delay[attempt])  # Wait before retrying
            else:
                print("All retries failed.")
                raise  # Re-raise the exception if all retries fail


def get_month_epoch_bounds(year: int, month: int) -> tuple[int, int]:
    """
    Returns the epoch seconds for the start and end of a given month.
    
    Args:
        year (int): The year (e.g., 2024).
        month (int): The month (1 for January, 12 for December).
        
    Returns:
        tuple: (start_epoch, end_epoch)
            - start_epoch: Epoch seconds for the start of the month.
            - end_epoch: Epoch seconds for the end of the month.
    """
    # Ensure the month is valid
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")
    
    # Start of the month
    start_date = datetime.datetime(year, month, 1)
    start_epoch = int(start_date.timestamp())
    
    # End of the month
    _, last_day = calendar.monthrange(year, month)  # Get the last day of the month
    end_date = datetime.datetime(year, month, last_day, 23, 59, 59)
    end_epoch = int(end_date.timestamp())
    
    return start_epoch, end_epoch
