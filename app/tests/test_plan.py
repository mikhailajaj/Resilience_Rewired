import math

import pytest

from app.engine.formulas import money
from app.engine import InvalidPlanError, Shock, IncomeCut, apply_shock, get_preset, get_profile, make_plan, monthly_history
from app.tests.raw import judges


def test_no_surplus_on_20111():
    n = judges(20111)
    g = make_plan(20111).goal
    assert g.state == "no_surplus" and g.monthly_amount == 0 and g.months_to_goal is None
    assert g.target_amount == pytest.approx(3 * n["S"])
    assert g.still_needed == pytest.approx(3 * n["S"] - n["B"])
    assert g.cut_to_break_even == pytest.approx(n["S"] - n["I"])
    assert g.cut_to_reach_in_horizon == pytest.approx(n["S"] - n["I"] + (3 * n["S"] - n["B"]) / 12)
    assert g.flexible_spending == pytest.approx(n["S"] - get_profile(20111).current_fixed_costs)
    assert g.cut_is_possible


def test_target_is_an_input():
    n = judges(20111)
    assert make_plan(20111, target_months=6).goal.target_amount == pytest.approx(6 * n["S"])


def test_on_track_and_already_there():
    n = judges(20176)
    assert n["I"] > n["S"]
    target = n["B"] / n["S"] + 3
    g = make_plan(20176, target_months=target).goal
    surplus = n["I"] - n["S"]
    assert g.state == "on_track" and g.monthly_amount == pytest.approx(surplus)
    assert g.months_to_goal == math.ceil((target * n["S"] - n["B"]) / surplus)
    assert 1 <= len(g.savings_path) <= 6
    assert g.savings_path[-1].month == g.months_to_goal and g.savings_path[-1].balance >= g.target_amount - 1e-6
    half = make_plan(20176, target_months=target, surplus_share=0.5).goal
    assert half.monthly_amount == pytest.approx(surplus / 2)
    done = make_plan(20176, target_months=0.5).goal
    assert done.state == "already_there" and done.months_to_goal == 0 and done.monthly_amount == 0
    assert done.months_covered == pytest.approx(n["B"] / n["S"])


def test_s_zero_has_no_target():
    g = make_plan(21132).goal
    assert g.state == "no_regular_spending" and g.target_amount is None and g.monthly_amount == 0


def test_negative_buffer_needs_getting_above_zero_first():
    n = judges(32078)
    g = make_plan(32078).goal
    assert g.below_zero_by == pytest.approx(-n["B"])
    assert g.still_needed == pytest.approx(3 * n["S"] - n["B"])


@pytest.mark.parametrize("kw", [{"target_months": 0}, {"target_months": math.nan}, {"surplus_share": 0}, {"surplus_share": 1.5},
                                {"horizon_months": 0}, {"through_months": 0}])
def test_bad_plan_inputs(kw):
    with pytest.raises(InvalidPlanError):
        make_plan(20111, **kw)


def test_low_balance_goal_on_a_running_loan():
    p = get_profile(20111)
    low = make_plan(20111).low_balance
    assert low.payment == pytest.approx(p.P) and low.lowest_balance == pytest.approx(p.lowest_balance)
    assert low.met == (p.lowest_balance >= p.P)
    assert low.top_up_needed == pytest.approx(max(p.P - p.lowest_balance, 0))
    assert make_plan(20176).low_balance is None


def test_backup_steps_on_20111_are_computed_and_ordered():
    n = judges(20111)
    p = get_profile(20111)
    b = make_plan(20111).backup
    gap = n["S"] - 0.55 * n["I"]
    flexible = n["S"] - p.current_fixed_costs
    assert b.state == "cuts_needed" and b.through_months == 6 and b.makes_it_before is False
    assert b.runway_before.months == 3.4
    assert b.fixed_costs == pytest.approx(p.current_fixed_costs)
    assert b.flexible_spending == pytest.approx(flexible)
    assert b.fixed_share_of_spending == pytest.approx(p.current_fixed_costs / n["S"])
    assert b.cut_to_last == pytest.approx(gap - n["B"] / 6)
    assert b.cut_to_last_share_of_spending == pytest.approx((gap - n["B"] / 6) / n["S"])
    assert b.cut_to_close_gap == pytest.approx(gap)
    assert b.cut_is_possible and b.makes_it_after_steps is True

    # First step: back to the leanest quarter of the account's own months.
    x = monthly_history(20111)
    lean = (x.money_out - x.household_bills - x.insurance - x.loan_payments).quantile(0.25)
    first = b.steps[0]
    assert first.code == "lean_months"
    assert first.monthly_saving == pytest.approx(flexible - lean)
    assert first.runway_after.months == round(n["B"] / (gap - first.monthly_saving), 1)
    assert first.adds_months == pytest.approx(first.runway_after.months - first.runway_before.months)
    assert [s.order for s in b.steps] == list(range(1, len(b.steps) + 1))
    assert all(s.action for s in b.steps)


def test_steps_stop_when_enough():
    b = make_plan(20111).backup
    total = 0
    for i, s in enumerate(b.steps):
        total += s.monthly_saving
        if i < len(b.steps) - 1:
            assert total < b.cut_to_last
    assert total >= b.cut_to_last


def test_cancel_other_orders_comes_first_when_there_is_one():
    from app.engine.data import get_dataset
    for a, orders in get_dataset().orders_by_account.items():
        if orders.purpose.isna().any():
            b = make_plan(a, Shock(income_cut=IncomeCut(keep_fraction=0, months=120))).backup
            if b.flexible_spending > orders.loc[orders.purpose.isna(), "amount"].sum() and b.state in ("cuts_needed", "cuts_not_enough"):
                assert b.steps[0].code == "cancel_other_orders"
                assert b.steps[0].monthly_saving == pytest.approx(orders.loc[orders.purpose.isna(), "amount"].sum())
                return
    pytest.fail("no account to test")


def test_no_shock_and_no_cuts_states():
    assert make_plan(20111, Shock()).backup.state == "no_shock"
    b = make_plan(20176, Shock(one_off_dollars=1)).backup
    assert b.state == "no_cuts_needed" and b.steps == ()


def test_runway_zero_returns_computed_actions():
    n = judges(32078)
    r = apply_shock(32078, get_preset("job_loss_ei"))
    b = make_plan(32078).backup
    assert b.state == "no_buffer" and b.runway_before.months == 0
    assert b.cover_needed == pytest.approx(-n["B"])
    assert b.cut_to_close_gap == pytest.approx(max(r.gap, 0))
    assert b.cut_to_last is None
    assert b.steps[0].code == "cover_buffer" and b.steps[0].one_time_amount == pytest.approx(-n["B"])
    assert all(s.runway_after.months == 0 for s in b.steps)


def test_one_off_cover_on_a_saver():
    n = judges(20176)
    b = make_plan(20176, Shock(one_off_dollars=n["B"] + 500)).backup
    assert b.state == "no_buffer" and b.cover_needed == pytest.approx(500)
    assert b.months_to_cover == math.ceil(500 / (n["I"] - n["S"]))


def test_cuts_not_enough_says_so_with_a_number():
    p = get_profile(20111)
    shock = Shock(income_cut=IncomeCut(keep_fraction=0, months=120), bills_increase_pct=0)
    b = make_plan(20111, shock).backup
    gap = p.S
    assert b.state == "cuts_not_enough" and b.cut_is_possible is False
    assert b.runway_if_all_flexible_cut.months == round(min(p.B / (gap - b.flexible_spending), 120), 1)


def test_low_balance_line_in_backup():
    p = get_profile(20111)
    r = apply_shock(20111, get_preset("job_loss_ei"))
    b = make_plan(20111).backup
    assert b.months_to_low_balance_line == round((r.buffer_left - p.P) / r.gap, 1)
    assert make_plan(20176).backup.months_to_low_balance_line is None


def test_fixed_share_capped_when_fixed_exceeds_spending():
    from app.engine.data import get_dataset
    a = next(a for a in sorted(get_dataset().rows_by_account)
             if get_profile(a).S > 0 and get_profile(a).current_fixed_costs > get_profile(a).S)
    b = make_plan(a).backup
    assert b.fixed_share_of_spending == 1 and b.fixed_exceeds_spending and b.flexible_spending == 0


def _step(plan, code):
    return next((s for s in plan.backup.steps if s.code == code), None)


def test_D8_cancel_other_orders_wording_on_95548():
    plan = make_plan(95548)
    s = _step(plan, "cancel_other_orders")
    assert s is not None and s.order in (1, 2)
    assert s.action == f"Cancel the other standing orders, if these aren't rent or bills. That saves {money(s.monthly_saving)} a month."
    assert s.action.startswith("Cancel the other standing orders, if these aren't rent or bills. That saves $")
    assert not s.needs_agreement and s.one_time_amount == 0


def test_D8_all_flexible_wording():
    seen = 0
    for a in (95548, 20111, 22286, 26699, 36427):
        s = _step(make_plan(a, get_preset("job_loss_bills")), "all_flexible")
        if s is None:
            continue
        seen += 1
        assert s.action == f"Cut the remaining {money(s.monthly_saving)} a month of other spending, if it isn't rent or bills. This leaves only fixed costs."
    assert seen >= 1


def test_D8_old_wording_is_gone_on_every_account():
    for a in sorted(_all_ids())[::50]:
        for s in make_plan(a).backup.steps:
            if s.code == "cancel_other_orders":
                assert "if these aren't rent or bills" in s.action
            if s.code == "all_flexible":
                assert "if it isn't rent or bills" in s.action


def test_D7_headline_and_judges_mirror_the_flat_fields_on_every_account():
    states = set()
    for a in _all_ids():
        g = make_plan(a).goal
        h, j = g.headline, g.judges
        assert (h.rate, j.rate) == ("actual", "judges")
        assert h.monthly == g.actual_change_last_12
        assert j.monthly == g.surplus
        assert (j.state, j.monthly_amount, j.months_to_goal, j.reaches_within_horizon) == (g.state, g.monthly_amount, g.months_to_goal, g.reaches_within_horizon)
        assert (j.cut_to_break_even, j.cut_to_reach_in_horizon, j.cut_is_possible) == (g.cut_to_break_even, g.cut_to_reach_in_horizon, g.cut_is_possible)
        states.add(h.state)
        if g.state in ("no_regular_spending", "already_there"):
            assert h.state == g.state and h.monthly_amount == 0
        elif h.monthly > 0:
            assert h.state == "on_track" and h.monthly_amount == pytest.approx(h.monthly * g.surplus_share)
            assert h.months_to_goal == math.ceil(g.still_needed / h.monthly_amount) and h.cut_to_break_even is None
        else:
            assert h.state == "no_surplus" and h.monthly_amount == 0 and h.months_to_goal is None and not h.reaches_within_horizon
            assert h.cut_to_break_even == -h.monthly
            assert h.cut_to_reach_in_horizon == pytest.approx(-h.monthly + g.still_needed / 12)
            assert h.cut_is_possible == (-h.monthly <= g.flexible_spending)
    assert states >= {"on_track", "no_surplus", "already_there", "no_regular_spending"}


def test_D7_the_two_rates_can_differ_on_20111():
    g = make_plan(20111).goal
    assert g.headline.monthly == pytest.approx(-747.89, abs=0.01) and g.judges.monthly == pytest.approx(-2260.22, abs=0.01)
    assert g.headline.cut_to_break_even < g.judges.cut_to_break_even


def test_D7_headline_follows_surplus_share_and_target():
    g = make_plan(66505, target_months=0.1).goal
    assert g.headline.state == "already_there" and g.judges.state == "already_there"
    for share in (0.25, 1.0):
        h = make_plan(20176, target_months=30, surplus_share=share).goal.headline
        if h.state == "on_track":
            assert h.monthly_amount == pytest.approx(h.monthly * share)


def test_lean_cut_equals_the_lean_months_step_wherever_it_exists_except_orders_above_lean():
    from app.engine import saving_rates

    seen = 0
    for a in _all_ids():
        s = _step(make_plan(a), "lean_months")
        if s is None:
            continue
        r = saving_rates(a)
        orders = sum(o.amount for o in get_profile(a).standing_orders if o.purpose == "other")
        if orders > r.lean_above:
            assert s.monthly_saving == pytest.approx(r.flexible_spending - orders, abs=1e-6)
        else:
            assert s.monthly_saving == pytest.approx(r.lean_cut, abs=1e-6)
        seen += 1
    assert seen > 100


def _all_ids():
    from app.engine.data import get_dataset

    return sorted(get_dataset().rows_by_account)
