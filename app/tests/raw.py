"""Independent figures from the raw CSVs, standard library only, for checking the engine."""
import csv
import statistics
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=None)
def _rows_by_account():
    out = {}
    with open(DATA / "monthly_summary.csv", newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault(int(row["account_id"]), []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: r["month"])
    return out


def judges(account_id):
    rows = _rows_by_account()[account_id]
    col = lambda name: [float(r[name]) for r in rows]
    fixed = [float(r["household_bills"]) + float(r["insurance"]) + float(r["loan_payments"]) for r in rows]
    payment = 0.0
    with open(DATA / "loans.csv", newline="") as f:
        for row in csv.DictReader(f):
            if int(row["account_id"]) == account_id and row["status"] in ("C", "D"):
                payment = float(row["monthly_payment"])
    return {
        "I": statistics.median(col("money_in")),
        "S": statistics.median(col("money_out")),
        "H": statistics.median(col("household_bills")),
        "F": statistics.median(fixed),
        "P": payment,
        "B": statistics.mean(float(r["avg_daily_balance"]) for r in rows[-6:]),
    }


def readme_runway(buffer_left, gap):
    """README rules. Returns 0.0, the string 'no shortfall', or months rounded to 1 decimal."""
    if buffer_left <= 0:
        return 0.0
    if gap <= 0:
        return "no shortfall"
    return round(min(buffer_left / gap, 120), 1)
