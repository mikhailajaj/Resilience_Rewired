"""Our monthly saving rates and a running loan's scheduled end. Beside the judges' numbers, never in place of them (ADR 0006, ADR 0007)."""
import math
from dataclasses import dataclass, replace
from functools import lru_cache

from .data import get_dataset
from .profile import account_flows, get_profile, parse_account_id
from .shock import MAX_MONTHS, DurationResult, duration_path

LEAN_QUANTILE = 0.25                        # moved here from plan.py; plan.py re-exports it
RATE_KEYS = ("actual", "judges", "lean")    # display order; "actual" is the headline (D7, RU-23)


@dataclass(frozen=True)
class LoanEnd:
    status: str                 # "C" or "D" (running)
    payment: float              # P
    payoff_month: int           # N = (loan_start year*12 + month + duration_months) - (last data year*12 + month); 1..60 here
    scheduled_only: bool        # status D: N is the schedule, not a certainty (P.loan_d)
    in_typical_spending: bool   # profile.loan_median > 0. False on the 197 recent loans (D12). Sets the D12 line and bump_judges only
    bump_judges: float          # LE-2: min(P, loan_median); exactly 0.0 on the 197
    bump_actual: float          # LE-1: min(P, mean loan_payments over the last actual_months rows); > 0 on all 448, the 197 included
    bump_lean: float            # LE-3: min(S, Fx + P + L) - min(S, Fx + L), Fx = current_fixed_costs - P, L = SavingRates.lean_above; 0..P
    paid_rows: int              # k: rows of the last actual_months with loan_payments > 0 (ADR 0007 known limit; 156 of the 197 have k < 12)


@dataclass(frozen=True)
class SavingRate:
    key: str                    # one of RATE_KEYS
    monthly: float              # signed $ a month, before the payoff month
    loan_bump: float            # LoanEnd.bump_<key>, added from the payoff month on; 0.0 with no running loan
    is_ours: bool               # actual and lean True; judges False
    is_headline: bool           # actual only

    def at(self, month: int, payoff_month: int | None) -> float:
        """Saving in month `month` (1-based): monthly, plus loan_bump once month >= payoff_month."""
        if payoff_month is not None and month >= payoff_month:
            return self.monthly + self.loan_bump
        return self.monthly


@dataclass(frozen=True)
class SavingRates:
    account_id: int
    actual: SavingRate          # account_flows(id).change_last_12, equal to GoalPlan.actual_change_last_12
    judges: SavingRate          # I - S
    lean: SavingRate            # I - lean_spending (OI-14 default)
    lean_spending: float        # S - lean_cut
    lean_cut: float             # max(flexible_spending - lean_above, 0): equals the backup's orders + lean_months saving (2,864 on 20111)
    lean_above: float           # max(lean_above_fixed(id) - max(bills_on_standing_orders - H, 0), 0)
    flexible_spending: float    # max(S - current_fixed_costs, 0)
    fixed_costs: float          # current_fixed_costs
    loan_end: LoanEnd | None    # None without a running loan
    actual_months: int          # rows behind the actual rate: min(12, n_months)

    @property
    def ordered(self) -> tuple[SavingRate, SavingRate, SavingRate]:
        """(actual, judges, lean): the headline first."""
        return (self.actual, self.judges, self.lean)


@lru_cache(maxsize=None)
def lean_above_fixed(account_id: int) -> float:
    """Spending above bills, insurance and loan payments in the lowest LEAN_QUANTILE of months. Cached. Same value as the old plan._lean_above_fixed."""
    x = get_dataset().rows_by_account[account_id]
    return float((x.money_out - x.household_bills - x.insurance - x.loan_payments).quantile(LEAN_QUANTILE))


def _month_index(text):
    year, month = str(text)[:7].split("-")
    return int(year) * 12 + int(month)


def _lean_above(p):
    return max(lean_above_fixed(p.account_id) - max(p.bills_on_standing_orders - p.H, 0.0), 0.0)


@lru_cache(maxsize=None)
def _loan_end(account_id):
    p = get_profile(account_id)
    if not p.running_loan:
        return None
    loan = p.loan
    months = min(12, p.n_months)
    paid = get_dataset().rows_by_account[account_id].loan_payments.tail(months)
    fixed_without = p.current_fixed_costs - p.P
    lean_above = _lean_above(p)
    return LoanEnd(
        status=loan.status, payment=p.P,
        payoff_month=_month_index(loan.start) + loan.duration_months - _month_index(p.last_month),
        scheduled_only=loan.status == "D",
        in_typical_spending=p.loan_median > 0,
        bump_judges=min(p.P, p.loan_median),
        bump_actual=min(p.P, float(paid.mean())),
        bump_lean=min(p.S, fixed_without + p.P + lean_above) - min(p.S, fixed_without + lean_above),
        paid_rows=int((paid > 0).sum()))


def loan_end(account_id) -> LoanEnd | None:
    """The running loan's scheduled end and the rise in each rate from that month (LE-1 to LE-4). None without a running loan."""
    return _loan_end(parse_account_id(account_id))


def saving_rates(account_id) -> SavingRates:
    """parse_account_id first, then cached per id."""
    return _saving_rates(parse_account_id(account_id))


@lru_cache(maxsize=None)
def _saving_rates(account_id):
    p = get_profile(account_id)
    flows = account_flows(account_id)
    end = _loan_end(account_id)
    flexible = max(p.S - p.current_fixed_costs, 0.0)
    lean_above = _lean_above(p)
    lean_cut = max(flexible - lean_above, 0.0)
    lean_spending = p.S - lean_cut
    bump = (lambda key: 0.0) if end is None else (lambda key: getattr(end, f"bump_{key}"))
    return SavingRates(
        account_id=account_id,
        actual=SavingRate("actual", flows.change_last_12, bump("actual"), True, True),
        judges=SavingRate("judges", p.I - p.S, bump("judges"), False, False),
        lean=SavingRate("lean", p.I - lean_spending, bump("lean"), True, False),
        lean_spending=lean_spending, lean_cut=lean_cut, lean_above=lean_above, flexible_spending=flexible,
        fixed_costs=p.current_fixed_costs, loan_end=end, actual_months=min(12, p.n_months))


def duration_with_loan_end(buffer_left: float, gap_during: float, gap_after: float, benefit_months: int | None, months_asked: int,
                           after_ends: str, *, payoff_month: int | None, monthly_drop: float) -> DurationResult:
    """shock.duration_path with the gap smaller by monthly_drop from month payoff_month on. Returns shock.DurationResult.
    Returns duration_path(...) itself (same object fields, bit for bit) when payoff_month is None, monthly_drop <= 0
    or payoff_month > months_asked."""
    base = duration_path(buffer_left, gap_during, gap_after, benefit_months, months_asked, after_ends)
    if payoff_month is None or monthly_drop <= 0 or payoff_month > months_asked:
        return base

    def balance(t):
        if benefit_months is None or t <= benefit_months:
            plain = buffer_left - gap_during * t
        else:
            plain = buffer_left - gap_during * benefit_months - gap_after * (t - benefit_months)
        return float(plain + monthly_drop * max(0, t - payoff_month + 1))

    path = tuple(balance(t) for t in range(months_asked + 1))
    makes_it = buffer_left > 0 and min(path) >= 0
    lasts = 0.0 if buffer_left <= 0 else None
    for t in range(1, MAX_MONTHS + 1):
        if lasts is not None:
            break
        if balance(t) < 0:
            before = balance(t - 1)
            lasts = (t - 1) + before / (before - balance(t))
    if makes_it:
        runs_out, short = None, None
    else:
        within = 0.0 if lasts is None else lasts
        runs_out = 0 if buffer_left <= 0 else math.floor(within) + 1
        short = round(months_asked - within, 1)
    return replace(
        base, verdict="makes_it" if makes_it else "runs_out", runs_out_in_month=runs_out, months_short=short,
        money_lasts_months=None if lasts is None or lasts > MAX_MONTHS else round(lasts, 1),
        balance_end=path[-1], lowest_balance=min(path), shortfall_at_end=max(-path[-1], 0.0), balance_by_month=path)
