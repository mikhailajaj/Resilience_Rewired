"""The running loan's end inside the backup plan's check (RU-28, AC-18, LE-5, LE-6, ADR 0006).

The AC-18 snapshots were computed on the engine at HEAD (before J5) and equal the current engine.
"""
import csv
from collections import Counter
from functools import lru_cache

import pytest

from app.engine import apply_shock, get_preset, get_profile, list_presets, loan_end, make_plan
from app.engine.data import get_dataset
from app.engine.rates import duration_with_loan_end
from app.engine.shock import duration_path, shock_gaps
from app.tests.raw import DATA

IDS = sorted(get_dataset().rows_by_account)
PRESETS = list_presets()
PRESET_KEYS = [p.key for p in PRESETS]


def _through(preset):
    cut = preset.shock.income_cut
    return cut.months if cut is not None else None


@lru_cache(maxsize=None)
def _plans(key):
    preset = next(p for p in PRESETS if p.key == key)
    tm = _through(preset)
    return tuple((a, make_plan(a, preset.shock, through_months=tm)) for a in IDS)


def _running():
    with open(DATA / "loans.csv", newline="") as f:
        return sorted(int(r["account_id"]) for r in csv.DictReader(f) if r["status"] in ("C", "D"))


RUNNING = _running()
RECENT_197 = [a for a in RUNNING if get_profile(a).loan_median == 0]

SNAPSHOT = {
    "job_loss_ei": ({"income_cut_makes_it": 2670, "income_cut_runs_out": 1573, "no_shortfall": 234, "runway_zero": 23},
                    {"cuts_needed": 1526, "cuts_not_enough": 47, "no_buffer": 23, "no_cuts_needed": 2904}),
    "furnace_repair": ({"cost_or_bills_only": 1066, "no_shortfall": 3253, "runway_zero": 181},
                       {"cuts_needed": 1066, "no_buffer": 181, "no_cuts_needed": 3253}),
    "job_loss_bills": ({"income_cut_makes_it": 2564, "income_cut_runs_out": 1729, "no_shortfall": 184, "runway_zero": 23},
                       {"cuts_needed": 1665, "cuts_not_enough": 64, "no_buffer": 23, "no_cuts_needed": 2748}),
    "bills_up": ({"cost_or_bills_only": 1623, "no_shortfall": 2854, "runway_zero": 23},
                 {"cuts_needed": 1623, "no_buffer": 23, "no_cuts_needed": 2854}),
    "no_shock": ({"no_shock": 4500}, {"no_shock": 4500}),
}


def _inputs(a, shock, through):
    p = get_profile(a)
    r = apply_shock(a, shock, through_months=through)
    if r.duration is None:
        return None
    during, after, benefit = shock_gaps(p, shock, r.spending_after, r.income_after)
    d = r.duration
    return r.buffer_left, during, after, benefit, d.months_asked, d.after_ends or "no_income"


def test_the_hand_worked_example():
    got = duration_with_loan_end(1000, 400, 400, None, 6, "no_income", payoff_month=2, monthly_drop=300)
    assert got.balance_by_month == (1000.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0)
    assert got.verdict == "makes_it" and got.runs_out_in_month is None and got.months_short is None
    assert got.lowest_balance == 100.0 and got.balance_end == 100.0
    plain = duration_path(1000, 400, 400, None, 6, "no_income")
    assert plain.verdict == "runs_out" and plain.runs_out_in_month == 3 and plain.months_short == 3.5


def test_a_drop_too_small_still_runs_out_and_the_balance_is_never_invented():
    got = duration_with_loan_end(1000, 400, 400, None, 6, "no_income", payoff_month=4, monthly_drop=100)
    assert got.balance_by_month == (1000.0, 600.0, 200.0, -200.0, -500.0, -800.0, -1100.0)
    assert got.verdict == "runs_out" and got.runs_out_in_month == 3
    assert got.months_short == pytest.approx(3.5)


def test_no_buffer_stays_no_buffer_whatever_the_drop():
    got = duration_with_loan_end(0, 400, 400, None, 6, "no_income", payoff_month=1, monthly_drop=900)
    assert got.verdict == "runs_out" and got.runs_out_in_month == 0 and got.money_lasts_months == 0.0


@pytest.mark.parametrize("key", PRESET_KEYS)
def test_delegation_equals_duration_path_on_every_account(key):
    preset = next(p for p in PRESETS if p.key == key)
    tm = _through(preset)
    checked = 0
    for a in IDS:
        args = _inputs(a, preset.shock, tm)
        if args is None:
            continue
        months = args[4]
        base = duration_path(*args)
        assert duration_with_loan_end(*args, payoff_month=3, monthly_drop=0.0) == base
        assert duration_with_loan_end(*args, payoff_month=None, monthly_drop=250.0) == base
        assert duration_with_loan_end(*args, payoff_month=months + 1, monthly_drop=250.0) == base
        assert duration_with_loan_end(*args, payoff_month=1, monthly_drop=-5.0) == base
        checked += 1
    assert (checked > 0) == key.startswith("job_loss")


def test_a_drop_from_a_payoff_inside_the_months_changes_the_path():
    args = (1000.0, 400.0, 400.0, None, 6, "no_income")
    assert duration_with_loan_end(*args, payoff_month=6, monthly_drop=50.0) != duration_path(*args)
    assert duration_with_loan_end(*args, payoff_month=6, monthly_drop=50.0).balance_end == pytest.approx(duration_path(*args).balance_end + 50)


@pytest.mark.parametrize("key,counts", [(k, v) for k, v in SNAPSHOT.items()])
def test_AC18_verdict_and_backup_state_snapshots_equal_the_unchanged_engine(key, counts):
    preset = next(p for p in PRESETS if p.key == key)
    tm = _through(preset)
    verdicts = Counter(apply_shock(a, preset.shock, through_months=tm).verdict_case for a in IDS)
    states = Counter(plan.backup.state for _, plan in _plans(key))
    assert dict(verdicts) == counts[0]
    assert dict(states) == counts[1]
    assert sum(verdicts.values()) == sum(states.values()) == 4500


def test_AC18_D13_split_on_job_loss_ei_through_6():
    split = Counter()
    for _, plan in _plans("job_loss_ei"):
        b = plan.backup
        if b.makes_it_before is False:
            split[b.makes_it_after_steps, any(s.code == "ask_lender" for s in b.steps)] += 1
    assert sum(split.values()) == 1596
    assert split[True, False] == 1526
    assert split[True, True] == 22
    assert split[True, False] + split[True, True] == 1548
    assert (split[False, False], split[False, True]) == (42, 6)


def test_the_loan_end_check_is_absent_without_a_running_loan():
    for a, plan in _plans("job_loss_ei"):
        assert (plan.backup.loan_end is None) == (loan_end(a) is None)


def test_reason_not_in_spending_on_all_197():
    assert len(RECENT_197) == 197
    for a in RECENT_197:
        check = make_plan(a, get_preset("job_loss_ei"), through_months=6).backup.loan_end
        assert check.reason == "not_in_spending"
        assert check.before is None and check.after_steps is None
        assert check.makes_it_before is None and check.makes_it_after_steps is None
        assert check.monthly_drop == 0.0


def _first(pred):
    return next(a for a, plan in _plans("job_loss_ei") if plan.backup.loan_end is not None and pred(plan.backup.loan_end))


def test_reason_per_case():
    reasons = Counter(plan.backup.loan_end.reason for _, plan in _plans("job_loss_ei") if plan.backup.loan_end)
    assert set(reasons) == {"applies", "after_months", "not_in_spending"}
    assert reasons["not_in_spending"] == 197 and sum(reasons.values()) == 448
    assert reasons["applies"] == 42
    for a, plan in _plans("job_loss_ei"):
        c = plan.backup.loan_end
        if c is None:
            continue
        e = loan_end(a)
        assert (c.payoff_month, c.scheduled_only) == (e.payoff_month, e.scheduled_only)
        if c.reason == "applies":
            assert e.in_typical_spending and e.payoff_month <= 6 and c.monthly_drop == e.bump_judges > 0
        elif c.reason == "after_months":
            assert e.in_typical_spending and e.payoff_month > 6
            assert c.before is None and c.after_steps is None
    a = _first(lambda c: c.reason == "after_months")
    assert make_plan(a, get_preset("job_loss_ei"), through_months=6).backup.loan_end.reason == "after_months"


def test_reason_no_shock_and_no_length():
    a = next(a for a in RUNNING if get_profile(a).loan_median > 0)
    assert make_plan(a, get_preset("no_shock")).backup.loan_end.reason == "no_shock"
    assert make_plan(a, get_preset("furnace_repair")).backup.loan_end.reason == "no_length"
    open_ended = get_preset("job_loss_ei", months=None)
    assert make_plan(a, open_ended).backup.loan_end.reason == "no_length"


def test_the_check_equals_duration_with_loan_end_on_the_plans_own_numbers():
    shock = get_preset("job_loss_ei")
    seen = 0
    for a, plan in _plans("job_loss_ei"):
        c = plan.backup.loan_end
        if c is None or c.reason != "applies":
            continue
        seen += 1
        p = get_profile(a)
        r = apply_shock(a, shock, through_months=6)
        during, after, benefit = shock_gaps(p, shock, r.spending_after, r.income_after)
        steps = plan.backup.steps
        saved = sum(s.monthly_saving for s in steps)
        left_after = r.buffer_left + sum(s.one_time_amount for s in steps)
        ends = r.duration.after_ends or "no_income"
        e = loan_end(a)
        assert c.before == duration_with_loan_end(r.buffer_left, during, after, benefit, 6, ends, payoff_month=e.payoff_month, monthly_drop=e.bump_judges)
        paused = any(s.code == "ask_lender" for s in steps)
        drop = 0.0 if paused else e.bump_judges
        assert c.after_steps == duration_with_loan_end(left_after, during - saved, after - saved, benefit, 6, ends, payoff_month=e.payoff_month, monthly_drop=drop)
        if paused:
            assert c.after_steps == duration_path(left_after, during - saved, after - saved, benefit, 6, ends)
        assert c.makes_it_before == (c.before.verdict == "makes_it")
        assert c.makes_it_after_steps == (c.after_steps.verdict == "makes_it")
    assert seen == 42


def test_makes_it_after_steps_is_unchanged_where_the_loan_end_applies():
    # HEAD (before J5) gives True for all 42 of these accounts; the backup's own verdict must not move.
    for a, plan in _plans("job_loss_ei"):
        c = plan.backup.loan_end
        if c is not None and c.reason == "applies":
            assert plan.backup.makes_it_after_steps is True


def test_RU28_loan_ends_within_the_six_months():
    ran_out = [plan for a, plan in _plans("job_loss_ei")
               if loan_end(a) is not None and loan_end(a).payoff_month <= 6 and plan.backup.makes_it_before is False]
    assert len(ran_out) == 44
    counted = [p for p in ran_out if p.backup.loan_end.makes_it_before]
    assert len(counted) == 6     # the inception script's 6
    in_spending = [p for p in ran_out if p.backup.loan_end.reason == "applies"]
    assert len(in_spending) == 32
    assert all(p.backup.loan_end.reason in ("applies", "not_in_spending") for p in ran_out)
