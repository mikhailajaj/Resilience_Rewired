"""The EI weekly maximum: beside the judges' number, never replacing it."""
import math
import statistics
from collections import Counter

import pytest

from app.engine import (EI_WEEKLY_MAX_2026, EI_WEEKLY_MAX_2026_SOURCE, WEEKS_PER_MONTH, IncomeCut, InvalidShockError, Shock, apply_shock,
                        get_preset, get_profile, make_plan, to_dict)
from app.engine.data import get_dataset
from app.tests.raw import judges, readme_runway

MONTHLY_729 = 729 * 52 / 12


def test_named_default_and_source():
    assert EI_WEEKLY_MAX_2026 == 729 and WEEKS_PER_MONTH == 52 / 12
    assert "canada.ca" in EI_WEEKLY_MAX_2026_SOURCE


def test_off_by_default_and_headline_never_changes():
    n = judges(20111)
    assert IncomeCut().ei_weekly_max is None
    off = apply_shock(20111, get_preset("job_loss_ei"))
    on = apply_shock(20111, get_preset("job_loss_ei", ei_weekly_max=729))
    expected = readme_runway(n["B"], n["S"] - 0.55 * n["I"])
    for r in (off, on):
        assert r.runway.months == expected == 3.4
        assert r.income_after == pytest.approx(0.55 * n["I"])
        assert r.verdict_case == off.verdict_case and r.duration == off.duration


def test_capped_figure_on_20111_from_the_formula():
    n = judges(20111)
    c = apply_shock(20111, get_preset("job_loss_ei", ei_weekly_max=729)).ei_capped
    assert c.available and c.switched_on and c.weekly_max_source == "supplied" and c.max_applied
    assert c.reason == "max_applied" and c.label
    assert c.weekly_max == 729 and c.monthly_max == pytest.approx(MONTHLY_729)
    assert c.income_after == pytest.approx(MONTHLY_729)
    assert c.effective_share_of_income == pytest.approx(MONTHLY_729 / n["I"])
    assert c.gap == pytest.approx(n["S"] - MONTHLY_729)
    assert c.runway.months == readme_runway(n["B"], n["S"] - MONTHLY_729)
    assert c.duration.verdict == "runs_out" and c.duration.months_asked == 6
    assert c.duration.balance_end == pytest.approx(n["B"] - 6 * (n["S"] - MONTHLY_729))


def test_capped_figure_is_there_with_the_switch_off_using_the_default():
    c = apply_shock(20111, get_preset("job_loss_ei")).ei_capped
    on = apply_shock(20111, get_preset("job_loss_ei", ei_weekly_max=EI_WEEKLY_MAX_2026)).ei_capped
    assert c.available and not c.switched_on and c.weekly_max_source == "default" and c.weekly_max == 729
    assert c.runway == on.runway and c.income_after == on.income_after and c.max_applied


def test_manual_values():
    n = judges(20111)
    low = apply_shock(20111, Shock(income_cut=IncomeCut(ei_weekly_max=500))).ei_capped
    assert low.income_after == pytest.approx(500 * 52 / 12) and low.max_applied
    zero = apply_shock(20111, Shock(income_cut=IncomeCut(ei_weekly_max=0))).ei_capped
    assert zero.income_after == 0 and zero.max_applied and zero.effective_share_of_income == 0
    assert zero.runway.months == readme_runway(n["B"], n["S"])
    high = apply_shock(20111, Shock(income_cut=IncomeCut(ei_weekly_max=100_000))).ei_capped
    assert not high.max_applied and high.reason == "max_not_reached"
    assert high.income_after == pytest.approx(0.55 * n["I"])
    assert high.effective_share_of_income == pytest.approx(0.55)
    assert high.runway == apply_shock(20111, Shock(income_cut=IncomeCut())).runway


def test_exactly_at_the_maximum_isnt_limited():
    p = get_profile(20111)
    weekly = 0.55 * p.I * 12 / 52
    c = apply_shock(20111, Shock(income_cut=IncomeCut(ei_weekly_max=weekly * 1.0001))).ei_capped
    assert not c.max_applied


@pytest.mark.parametrize("bad", [-1, -0.01, math.nan, math.inf, "729", True])
def test_bad_maximum_raises_a_typed_error(bad):
    with pytest.raises(InvalidShockError) as e:
        IncomeCut(ei_weekly_max=bad)
    assert e.value.field == "ei_weekly_max" and str(e.value)
    with pytest.raises(InvalidShockError):
        get_preset("job_loss_ei", ei_weekly_max=bad)


@pytest.mark.parametrize("shock", [None, Shock(), get_preset("furnace_repair"), Shock(income_cut=IncomeCut(keep_fraction=1, ei_weekly_max=729))])
def test_no_figure_without_an_income_cut(shock):
    r = apply_shock(20111, shock)
    c = r.ei_capped
    assert not c.available and c.reason == "no_income_cut" and c.runway is None and c.duration is None
    assert c.max_applied is False and c.income_after is None and c.effective_share_of_income is None


def test_after_the_benefit_uses_the_same_assumption():
    n = judges(20176)
    shock = get_preset("job_loss_ei", months=2, ei_weekly_max=100)
    c = apply_shock(20176, shock, through_months=10).ei_capped
    capped = 100 * 52 / 12
    assert c.duration.assumption_applied
    assert c.duration.balance_end == pytest.approx(n["B"] - 2 * (n["S"] - capped) - 8 * n["S"])


def test_zero_income_has_no_share():
    c = apply_shock(21132, get_preset("job_loss_ei", ei_weekly_max=729)).ei_capped
    assert c.available and not c.max_applied and c.effective_share_of_income is None and c.income_after == 0


def test_fact_only_when_switched_on_and_applied():
    code = "ei_weekly_max_applied"
    assert code in {f.code for f in apply_shock(20111, get_preset("job_loss_ei", ei_weekly_max=729)).facts}
    assert code not in {f.code for f in apply_shock(20111, get_preset("job_loss_ei")).facts}


def test_plan_keeps_the_judges_backup_and_adds_a_capped_one():
    n = judges(20111)
    assert make_plan(20111).backup_capped is None
    flat = make_plan(20111)
    plan = make_plan(20111, get_preset("job_loss_ei", ei_weekly_max=729))
    assert plan.backup.runway_before == flat.backup.runway_before
    assert plan.backup.cut_to_last == flat.backup.cut_to_last and plan.backup.income_basis == "flat"
    b = plan.backup_capped
    gap = n["S"] - MONTHLY_729
    assert b.income_basis == "ei_weekly_max"
    assert b.runway_before.months == readme_runway(n["B"], gap)
    assert b.cut_to_last == pytest.approx(gap - n["B"] / 6)
    assert b.cut_to_close_gap == pytest.approx(gap)
    assert b.steps[0].runway_before == b.runway_before


def test_make_plan_signature_is_stable():
    import inspect
    assert str(inspect.signature(make_plan)) == "(account_id, shock=None, *, target_months=3.0, surplus_share=1.0, horizon_months=12, through_months=None)"


def test_positional_income_cut_still_works():
    c = IncomeCut(0.55, 6, "income_returns")
    assert (c.keep_fraction, c.months, c.after_ends, c.ei_weekly_max) == (0.55, 6, "income_returns", None)


# --- Population, against docs/shock_sizing.md ---

@pytest.fixture(scope="module")
def population():
    shock = Shock(income_cut=IncomeCut(ei_weekly_max=729))
    ids = sorted(get_dataset().rows_by_account)
    return [(get_profile(a), apply_shock(a, shock)) for a in ids]


def _median(runways):
    return statistics.median(math.inf if r.months is None else r.months for r in runways)


def _under(runways, limit):
    return sum(r.months is not None and r.months < limit for r in runways) / len(runways) * 100


def test_population_with_the_maximum(population):
    limited = [(p, r) for p, r in population if r.ei_capped.max_applied]
    capped = [r.ei_capped.runway for _, r in population]
    assert len(population) == 4500
    assert len(limited) == 2574 and round(len(limited) / 45, 1) == 57.2
    assert round(_median(capped), 1) == 5.7
    assert round(_under(capped, 6), 1) == 51.2
    assert round(_under(capped, 3), 1) == 27.9
    assert not [p for p, _ in limited if p.income_type == "Pension"]
    assert round(statistics.median(r.ei_capped.effective_share_of_income for _, r in limited) * 100) == 25


def test_population_by_income_type_and_limited_median(population):
    limited = [(p, r) for p, r in population if r.ei_capped.max_applied]
    totals = Counter(p.income_type for p, _ in population)
    hit = Counter(p.income_type for p, _ in limited)
    assert round(hit["Cash only"] / totals["Cash only"] * 100, 1) == 74.1
    assert round(hit["Transfers"] / totals["Transfers"] * 100, 1) == 49.5
    assert round(_median([r.ei_capped.runway for _, r in limited]), 1) == 3.1
    assert round(_median([r.runway for _, r in limited]), 1) == 5.4


def test_judges_numbers_are_unchanged_across_the_population(population):
    flat = [r.runway for _, r in population]
    assert round(_median(flat), 1) == 8.6
    assert round(_under(flat, 6), 1) == 35.1
    assert round(_under(flat, 3), 1) == 9.7


def test_sweep_is_json_safe_with_any_maximum():
    import json
    for a in sorted(get_dataset().rows_by_account)[::9]:
        for weekly in (0, 729):
            shock = get_preset("job_loss_bills", ei_weekly_max=weekly)
            json.dumps(to_dict(apply_shock(a, shock)), allow_nan=False)
            json.dumps(to_dict(make_plan(a, shock)), allow_nan=False)
