"""Plan designer wording on hand-built PlanDesign objects: every P.* branch, AC-19 (no number is computed here) and the copy deck."""
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.engine import saving_rates
from app.engine.goals import (DeadlineAnswer, EmergencyCost, EmergencyResult, GoalResult, PlanDesign, PlanRequest, Reach, Rebuild, SavingsGoal, TimeOff,
                              TimeOffCheck, TimeOffResult, Timeline, TimelineEvent, TimelineLine, Wallet)
from app.engine.rates import RATE_KEYS, LoanEnd, SavingRate
from app.engine.shock import DurationResult, Fact
from app.ui import plan_text
from app.ui.plan_text import P

COPY = Path(__file__).resolve().parents[2] / "docs" / "design" / "ux" / "copy.md"
BIG = 12345.67          # "$12,346": a sentinel that no code path can reach by arithmetic (AC-19)
SENTINEL = "$12,346"
LABELS = [P.r_actual, P.r_judges, P.r_lean]


def reach(rate="actual", state="reached", month=10, plain=None, plain_month=-1, cut_to_start=None, cut_to_reach=None):
    plain = state if plain is None else plain
    plain_month = month if plain_month == -1 else plain_month
    return Reach(rate, state, month, plain, plain_month, cut_to_start, cut_to_reach)


def three(**kw):
    return tuple(reach(rate, **kw) for rate in RATE_KEYS)


def deadline(**kw):
    base = dict(months=24, need=BIG, monthly_needed=BIG, headline_rate=-748.0, cut_needed=BIG, on_pace=False, flexible_spending=BIG,
                cut_share_of_flexible=0.57, lean_cut=BIG, within_lean=False, over_flexible=False, includes_fund=False, counts_loan_end=False,
                payoff_month=None, cut_with_loan=None, on_pace_with_loan=None)
    return DeadlineAnswer(**{**base, **kw})


def goal(*, state="planned", reaches=None, fund_needed=0.0, amount=60000.0, name="car", dl=None):
    return GoalResult(SavingsGoal(name, amount, None if dl is None else dl.months), 1, fund_needed, fund_needed + amount, state, reaches or three(), dl)


def duration(verdict="makes_it", runs_out=None, months=24):
    return DurationResult(months, verdict, runs_out, None, None, 0.0, 0.0, 0.0, (), None, None, False, "")


def timeline(events=(), after_cap=(), horizon=12, balance=0.0):
    lines = tuple(TimelineLine(k, tuple(balance + 100.0 * m * (i + 1) for m in range(horizon + 1))) for i, k in enumerate(RATE_KEYS))
    return Timeline(horizon, balance, lines, tuple(events), tuple(after_cap))


def design(*, goals=(), time_off=None, emergency=None, tl=None, facts=(), items=(), interest=0.0, rates=None, fund=25799.0):
    return PlanDesign(20111, PlanRequest(tuple(items), None, 3.0, interest), rates or saving_rates(20111), fund, tuple(goals), time_off, emergency,
                      tl or timeline(), tuple(facts))


def with_loan(loan):
    return replace(saving_rates(20111), loan_end=loan)


def a_loan(**kw):
    base = dict(status="C", payment=2330.19, payoff_month=36, scheduled_only=False, in_typical_spending=True, bump_judges=2330.0, bump_actual=1941.7,
                bump_lean=2330.19, paid_rows=10)
    return LoanEnd(**{**base, **kw})


# --- the copy deck ----------------------------------------------------------------------------------------------------

def test_p_constants_equal_the_copy_11_rows():
    """Every row of copy §11 without an ellipsis or a choice in braces is the P constant, character for character."""
    section = COPY.read_text().split("## 11. Plan designer (P)")[1]
    checked = 0
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not cells[0].startswith("P.") or cells[0] == "P.m_*":
            continue
        keys = [k.strip() for k in cells[0].split(",")]
        texts = [t.strip() for t in cells[1].split(" · ")]
        if len(keys) != len(texts):
            continue
        for key, copy in zip(keys, texts):
            if "..." in copy or "{within or" in copy:
                continue
            name = key.removeprefix("P.")
            assert getattr(P, name) == copy, (key, copy)
            checked += 1
    assert checked == 46


def test_the_markers_match_copy_11_and_each_has_a_letter():
    assert [P.m_fund_reached, P.m_goal_reached, P.m_goal_bought, P.m_time_off_start, P.m_time_off_end, P.m_emergency_cost, P.m_loan_paid_off] == [
        "Emergency fund reached", "{goal_name} reached", "{goal_name} bought", "Time off starts", "Time off ends", "Emergency cost", "Loan paid off"]
    assert plan_text.MARKER_LETTER == {"fund_reached": "F", "goal_reached": "G", "goal_bought": "B", "time_off_start": "O", "time_off_end": "O",
                                       "emergency_cost": "E", "loan_paid_off": "L"}


def test_new_copy_22_and_loan_backup_are_shared_with_text_py():
    from app.ui import text
    assert P.loan_not_in_spending == text.LOAN_NOT_IN_SPENDING and P.loan_backup == text.LOAN_BACKUP


# --- rates ------------------------------------------------------------------------------------------------------------

def test_rate_rows_on_20111_put_the_headline_first_and_sign_the_money():
    assert plan_text.rate_rows(saving_rates(20111)) == [
        ("Actual change, last 12 months (ours)", "-$748 a month", True),
        ("Typical money in minus typical spending", "-$2,260 a month", False),
        ("Spending at its lean months (ours)", "+$604 a month", False)]


def test_rate_rows_show_a_zero_rate_without_a_sign():
    rates = replace(saving_rates(20111), actual=SavingRate("actual", 0.2, 0.0, True, True))
    assert plan_text.rate_rows(rates)[0] == (P.r_actual, "$0 a month", True)


# --- savings goal -----------------------------------------------------------------------------------------------------

def test_goal_months_never_and_over_cap_use_the_rate_labels():
    reaches = (reach("actual", "reached", 30), reach("judges", "never", None), reach("lean", "over_cap", None))
    lines = plan_text.goal_lines(design(), goal(reaches=reaches))
    assert lines == ["Actual change, last 12 months (ours): 30 months.",
                     "Typical money in minus typical spending: never at this rate.",
                     "Spending at its lean months (ours): more than 120 months."]


def test_goal_one_month_is_singular():
    lines = plan_text.goal_lines(design(), goal(reaches=(reach("actual", "reached", 1), reach("judges", "reached", 2), reach("lean", "reached", 3))))
    assert lines[0] == "Actual change, last 12 months (ours): 1 month."
    assert lines[1] == "Typical money in minus typical spending: 2 months."


def test_goal_needs_the_fund_first():
    lines = plan_text.goal_lines(design(), goal(fund_needed=8187.0))
    assert lines[0] == "$8,187 to finish the emergency fund first, then $60,000 for the car."


def test_goal_already_affordable_zero_amount():
    assert plan_text.goal_lines(design(), goal(state="now")) == ["The money above the emergency fund already covers the car, so it can be bought now."]
    assert plan_text.goal_lines(design(), goal(state="zero", amount=0.0)) == ["The amount is $0, so there is nothing to save."]


def test_deadline_cut_with_more_than_lean_and_the_share_as_a_whole_percent():
    dl = deadline(monthly_needed=2841.12, cut_needed=3589.01, flexible_spending=6269.0, lean_cut=2864.0, cut_share_of_flexible=0.5725)
    lines = plan_text.goal_lines(design(), goal(dl=dl))
    assert lines[-2:] == ["To have it in 24 months, save $2,841 a month.",
                          "That needs $3,589 a month less spending: 57% of the $6,269 above fixed costs, more than the $2,864 the lean-quarter level would save."]


def test_deadline_cut_within_lean():
    dl = deadline(within_lean=True, cut_needed=500.0, lean_cut=2864.0, flexible_spending=6269.0, cut_share_of_flexible=0.08)
    assert plan_text.goal_lines(design(), goal(dl=dl))[-1] == (
        "That needs $500 a month less spending: 8% of the $6,269 above fixed costs, within the $2,864 the lean-quarter level would save.")


def test_deadline_on_pace_has_no_cut():
    lines = plan_text.goal_lines(design(), goal(dl=deadline(on_pace=True, cut_needed=0.0, cut_share_of_flexible=0.0)))
    assert lines[-1] == "The actual change already does that, so no cut is needed." and not any("a month less" in line for line in lines)


def test_deadline_over_flexible_adds_the_cuts_alone_line():
    dl = deadline(over_flexible=True, cut_needed=7000.0, flexible_spending=6269.0, cut_share_of_flexible=1.12, lean_cut=2864.0)
    assert plan_text.goal_lines(design(), goal(dl=dl))[-1] == "That is more than the $6,269 above fixed costs, so cuts alone can't reach it by then."


def test_deadline_over_flexible_with_no_flexible_spending_still_names_the_cut():
    dl = deadline(over_flexible=True, cut_needed=700.0, flexible_spending=0.0, cut_share_of_flexible=None)
    assert plan_text.goal_lines(design(), goal(dl=dl))[-2:] == [
        "That needs $700 a month less spending.", "That is more than the $0 above fixed costs, so cuts alone can't reach it by then."]


def test_deadline_one_month_and_fund_first():
    lines = plan_text.goal_lines(design(), goal(dl=deadline(months=1, includes_fund=True)))
    assert "To have it in 1 month, save $12,346 a month." in lines
    assert lines[lines.index("To have it in 1 month, save $12,346 a month.") + 1] == "This includes finishing the emergency fund first."


def test_new_copy_27_second_cut_follows_the_cautious_cut_and_only_when_it_counts():
    counted = deadline(counts_loan_end=True, payoff_month=17, cut_with_loan=672.08, on_pace_with_loan=False)
    lines = plan_text.goal_lines(design(), goal(dl=counted))
    cautious = next(i for i, line in enumerate(lines) if line.startswith("That needs"))
    assert lines[cautious + 1] == "Counting the loan ending in month 17, spend $672 a month less (ours)."
    plain = plan_text.goal_lines(design(), goal(dl=deadline(counts_loan_end=False)))
    assert not any("Counting the loan" in line for line in plain)


def test_new_copy_27_on_pace_form():
    counted = deadline(counts_loan_end=True, payoff_month=17, cut_with_loan=0.0, on_pace_with_loan=True)
    assert plan_text.goal_lines(design(), goal(dl=counted))[-1] == "Counting the loan ending in month 17, the current pace is enough (ours)."


def test_loan_line_loan_never_and_loan_over_lines():
    reaches = (reach("actual", "reached", 22, plain="reached", plain_month=31), reach("judges", "reached", 115, plain="never", plain_month=None),
               reach("lean", "over_cap", None, plain="never", plain_month=None))
    lines = plan_text.goal_lines(design(rates=with_loan(a_loan(payoff_month=9))), goal(reaches=reaches))
    assert lines == ["Actual change, last 12 months (ours): 31 months; 22 counting the loan ending in month 9 (ours).",
                     "Typical money in minus typical spending: never at this rate; 115 months counting the loan ending in month 9 (ours).",
                     "Spending at its lean months (ours): never at this rate, and more than 120 months counting the loan ending in month 9 (ours)."]


def test_loan_lines_are_singular_when_one_month_and_silent_without_a_loan_difference():
    reaches = (reach("actual", "reached", 1, plain="reached", plain_month=2), reach("judges", "reached", 5), reach("lean", "never", None))
    lines = plan_text.goal_lines(design(rates=with_loan(a_loan(payoff_month=1))), goal(reaches=reaches))
    assert lines[0].endswith("2 months; 1 counting the loan ending in month 1 (ours).")
    assert lines[1] == "Typical money in minus typical spending: 5 months."
    never_then_one = replace(reaches[0], state_no_loan="never", month_no_loan=None)
    assert plan_text.goal_lines(design(rates=with_loan(a_loan())), goal(reaches=(never_then_one,) + reaches[1:]))[0].startswith(
        "Actual change, last 12 months (ours): never at this rate; 1 month counting")


def test_loan_end_difference_without_a_loan_is_not_printed():
    reaches = (reach("actual", "reached", 22, plain="reached", plain_month=31),) + three()[1:]
    assert plan_text.goal_lines(design(rates=with_loan(None)), goal(reaches=reaches))[0] == "Actual change, last 12 months (ours): 22 months."


def test_cut_to_start_for_a_rate_at_or_below_zero():
    reaches = (reach("actual", "never", None, cut_to_start=747.89, cut_to_reach=1247.0), ) + three()[1:]
    lines = plan_text.goal_lines(design(), goal(reaches=reaches))
    assert lines[3] == "Actual change, last 12 months (ours): Saving starts with spending $748 a month less. $1,247 a month less would reach it in 120 months."


def test_interest_and_other_facts_in_fact_lines():
    facts = [Fact("interest_applied", ""), Fact("no_fund_target", ""), Fact("no_buffer", ""), Fact("data_stops_early", ""), Fact("rates_disagree", ""),
             Fact("pension_time_off", ""), Fact("loan_scheduled_only", ""), Fact("loan_not_in_spending", "")]
    lines = plan_text.fact_lines(design(facts=facts, interest=4.5))
    assert "Includes 4.5% a year interest (ours)." in lines
    assert "Not enough regular spending to set an emergency fund, so goals count from $0." in lines
    assert "Data stops in 2025-12, so month 1 is the month after." in lines
    assert P.r_note in lines and P.pension_time_off in lines and P.no_buffer in lines
    assert len(lines) == 6 and plan_text.fact_lines(design()) == []


def test_interest_whole_number_has_no_decimal():
    assert plan_text.fact_lines(design(facts=[Fact("interest_applied", "")], interest=5.0)) == ["Includes 5% a year interest (ours)."]


# --- loan lines -------------------------------------------------------------------------------------------------------

def test_loan_d_for_status_d_and_nothing_without_a_loan():
    assert plan_text.loan_lines(design(rates=with_loan(a_loan(status="D", scheduled_only=True)))) == [
        "The loan is behind, so month 36 is the scheduled end, not a certain one."]
    assert plan_text.loan_lines(design(rates=with_loan(None))) == []
    assert plan_text.loan_lines(design(rates=with_loan(a_loan()))) == []


def test_d12_line_for_the_judges_rate_on_a_recent_loan():
    loan = a_loan(payment=2956.31, payoff_month=42, in_typical_spending=False, bump_judges=0.0)
    assert plan_text.loan_lines(design(rates=with_loan(loan))) == [
        "The loan payment of $2,956 a month isn't in the judges' typical spending yet, because the loan started recently, "
        "so the judges' figure doesn't rise when it ends in month 42 (ours)."]


# --- time off ---------------------------------------------------------------------------------------------------------

def check(rate="actual", verdict="makes_it", runs_out=None, start=0, now=False, counts=False, months=24):
    return TimeOffCheck(rate, now, start, BIG, duration(verdict, runs_out, months), counts)


def time_off(checks, months_off=24, reaches=None):
    return TimeOffResult(TimeOff(months_off), 2, BIG, 7654.32, reaches or three(), checks)


def test_time_off_amount_and_runs_out_from_month_zero():
    checks = tuple(check(k, "runs_out", 3, 0, True) for k in RATE_KEYS)
    lines = plan_text.time_off_lines(design(time_off=time_off(checks, reaches=three(state="never", month=None))))
    assert lines[0] == "24 months off at typical spending: $12,346. At lean spending: $7,654 (ours)."
    assert lines[1] == "Actual change, last 12 months (ours): never at this rate."
    assert lines[4:] == ["Not saved by month 120, so this checks starting now.",
                         "With no income for 24 months from month 0, the money runs out in month 3 of the time off."]


def test_time_off_makes_it_and_one_month_off():
    checks = tuple(check(k, "makes_it", None, 18, False, months=1) for k in RATE_KEYS)
    lines = plan_text.time_off_lines(design(time_off=time_off(checks, months_off=1)))
    assert lines[0].startswith("1 month off at typical spending:")
    assert lines[-1] == "With no income for 1 month from month 18, the money lasts. They make it."


def test_time_off_checks_that_differ_name_their_rate():
    checks = (check("actual", "makes_it", None, 18), check("judges", "runs_out", 5, 40), check("lean", "makes_it", None, 18))
    lines = plan_text.time_off_lines(design(time_off=time_off(checks)))
    assert lines[-3:] == ["Actual change, last 12 months (ours): With no income for 24 months from month 18, the money lasts. They make it.",
                          "Typical money in minus typical spending: With no income for 24 months from month 40, the money runs out in month 5 of the time off.",
                          "Spending at its lean months (ours): With no income for 24 months from month 18, the money lasts. They make it."]


def test_time_off_with_no_buffer_and_with_a_loan_inside():
    zero = tuple(check(k, "runs_out", 0, 0, True) for k in RATE_KEYS)
    assert plan_text.time_off_lines(design(time_off=time_off(zero)))[-1] == "With no income for 24 months from month 0, there is no money before month 1."
    counted = tuple(check(k, "makes_it", None, 0, True, counts=True) for k in RATE_KEYS)
    lines = plan_text.time_off_lines(design(rates=with_loan(a_loan(payoff_month=9)), time_off=time_off(counted)))
    assert lines[-1] == "This counts the loan ending in month 9 (ours)."


def test_no_time_off_no_lines():
    assert plan_text.time_off_lines(design()) == []


# --- emergency --------------------------------------------------------------------------------------------------------

class FakeBackup:
    class Step:
        def __init__(self, order, action):
            self.order, self.action = order, action
    steps = (Step(1, "Find $12,513 to get back to $0."), Step(2, "Cut other spending."))


def emergency(cost=10000.0, before=17612.0, left=7612.0, covered=True, backup=None, from_wallet=0.0, from_fund=10000.0, rebuild=None):
    rebuild = rebuild or tuple(Rebuild(k, reach(k, "reached", 4), reach(k, "reached", 9)) for k in RATE_KEYS)
    return EmergencyResult(cost, before, left, covered, backup, 1346.0, 900.0, 446.0, rebuild, from_wallet, from_fund)


def test_emergency_covered_zero_and_negative_balance():
    assert plan_text.emergency_lines(design(emergency=emergency())) == ["The buffer covers it: $7,612 is left."]
    assert plan_text.emergency_lines(design(emergency=emergency(cost=0.0))) == ["The cost is $0, so the buffer is unchanged."]
    negative = emergency(before=-2513.0, left=-12513.0, covered=False, backup=FakeBackup())
    assert plan_text.emergency_lines(design(emergency=negative))[0] == "The balance was already -$2,513, so the cost isn't what empties the buffer."
    assert plan_text.emergency_lines(design()) == []


def test_emergency_that_the_buffer_cannot_cover_lists_the_budget_and_the_rebuild():
    e = emergency(before=-2513.0 + 3000, left=-12513.0, covered=False, backup=FakeBackup())
    lines = plan_text.emergency_lines(design(emergency=e))
    assert lines == [
        "The buffer can't cover it: -$12,513 left.",
        "Do this first, in order:", "1. Find $12,513 to get back to $0.", "2. Cut other spending.",
        "Lean budget: $1,346 a month, $900 fixed and $446 other (ours).",
        "Actual change, last 12 months (ours): back to $487 in 4 months, emergency fund in 9 months.",
        "Typical money in minus typical spending: back to $487 in 4 months, emergency fund in 9 months.",
        "Spending at its lean months (ours): back to $487 in 4 months, emergency fund in 9 months."]


def test_rebuild_singular_never_over_cap_and_no_fund_target():
    rebuild = (Rebuild("actual", reach("actual", "reached", 1), reach("actual", "reached", 1)),
               Rebuild("judges", reach("judges", "never", None), reach("judges", "over_cap", None)),
               Rebuild("lean", reach("lean", "over_cap", None), None))
    e = emergency(before=500.0, left=-9500.0, covered=False, rebuild=rebuild)
    lines = plan_text.emergency_lines(design(emergency=e))[-3:]
    assert lines == ["Actual change, last 12 months (ours): back to $500 in 1 month, emergency fund in 1 month.",
                     "Typical money in minus typical spending: back to $500 never at this rate, emergency fund in more than 120 months.",
                     "Spending at its lean months (ours): back to $500 in more than 120 months."]


def test_emergency_split_names_the_wallet_in_progress_then_the_fund(monkeypatch):
    wallets = (Wallet("fund", 0, 25799.0, 25799.0, "full", None), Wallet("car", 1, 60000.0, 4000.0, "filling", None))
    monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month: wallets)
    e = emergency(cost=BIG, left=5000.0, from_wallet=4000.0, from_fund=8345.67)
    lines = plan_text.emergency_lines(design(emergency=e, items=(SavingsGoal("car", 60000.0),)))
    assert lines == ["The buffer covers it: $5,000 is left.", "The $12,346 cost comes out of $4,000 saved for car, then $8,346 of the emergency fund."]


def test_emergency_split_names_a_time_off_and_skips_without_items_or_fund(monkeypatch):
    monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month: (Wallet("time_off", 1, 100.0, 50.0, "filling", None),))
    e = emergency(from_wallet=50.0, from_fund=9950.0)
    assert plan_text.emergency_lines(design(emergency=e, items=(TimeOff(6),)))[-1] == (
        "The $10,000 cost comes out of $50 saved for time off, then $9,950 of the emergency fund.")
    assert len(plan_text.emergency_lines(design(emergency=e))) == 1
    assert len(plan_text.emergency_lines(design(emergency=e, items=(TimeOff(6),), fund=None))) == 1


# --- timeline ---------------------------------------------------------------------------------------------------------

def ev(month, code, rate=None, item=None):
    return TimelineEvent(month, code, rate, item)


def test_marker_labels_cover_every_code():
    assert [plan_text.marker_label(ev(1, c, None, "car")) for c in
            ("fund_reached", "goal_reached", "goal_bought", "time_off_start", "time_off_end", "emergency_cost", "loan_paid_off")] == [
        "Emergency fund reached", "car reached", "car bought", "Time off starts", "Time off ends", "Emergency cost", "Loan paid off"]
    assert plan_text.marker_label(ev(1, "mystery")) == "mystery"


def test_timeline_alt_lists_the_headline_markers_once():
    events = [ev(0, "emergency_cost"), ev(5, "fund_reached", "actual"), ev(5, "fund_reached", "judges"), ev(9, "loan_paid_off"), ev(30, "goal_bought", "judges", "car")]
    assert plan_text.timeline_alt(design(tl=timeline(events, horizon=36))) == (
        "Line chart of the balance over 36 months at each saving rate. Markers: Emergency cost in month 0; Emergency fund reached in month 5; Loan paid off in month 9.")
    assert plan_text.timeline_alt(design()).endswith("Markers: none.")


def test_after_cap_line_names_each_item_once():
    after = [ev(None, "goal_reached", "actual", "car"), ev(None, "goal_bought", "actual", "car"), ev(None, "goal_reached", "lean", "car")]
    assert plan_text.after_cap_line(design(tl=timeline(after_cap=after, horizon=120))) == "After month 120: car reached; car bought."
    assert plan_text.after_cap_line(design()) is None


FUND, CAR, OFF = (Wallet("fund", 0, 25799.0, -8564.0, "full", None), Wallet("car", 1, 60000.0, 0.0, "waiting", None),
                  Wallet("time_off", 2, 206391.0, 0.0, "waiting", None))


def test_wallet_rows_states(monkeypatch):
    rows = {
        "filling": (Wallet("fund", 0, 25799.0, 4000.0, "filling", None),),
        "full": (Wallet("fund", 0, 25799.0, 25799.0, "full", None),),
        "spending": (Wallet("time_off", 1, 100.0, 40.0, "spending", None),),
        "accomplished": (Wallet("car", 1, 60000.0, 0.0, "accomplished", 45),),
    }
    expect = {"filling": ("Emergency fund", "$4,000 of $25,799", "filling"), "full": ("Emergency fund", "$25,799 of $25,799", "full"),
              "spending": ("Time off", "$40 of $100", "spending during the time off"), "accomplished": ("car", "$0 of $60,000", "accomplished in month 45")}
    for state, wallets in rows.items():
        monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month, w=wallets: w)
        assert plan_text.wallet_rows(design()) == [expect[state]], state


def test_wallet_rows_waiting_names_the_previous_wallet_and_a_negative_fund_says_so(monkeypatch):
    monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month: (FUND, CAR, OFF))
    loan = design(rates=with_loan(a_loan(payoff_month=36)))
    assert plan_text.wallet_rows(loan) == [("Emergency fund", "-$8,564 of $25,799", "below $0 before the loan ends"),
                                           ("car", "$0 of $60,000", "waiting for Emergency fund"),
                                           ("Time off", "$0 of $206,391", "waiting for car")]
    fund_label, amount, state = plan_text.wallet_rows(loan)[0]
    assert f"{fund_label}: {amount}, {state}" == P.w_negative_fund.format(amount="-$8,564", target="$25,799")
    assert plan_text.wallet_rows(design(rates=with_loan(None)))[0][2] == "below $0"


def test_wallet_rows_use_the_month_asked(monkeypatch):
    seen = []
    monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month: seen.append((rate, month)) or ())
    plan_text.wallet_rows(design(), 7)
    assert seen == [("actual", 7)]


def test_table_rows_have_one_wallet_column_per_item_and_events_joined(monkeypatch):
    def fake(d, rate, month):
        return (Wallet("fund", 0, 25799.0, 100.0 * month, "filling", None), Wallet("car", 1, 60000.0, 0.0, "waiting", None))
    monkeypatch.setattr(plan_text, "wallets_at", fake)
    events = [ev(2, "emergency_cost"), ev(2, "fund_reached", "actual"), ev(2, "fund_reached", "judges"), ev(2, "fund_reached", "lean"),
              ev(3, "goal_bought", "lean", "car")]
    rows = plan_text.table_rows(design(tl=timeline(events, horizon=12, balance=1000.0)))
    assert len(rows) == 13
    assert list(rows[0]) == ["Month", *LABELS, "Emergency fund wallet", "car wallet", "Events"]
    assert rows[2]["Events"] == "Emergency cost; Emergency fund reached"
    assert rows[3]["Events"] == "car bought (lean months)" and rows[4]["Events"] == ""
    assert rows[2]["Emergency fund wallet"] == "$200" and rows[1][P.r_actual] == "$1,100" and rows[1][P.r_judges] == "$1,200" and rows[1][P.r_lean] == "$1,300"


def test_table_rows_without_a_fund_target_have_no_wallet_columns(monkeypatch):
    monkeypatch.setattr(plan_text, "wallets_at", lambda d, rate, month: ())
    assert list(plan_text.table_rows(design(fund=None))[0]) == ["Month", *LABELS, "Events"]


# --- AC-19 ------------------------------------------------------------------------------------------------------------

def test_ac19_every_sentinel_comes_back_unchanged():
    """A sentinel in each money field of a hand-built design appears rounded and nothing else: no number is computed in plan_text."""
    lean = BIG
    e = emergency(cost=BIG, before=BIG, left=BIG, covered=False)
    e = replace(e, lean_budget=BIG, lean_fixed=BIG, lean_other=BIG)
    dl = deadline(counts_loan_end=True, payoff_month=17, cut_with_loan=BIG, on_pace_with_loan=False)
    d = design(goals=[goal(fund_needed=BIG, amount=BIG, dl=dl)], time_off=time_off(tuple(check(k) for k in RATE_KEYS)), emergency=e)
    d = replace(d, rates=with_loan(a_loan(payment=BIG, in_typical_spending=False, payoff_month=17)))
    lines = plan_text.goal_lines(d, d.goals[0]) + plan_text.time_off_lines(d) + plan_text.emergency_lines(d) + plan_text.loan_lines(d)
    joined = "\n".join(lines)
    assert joined.count(SENTINEL) >= 11
    assert "12,345" not in joined and "12346" not in joined and lean == BIG
    assert plan_text.rate_rows(replace(d.rates, judges=SavingRate("judges", BIG, 0.0, False, False)))[1][1] == "+$12,346 a month"


def test_ac19_no_arithmetic_in_the_module():
    source = (Path(plan_text.__file__)).read_text()
    code = re.sub(r'"[^"\n]*"', '""', source)
    for forbidden in ("sum(", "round(", "min(", " * ", " / "):
        assert forbidden not in code, forbidden


def test_plan_text_has_no_streamlit():
    assert "streamlit" not in Path(plan_text.__file__).read_text()
