"""Make a plan: a goal plan before any shock, and a backup plan if the shock hits. Every figure comes from the account."""
import math
from dataclasses import dataclass
from numbers import Integral, Real

from .data import get_dataset
from .errors import InvalidPlanError
from .formulas import Runway, money, runway_from
from .profile import get_profile, parse_account_id
from .rates import LEAN_QUANTILE, duration_with_loan_end, lean_above_fixed, loan_end
from .shock import MAX_MONTHS, DurationResult, Fact, Shock, apply_shock, duration_path, get_preset, shock_gaps

MAX_PATH_ROWS = 6


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
    headline: "GoalAtRate | None" = None      # D7: the goal at the actual 12-month change (ours), shown first
    judges: "GoalAtRate | None" = None        # the same at I - S; mirrors the flat fields above


@dataclass(frozen=True)
class GoalAtRate:
    rate: str                         # "actual" (headline, ours) or "judges" (I - S)
    monthly: float                    # the rate, signed
    state: str                        # the GoalPlan.state codes
    monthly_amount: float             # monthly * surplus_share when monthly > 0, else 0
    months_to_goal: int | None
    reaches_within_horizon: bool
    cut_to_break_even: float | None
    cut_to_reach_in_horizon: float | None
    cut_is_possible: bool | None


@dataclass(frozen=True)
class LoanEndCheck:
    """Ours (RU-28, ADR 0006). The backup plan's month-by-month check with the gap falling at the payoff month."""
    payoff_month: int
    monthly_drop: float               # LoanEnd.bump_judges: the part of P inside S and so inside the shocked gap
    scheduled_only: bool              # status D
    reason: str                       # applies | after_months | not_in_spending | no_length | no_shock
    before: DurationResult | None     # the shock alone, counting the loan end
    after_steps: DurationResult | None    # the same after the steps; drop 0 if an ask_lender step already pauses P
    makes_it_before: bool | None
    makes_it_after_steps: bool | None


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
    loan_end: LoanEndCheck | None = None    # ours (ADR 0006); set whenever the loan is running


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


def _savings_path(buffer, monthly, months):
    rows = min(MAX_PATH_ROWS, months)
    points = sorted({math.ceil(k * months / rows) for k in range(1, rows + 1)})
    return tuple(PathPoint(m, buffer + m * monthly) for m in points)


def _goal_at(p, rate, monthly, target_months, surplus_share, horizon):
    flexible = max(p.S - p.current_fixed_costs, 0.0)
    if p.S <= 0:
        return GoalAtRate(rate, monthly, "no_regular_spending", 0.0, None, False, None, None, None)
    needed = target_months * p.S - p.B
    if needed <= 0:
        return GoalAtRate(rate, monthly, "already_there", 0.0, 0, True, None, None, None)
    if monthly > 0:
        amount = monthly * surplus_share
        months = math.ceil(needed / amount)
        return GoalAtRate(rate, monthly, "on_track", amount, months, months <= horizon, None, None, None)
    return GoalAtRate(rate, monthly, "no_surplus", 0.0, None, False, -monthly, -monthly + needed / horizon, -monthly <= flexible)


def _goal(p, target_months, surplus_share, horizon):
    x = get_dataset().rows_by_account[p.account_id]
    actual = float((x.money_in - x.money_out).tail(12).mean())
    surplus = p.I - p.S
    judges = _goal_at(p, "judges", surplus, target_months, surplus_share, horizon)
    headline = _goal_at(p, "actual", actual, target_months, surplus_share, horizon)
    flexible = max(p.S - p.current_fixed_costs, 0.0)
    target = target_months * p.S if p.S > 0 else None
    needed = None if target is None else target - p.B
    path = ()
    if judges.state == "on_track":
        path = _savings_path(p.B, judges.monthly_amount, judges.months_to_goal)
    return GoalPlan(
        state=judges.state, target_months=target_months, target_amount=target,
        current_buffer=p.B, still_needed=None if needed is None else 0.0 if judges.state == "already_there" else needed,
        months_covered=None if p.S <= 0 else p.B / p.S if judges.state == "already_there" else max(p.B, 0.0) / p.S,
        surplus=surplus, surplus_share=surplus_share, monthly_amount=judges.monthly_amount, months_to_goal=judges.months_to_goal,
        reaches_within_horizon=judges.reaches_within_horizon, below_zero_by=max(-p.B, 0.0),
        cut_to_break_even=judges.cut_to_break_even, cut_to_reach_in_horizon=judges.cut_to_reach_in_horizon,
        flexible_spending=flexible, cut_is_possible=judges.cut_is_possible, savings_path=path,
        actual_change_last_12=actual, headline=headline, judges=judges)


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
    check = _loan_end_check(p, r, shock, steps, left, gap_during, gap_after, benefit, months, duration, saved, after_left)
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
        months_to_low_balance_line=line, steps=steps, income_basis="ei_weekly_max" if use_cap else "flat", loan_end=check)


def _loan_end_check(p, r, shock, steps, left, gap_during, gap_after, benefit, months, duration, saved, after_left):
    if not p.running_loan:
        return None
    end = loan_end(p.account_id)
    if r.no_shock:
        reason = "no_shock"
    elif months is None:
        reason = "no_length"
    elif not end.in_typical_spending:
        reason = "not_in_spending"
    elif end.payoff_month > months:
        reason = "after_months"
    else:
        reason = "applies"
    before = after = None
    if reason == "applies":
        ends = duration.after_ends or "no_income"
        drop = 0.0 if any(s.code == "ask_lender" for s in steps) else end.bump_judges
        before = duration_with_loan_end(left, gap_during, gap_after, benefit, months, ends, payoff_month=end.payoff_month, monthly_drop=end.bump_judges)
        after = duration_with_loan_end(after_left, gap_during - saved, gap_after - saved, benefit, months, ends, payoff_month=end.payoff_month, monthly_drop=drop)
    return LoanEndCheck(end.payoff_month, end.bump_judges, end.scheduled_only, reason, before, after,
                        None if before is None else before.verdict == "makes_it", None if after is None else after.verdict == "makes_it")


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
        add("cancel_other_orders", f"Cancel the other standing orders, if these aren't rent or bills. That saves {money(from_orders)} a month.", from_orders)

    hidden_bills = max(p.bills_on_standing_orders - p.H, 0.0)
    lean = max(lean_above_fixed(p.account_id) - hidden_bills, 0.0)
    target_after = max(lean - from_orders, 0.0)
    from_lean = max(flexible - from_orders - target_after, 0.0)
    if from_lean > 0 and saved() < needed:
        add("lean_months", f"Bring other spending down to {money(target_after)} a month, the level of this account's lowest quarter of months. That saves {money(from_lean)} a month.", from_lean)

    rest = flexible - from_orders - from_lean
    if rest > 0 and saved() < needed:
        add("all_flexible", f"Cut the remaining {money(rest)} a month of other spending, if it isn't rent or bills. This leaves only fixed costs.", rest)

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
