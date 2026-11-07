"""Make a plan: a goal plan before any shock, and a backup plan if the shock hits. Every figure comes from the account."""
import math
from dataclasses import dataclass
from functools import lru_cache
from numbers import Integral, Real

from .data import get_dataset
from .errors import InvalidPlanError
from .formulas import Runway, money, runway_from
from .profile import get_profile, parse_account_id
from .shock import MAX_MONTHS, Fact, Shock, apply_shock, duration_path, get_preset, shock_gaps

MAX_PATH_ROWS = 6
LEAN_QUANTILE = 0.25


@dataclass(frozen=True)
class PathPoint:
    month: int
    balance: float


@dataclass(frozen=True)
class GoalPlan:
    state: str
    target_months: float
    target_amount: float | None
    current_buffer: float
    still_needed: float | None
    months_covered: float | None
    surplus: float
    surplus_share: float
    monthly_amount: float
    months_to_goal: int | None
    reaches_within_horizon: bool
    below_zero_by: float
    cut_to_break_even: float | None
    cut_to_reach_in_horizon: float | None
    flexible_spending: float
    cut_is_possible: bool | None
    savings_path: tuple
    actual_change_last_12: float


@dataclass(frozen=True)
class BackupStep:
    order: int
    code: str
    action: str
    monthly_saving: float
    one_time_amount: float
    needs_agreement: bool
    runway_before: Runway
    runway_after: Runway
    adds_months: float | None


@dataclass(frozen=True)
class BackupPlan:
    state: str
    shock: Shock
    through_months: int | None
    runway_before: Runway
    runway_after_steps: Runway
    makes_it_before: bool | None
    makes_it_after_steps: bool | None
    fixed_costs: float
    flexible_spending: float
    fixed_share_of_spending: float | None
    fixed_exceeds_spending: bool
    cut_to_last: float | None
    cut_to_last_share_of_spending: float | None
    cut_to_last_share_of_flexible: float | None
    cut_to_close_gap: float
    cut_is_possible: bool
    runway_if_all_flexible_cut: Runway
    cover_needed: float
    months_to_cover: int | None
    months_to_low_balance_line: float | None
    steps: tuple
    income_basis: str   # flat (the judges' rate) or ei_weekly_max


@dataclass(frozen=True)
class LowBalanceGoal:
    payment: float
    lowest_balance: float
    met: bool
    top_up_needed: float
    months_to_line: int | None


@dataclass(frozen=True)
class Plan:
    account_id: int
    goal: GoalPlan
    backup: BackupPlan
    low_balance: LowBalanceGoal | None
    facts: tuple
    backup_capped: BackupPlan | None = None


@lru_cache(maxsize=None)
def _lean_above_fixed(account_id):
    """Spending above bills, insurance and loan payments in the account's lowest quarter of months."""
    x = get_dataset().rows_by_account[account_id]
    return float((x.money_out - x.household_bills - x.insurance - x.loan_payments).quantile(LEAN_QUANTILE))


def _savings_path(buffer, monthly, months):
    rows = min(MAX_PATH_ROWS, months)
    points = sorted({math.ceil(k * months / rows) for k in range(1, rows + 1)})
    return tuple(PathPoint(m, buffer + m * monthly) for m in points)


def _goal(p, target_months, surplus_share, horizon):
    x = get_dataset().rows_by_account[p.account_id]
    actual = float((x.money_in - x.money_out).tail(12).mean())
    surplus = p.I - p.S
    flexible = max(p.S - p.current_fixed_costs, 0.0)
    below = max(-p.B, 0.0)
    common = dict(target_months=target_months, current_buffer=p.B, surplus=surplus, surplus_share=surplus_share,
                  below_zero_by=below, flexible_spending=flexible, actual_change_last_12=actual)
    if p.S <= 0:
        return GoalPlan(state="no_regular_spending", target_amount=None, still_needed=None, months_covered=None, monthly_amount=0.0,
                        months_to_goal=None, reaches_within_horizon=False, cut_to_break_even=None, cut_to_reach_in_horizon=None,
                        cut_is_possible=None, savings_path=(), **common)
    target = target_months * p.S
    needed = target - p.B
    if needed <= 0:
        return GoalPlan(state="already_there", target_amount=target, still_needed=0.0, months_covered=p.B / p.S, monthly_amount=0.0,
                        months_to_goal=0, reaches_within_horizon=True, cut_to_break_even=None, cut_to_reach_in_horizon=None,
                        cut_is_possible=None, savings_path=(), **common)
    if surplus > 0:
        monthly = surplus * surplus_share
        months = math.ceil(needed / monthly)
        return GoalPlan(state="on_track", target_amount=target, still_needed=needed, months_covered=max(p.B, 0.0) / p.S, monthly_amount=monthly,
                        months_to_goal=months, reaches_within_horizon=months <= horizon, cut_to_break_even=None, cut_to_reach_in_horizon=None,
                        cut_is_possible=None, savings_path=_savings_path(p.B, monthly, months), **common)
    return GoalPlan(state="no_surplus", target_amount=target, still_needed=needed, months_covered=max(p.B, 0.0) / p.S, monthly_amount=0.0,
                    months_to_goal=None, reaches_within_horizon=False, cut_to_break_even=-surplus, cut_to_reach_in_horizon=-surplus + needed / horizon,
                    cut_is_possible=-surplus <= flexible, savings_path=(), **common)


def _low_balance(p, surplus_share):
    if not p.running_loan:
        return None
    top_up = max(p.P - p.lowest_balance, 0.0)
    monthly = max(p.I - p.S, 0.0) * surplus_share
    months = 0 if top_up == 0 else (math.ceil(top_up / monthly) if monthly > 0 else None)
    return LowBalanceGoal(p.P, p.lowest_balance, p.lowest_balance >= p.P, top_up, months)


def _cut_to_last(buffer_left, gap_during, gap_after, benefit, months):
    """Smallest monthly cut that keeps the balance at or above 0 through the months asked."""
    during = months if benefit is None else min(benefit, months)
    spent_at_end = gap_during * during + gap_after * (months - during)
    return max((gap_during * during - buffer_left) / during, (spent_at_end - buffer_left) / months, 0.0)


def _backup(p, shock, through_months, use_cap=False):
    r = apply_shock(p.account_id, shock, through_months=through_months)
    income, gap, runway, duration = r.income_after, r.gap, r.runway, r.duration
    if use_cap:
        c = r.ei_capped
        income, gap, runway, duration = c.income_after, c.gap, c.runway, c.duration
    months = duration.months_asked if duration else None
    gap_during, gap_after, benefit = shock_gaps(p, shock, r.spending_after, income)
    left = r.buffer_left

    flexible = max(p.S + min(shock.other_spending_change, 0.0) - p.current_fixed_costs, 0.0)
    share = min(p.current_fixed_costs / p.S, 1.0) if p.S > 0 else None
    close_gap = max(gap, 0.0)
    cut_last = _cut_to_last(left, gap_during, gap_after, benefit, months) if months is not None and left > 0 else None
    needed = cut_last if cut_last is not None else close_gap
    cover = max(-left, 0.0)
    surplus = p.I - p.S

    if r.no_shock:
        state = "no_shock"
    elif left <= 0:
        state = "no_buffer"
    elif needed <= 0:
        state = "no_cuts_needed"
    elif months is not None and needed > flexible:
        state = "cuts_not_enough"
    else:
        state = "cuts_needed"

    steps = () if state in ("no_shock", "no_cuts_needed") else _steps(p, left, gap, r.spending_after, flexible, needed, cover)
    saved = sum(s.monthly_saving for s in steps)
    after_left = left + sum(s.one_time_amount for s in steps)
    makes_after = None
    if months is not None:
        makes_after = duration_path(after_left, gap_during - saved, gap_after - saved, benefit, months, "no_income").verdict == "makes_it"
    line = None
    if p.P > 0:
        line = 0.0 if left <= p.P else (round((left - p.P) / gap, 1) if gap > 0 else None)

    return BackupPlan(
        state=state, shock=shock, through_months=months, runway_before=runway,
        runway_after_steps=steps[-1].runway_after if steps else runway,
        makes_it_before=None if duration is None else duration.verdict == "makes_it", makes_it_after_steps=makes_after,
        fixed_costs=p.current_fixed_costs + r.bills_added, flexible_spending=flexible, fixed_share_of_spending=share,
        fixed_exceeds_spending=p.S > 0 and p.current_fixed_costs > p.S,
        cut_to_last=cut_last, cut_to_last_share_of_spending=cut_last / p.S if cut_last is not None and p.S > 0 else None,
        cut_to_last_share_of_flexible=cut_last / flexible if cut_last is not None and flexible > 0 else None,
        cut_to_close_gap=close_gap, cut_is_possible=needed <= flexible, runway_if_all_flexible_cut=runway_from(left, gap - flexible),
        cover_needed=cover, months_to_cover=math.ceil(cover / surplus) if cover > 0 and surplus > 0 else None,
        months_to_low_balance_line=line, steps=steps, income_basis="ei_weekly_max" if use_cap else "flat")


def _steps(p, left, gap, spending_after, flexible, needed, cover):
    steps = []

    def add(code, action, saving, one_time=0.0, needs_agreement=False):
        nonlocal left, gap
        before = runway_from(left, gap)
        left += one_time
        gap -= saving
        after = runway_from(left, gap)
        adds = round(after.months - before.months, 1) if after.months is not None and before.months is not None else None
        steps.append(BackupStep(len(steps) + 1, code, action, saving, one_time, needs_agreement, before, after, adds))

    def saved():
        return sum(s.monthly_saving for s in steps)

    if cover > 0:
        add("cover_buffer", f"Find {money(cover)} to bring the balance back up to $0. Until then, runway is 0 months.", 0.0, cover)

    orders = sum(o.amount for o in p.standing_orders if o.purpose == "other")
    from_orders = min(orders, flexible)
    if from_orders > 0 and saved() < needed:
        add("cancel_other_orders", f"Cancel the other standing orders, which save {money(from_orders)} a month.", from_orders)

    hidden_bills = max(p.bills_on_standing_orders - p.H, 0.0)
    lean = max(_lean_above_fixed(p.account_id) - hidden_bills, 0.0)
    target_after = max(lean - from_orders, 0.0)
    from_lean = max(flexible - from_orders - target_after, 0.0)
    if from_lean > 0 and saved() < needed:
        add("lean_months", f"Bring other spending down to {money(target_after)} a month, the level of this account's lowest quarter of months. That saves {money(from_lean)} a month.", from_lean)

    rest = flexible - from_orders - from_lean
    if rest > 0 and saved() < needed:
        add("all_flexible", f"Cut the remaining {money(rest)} a month of other spending. This leaves only fixed costs.", rest)

    from_loan = min(p.P, max(spending_after - saved(), 0.0))
    if from_loan > 0 and saved() < needed:
        add("ask_lender", f"Ask the lender to pause the {money(p.P)} loan payment. This needs the lender's agreement.", from_loan, needs_agreement=True)
    return tuple(steps)


def _check_inputs(target_months, surplus_share, horizon_months, through_months):
    def finite(value):
        return not isinstance(value, bool) and isinstance(value, Real) and math.isfinite(value)

    def whole(value, low, high):
        return not isinstance(value, bool) and isinstance(value, Integral) and low <= value <= high

    if not finite(target_months) or target_months <= 0:
        raise InvalidPlanError("target_months", f"target_months must be above 0, not {target_months!r}.")
    if not finite(surplus_share) or not 0 < surplus_share <= 1:
        raise InvalidPlanError("surplus_share", f"surplus_share must be above 0 and at most 1, not {surplus_share!r}.")
    if not whole(horizon_months, 1, MAX_MONTHS):
        raise InvalidPlanError("horizon_months", f"horizon_months must be a whole number from 1 to {MAX_MONTHS}, not {horizon_months!r}.")
    if through_months is not None and not whole(through_months, 1, MAX_MONTHS):
        raise InvalidPlanError("through_months", f"through_months must be a whole number from 1 to {MAX_MONTHS}, not {through_months!r}.")


def make_plan(account_id, shock=None, *, target_months=3.0, surplus_share=1.0, horizon_months=12, through_months=None):
    account_id = parse_account_id(account_id)
    _check_inputs(target_months, surplus_share, horizon_months, through_months)
    p = get_profile(account_id)
    shock = get_preset("job_loss_ei") if shock is None else shock
    goal = _goal(p, float(target_months), float(surplus_share), int(horizon_months))
    facts = ()
    if goal.surplus > 0 and goal.actual_change_last_12 <= 0:
        facts = (Fact("surplus_not_seen_in_balance",
                      f"Typical money in is {money(goal.surplus)} above typical spending, but over the last 12 months the balance changed by {money(goal.actual_change_last_12)} a month on average. Treat the savings figure as the most this could be."),)
    elif goal.surplus < 0 and goal.actual_change_last_12 > 0:
        facts = (Fact("balance_rose_despite_gap",
                      f"Typical spending is {money(-goal.surplus)} above typical money in, but over the last 12 months the balance rose {money(goal.actual_change_last_12)} a month on average. Typical months can overstate the gap, so the cut needed may be smaller."),)
    capped = None
    if shock.active_cut is not None and shock.income_cut.ei_weekly_max is not None:
        capped = _backup(p, shock, through_months, use_cap=True)
    return Plan(account_id, goal, _backup(p, shock, through_months), _low_balance(p, float(surplus_share)), facts, capped)
