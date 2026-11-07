import math

import pytest

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
