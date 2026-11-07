"""Loads the CSVs once. Paths are relative to this file, so any working directory works."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
END_OF_DATA = pd.Timestamp("2025-12-31")
LAST_DATA_MONTH = "2025-12"


@dataclass(frozen=True)
class Dataset:
    rows_by_account: dict       # account_id -> DataFrame of monthly_summary rows, sorted by month
    orders_by_account: dict     # account_id -> DataFrame of standing orders
    people_by_account: dict     # account_id -> DataFrame of dispositions
    loans: dict                 # account_id -> dict of loan fields
    clients: dict               # client_id -> dict of client fields
    branch: dict                # account_id -> dict of account fields
    districts: dict             # district_id -> dict of district fields
    card_by_disposition: dict   # disposition_id -> card type
    card_issued: dict           # disposition_id -> date the card was issued


@lru_cache(maxsize=1)
def get_dataset():
    ms = pd.read_csv(DATA_DIR / "monthly_summary.csv").sort_values(["account_id", "month"], ignore_index=True)
    ms["days_below_zero"] = ms["days_below_zero"].astype(int)  # some rows write this as 4.0
    loans = pd.read_csv(DATA_DIR / "loans.csv").set_index("account_id")
    accounts = pd.read_csv(DATA_DIR / "accounts.csv").set_index("account_id")
    clients = pd.read_csv(DATA_DIR / "clients.csv", parse_dates=["birth_date"]).set_index("client_id")
    dispositions = pd.read_csv(DATA_DIR / "dispositions.csv")
    districts = pd.read_csv(DATA_DIR / "districts.csv").set_index("district_id")
    orders = pd.read_csv(DATA_DIR / "standing_orders.csv")
    cards = pd.read_csv(DATA_DIR / "cards.csv")
    return Dataset(
        rows_by_account={int(a): x.reset_index(drop=True) for a, x in ms.groupby("account_id")},
        orders_by_account={int(a): x for a, x in orders.groupby("account_id")},
        people_by_account={int(a): x for a, x in dispositions.groupby("account_id")},
        loans=loans.to_dict("index"),
        clients=clients.to_dict("index"),
        branch=accounts.to_dict("index"),
        districts=districts.to_dict("index"),
        card_by_disposition=cards.set_index("disposition_id").card_type.to_dict(),
        card_issued=cards.set_index("disposition_id").issued.to_dict(),
    )
