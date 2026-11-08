"""The judges' numbers never change (R18, R15). An independent oracle, transliterated from the README's "How judges calculate the numbers".

It reads the raw CSVs with `csv` and `statistics.median` and imports nothing from app.engine.data, formulas or profile. It checks
I, F, S, B, H and P and the before-runway label on every account, then 13 shocks through apply_shock, with 0 mismatches allowed.
"""
import csv
import statistics
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

from app.engine import IncomeCut, Shock, apply_shock, get_profile

DATA = Path(__file__).resolve().parents[2] / "data"
TOL = 1e-6


@lru_cache(maxsize=1)
def oracle_data():
    rows = {}
    with open(DATA / "monthly_summary.csv", newline="") as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["account_id"]), []).append(r)
    for x in rows.values():
        x.sort(key=lambda r: r["month"])
    with open(DATA / "loans.csv", newline="") as f:
        loans = {int(r["account_id"]): r for r in csv.DictReader(f)}
    return rows, loans


def oracle_inputs(a):
    rows, loans = oracle_data()
    x = rows[a]
    v = lambda r, k: float(r[k])
    last6 = x[-6:]
    running = a in loans and loans[a]["status"] in ("C", "D")      # still running at the end of 2025
    return dict(
        I=statistics.median(v(r, "money_in") for r in x),
        F=statistics.median(v(r, "household_bills") + v(r, "insurance") + v(r, "loan_payments") for r in x),
        S=statistics.median(v(r, "money_out") for r in x),
        B=sum(v(r, "avg_daily_balance") for r in last6) / len(last6),
        H=statistics.median(v(r, "household_bills") for r in x),
        P=float(loans[a]["monthly_payment"]) if running else 0.0,
    )


def oracle_runway(buffer_left, gap):
    """The README block, verbatim logic. (months or None, label)."""
    if buffer_left <= 0:
        return 0.0, "0 months"
    if gap <= 0:
        return None, "No shortfall (120+)"
    r = round(min(buffer_left / gap, 120), 1)
    return r, f"{r:.1f} months"


def oracle_shocked(d, keep=None, bills_pct=0.0, rent=0.0, one_off_dollars=0.0, one_off_mult=0.0):
    income_after = keep * d["I"] if keep is not None else d["I"]
    spending_after = d["S"] + bills_pct / 100 * d["H"] + rent
    one_off = one_off_dollars + one_off_mult * d["S"]
    buffer_left = d["B"] - one_off
    gap = spending_after - income_after
    months, label = oracle_runway(buffer_left, gap)
    return dict(income_after=income_after, spending_after=spending_after, one_off=one_off, buffer_left=buffer_left, gap=gap,
                months=months, label=label)


# name: (engine shock, through_months, oracle kwargs). The 5 base twists, then the QA additions (R18).
SHOCKS = {
    "none": (Shock(), None, {}),
    "ei55": (Shock(income_cut=IncomeCut(0.55, 6)), None, dict(keep=0.55)),
    "ei55_bills15": (Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15), None, dict(keep=0.55, bills_pct=15)),
    "bills15": (Shock(bills_increase_pct=15), None, dict(bills_pct=15)),
    "oneoff1S": (Shock(one_off_spending_multiple=1), None, dict(one_off_mult=1)),
    "ei40": (Shock(income_cut=IncomeCut(0.40, 6)), None, dict(keep=0.40)),
    "income0": (Shock(income_cut=IncomeCut(0.0, 6)), None, dict(keep=0.0)),
    "bills50": (Shock(bills_increase_pct=50), None, dict(bills_pct=50)),
    "bills100": (Shock(bills_increase_pct=100), None, dict(bills_pct=100)),
    "oneoff2S": (Shock(one_off_spending_multiple=2), None, dict(one_off_mult=2)),
    "oneoff10000": (Shock(one_off_dollars=10000), None, dict(one_off_dollars=10000)),
    "rent300": (Shock(other_spending_change=300), None, dict(rent=300)),
    "triple_ei55_bills15_oneoff1S": (Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15, one_off_spending_multiple=1), 6,
                                     dict(keep=0.55, bills_pct=15, one_off_mult=1)),
}


def ids():
    return sorted(oracle_data()[0])


def test_oracle_covers_every_account():
    assert len(ids()) == 4500


def test_inputs_and_before_runway_match_on_every_account():
    bad = []
    for a in ids():
        d, p = oracle_inputs(a), get_profile(a)
        for k in ("I", "F", "S", "B", "H", "P"):
            if abs(getattr(p, k) - d[k]) > TOL:
                bad.append((a, k, getattr(p, k), d[k]))
        months, label = oracle_runway(d["B"], d["S"] - d["I"])
        if p.runway.label != label:
            bad.append((a, "runway.label", p.runway.label, label))
    assert bad == []


@pytest.mark.parametrize("name", list(SHOCKS))
def test_shock_matches_the_oracle_on_every_account(name):
    shock, through, kwargs = SHOCKS[name]
    bad = []
    for a in ids():
        o = oracle_shocked(oracle_inputs(a), **kwargs)
        r = apply_shock(a, shock, through_months=through)
        for k in ("income_after", "spending_after", "one_off", "buffer_left", "gap"):
            if abs(getattr(r, k) - o[k]) > TOL:
                bad.append((a, k, getattr(r, k), o[k]))
        if r.runway.label != o["label"]:
            bad.append((a, "runway.label", r.runway.label, o["label"]))
        if (r.runway.months is None) != (o["months"] is None) or (o["months"] is not None and r.runway.months != o["months"]):
            bad.append((a, "runway.months", r.runway.months, o["months"]))
    assert bad == []


def test_finished_loans_have_no_payment_and_running_loans_have_theirs():
    """R15: P is 0 for status A and B, and the monthly payment for C and D. A mutant treating A or B as running fails here."""
    _, loans = oracle_data()
    by_status = Counter(r["status"] for r in loans.values())
    assert {s: by_status[s] for s in "ABCD"} == {"A": 203, "B": 31, "C": 403, "D": 45}
    bad = []
    for a, loan in loans.items():
        p = get_profile(a)
        expected = float(loan["monthly_payment"]) if loan["status"] in ("C", "D") else 0.0
        if p.P != expected or p.running_loan != (loan["status"] in ("C", "D")):
            bad.append((a, loan["status"], p.P, expected))
    assert bad == []


@pytest.mark.parametrize("account,status", [(20111, "D"), (66505, "C")])
def test_running_loan_examples_carry_their_payment(account, status):
    _, loans = oracle_data()
    assert loans[account]["status"] == status
    assert get_profile(account).P == pytest.approx(float(loans[account]["monthly_payment"]), abs=1e-9)


def test_a_finished_loan_example_has_no_payment():
    _, loans = oracle_data()
    finished = sorted(a for a, r in loans.items() if r["status"] in ("A", "B"))
    assert finished and all(get_profile(a).P == 0.0 for a in finished[:5])
