import math

import pytest

from app.engine import IncomeCut, InvalidShockError, Shock, apply_shock, get_preset, get_profile, list_presets, spending_response
from app.tests.raw import judges, readme_runway


def expect(result, expected):
    if expected == "no shortfall":
        assert result.runway.state == "no_shortfall" and result.runway.months is None
    else:
        assert result.runway.months == expected


def test_ei_55_on_20111_from_the_formula():
    n = judges(20111)
    r = apply_shock(20111, get_preset("job_loss_ei"))
    assert r.income_after == pytest.approx(0.55 * n["I"])
    assert r.spending_after == pytest.approx(n["S"])
    assert r.gap == pytest.approx(n["S"] - 0.55 * n["I"])
    assert r.buffer_left == pytest.approx(n["B"])
    assert r.runway.months == readme_runway(n["B"], n["S"] - 0.55 * n["I"]) == 3.4


def test_furnace_on_20111_from_the_formula():
    n = judges(20111)
    r = apply_shock(20111, get_preset("furnace_repair"))
    assert r.one_off == pytest.approx(n["S"])
    assert r.buffer_left == pytest.approx(n["B"] - n["S"])
    assert r.runway.months == readme_runway(n["B"] - n["S"], n["S"] - n["I"])


@pytest.mark.parametrize("account_id", [20111, 20176, 20208, 32078, 21132])
@pytest.mark.parametrize("keep,pct,other,dollars,multiple", [
    (0.55, 0, 0, 0, 0), (0.55, 15, 0, 0, 0), (None, 15, 0, 0, 0), (None, 0, 0, 0, 1), (0.57, 10, 250, 1000, 0.5),
    (0, 50, -100, 0, 3), (None, 0, 0, 0, 0),
])
def test_any_mix_matches_the_readme(account_id, keep, pct, other, dollars, multiple):
    n = judges(account_id)
    shock = Shock(income_cut=None if keep is None else IncomeCut(keep_fraction=keep), bills_increase_pct=pct,
                  other_spending_change=other, one_off_dollars=dollars, one_off_spending_multiple=multiple)
    income = n["I"] if keep is None else keep * n["I"]
    spending = n["S"] + pct / 100 * n["H"] + other
    expect(apply_shock(account_id, shock), readme_runway(n["B"] - dollars - multiple * n["S"], spending - income))


def test_default_income_cut_is_ei():
    assert IncomeCut().keep_fraction == 0.55


def test_no_shock_equals_profile():
    for shock in (None, Shock(), get_preset("no_shock")):
        r = apply_shock(20111, shock)
        assert r.no_shock and r.verdict_case == "no_shock" and r.runway == get_profile(20111).runway and r.duration is None


def test_presets_exist():
    keys = {p.key for p in list_presets()}
    assert keys == {"job_loss_ei", "furnace_repair", "job_loss_bills", "bills_up", "no_shock"}
    s = get_preset("job_loss_bills")
    assert (s.income_cut.keep_fraction, s.income_cut.months, s.bills_increase_pct) == (0.55, 6, 15)
    assert get_preset("furnace_repair").one_off_spending_multiple == 1
    assert get_preset("job_loss_ei", keep_fraction=0.57, months=9).income_cut.keep_fraction == 0.57
    with pytest.raises(InvalidShockError):
        get_preset("nope")
    with pytest.raises(InvalidShockError):
        get_preset("job_loss_ei", size=3)


@pytest.mark.parametrize("build", [
    lambda: IncomeCut(keep_fraction=-0.1), lambda: IncomeCut(keep_fraction=1.1), lambda: IncomeCut(keep_fraction=math.nan),
    lambda: IncomeCut(keep_fraction="x"), lambda: IncomeCut(months=0), lambda: IncomeCut(months=2.5), lambda: IncomeCut(after_ends="maybe"),
    lambda: Shock(bills_increase_pct=-1), lambda: Shock(one_off_dollars=-1), lambda: Shock(one_off_spending_multiple=math.inf),
    lambda: Shock(other_spending_change=math.nan), lambda: Shock(start_month=13), lambda: Shock(income_cut=0.55),
])
def test_bad_shock_values_raise_a_typed_error(build):
    with pytest.raises(InvalidShockError) as e:
        build()
    assert e.value.field and str(e.value)


def test_bad_through_months():
    with pytest.raises(InvalidShockError):
        apply_shock(20111, None, through_months=0)


# --- Duration ---

def test_20111_ei_six_months_runs_out():
    n = judges(20111)
    gap = n["S"] - 0.55 * n["I"]
    d = apply_shock(20111, get_preset("job_loss_ei")).duration
    assert d.months_asked == 6 and d.verdict == "runs_out"
    assert d.runs_out_in_month == math.floor(n["B"] / gap) + 1 == 4
    assert d.months_short == round(6 - n["B"] / gap, 1)
    assert d.balance_end == pytest.approx(n["B"] - 6 * gap)
    assert d.shortfall_at_end == pytest.approx(6 * gap - n["B"])
    assert len(d.balance_by_month) == 7 and d.balance_by_month[0] == pytest.approx(n["B"])
    assert not d.assumption_applied and d.assumption


def test_after_the_benefit_is_assumed_to_be_no_income_and_runway_is_unchanged():
    n = judges(20176)
    shock = get_preset("job_loss_ei", months=2)
    long_ask = apply_shock(20176, shock, through_months=60)
    gap_on_ei = n["S"] - 0.55 * n["I"]
    assert long_ask.runway == apply_shock(20176, shock).runway
    assert long_ask.duration.assumption_applied and "no income" in long_ask.duration.assumption.lower()
    assert long_ask.duration.balance_end == pytest.approx(n["B"] - 2 * gap_on_ei - 58 * n["S"])
    back = apply_shock(20176, get_preset("job_loss_ei", months=2, after_ends="income_returns"), through_months=60)
    assert back.duration.balance_end == pytest.approx(n["B"] - 2 * gap_on_ei - 58 * (n["S"] - n["I"]))
    assert back.runway == long_ask.runway


def test_rounding_doesnt_flip_the_verdict():
    from app.engine.shock import duration_path
    # 5.96 months rounds to 6.0 but doesn't last 6.
    d = duration_path(596.0, 100.0, 100.0, benefit_months=6, months_asked=6, after_ends="no_income")
    assert d.verdict == "runs_out" and d.runs_out_in_month == 6
    exact = duration_path(400.0, 100.0, 100.0, benefit_months=None, months_asked=4, after_ends="no_income")
    assert exact.verdict == "makes_it" and exact.runs_out_in_month is None and exact.balance_end == 0
    next_month = duration_path(400.0, 100.0, 100.0, benefit_months=None, months_asked=5, after_ends="no_income")
    assert next_month.verdict == "runs_out" and next_month.runs_out_in_month == 5


def test_duration_on_no_buffer_and_on_surplus():
    d = apply_shock(32078, get_preset("job_loss_ei")).duration
    assert d.verdict == "runs_out" and d.runs_out_in_month == 0
    assert apply_shock(32078, get_preset("job_loss_ei")).verdict_case == "runway_zero"
    assert apply_shock(21132, Shock(), through_months=6).duration.verdict == ("makes_it" if get_profile(21132).B > 0 else "runs_out")


def test_keep_all_income_has_no_duration_question():
    r = apply_shock(20111, Shock(income_cut=IncomeCut(keep_fraction=1.0, months=6)))
    assert r.duration is None and r.no_shock


def test_any_fraction_works():
    n = judges(20111)
    r = apply_shock(20111, Shock(income_cut=IncomeCut(keep_fraction=0.57)))
    assert r.income_after == pytest.approx(0.57 * n["I"])
    assert r.verdict_case == "income_cut_open_ended" and r.duration is None


def test_start_month_never_changes_runway_and_warns_on_january():
    base = apply_shock(20111, get_preset("job_loss_ei"))
    nov = apply_shock(20111, get_preset("job_loss_ei", start_month=11))
    feb = apply_shock(20111, get_preset("job_loss_ei", start_month=2))
    assert base.runway == nov.runway == feb.runway
    assert "runs_into_january" in {f.code for f in nov.facts}
    assert "runs_into_january" not in {f.code for f in feb.facts}


# --- Extra figures ---

def test_bills_on_standing_orders_on_20176():
    n = judges(20176)
    p = get_profile(20176)
    assert p.bills_hidden
    r = apply_shock(20176, Shock(income_cut=IncomeCut(keep_fraction=0.1), bills_increase_pct=15))
    extra = r.bills_on_standing_orders
    spending = n["S"] + 0.15 * max(n["H"], p.bills_on_standing_orders)
    assert extra.applies and extra.spending_after == pytest.approx(spending)
    assert extra.runway.months == readme_runway(n["B"], spending - 0.1 * n["I"])
    assert r.runway.months == readme_runway(n["B"], n["S"] + 0.15 * n["H"] - 0.1 * n["I"])
    assert r.runway != extra.runway
    assert "bills_shock_too_small" in {f.code for f in r.facts}


@pytest.mark.parametrize("account_id,shock,reason", [
    (20176, Shock(), "no_bills_shock"),
    (20111, Shock(bills_increase_pct=15), "bills_not_missing"),
])
def test_bills_figure_when_not_applicable(account_id, shock, reason):
    e = apply_shock(account_id, shock).bills_on_standing_orders
    assert not e.applies and e.reason == reason and e.runway is None


def test_response_recomputed_from_the_data_matches_discovery():
    r = spending_response()
    assert [t.events for t in r.tiers] == [410, 219, 106]
    assert [round(t.response_per_dollar, 2) for t in r.tiers] == [0.70, 0.27, 0.0]
    assert r.tiers[2].raw_pass_through < 0
    assert r.total_events == 735


def test_if_you_adjust_on_cash_only_20111():
    n = judges(20111)
    r = apply_shock(20111, get_preset("job_loss_ei"))
    e = r.if_you_adjust
    tier = spending_response().tiers[1]   # B / S = 2.05
    spending = max(n["S"] - tier.response_per_dollar * 0.45 * n["I"], 0)
    assert e.applies and e.is_illustration and e.metadata["illustration"] is True
    assert "illustration" in e.metadata["statement"].lower()
    assert e.spending_after == pytest.approx(spending)
    assert e.runway.months == readme_runway(n["B"], spending - 0.55 * n["I"])
    assert r.runway.months == 3.4     # never replaced


def test_if_you_adjust_population_matches_the_notebook():
    """Notebook: 9.6% of cash-only accounts under 6 months, median 12.3. Where it doesn't apply, the notebook leaves spending flat."""
    cash = []
    for a in _all_ids():
        if get_profile(a).income_type == "Cash only":
            r = apply_shock(a, Shock(income_cut=IncomeCut()))
            cash.append(r.if_you_adjust.runway if r.if_you_adjust.applies else r.runway)
    assert len(cash) == 2894
    under_6 = sum(r.months is not None and r.months < 6 for r in cash)
    assert round(under_6 / 2894 * 100, 1) == 9.6
    values = sorted(math.inf if r.months is None else r.months for r in cash)
    assert round((values[1446] + values[1447]) / 2, 1) == 12.3


@pytest.mark.parametrize("account_id,reason", [(20176, "pension_income")])
def test_if_you_adjust_na_for_pension(account_id, reason):
    e = apply_shock(account_id, get_preset("job_loss_ei")).if_you_adjust
    assert not e.applies and e.reason == reason and e.runway is None and e.is_illustration


def test_if_you_adjust_na_for_transfers_and_no_income_loss():
    transfers = next(a for a in _all_ids() if get_profile(a).income_type == "Transfers")
    assert apply_shock(transfers, get_preset("job_loss_ei")).if_you_adjust.reason == "transfers_income"
    assert apply_shock(20111, get_preset("furnace_repair")).if_you_adjust.reason == "no_income_lost"


# --- Facts on awkward accounts ---

def test_pension_layoff_still_returns_the_number_and_the_fact():
    n = judges(20176)
    r = apply_shock(20176, get_preset("job_loss_ei"))
    assert "layoff_doesnt_fit_pension" in {f.code for f in r.facts}
    expect(r, readme_runway(n["B"], n["S"] - 0.55 * n["I"]))


def test_zero_activity_shocks():
    r = apply_shock(21132, get_preset("furnace_repair"))
    assert r.one_off == 0 and "one_off_zero_spending" in {f.code for f in r.facts}
    assert "income_cut_no_income" in {f.code for f in apply_shock(21132, get_preset("job_loss_ei")).facts}


def test_bills_shock_with_no_bills():
    r = apply_shock(20111, get_preset("bills_up"))
    assert r.bills_added == 0 and "bills_shock_no_bills" in {f.code for f in r.facts}


def test_one_off_larger_than_buffer():
    r = apply_shock(20111, Shock(one_off_dollars=1_000_000))
    assert r.verdict_case == "runway_zero" and r.runway.state == "no_buffer" and r.buffer_left < 0
    assert "one_off_exceeds_buffer" in {f.code for f in r.facts}


def test_spending_cannot_go_below_zero_and_runway_agrees_with_the_formula():
    r = apply_shock(20111, Shock(other_spending_change=-1_000_000))
    assert r.spending_after == 0 and r.runway.state == "no_shortfall"
    assert "spending_floored_at_zero" in {f.code for f in r.facts}


def test_stale_account_gets_a_fact():
    a = next(a for a in _all_ids() if get_profile(a).last_month != "2025-12")
    assert "data_stops_early" in {f.code for f in apply_shock(a, get_preset("job_loss_ei")).facts}


def _all_ids():
    from app.engine.data import get_dataset
    return sorted(get_dataset().rows_by_account)


# --- Confirmed for the shock-sizing work ---

def test_one_off_dollars_add_to_the_spending_multiple():
    n = judges(20111)
    r = apply_shock(20111, Shock(one_off_dollars=3500, one_off_spending_multiple=0.5))
    assert r.one_off == pytest.approx(3500 + 0.5 * n["S"])
    assert r.buffer_left == pytest.approx(n["B"] - 3500 - 0.5 * n["S"])
    assert r.runway.months == readme_runway(n["B"] - 3500 - 0.5 * n["S"], n["S"] - n["I"])
    assert apply_shock(20111, Shock(one_off_dollars=3500)).one_off == 3500


@pytest.mark.parametrize("month", range(1, 13))
def test_any_start_month_leaves_the_judges_number_alone(month):
    base = apply_shock(20111, get_preset("job_loss_bills"))
    r = apply_shock(20111, get_preset("job_loss_bills", start_month=month))
    assert r.runway == base.runway and r.duration == base.duration and r.ei_capped.runway == base.ei_capped.runway


def test_start_month_default_is_off():
    assert Shock().start_month is None
    assert "runs_into_january" not in {f.code for f in apply_shock(20111, get_preset("job_loss_ei")).facts}


# --- Conflicts in docs/inception/scope.md, as the contract resolves them ---

def test_con7_no_shortfall_can_still_run_out_past_the_benefit():
    r = apply_shock(20176, get_preset("job_loss_ei", months=2, keep_fraction=0.9), through_months=120)
    assert r.verdict_case == "no_shortfall" and r.runway.state == "no_shortfall"
    assert r.duration.verdict == "runs_out" and r.duration.assumption_applied


def test_con8_capped_runway_isnt_no_shortfall():
    r = apply_shock(20134, Shock()).runway
    assert r.state == "months" and r.months == 120.0 and r.label == "120.0 months"


def test_con3_na_reasons_on_the_furnace_twist():
    r = apply_shock(20134, get_preset("furnace_repair")).if_you_adjust
    assert not r.applies and r.reason in ("pension_income", "transfers_income", "no_income_lost", "no_typical_spending")


def test_con10_engine_values_for_20111():
    p, r = get_profile(20111), apply_shock(20111, get_preset("job_loss_ei"))
    assert p.first_month == "2022-11" and r.runway.months == 3.4 and p.bills_on_standing_orders == 0
