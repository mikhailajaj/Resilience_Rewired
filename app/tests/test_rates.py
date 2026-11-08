"""The three saving rates and the running loan's end (RU-23, RU-27, AC-17, D12, LE-1 to LE-5)."""
import csv
from collections import Counter

import pytest

from app.engine import get_profile, make_plan
from app.engine.data import get_dataset
from app.engine.profile import account_flows
from app.engine.rates import RATE_KEYS, LoanEnd, loan_end, saving_rates
from app.tests.raw import DATA, _rows_by_account

IDS = sorted(get_dataset().rows_by_account)
CENT = dict(abs=0.01)


def _running_loans():
    with open(DATA / "loans.csv", newline="") as f:
        return [r for r in csv.DictReader(f) if r["status"] in ("C", "D")]


RUNNING = {int(r["account_id"]): r for r in _running_loans()}
IN_TYPICAL = {a for a in RUNNING if get_profile(a).loan_median > 0}
RECENT_197 = sorted(set(RUNNING) - IN_TYPICAL)


def _payoff(row, account_id):
    start = row["loan_start"]
    last = _rows_by_account()[account_id][-1]["month"]
    return (int(start[:4]) * 12 + int(start[5:7]) + int(row["duration_months"])) - (int(last[:4]) * 12 + int(last[5:7]))


def test_20111_rates_and_cuts():
    r = saving_rates(20111)
    assert [k.key for k in r.ordered] == list(RATE_KEYS) == ["actual", "judges", "lean"]
    assert r.actual.monthly == pytest.approx(-747.89, **CENT)
    assert r.judges.monthly == pytest.approx(-2260.22, **CENT)
    assert r.lean.monthly == pytest.approx(604.25, **CENT)
    assert r.lean_cut == pytest.approx(2864.46, **CENT)
    assert r.flexible_spending == pytest.approx(6269.41, **CENT)
    assert r.loan_end.payoff_month == 36 and r.loan_end.status == "D"
    assert (r.actual.is_headline, r.actual.is_ours) == (True, True)
    assert (r.judges.is_headline, r.judges.is_ours) == (False, False)
    assert (r.lean.is_headline, r.lean.is_ours) == (False, True)


def test_32078_lean_budget_and_no_fixed_costs():
    r = saving_rates(32078)
    assert r.lean_spending == pytest.approx(1346.39, **CENT)
    assert r.fixed_costs == 0.0 and r.loan_end is None


def test_rates_match_flows_and_plan_on_every_account():
    for a in IDS:
        r = saving_rates(a)
        assert r.actual.monthly == account_flows(a).change_last_12
        assert r.actual.monthly == pytest.approx(make_plan(a).goal.actual_change_last_12, abs=1e-9)


ORDERS_ABOVE_LEAN = {22286, 26699, 36427}


def test_lean_cut_is_the_lean_months_step_wherever_it_exists():
    seen = with_orders = 0
    for a in IDS:
        steps = make_plan(a).backup.steps
        step = [s for s in steps if s.code == "lean_months"]
        if not step:
            continue
        seen += 1
        r = saving_rates(a)
        orders = sum(o.amount for o in get_profile(a).standing_orders if o.purpose == "other")
        with_orders += orders > 0
        if a in ORDERS_ABOVE_LEAN:
            assert orders > r.lean_above
            assert step[0].monthly_saving == pytest.approx(r.flexible_spending - orders, abs=1e-6)
        else:
            assert r.lean_cut == pytest.approx(step[0].monthly_saving, abs=1e-6)
    assert seen > 100 and with_orders > 0


def test_lean_cut_on_95548_is_the_lean_step_not_orders_plus_lean():
    steps = {s.code: s.monthly_saving for s in make_plan(95548).backup.steps}
    assert saving_rates(95548).lean_cut == pytest.approx(1258.54, **CENT)
    assert steps["lean_months"] == pytest.approx(saving_rates(95548).lean_cut, abs=1e-6)
    assert steps["cancel_other_orders"] == pytest.approx(1413, abs=1)


def test_lean_above_fixed_equals_the_old_formula_on_a_sample():
    from app.engine.rates import lean_above_fixed

    for a in IDS[::225]:
        x = get_dataset().rows_by_account[a]
        old = float((x.money_out - x.household_bills - x.insurance - x.loan_payments).quantile(0.25))
        assert lean_above_fixed(a) == old
    assert len(IDS[::225]) == 20


def test_AC17_payoff_month_equals_an_independent_date_computation():
    assert len(RUNNING) == 448
    ns = []
    for a, row in RUNNING.items():
        n = loan_end(a).payoff_month
        assert n == _payoff(row, a)
        ns.append(n)
    assert (min(ns), max(ns)) == (1, 60)
    assert [sum(n <= k for n in ns) for k in (6, 12, 24, 36)] == [60, 125, 235, 335]
    assert sum(loan_end(a).scheduled_only for a in RUNNING) == 45
    assert loan_end(48938).payoff_month == 10 and loan_end(76493).payoff_month == 5


def test_D12_the_197_recent_loans():
    assert len(RECENT_197) == 197
    ends = [loan_end(a) for a in RECENT_197]
    assert not any(e.in_typical_spending for e in ends)
    assert all(e.bump_judges == 0.0 for e in ends)
    assert all(e.bump_actual > 0 for e in ends)
    full = sum(abs(e.bump_lean - e.payment) < 0.005 for e in ends)
    zero = [a for a in RECENT_197 if loan_end(a).bump_lean == 0]
    part = 197 - full - len(zero)
    assert (full, part, len(zero)) == (166, 29, 2)
    assert sorted(zero) == [38528, 52185]
    assert sum(e.paid_rows < 12 for e in ends) == 156
    assert sum(e.paid_rows == 12 for e in ends) == 41


def test_the_other_251():
    others = [a for a in RUNNING if a in IN_TYPICAL]
    assert len(others) == 251
    ends = [loan_end(a) for a in others]
    assert all(e.in_typical_spending for e in ends)
    assert sum(e.paid_rows == 12 for e in ends) == 225
    assert sum(abs(e.bump_lean - e.payment) < 0.005 for e in ends) == 250
    assert loan_end(22609).payment - loan_end(22609).bump_lean == pytest.approx(0.13, **CENT)


def test_LE1_to_LE4_95548():
    e = loan_end(95548)
    r = saving_rates(95548)
    assert (e.payoff_month, e.paid_rows, e.in_typical_spending) == (42, 6, False)
    assert r.actual.monthly == pytest.approx(447.37, **CENT)
    assert r.actual.at(42, 42) == pytest.approx(1925.53, **CENT)
    assert r.actual.at(41, 42) == r.actual.monthly
    assert e.bump_judges == 0.0
    assert e.bump_lean == pytest.approx(2956.31, **CENT)


def test_LE1_to_LE4_60630_lean_is_capped_by_spending():
    e = loan_end(60630)
    assert e.payoff_month == 11 and e.payment == pytest.approx(2201.82, **CENT)
    assert e.bump_actual == pytest.approx(366.97, **CENT)
    assert e.bump_judges == 0.0
    assert e.bump_lean == pytest.approx(597.81, **CENT) and e.bump_lean < e.payment


def test_LE1_to_LE4_66505():
    e = loan_end(66505)
    r = saving_rates(66505)
    assert e.payoff_month == 17
    assert r.actual.monthly == pytest.approx(815.23, **CENT)
    assert r.actual.at(17, 17) == pytest.approx(2798.06, **CENT)
    assert r.judges.monthly == pytest.approx(-950.62, **CENT)
    assert r.judges.at(17, 17) == pytest.approx(1032.22, **CENT)
    assert e.bump_lean == pytest.approx(1982.83, **CENT)


def test_LE1_to_LE4_20111():
    e = loan_end(20111)
    r = saving_rates(20111)
    assert e.status == "D" and e.payoff_month == 36
    assert r.actual.at(36, 36) == pytest.approx(1193.83, **CENT)
    assert e.bump_actual == pytest.approx(1941.72, **CENT)
    assert e.bump_judges == pytest.approx(2330.06, **CENT)
    assert e.bump_lean == pytest.approx(2330.19, **CENT)
    assert r.judges.at(36, 36) == pytest.approx(69.84, **CENT)


def test_at_without_a_payoff_never_adds_the_bump():
    r = saving_rates(66505)
    assert r.actual.at(120, None) == r.actual.monthly
    assert r.actual.at(16, 17) == r.actual.monthly


def test_LE4_no_running_loan_has_no_loan_end_and_no_bump():
    quiet = [a for a in IDS if a not in RUNNING]
    assert len(quiet) == 4500 - 448
    for a in quiet[::20]:
        r = saving_rates(a)
        assert loan_end(a) is None and r.loan_end is None
        assert all(k.loan_bump == 0.0 for k in r.ordered)


def test_loan_end_is_a_frozen_loanend():
    assert isinstance(loan_end(20111), LoanEnd)
    with pytest.raises(Exception):
        loan_end(20111).payoff_month = 1


def test_ids_are_parsed():
    assert saving_rates("20,111").account_id == 20111
    assert Counter(type(saving_rates(20111)).__name__ for _ in range(2)) == {"SavingRates": 2}
