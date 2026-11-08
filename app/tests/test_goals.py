"""The plan designer engine (AC-11 to AC-16, RU-24 to RU-26, RU-29, RU-30, OI-17 to OI-19, WL-1 to WL-9) on real account IDs."""
import dataclasses
import math

import pytest

from app.engine import (EmergencyCost, IncomeCut, InvalidPlanError, PlanRequest, SavingsGoal, Shock, TimeOff, apply_shock, design_plan,
                        get_profile, make_plan, saving_rates, wallets_at)
from app.engine import goals
from app.engine.goals import MARKER_CODES, MAX_INTEREST_PCT
from app.engine.rates import RATE_KEYS, duration_with_loan_end

CAR = SavingsGoal("car", 60000)
CENT = 0.01


def design(account, *items, emergency=None, **kw):
    return design_plan(account, PlanRequest(tuple(items), emergency, **kw))


def month_of(d, code, rate, item=None):
    found = [e.month for e in d.timeline.events if e.code == code and e.rate == rate and e.item == item]
    return found[0] if found else None


def reach(d, rate, goal=0):
    return d.goals[goal].reach[RATE_KEYS.index(rate)]


# AC-11
def test_ac11_car_on_20111_at_the_three_rates():
    d = design(20111, CAR)
    a, j, lean = (reach(d, k) for k in RATE_KEYS)
    assert lean.state == lean.state_no_loan == "reached"
    assert (lean.month_no_loan, lean.month) == (113, 52)
    assert (j.state_no_loan, j.state) == ("never", "over_cap")
    assert (a.state_no_loan, a.state, a.month) == ("never", "reached", 115)
    assert a.cut_to_start == pytest.approx(747.89, abs=CENT)
    assert lean.cut_to_start is None and lean.cut_to_reach_by_cap is None
    assert d.goals[0].state == "planned" and d.goals[0].deadline is None


def test_ac11_the_rates_are_the_engines_three():
    d = design(20111, CAR)
    assert d.rates == saving_rates(20111)
    assert [r.key for r in d.rates.ordered] == list(RATE_KEYS)


# AC-12, WL-7, WL-8
def test_ac12_deadline_24_on_20111_has_one_cut():
    ans = design(20111, SavingsGoal("car", 60000, 24)).goals[0].deadline
    assert ans.need == pytest.approx(68187, abs=1) and ans.need == pytest.approx(25798.815 + 60000 - get_profile(20111).B, abs=CENT)
    assert ans.monthly_needed == pytest.approx(2841.12, abs=CENT)
    assert ans.cut_needed == pytest.approx(3589.01, abs=CENT)
    assert ans.cut_share_of_flexible == pytest.approx(0.57, abs=0.005)
    assert ans.flexible_spending == pytest.approx(6269, abs=1) and ans.lean_cut == pytest.approx(2864, abs=1)
    assert not ans.within_lean and not ans.over_flexible and not ans.on_pace and ans.includes_fund
    assert (ans.counts_loan_end, ans.payoff_month, ans.cut_with_loan, ans.on_pace_with_loan) == (False, None, None, None)


def test_wl8_deadline_48_on_20111_shows_both_cuts():
    ans = design(20111, SavingsGoal("car", 60000, 48)).goals[0].deadline
    assert ans.monthly_needed == pytest.approx(1420.56, abs=CENT)
    assert ans.cut_needed == pytest.approx(2168.45, abs=CENT)
    assert ans.cut_with_loan == pytest.approx(1642.57, abs=CENT)
    assert ans.counts_loan_end and ans.payoff_month == 36 and ans.on_pace_with_loan is False
    assert ans.within_lean


def test_wl8_66505_car_deadline_36():
    d = design(66505, SavingsGoal("car", 60000, 36))
    ans = d.goals[0].deadline
    assert ans.need == pytest.approx(93200, abs=1)
    assert ans.monthly_needed == pytest.approx(2588.89, abs=CENT)
    assert ans.cut_needed == pytest.approx(1773.66, abs=CENT)
    assert ans.cut_with_loan == pytest.approx(672.08, abs=CENT)
    actual = reach(d, "actual")
    assert (actual.month, actual.month_no_loan) == (45, 115)
    fund = get_profile(66505).S * 3
    assert month_of(d, "fund_reached", "actual") == 24
    b = get_profile(66505).B
    assert math.ceil((fund - b) / saving_rates(66505).actual.monthly) == 41


def test_wl8_account_with_no_running_loan_has_no_second_cut():
    ans = design(20133, SavingsGoal("car", 60000, 36)).goals[0].deadline
    assert get_profile(20133).running_loan is False
    assert ans.cut_with_loan is None and not ans.counts_loan_end and ans.payoff_month is None


def test_wl8_on_pace_with_loan_is_the_second_cut_being_zero():
    ans = design(66505, SavingsGoal("tv", 100, 36)).goals[0].deadline
    assert ans.cut_with_loan == 0.0 and ans.on_pace_with_loan is True
    assert ans.cut_needed > 0 and not ans.on_pace


def test_wl8_with_interest_the_loan_cut_is_the_smallest_to_the_cent():
    d = design(66505, SavingsGoal("car", 60000, 36), interest_pct=6.0)
    ans = d.goals[0].deadline
    assert ans.counts_loan_end and ans.cut_with_loan < 672.08
    rate, p = saving_rates(66505).actual, get_profile(66505)
    target = 3 * p.S + 60000

    def final_balance(cut):
        bal = p.B
        for t in range(1, 37):
            bal += (bal * 0.005 if bal > 0 else 0.0) + rate.at(t, 17) + cut
        return bal

    assert final_balance(ans.cut_with_loan) >= target - 1e-6
    assert final_balance(ans.cut_with_loan - 0.01) < target
    assert d.goals[0].deadline.monthly_needed < 2588.89


# AC-13
def test_ac13_24_months_off_on_20111():
    d = design(20111, TimeOff(24))
    t = d.time_off
    assert t.amount == pytest.approx(206391, abs=1) and t.lean_amount == pytest.approx(137643, abs=1)
    shock = apply_shock(20111, Shock(IncomeCut(0, 24)), through_months=24).duration
    for check in t.checks[:2]:
        assert check.started_now and check.start_month == 0 and check.start_balance == get_profile(20111).B
        assert check.duration == shock and not check.counts_loan_end
    assert shock.runs_out_in_month == 3
    assert [r.state for r in t.reach[:2]] == ["over_cap", "over_cap"]
    lean = t.checks[2]
    assert t.reach[2].state == "reached" and not lean.started_now and lean.start_month == t.reach[2].month > 0


def test_oi17_a_saved_time_off_is_checked_from_its_start_month():
    d = design(66505, TimeOff(3))
    check = d.time_off.checks[0]
    assert not check.started_now and check.start_month == d.time_off.reach[0].month > 0
    assert check.start_balance == pytest.approx(d.timeline.lines[0].balance[check.start_month], abs=CENT)
    assert month_of(d, "time_off_start", "actual") == check.start_month
    assert month_of(d, "time_off_end", "actual") == check.start_month + 3


def test_ri_a_loan_ending_inside_the_time_off_lifts_the_check():
    d = design(20111, TimeOff(48))
    p, loan = get_profile(20111), saving_rates(20111).loan_end
    plain = apply_shock(20111, Shock(IncomeCut(0, 48)), through_months=48).duration
    for check in d.time_off.checks[:2]:
        assert check.started_now and check.counts_loan_end
        expected = duration_with_loan_end(check.start_balance, p.S, p.S, 48, 48, "no_income",
                                          payoff_month=loan.payoff_month, monthly_drop=loan.bump_judges)
        assert check.duration == expected
        assert check.duration.balance_end == pytest.approx(plain.balance_end + loan.bump_judges * (48 - loan.payoff_month + 1), abs=CENT)


def test_ri_a_check_started_later_shifts_the_payoff_month():
    d = design(66505, TimeOff(3))
    check = d.time_off.checks[0]
    p, loan = get_profile(66505), saving_rates(66505).loan_end
    start = check.start_month
    assert not check.started_now and start > 0
    expected = duration_with_loan_end(check.start_balance, p.S, p.S, 3, 3, "no_income",
                                      payoff_month=max(loan.payoff_month - start, 1), monthly_drop=loan.bump_judges)
    assert check.duration == expected
    assert check.counts_loan_end == (start < loan.payoff_month <= start + 3) and not check.counts_loan_end


# AC-14, WL-9
def test_ac14_emergency_covered_on_20111():
    e = design(20111, emergency=EmergencyCost(10000)).emergency
    assert e.buffer_left == pytest.approx(7612, abs=1) and e.covered and e.backup is None
    assert e.buffer_left == apply_shock(20111, Shock(one_off_dollars=10000)).buffer_left
    assert e.buffer_before == get_profile(20111).B


def test_ac14_emergency_not_covered_on_32078_uses_the_backup_plan():
    d = design(32078, emergency=EmergencyCost(10000))
    e = d.emergency
    assert e.buffer_left == pytest.approx(-12513, abs=1) and not e.covered
    assert e.buffer_left == apply_shock(32078, Shock(one_off_dollars=10000)).buffer_left
    assert e.backup == make_plan(32078, Shock(one_off_dollars=10000)).backup
    assert e.backup.steps[0].code == "cover_buffer"
    assert e.lean_budget == pytest.approx(1346, abs=1)
    assert e.lean_fixed + e.lean_other == pytest.approx(e.lean_budget, abs=CENT)
    assert e.lean_fixed == min(saving_rates(32078).fixed_costs, e.lean_budget)
    assert d.timeline.lines[0].balance[0] == pytest.approx(get_profile(32078).B - 10000, abs=CENT)


def test_emergency_rebuild_has_a_reach_on_each_line():
    e = design(32078, emergency=EmergencyCost(10000)).emergency
    assert [r.rate for r in e.rebuild] == list(RATE_KEYS)
    assert all(r.to_buffer.state in ("reached", "now", "over_cap", "never") for r in e.rebuild)
    z = design(20578, emergency=EmergencyCost(500)).emergency
    assert all(r.to_fund is None for r in z.rebuild)


def test_wl9_emergency_split_66505_comes_out_of_the_fund():
    e = design(66505, emergency=EmergencyCost(10000)).emergency
    assert e.from_wallet == 0 and e.from_fund == 10000


def test_wl9_emergency_split_with_money_above_the_fund_comes_out_of_the_wallet():
    p = get_profile(20176)
    assert p.B > 3 * p.S + 10000
    e = design(20176, emergency=EmergencyCost(10000)).emergency
    assert e.from_wallet == 10000 and e.from_fund == 0


def test_wl9_emergency_split_partly_from_each():
    p = get_profile(20176)
    cost = p.B - 3 * p.S + 1000
    e = design(20176, emergency=EmergencyCost(cost)).emergency
    assert e.from_wallet == pytest.approx(p.B - 3 * p.S, abs=CENT) and e.from_fund == pytest.approx(1000, abs=CENT)


def test_emergency_of_zero_leaves_the_buffer_and_adds_no_marker():
    d = design(20111, emergency=EmergencyCost(0))
    assert d.emergency.buffer_left == get_profile(20111).B and d.emergency.covered
    assert all(e.code != "emergency_cost" for e in d.timeline.events)


# AC-15
@pytest.mark.parametrize("account", [20111, 66505, 32078, 20578, 95548])
def test_ac15_timeline_shape(account):
    p = get_profile(account)
    d = design(account, SavingsGoal("car", 60000, 24), TimeOff(6), emergency=EmergencyCost(10000))
    t = d.timeline
    assert t.start == p.B and len(t.lines) == 3 and [ln.rate for ln in t.lines] == list(RATE_KEYS)
    assert 12 <= t.horizon <= 120
    for line in t.lines:
        assert len(line.balance) == t.horizon + 1
        assert line.balance[0] == pytest.approx(p.B - 10000, abs=CENT)
        assert all(math.isfinite(x) for x in line.balance)
    order = {k: n for n, k in enumerate(RATE_KEYS)}
    keys = [(e.month, order.get(e.rate, -1), MARKER_CODES.index(e.code)) for e in t.events]
    assert keys == sorted(keys)
    assert all(e.month <= t.horizon and e.code in MARKER_CODES for e in t.events)
    assert all(e.month is None for e in t.after_cap)
    assert sum(e.code == "emergency_cost" for e in t.events) == 1


def test_loan_paid_off_marker_and_horizon():
    d = design(20111, CAR)
    marks = [e for e in d.timeline.events if e.code == "loan_paid_off"]
    assert [(m.month, m.rate, m.item) for m in marks] == [(36, None, None)]
    assert d.timeline.horizon == 120 and d.timeline.after_cap
    assert not design(20133, SavingsGoal("tv", 1)).timeline.after_cap
    assert not any(e.code == "loan_paid_off" for e in design(20133).timeline.events)


def test_ru26_horizon_follows_the_events_and_the_deadline():
    d = design(66505, SavingsGoal("tv", 100, 90))
    last = max(e.month for e in d.timeline.events)
    assert d.timeline.after_cap == () and d.timeline.horizon == max(90, last)
    assert design(20578, SavingsGoal("tv", 1, 5)).timeline.horizon == 12
    assert design(20578, SavingsGoal("tv", 1, 40)).timeline.horizon == 40


def test_after_cap_lists_items_not_reached_by_month_120():
    d = design(20111, CAR)
    cap = {(e.rate, e.code, e.item) for e in d.timeline.after_cap}
    assert ("judges", "goal_reached", "car") in cap and ("judges", "goal_bought", "car") in cap
    assert ("actual", "goal_reached", "car") not in cap
    assert ("judges", "fund_reached", None) in cap


# RU-24
def test_ru24_two_goals_are_bought_in_tick_order():
    d = design(66505, SavingsGoal("boat", 20000), SavingsGoal("car", 10000))
    boat, car = month_of(d, "goal_bought", "actual", "boat"), month_of(d, "goal_bought", "actual", "car")
    fund = month_of(d, "fund_reached", "actual")
    assert fund < boat < car
    swapped = design(66505, SavingsGoal("car", 10000), SavingsGoal("boat", 20000))
    assert month_of(swapped, "goal_bought", "actual", "car") < month_of(swapped, "goal_bought", "actual", "boat")
    assert [g.position for g in d.goals] == [1, 2] and d.goals[0].fund_needed > 0 and d.goals[1].fund_needed == 0


def test_ru24_a_goal_is_never_bought_below_the_fund():
    for account in (66505, 20111, 20176):
        d = design(account, SavingsGoal("a", 15000), SavingsGoal("b", 15000), TimeOff(2))
        fund = d.fund_target
        for line in d.timeline.lines:
            for e in d.timeline.events:
                if e.code == "goal_bought" and e.rate == line.rate:
                    assert line.balance[e.month] >= fund - 1e-6


def test_ru24_the_time_off_waits_for_the_fund():
    d = design(66505, TimeOff(2))
    for rate in RATE_KEYS:
        fund, start = month_of(d, "fund_reached", rate), month_of(d, "time_off_start", rate)
        assert fund is not None and start is not None and start >= fund
        assert d.timeline.lines[RATE_KEYS.index(rate)].balance[start] >= d.fund_target + d.time_off.amount - 1e-6


def test_ru24_the_goal_after_a_time_off_waits_for_it_to_end():
    d = design(66505, TimeOff(2), SavingsGoal("car", 5000))
    end = month_of(d, "time_off_end", "actual")
    assert end == month_of(d, "time_off_start", "actual") + 2
    assert month_of(d, "goal_bought", "actual", "car") > end
    assert d.time_off.position == 1 and d.goals[0].position == 2


def test_ru24_a_blocked_item_blocks_the_ones_behind_it():
    d = design(20111, TimeOff(24), SavingsGoal("car", 60000))
    assert d.goals[0].reach[1].state in ("never", "over_cap")
    assert d.time_off.reach[1].state in ("never", "over_cap")


def test_wl3_the_goal_drops_the_balance_when_bought():
    d = design(66505, CAR)
    line = d.timeline.lines[0].balance
    bought = month_of(d, "goal_bought", "actual", "car")
    assert line[bought - 1] > 60000 and line[bought] < line[bought - 1]


# OI-19
def test_oi19_zero_interest_is_the_same_as_no_interest():
    assert design(66505, CAR, interest_pct=0.0) == design(66505, CAR)
    assert design(66505, CAR, interest_pct=0) == design_plan(66505, PlanRequest((CAR,), interest_pct=0.0))


def test_oi19_six_percent_shortens_months_on_a_positive_rate_and_leaves_never():
    base, six = design(66505, CAR), design(66505, CAR, interest_pct=6.0)
    assert reach(six, "actual").month < reach(base, "actual").month
    assert reach(six, "actual").month_no_loan < reach(base, "actual").month_no_loan
    never = design(20111, CAR, interest_pct=6.0)
    assert reach(never, "actual").state_no_loan == "never" and reach(never, "judges").state_no_loan == "never"


def test_interest_that_grows_a_positive_balance_reads_over_cap_not_never():
    d = design(20176, SavingsGoal("big", 5e9), interest_pct=25.0)
    assert {r.state for r in d.goals[0].reach} <= {"over_cap", "reached"}


def test_interest_is_not_paid_on_a_negative_balance():
    d = design(32078, interest_pct=25.0)
    plain = design(32078)
    assert get_profile(32078).B < 0
    assert d.timeline.lines[1].balance[:3] == pytest.approx(plain.timeline.lines[1].balance[:3])


def test_interest_cap_constant_and_default():
    assert MAX_INTEREST_PCT == 25.0 and PlanRequest().interest_pct == 0.0 and PlanRequest().target_months == 3.0
    assert design(20111, interest_pct=25.0).request.interest_pct == 25.0
    design(20111, interest_pct=0)
    design(20111, interest_pct=MAX_INTEREST_PCT)
    for bad in (25.01, -0.01, math.nan, math.inf, True, "5"):
        with pytest.raises(InvalidPlanError) as e:
            design(20111, interest_pct=bad)
        assert e.value.field == "interest_pct"


def test_fact_interest_applied():
    codes = lambda d: {f.code for f in d.facts}
    assert "interest_applied" in codes(design(20111, interest_pct=5.0))
    assert "interest_applied" not in codes(design(20111))


# Wallets, WL-1 to WL-4
def test_wl3_20111_fund_wallet_goes_negative_with_the_car_waiting():
    d = design(20111, CAR)
    fund, car = wallets_at(d, "actual", 35)
    assert fund.item == "fund" and fund.position == 0 and fund.amount == pytest.approx(-8564, abs=1) and fund.state == "filling"
    assert fund.target == pytest.approx(d.fund_target)
    assert (car.item, car.position, car.amount, car.state, car.month_accomplished) == ("car", 1, 0.0, "waiting", 115)


def test_wl4_66505_car_fills_from_month_24_and_is_accomplished_at_45():
    d = design(66505, CAR)
    fund = d.fund_target
    before = wallets_at(d, "actual", 23)
    assert before[0].state == "filling" and before[1].state == "waiting" and before[1].amount == 0.0
    f, c = wallets_at(d, "actual", 24)
    assert f.state == "full" and f.amount == pytest.approx(fund) and c.state == "filling" and c.amount > 0
    f, c = wallets_at(d, "actual", 44)
    assert c.state == "filling" and c.amount < 60000 and c.month_accomplished == 45
    f, c = wallets_at(d, "actual", 45)
    assert (c.state, c.amount, c.month_accomplished) == ("accomplished", 0.0, 45)
    assert wallets_at(d, "actual", 60)[1].amount == 0.0


@pytest.mark.parametrize("account,items", [
    (20111, (CAR,)), (66505, (CAR, TimeOff(3))), (66505, (TimeOff(3), SavingsGoal("a", 9000), SavingsGoal("b", 9000))),
    (20176, (SavingsGoal("a", 1000),)), (95548, (TimeOff(4), CAR)), (66505, ())])
def test_wl3_the_wallets_add_up_to_the_balance_and_one_is_active(account, items):
    d = design(account, *items, emergency=EmergencyCost(3000))
    for k, rate in enumerate(RATE_KEYS):
        for month in range(d.timeline.horizon + 1):
            ws = wallets_at(d, rate, month)
            assert sum(w.amount for w in ws) == pytest.approx(d.timeline.lines[k].balance[month], abs=1e-6)
            assert sum(w.state in ("filling", "spending") for w in ws) <= 1
            assert ws[0].item == "fund" and [w.position for w in ws] == list(range(len(ws)))


def test_wl3_the_time_off_wallet_spends_while_the_time_off_runs():
    d = design(66505, TimeOff(3))
    start = month_of(d, "time_off_start", "actual")
    assert wallets_at(d, "actual", start - 1)[1].state in ("filling", "waiting")
    states = [wallets_at(d, "actual", m)[1].state for m in range(start, start + 4)]
    assert states == ["spending", "spending", "spending", "accomplished"]
    assert wallets_at(d, "actual", start)[1].month_accomplished == start + 3
    assert wallets_at(d, "actual", start + 3)[1].amount == 0.0


def test_wl3_no_fund_wallet_when_there_is_no_fund_target():
    d = design(20578, SavingsGoal("bike", 100))
    assert d.fund_target is None
    ws = wallets_at(d, "actual", 0)
    assert [w.item for w in ws] == ["bike"]
    assert "no_fund_target" in {f.code for f in d.facts}


def test_wl3_a_later_wallet_is_waiting_with_zero():
    d = design(66505, SavingsGoal("a", 9000), SavingsGoal("b", 9000))
    fund, a, b = wallets_at(d, "actual", 25)
    assert a.state == "filling" and a.amount > 0 and b.state == "waiting" and b.amount == 0.0 and b.target == 9000


def test_wl3_wallets_outside_the_horizon_raise():
    d = design(20111, CAR)
    h = d.timeline.horizon
    wallets_at(d, "actual", h)
    for bad in (h + 1, -1, 1.5, "3", True):
        with pytest.raises(InvalidPlanError) as e:
            wallets_at(d, "actual", bad)
        assert e.value.field == "month"
    with pytest.raises(InvalidPlanError) as e:
        wallets_at(d, "best", 0)
    assert e.value.field == "rate"


# Validation
BAD = [
    ("items", dict(items=(CAR,) * 5)),
    ("items", dict(items=(TimeOff(1), TimeOff(2)))),
    ("items", dict(items=("car",))),
    ("name", dict(items=(SavingsGoal("", 1),))),
    ("name", dict(items=(SavingsGoal("   ", 1),))),
    ("name", dict(items=(SavingsGoal("x" * 41, 1),))),
    ("name", dict(items=(SavingsGoal(None, 1),))),
    ("amount", dict(items=(SavingsGoal("a", -1),))),
    ("amount", dict(items=(SavingsGoal("a", math.nan),))),
    ("amount", dict(items=(SavingsGoal("a", math.inf),))),
    ("amount", dict(items=(SavingsGoal("a", True),))),
    ("amount", dict(items=(SavingsGoal("a", "5"),))),
    ("deadline_months", dict(items=(SavingsGoal("a", 1, 0),))),
    ("deadline_months", dict(items=(SavingsGoal("a", 1, 121),))),
    ("deadline_months", dict(items=(SavingsGoal("a", 1, 2.5),))),
    ("deadline_months", dict(items=(SavingsGoal("a", 1, True),))),
    ("months_off", dict(items=(TimeOff(0),))),
    ("months_off", dict(items=(TimeOff(121),))),
    ("months_off", dict(items=(TimeOff(1.5),))),
    ("months_off", dict(items=(TimeOff(True),))),
    ("cost", dict(emergency=EmergencyCost(-1))),
    ("cost", dict(emergency=EmergencyCost(math.nan))),
    ("cost", dict(emergency=EmergencyCost(True))),
    ("target_months", dict(target_months=0)),
    ("target_months", dict(target_months=-1)),
    ("target_months", dict(target_months=math.inf)),
    ("target_months", dict(target_months=True)),
]


@pytest.mark.parametrize("field,kw", BAD)
def test_each_invalid_input_names_its_field(field, kw):
    with pytest.raises(InvalidPlanError) as e:
        design_plan(20111, PlanRequest(**kw))
    assert e.value.field == field


def test_boundaries_are_accepted():
    d = design(20111, SavingsGoal("x" * 40, 0, 1), TimeOff(120), emergency=EmergencyCost(0), target_months=0.5)
    assert d.request.target_months == 0.5
    assert design(20111, SavingsGoal("  car  ", 10, 120)).goals[0].goal.name == "  car  "
    assert design(20111, SavingsGoal("a", 1), SavingsGoal("b", 1), SavingsGoal("c", 1), TimeOff(1))


def test_a_bad_account_id_still_raises_the_accounts_error():
    from app.engine import InvalidAccountIdError
    with pytest.raises(InvalidAccountIdError):
        design_plan("abc")
    assert design_plan("20,111").account_id == 20111


# AC-16 edges
def test_ac16_amount_zero():
    g = design(20111, SavingsGoal("none", 0, 12)).goals[0]
    assert g.state == "zero" and g.total_needed == g.fund_needed


def test_ac16_now_when_the_money_above_the_fund_covers_it():
    d = design(91858, CAR, emergency=EmergencyCost(10000))
    g = d.goals[0]
    assert d.fund_target is None and g.state == "now" and all(r.state == "now" and r.month == 0 for r in g.reach)
    assert g.fund_needed == 0.0
    assert month_of(d, "goal_bought", "actual", "car") == 0
    assert wallets_at(d, "actual", 0)[0].state == "accomplished"


def test_ac16_a_negative_buffer():
    d = design(32078, SavingsGoal("car", 1000, 1))
    assert get_profile(32078).B < 0
    assert {"no_buffer"} <= {f.code for f in d.facts}
    assert d.goals[0].fund_needed > 0 and d.goals[0].reach[0].state in ("never", "over_cap", "reached")
    assert all(math.isfinite(x) for x in d.timeline.lines[0].balance)


def test_ac16_a_deadline_shorter_than_possible_exceeds_flexible_spending():
    ans = design(20111, SavingsGoal("car", 60000, 1)).goals[0].deadline
    assert ans.over_flexible and ans.cut_needed > ans.flexible_spending and ans.monthly_needed == pytest.approx(ans.need)


def test_ac16_121_months_off_is_rejected_and_120_is_checked_from_now():
    with pytest.raises(InvalidPlanError):
        design(20111, TimeOff(121))
    d = design(20111, TimeOff(120))
    assert all(c.started_now for c in d.time_off.checks)


def test_an_empty_request_still_draws_the_timeline_and_the_loan_marker():
    d = design(20111)
    assert d.goals == () and d.time_off is None and d.emergency is None
    assert d.timeline.horizon == 120 and [e.code for e in d.timeline.events if e.code == "loan_paid_off"] == ["loan_paid_off"]


# Facts
def test_facts_on_the_populations():
    codes = lambda a, *items, **kw: {f.code for f in design(a, *items, **kw).facts}
    assert "loan_scheduled_only" in codes(20111)
    assert "loan_not_in_spending" in codes(20208) and "loan_not_in_spending" not in codes(20111)
    assert "data_stops_early" in codes(20866)
    assert "pension_time_off" in codes(20176, TimeOff(3)) and "pension_time_off" not in codes(20176)
    assert "rates_disagree" in codes(66505) and "rates_disagree" not in codes(20111)
    assert "no_fund_target" in codes(20578) and "no_buffer" in codes(32078)
    assert all(f.message and "None" not in f.message and "{" not in f.message for a in (20111, 20208, 20866, 32078) for f in design(a).facts)


def test_design_is_pure_and_repeatable():
    r = PlanRequest((SavingsGoal("car", 60000, 24), TimeOff(12)), EmergencyCost(5000))
    assert design_plan(20111, r) == design_plan(20111, r)
    assert dataclasses.is_dataclass(design_plan(20111, r)) and design_plan(20111).request == PlanRequest()
    assert goals.MAX_ITEMS == 4
