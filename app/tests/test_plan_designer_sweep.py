"""AC-16 and AC-20 (plan half): every account, two requests. The engine invariants first, then the plan designer sentences."""
import math
import re

import pytest

from app.engine import EmergencyCost, InvalidPlanError, PlanRequest, SavingsGoal, TimeOff, design_plan, get_profile, wallets_at
from app.engine.data import get_dataset
from app.engine.goals import MARKER_CODES
from app.engine.rates import RATE_KEYS
from app.ui import plan_text

IDS = sorted(get_dataset().rows_by_account)
COST = 10000
REQUEST_A = PlanRequest((SavingsGoal("car", 60000, 24), TimeOff(24)), EmergencyCost(COST))
REQUEST_B = PlanRequest((SavingsGoal("none", 0, 1), TimeOff(120)), EmergencyCost(0))
REQUESTS = {"A": REQUEST_A, "B": REQUEST_B}
BANNED = ("None", "nan", "{", "$$", "-$0")
ONE_MONTHS = re.compile(r"(?<![\d.,])1 months")


@pytest.fixture(scope="module")
def designs():
    return {name: [(a, design_plan(a, request)) for a in IDS] for name, request in REQUESTS.items()}


def _walk(value):
    if value is None:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(k)
            yield from _walk(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _walk(v)


def _text_problems(design):
    lines = list(_walk(plan_text.rate_rows(design.rates)))
    for goal in design.goals:
        lines += _walk(plan_text.goal_lines(design, goal))
    for call in (plan_text.time_off_lines, plan_text.emergency_lines, plan_text.loan_lines, plan_text.fact_lines):
        lines += _walk(call(design))
    for month in sorted({0, design.timeline.horizon // 2, design.timeline.horizon}):
        lines += _walk(plan_text.wallet_rows(design, month))
    lines += _walk(plan_text.table_rows(design))
    lines += _walk(plan_text.timeline_alt(design))
    lines += _walk(plan_text.after_cap_line(design))
    return [(line, ban) for line in lines for ban in BANNED if ban in line] + \
           [(line, "1 months") for line in lines if ONE_MONTHS.search(line)]


def _item_months(design, k):
    """(position, kind, start month, end month, months_no_loan) of each item on line k, from the Reach cuts."""
    rows = [(g.position, "goal", g.reach[k].month, g.reach[k].month, g.reach[k].month_no_loan) for g in design.goals]
    if design.time_off is not None:
        t = design.time_off
        start = t.reach[k].month
        rows.append((t.position, "off", start, None if start is None else start + t.time_off.months_off, t.reach[k].month_no_loan))
    return sorted(rows)


def _check_engine(account, design, request):
    p = get_profile(account)
    cost = request.emergency.cost
    t = design.timeline
    assert 12 <= t.horizon <= 120, account
    assert design.account_id == account and len(t.lines) == 3 and t.start == p.B
    if t.after_cap:
        assert t.horizon == 120
    keys = [(e.month, -1 if e.rate is None else RATE_KEYS.index(e.rate), MARKER_CODES.index(e.code)) for e in t.events]
    assert keys == sorted(keys), account
    assert all(e.month <= t.horizon and 0 <= e.month <= 120 for e in t.events)
    purchased_now = any(e.code == "goal_bought" and e.month == 0 for e in t.events)
    for k, line in enumerate(t.lines):
        assert line.rate == RATE_KEYS[k] and len(line.balance) == t.horizon + 1, account
        assert all(math.isfinite(x) for x in line.balance), account
        if not purchased_now:
            assert line.balance[0] == pytest.approx(p.B - cost, abs=1e-6), account
        previous_end = 0
        unreached = False
        for position, kind, start, end, no_loan in _item_months(design, k):
            for month in (start, no_loan):
                assert month is None or 0 <= month <= 120, account
            if start is None:
                unreached = True
            else:
                assert not unreached, (account, "an item was reached behind one that was not")
                assert start >= previous_end, (account, "an item was reached before the one ahead of it")
                previous_end = end
        for e in t.events:
            if e.code == "goal_bought" and e.rate == line.rate and design.fund_target is not None:
                assert line.balance[e.month] >= design.fund_target - 1e-6, (account, "bought below the fund")
    for g in design.goals:
        assert g.state in ("zero", "now", "planned")
        for r in g.reach:
            assert (r.month is not None) == (r.state in ("now", "reached")), account
            assert (r.month_no_loan is not None) == (r.state_no_loan in ("now", "reached")), account
            assert r.state in ("now", "reached", "over_cap", "never")
            if r.month is not None and r.month_no_loan is not None:
                assert r.month <= r.month_no_loan or r.state != "reached", account
        if g.state == "now":
            assert all(r.state == "now" for r in g.reach)
        a = g.deadline
        if a is None:
            continue
        assert math.isfinite(a.monthly_needed) and a.cut_needed >= 0 and a.need >= 0
        if a.counts_loan_end:
            assert a.payoff_month is not None and a.payoff_month <= a.months, account
            assert a.cut_with_loan is not None and a.cut_with_loan <= a.cut_needed + 1e-6, account
            assert a.on_pace_with_loan == (a.cut_with_loan == 0)
        else:
            assert a.cut_with_loan is None and a.payoff_month is None and a.on_pace_with_loan is None, account
        assert a.on_pace == (a.cut_needed == 0) and a.within_lean == (a.cut_needed <= a.lean_cut)
    if design.time_off is not None:
        for c in design.time_off.checks:
            assert c.started_now == (design.time_off.reach[RATE_KEYS.index(c.rate)].month is None)
            assert math.isfinite(c.start_balance) and c.duration.months_asked == design.time_off.time_off.months_off
    e = design.emergency
    if e is not None:
        assert e.covered == (e.buffer_left > 0) and (e.backup is None) == e.covered, account
        assert e.from_wallet + e.from_fund == pytest.approx(e.cost) and e.from_wallet >= 0 and e.from_fund >= 0
        assert all(r.to_fund is None for r in e.rebuild) == (design.fund_target is None)
    assert design.fund_target is None or design.fund_target > 0
    assert (design.fund_target is None) == (p.S <= 0)


def _check_wallets(account, design):
    t = design.timeline
    for k, rate in enumerate(RATE_KEYS):
        balance = t.lines[k].balance
        for month in range(t.horizon + 1):
            ws = wallets_at(design, rate, month)
            assert sum(w.state in ("filling", "spending") for w in ws) <= 1, (account, rate, month)
            if design.fund_target is not None:
                assert ws[0].item == "fund"
                assert sum(w.amount for w in ws) == pytest.approx(balance[month], abs=1e-6), (account, rate, month)
            else:
                assert all(w.item != "fund" for w in ws)
            assert all(w.state != "full" for w in ws[1:] if w.item != "fund")
    with pytest.raises(InvalidPlanError):
        wallets_at(design, "actual", t.horizon + 1)


def test_engine_invariants_on_every_account(designs):
    for name, request in REQUESTS.items():
        for account, design in designs[name]:
            _check_engine(account, design, request)


def test_wallets_add_up_and_one_is_active_on_every_account(designs):
    for name in REQUESTS:
        for account, design in designs[name]:
            _check_wallets(account, design)


def test_plan_designer_sentences_have_no_placeholders_on_every_account(designs):
    problems = []
    for name in REQUESTS:
        for account, design in designs[name]:
            problems += [(account, name, *x) for x in _text_problems(design)]
    assert not problems[:5], f"{len(problems)} bad lines, for example {problems[:5]}"


def test_ac16_amount_zero_has_its_state_on_every_account(designs):
    assert {d.goals[0].state for _, d in designs["B"]} == {"zero"}
    assert all(d.goals[0].goal.amount == 0 and d.goals[0].deadline.months == 1 for _, d in designs["B"])


def test_ac16_the_goal_covered_above_the_fund_is_now(designs):
    now = [a for a, d in designs["A"] if d.goals[0].state == "now"]
    assert now, "at least one account can buy $60,000 at once"
    assert 91858 in now
    for a, d in designs["A"]:
        if a in now:
            assert all(r.state == "now" and r.month == 0 for r in d.goals[0].reach)
            assert d.goals[0].fund_needed == 0.0


def test_ac16_121_months_off_is_rejected():
    for account in (20111, 91858, 20578):
        with pytest.raises(InvalidPlanError) as e:
            design_plan(account, PlanRequest((TimeOff(121),)))
        assert e.value.field == "months_off"


def test_ac16_negative_buffer_accounts(designs):
    low = [(a, d) for a, d in designs["A"] if get_profile(a).B <= 0]
    assert len(low) == 23
    for a, d in low:
        assert "no_buffer" in {f.code for f in d.facts}
        assert d.emergency.covered is False and d.emergency.backup is not None
        assert d.goals[0].reach[0].state in ("never", "over_cap", "reached")


def test_ac16_accounts_without_a_fund_target(designs):
    none = [(a, d) for a, d in designs["A"] if get_profile(a).S == 0]
    assert len(none) == 77
    for a, d in none:
        assert d.fund_target is None and "no_fund_target" in {f.code for f in d.facts}
        assert d.goals[0].fund_needed == 0.0
        assert all(w.item != "fund" for w in wallets_at(d, "actual", 0))


def test_ac16_a_deadline_shorter_than_possible_exceeds_flexible_spending(designs):
    over = [a for a, d in designs["A"] if d.goals[0].deadline.over_flexible]
    assert len(over) > 1000
    for a, d in designs["A"]:
        ans = d.goals[0].deadline
        assert ans.over_flexible == (ans.cut_needed > ans.flexible_spending)


def test_ac16_both_cuts_appear_where_a_loan_ends_inside_the_deadline(designs):
    both = [a for a, d in designs["A"] if d.goals[0].deadline.counts_loan_end]
    assert both and 20111 not in both
    assert all(d.goals[0].deadline.cut_with_loan is None for a, d in designs["A"] if not get_profile(a).running_loan)
