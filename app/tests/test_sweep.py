"""Every account, every preset: nothing crashes, and every number follows the rules."""
import json
import math
from collections import Counter

import pytest

from app.engine import IncomeCut, Shock, get_preset, get_profile, list_presets, make_plan, apply_shock, note_catalogue, to_dict
from app.engine.data import get_dataset

IDS = sorted(get_dataset().rows_by_account)
PRESETS = [p.key for p in list_presets()]

EXPECTED_WARNINGS = {
    "Little activity": 10, "Irregular income": 4, "Irregular spending": 67, "Out of date": 76, "No buffer": 23,
    "Pension income": 740, "Cash income": 2894, "High flow": 1402, "Bills missing from H": 293,
    "No regular bills visible": 1063, "Recent loan missed by F": 197, "Finished loan still counted": 79,
    "Loan in trouble": 76, "Missed payment": 12, "Went negative": 105, "Thin low point": 23, "Leasing not counted": 341,
}


def test_there_are_4500_accounts():
    assert len(IDS) == 4500


def test_warning_counts_match_the_doc():
    counts = Counter()
    clean = 0
    for a in IDS:
        titles = [w.title for w in get_profile(a).warnings]
        counts.update(titles)
        clean += not titles
    assert dict(counts) == EXPECTED_WARNINGS
    assert clean == 324
    assert {n.title for n in note_catalogue()} == set(EXPECTED_WARNINGS)


def test_no_shock_population_matches_the_notebook():
    runways = [get_profile(a).runway for a in IDS]
    assert sum(r.state == "no_shortfall" for r in runways) == 3315
    assert sum(r.months == 0 for r in runways) == 24
    assert sum(r.state == "no_buffer" for r in runways) == 23
    assert sum(r.months is not None and r.months < 6 for r in runways) == 120


@pytest.mark.parametrize("key,share", [("no_shock", 3), ("furnace_repair", 9), ("job_loss_ei", 35), ("job_loss_bills", 39)])
def test_share_under_six_months_matches_discovery(key, share):
    shock = get_preset(key)
    under = sum((lambda r: r.months is not None and r.months < 6)(apply_shock(a, shock).runway) for a in IDS)
    assert round(under / 45) == share


def _check_runway(r):
    assert r.state in ("no_buffer", "no_shortfall", "months")
    if r.state == "no_buffer":
        assert r.months == 0
    elif r.state == "no_shortfall":
        assert r.months is None
    else:
        assert 0 <= r.months <= 120


@pytest.mark.parametrize("key", PRESETS)
def test_sweep(key):
    shock = get_preset(key)
    verdicts = Counter()
    for a in IDS:
        p = get_profile(a)
        r = apply_shock(a, shock)
        plan = make_plan(a, shock)
        json.dumps(to_dict(r), allow_nan=False)
        json.dumps(to_dict(plan), allow_nan=False)
        verdicts[r.verdict_case] += 1

        # README rule, restated.
        _check_runway(r.runway)
        if r.buffer_left <= 0:
            assert r.runway.state == "no_buffer"
        elif r.gap <= 0:
            assert r.runway.state == "no_shortfall"
        else:
            assert r.runway.months == round(min(r.buffer_left / r.gap, 120), 1)

        # The extra figures never replace the standard (judges') number.
        assert r.runway == r.after.runway
        for e in (r.bills_on_standing_orders, r.if_you_adjust):
            assert e.label and e.reason and e.note
            assert (e.runway is not None) == e.applies
        assert not r.if_you_adjust.applies or p.income_type == "Cash only"
        assert r.if_you_adjust.is_illustration
        assert not r.bills_on_standing_orders.applies or p.bills_hidden

        # The verdict agrees with the unrounded formula within the lower income's length.
        d = r.duration
        if d is not None:
            assert (d.verdict == "makes_it") == (r.buffer_left > 0 and (r.gap <= 0 or r.buffer_left / r.gap >= d.months_asked))
            assert (d.runs_out_in_month is None) == (d.verdict == "makes_it")

        # CON-5: a runway of 0 always says whose fault it is, exactly once.
        if r.verdict_case == "runway_zero":
            assert len({f.code for f in r.facts} & {"no_buffer_before_shock", "one_off_exceeds_buffer"}) == 1

        if p.income_type == "Pension" and shock.income_cut:
            assert "layoff_doesnt_fit_pension" in {f.code for f in r.facts}

        # Plan.
        g, b = plan.goal, plan.backup
        assert g.state in ("already_there", "on_track", "no_surplus", "no_regular_spending")
        assert (g.state == "no_regular_spending") == (p.S == 0)
        assert g.monthly_amount >= 0
        assert g.state != "on_track" or (g.months_to_goal >= 1 and g.monthly_amount > 0)
        assert b.flexible_spending >= 0 and b.fixed_costs >= 0
        assert (plan.low_balance is not None) == p.running_loan
        if b.state == "no_buffer":
            assert b.cover_needed == pytest.approx(max(-r.buffer_left, 0))
            assert b.steps and b.steps[0].code == "cover_buffer"
        if key == "no_shock":
            assert b.state == "no_shock" and not b.steps
        before = None
        for s in b.steps:
            assert s.action and s.monthly_saving >= 0
            assert s.runway_before == (before or b.runway_before)
            before = s.runway_after
            _check_runway(s.runway_after)
        assert before is None or before == b.runway_after_steps
    assert sum(verdicts.values()) == 4500


def test_sweep_with_a_harsh_mix_and_a_start_month():
    """Beyond the presets: no income, bills up, spending change, a large cost, and a January start."""
    shock = Shock(income_cut=IncomeCut(keep_fraction=0, months=24, after_ends="income_returns"), bills_increase_pct=50,
                  other_spending_change=-500, one_off_dollars=5000, one_off_spending_multiple=3, start_month=1)
    for a in IDS:
        r = apply_shock(a, shock, through_months=36)
        json.dumps(to_dict(r), allow_nan=False)
        json.dumps(to_dict(make_plan(a, shock, target_months=6, through_months=36)), allow_nan=False)
        assert "runs_into_january" in {f.code for f in r.facts}
        _check_runway(r.runway)


def test_shock_on_the_awkward_groups_is_deliberate():
    assert all(apply_shock(a, get_preset("job_loss_ei")).runway.months == 0 for a in IDS if get_profile(a).B <= 0)
    assert all(make_plan(a).goal.state == "no_regular_spending" for a in IDS if get_profile(a).S == 0)


def test_no_nan_in_any_figure():
    for a in IDS[::50]:
        for value in _numbers(to_dict(apply_shock(a, get_preset("job_loss_bills")))):
            assert math.isfinite(value)


def _numbers(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from _numbers(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _numbers(v)
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield node
