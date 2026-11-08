"""Take a shock. The standard (judges') runway follows the README exactly; everything else sits beside it."""
import math
from dataclasses import dataclass, replace
from numbers import Integral, Real

from .data import LAST_DATA_MONTH, get_dataset
from .errors import InvalidShockError
from .formulas import Runway, money, runway_from
from .profile import get_profile, parse_account_id
from .response import spending_response

EI_KEEP = 0.55
EI_WEEKLY_MAX_2026 = 729.0
EI_WEEKLY_MAX_2026_SOURCE = "https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/benefit-amount.html (2026 maximum, page dated 2026-10-19)"
WEEKS_PER_MONTH = 52 / 12
MAX_MONTHS = 120
AFTER_ENDS = ("no_income", "income_returns")


def _number(field, value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise InvalidShockError(field, f"{field} must be a finite number, not {value!r}.")
    value = float(value)
    if (low is not None and value < low) or (high is not None and value > high):
        limits = f"at least {low}" if high is None else f"from {low} to {high}"
        raise InvalidShockError(field, f"{field} must be {limits}, not {value}.")
    return value


def _whole(field, value, low, high):
    if isinstance(value, bool) or not isinstance(value, Integral) or not low <= value <= high:
        raise InvalidShockError(field, f"{field} must be a whole number from {low} to {high}, not {value!r}.")
    return int(value)


@dataclass(frozen=True)
class IncomeCut:
    keep_fraction: float = EI_KEEP
    months: int | None = None
    after_ends: str = "no_income"
    ei_weekly_max: float | None = None   # dollars a week. None is off, which is the standard (judges') flat rate

    def __post_init__(self):
        if self.ei_weekly_max is not None:
            object.__setattr__(self, "ei_weekly_max", _number("ei_weekly_max", self.ei_weekly_max, 0))
        object.__setattr__(self, "keep_fraction", _number("keep_fraction", self.keep_fraction, 0, 1))
        if self.months is not None:
            object.__setattr__(self, "months", _whole("months", self.months, 1, MAX_MONTHS))
        if self.after_ends not in AFTER_ENDS:
            raise InvalidShockError("after_ends", f"after_ends must be one of {AFTER_ENDS}, not {self.after_ends!r}.")


@dataclass(frozen=True)
class Shock:
    income_cut: IncomeCut | None = None
    bills_increase_pct: float = 0.0
    other_spending_change: float = 0.0
    one_off_dollars: float = 0.0
    one_off_spending_multiple: float = 0.0
    start_month: int | None = None

    def __post_init__(self):
        if self.income_cut is not None and not isinstance(self.income_cut, IncomeCut):
            raise InvalidShockError("income_cut", "income_cut must be an IncomeCut or None.")
        object.__setattr__(self, "bills_increase_pct", _number("bills_increase_pct", self.bills_increase_pct, 0))
        object.__setattr__(self, "other_spending_change", _number("other_spending_change", self.other_spending_change))
        object.__setattr__(self, "one_off_dollars", _number("one_off_dollars", self.one_off_dollars, 0))
        object.__setattr__(self, "one_off_spending_multiple", _number("one_off_spending_multiple", self.one_off_spending_multiple, 0))
        if self.start_month is not None:
            object.__setattr__(self, "start_month", _whole("start_month", self.start_month, 1, 12))

    @property
    def active_cut(self):
        """The income cut, unless it keeps all the income."""
        return self.income_cut if self.income_cut is not None and self.income_cut.keep_fraction < 1 else None

    @property
    def changes_nothing(self):
        return (self.active_cut is None and self.bills_increase_pct == 0 and self.other_spending_change == 0
                and self.one_off_dollars == 0 and self.one_off_spending_multiple == 0)


@dataclass(frozen=True)
class Preset:
    key: str
    name: str
    twist: str
    shock: Shock


PRESETS = (
    Preset("job_loss_ei", "Laid off, EI 55%", "This customer was laid off. EI pays 55% of their usual income for 6 months. Do they make it?",
           Shock(income_cut=IncomeCut(EI_KEEP, 6))),
    Preset("furnace_repair", "Furnace dies", "The furnace dies, and the repair costs a full month of their typical spending.",
           Shock(one_off_spending_multiple=1)),
    Preset("job_loss_bills", "Laid off + bills up 15%", "They lose their job (EI at 55%) and their household bills go up 15% in the same month.",
           Shock(income_cut=IncomeCut(EI_KEEP, 6), bills_increase_pct=15)),
    Preset("bills_up", "Rent or bills up", "Rent or household bills go up 15%.", Shock(bills_increase_pct=15)),
    Preset("no_shock", "Reset (no shock)", "No shock.", Shock()),
)
_CUT_FIELDS = ("keep_fraction", "months", "after_ends", "ei_weekly_max")
_SHOCK_FIELDS = ("bills_increase_pct", "other_spending_change", "one_off_dollars", "one_off_spending_multiple", "start_month")


def list_presets():
    return PRESETS


def get_preset(key, **overrides):
    preset = next((p for p in PRESETS if p.key == key), None)
    if preset is None:
        raise InvalidShockError("key", f"There's no preset called {key!r}. Use one of {[p.key for p in PRESETS]}.")
    shock = preset.shock
    cut_changes = {k: v for k, v in overrides.items() if k in _CUT_FIELDS}
    shock_changes = {k: v for k, v in overrides.items() if k in _SHOCK_FIELDS}
    unknown = set(overrides) - set(cut_changes) - set(shock_changes)
    if unknown:
        raise InvalidShockError(sorted(unknown)[0], f"Unknown shock setting: {sorted(unknown)[0]}.")
    if cut_changes:
        shock_changes["income_cut"] = replace(shock.income_cut or IncomeCut(), **cut_changes)
    return replace(shock, **shock_changes)


@dataclass(frozen=True)
class Figures:
    income: float
    spending: float
    buffer: float
    gap: float
    runway: Runway


@dataclass(frozen=True)
class Fact:
    code: str
    message: str


@dataclass(frozen=True)
class DurationResult:
    months_asked: int
    verdict: str
    runs_out_in_month: int | None
    months_short: float | None
    money_lasts_months: float | None
    balance_end: float
    lowest_balance: float
    shortfall_at_end: float
    balance_by_month: tuple
    benefit_months: int | None
    after_ends: str | None
    assumption_applied: bool
    assumption: str


@dataclass(frozen=True)
class ExtraFigure:
    label: str
    applies: bool
    reason: str
    runway: Runway | None
    spending_after: float | None
    is_illustration: bool
    note: str
    metadata: dict


@dataclass(frozen=True)
class CappedFigure:
    """Runway with the EI weekly maximum. Our addition, beside the standard (judges') number."""
    label: str
    available: bool
    reason: str               # max_applied, max_not_reached or no_income_cut
    switched_on: bool         # the caller supplied a maximum
    weekly_max: float
    weekly_max_source: str    # supplied or default
    monthly_max: float
    max_applied: bool
    income_after: float | None
    effective_share_of_income: float | None
    gap: float | None
    runway: Runway | None
    duration: DurationResult | None
    note: str


@dataclass(frozen=True)
class ShockResult:
    account_id: int
    shock: Shock
    no_shock: bool
    before: Figures
    after: Figures
    one_off: float
    bills_added: float
    runway: Runway
    buffer_left: float
    gap: float
    income_after: float
    spending_after: float
    verdict_case: str
    duration: DurationResult | None
    bills_on_standing_orders: ExtraFigure
    if_you_adjust: ExtraFigure
    ei_capped: CappedFigure
    facts: tuple


_ASSUME_NO_INCOME = "After the lower income ends, we assume no income, because a benefit ending doesn't mean a new job has started. Spending stays at its shocked level."
_ASSUME_RETURNS = "After the lower income ends, we assume income returns to its typical level. Spending stays at its shocked level."
_ASSUME_OPEN = "The lower income is assumed to last the whole period."


def _money_lasts(buffer_left, gap_during, gap_after, benefit_months):
    """Months until the balance goes below zero on this path, or None if it never does."""
    if buffer_left <= 0:
        return 0.0
    if gap_during > 0:
        t = buffer_left / gap_during
        if benefit_months is None or t <= benefit_months:
            return t
    if benefit_months is None:
        return None
    if gap_after > 0:
        return benefit_months + (buffer_left - gap_during * benefit_months) / gap_after
    return None


def duration_path(buffer_left, gap_during, gap_after, benefit_months, months_asked, after_ends):
    """Answers "do they make it through N months?". The README runway isn't involved."""
    def balance(t):
        if benefit_months is None or t <= benefit_months:
            return buffer_left - gap_during * t
        return buffer_left - gap_during * benefit_months - gap_after * (t - benefit_months)

    path = tuple(float(balance(t)) for t in range(months_asked + 1))
    makes_it = buffer_left > 0 and min(path) >= 0
    lasts = _money_lasts(buffer_left, gap_during, gap_after, benefit_months)
    if makes_it:
        runs_out, short = None, None
    else:
        lasts_within = 0.0 if lasts is None else lasts
        runs_out = 0 if buffer_left <= 0 else math.floor(lasts_within) + 1
        short = round(months_asked - lasts_within, 1)
    if benefit_months is None:
        assumption = _ASSUME_OPEN
    else:
        assumption = _ASSUME_NO_INCOME if after_ends == "no_income" else _ASSUME_RETURNS
    return DurationResult(
        months_asked=months_asked, verdict="makes_it" if makes_it else "runs_out", runs_out_in_month=runs_out, months_short=short,
        money_lasts_months=None if lasts is None or lasts > MAX_MONTHS else round(lasts, 1),
        balance_end=path[-1], lowest_balance=min(path), shortfall_at_end=max(-path[-1], 0.0), balance_by_month=path,
        benefit_months=benefit_months, after_ends=None if benefit_months is None else after_ends,
        assumption_applied=benefit_months is not None and months_asked > benefit_months, assumption=assumption)


def _capped_figure(p, shock, spending_after, buffer_left, months):
    """Always worked out when income is cut, so the UI can show it without a second call."""
    cut = shock.active_cut
    supplied = shock.income_cut.ei_weekly_max if shock.income_cut is not None else None
    weekly = EI_WEEKLY_MAX_2026 if supplied is None else supplied
    monthly = weekly * WEEKS_PER_MONTH
    common = dict(label="Runway with the EI weekly maximum", switched_on=supplied is not None, weekly_max=weekly,
                  weekly_max_source="default" if supplied is None else "supplied", monthly_max=monthly)
    if cut is None:
        return CappedFigure(available=False, reason="no_income_cut", max_applied=False, income_after=None, effective_share_of_income=None,
                            gap=None, runway=None, duration=None, note="There's no income cut in this shock, so the maximum has nothing to limit.", **common)
    flat = cut.keep_fraction * p.I
    income = min(flat, monthly)
    applied = flat > monthly
    gap = spending_after - income
    gap_during, gap_after, benefit = shock_gaps(p, shock, spending_after, income)
    duration = None if months is None else duration_path(buffer_left, gap_during, gap_after, benefit, months, cut.after_ends)
    note = (f"Income is held at {money(monthly)} a month, the {money(weekly)} weekly maximum. This treats typical money in as insurable earnings."
            if applied else f"{money(flat)} a month is within the {money(weekly)} weekly maximum, so this equals the standard (judges') number.")
    return CappedFigure(available=True, reason="max_applied" if applied else "max_not_reached", max_applied=applied, income_after=income,
                        effective_share_of_income=income / p.I if p.I > 0 else None, gap=gap, runway=runway_from(buffer_left, gap),
                        duration=duration, note=note, **common)


def shock_gaps(profile, shock, spending_after, income_after):
    """(gap while the lower income lasts, gap after it ends, its length or None)."""
    cut = shock.active_cut
    gap = spending_after - income_after
    if cut is None or cut.months is None:
        return gap, gap, None
    income_later = 0.0 if cut.after_ends == "no_income" else profile.I
    return gap, spending_after - income_later, cut.months


def _bills_figure(p, shock, spending_after, income_after, buffer_left):
    label = "Bills shock using standing orders"
    if shock.bills_increase_pct == 0:
        return ExtraFigure(label, False, "no_bills_shock", None, None, False, "There's no bills increase in this shock.", {})
    if not p.bills_hidden:
        return ExtraFigure(label, False, "bills_not_missing", None, None, False, "Standing orders don't show more bills than H, so the standard (judges') figure already fits.", {})
    basis = max(p.H, p.bills_on_standing_orders)
    spending = max(spending_after + shock.bills_increase_pct / 100 * (basis - p.H), 0.0)
    note = f"Uses {money(basis)} of bills on standing orders instead of H of {money(p.H)}. Shown beside the standard (judges') number, not in place of it."
    return ExtraFigure(label, True, "bills_missing_from_h", runway_from(buffer_left, spending - income_after), spending, False, note, {"bills_basis": basis})


def _adjust_figure(p, spending_after, income_after, buffer_left):
    label = "If you adjust"
    response = spending_response()
    statement = "This is an illustration, not a forecast or a measured result. It applies a spending response seen on cash-only accounts."
    metadata = {"illustration": True, "statement": statement, "evidence": response.evidence, "tier": None, "response_per_dollar": None, "events_in_tier": None}

    def not_applicable(reason, note):
        return ExtraFigure(label, False, reason, None, None, True, note, metadata)

    if p.income_type == "Pension":
        return not_applicable("pension_income", "The evidence comes from cash-only accounts, so this doesn't apply to pension income.")
    if p.income_type == "Transfers":
        return not_applicable("transfers_income", "The evidence comes from cash-only accounts, so this doesn't apply to transfer income.")
    lost = p.I - income_after
    if lost <= 0:
        return not_applicable("no_income_lost", "This shock doesn't lower income, so there's no spending response to apply.")
    if p.S <= 0:
        return not_applicable("no_typical_spending", "Needs typical spending above $0.")
    tier = response.tier_for(p.B / p.S)
    spending = max(spending_after - tier.response_per_dollar * lost, 0.0)
    note = f"Illustration: spending falls by {tier.response_per_dollar:.2f} per $1 of lost income, as seen on accounts with a buffer of {tier.name.lower()}."
    return ExtraFigure(label, True, "cash_only_response", runway_from(buffer_left, spending - income_after), spending, True, note,
                       {**metadata, "tier": tier.name, "response_per_dollar": tier.response_per_dollar, "events_in_tier": tier.events})


def _touches_january(start_month, months):
    return any((start_month - 1 + k) % 12 == 0 for k in range(months))


def _facts(p, shock, *, bills_added, one_off, buffer_left, raw_spending, months, capped):
    out = []

    def add(code, message):
        out.append(Fact(code, message))

    cut = shock.active_cut
    if p.I == 0 and p.S == 0:
        add("little_activity", "Almost no activity on this account, so these numbers say little about it.")
    if cut is not None and p.income_type == "Pension":
        add("layoff_doesnt_fit_pension", "Pension income: a layoff wouldn't stop this. The numbers apply the layoff as asked.")
    if cut is not None and p.I == 0:
        add("income_cut_no_income", "No regular money in, so a lower income changes nothing here.")
    if capped.switched_on and capped.max_applied:
        add("ei_weekly_max_applied", f"The EI weekly maximum holds income at {money(capped.income_after)} a month, not {money(cut.keep_fraction * p.I)}.")
    if shock.bills_increase_pct > 0 and p.H == 0:
        add("bills_shock_no_bills", "No regular bills visible in H, so this changes nothing in the standard (judges') formula.")
    if shock.bills_increase_pct > 0 and p.bills_hidden:
        add("bills_shock_too_small", f"The standard (judges') bills are {money(p.H)}. Standing orders show {money(p.bills_on_standing_orders)}, so the shock on H is too small.")
    if shock.one_off_spending_multiple > 0 and p.S == 0:
        add("one_off_zero_spending", "Typical spending is $0, so a cost sized in months of spending comes to $0.")
    if p.B <= 0:
        add("no_buffer_before_shock", f"The buffer was already {money(p.B)} before this shock, so runway is 0 whatever the shock.")
    elif buffer_left <= 0:
        add("one_off_exceeds_buffer", f"The one-off cost of {money(one_off)} is more than the buffer of {money(p.B)}.")
    if p.last_month != LAST_DATA_MONTH:
        add("data_stops_early", f"Data stops in {p.last_month}. Figures are as of then.")
    if raw_spending < 0:
        add("spending_floored_at_zero", "This change would take spending below $0, so spending is held at $0.")
    if shock.start_month is not None and _touches_january(shock.start_month, months or 1):
        rows = get_dataset().rows_by_account[p.account_id]
        january = float(rows[rows.month.str.endswith("-01")].money_out.median())
        add("runs_into_january", f"This shock runs into January. This account's typical January spending is {money(january)}, against {money(p.S)} in a typical month.")
    return tuple(out)


def _verdict_case(shock, no_shock, buffer_left, gap, duration):
    if no_shock:
        return "no_shock"
    if buffer_left <= 0:
        return "runway_zero"
    if gap <= 0:
        return "no_shortfall"
    cut = shock.active_cut
    if cut is None:
        return "cost_or_bills_only"
    if cut.months is None and duration is None:
        return "income_cut_open_ended"
    return "income_cut_makes_it" if duration.verdict == "makes_it" else "income_cut_runs_out"


def apply_shock(account_id, shock=None, *, through_months=None):
    account_id = parse_account_id(account_id)
    shock = Shock() if shock is None else shock
    if not isinstance(shock, Shock):
        raise InvalidShockError("shock", "shock must be a Shock or None.")
    if through_months is not None:
        through_months = _whole("through_months", through_months, 1, MAX_MONTHS)
    p = get_profile(account_id)

    # The README formula. Flooring spending at 0 can't change it: the gap is <= 0 either way.
    cut = shock.active_cut
    income_after = cut.keep_fraction * p.I if cut else p.I
    bills_added = shock.bills_increase_pct / 100 * p.H
    raw_spending = p.S + bills_added + shock.other_spending_change
    spending_after = max(raw_spending, 0.0)
    one_off = shock.one_off_dollars + shock.one_off_spending_multiple * p.S
    buffer_left = p.B - one_off
    gap = spending_after - income_after
    runway = runway_from(buffer_left, gap)

    gap_during, gap_after, benefit = shock_gaps(p, shock, spending_after, income_after)
    months = through_months if through_months is not None else (cut.months if cut else None)
    duration = None
    if months is not None:
        duration = duration_path(buffer_left, gap_during, gap_after, benefit, months, cut.after_ends if cut else "no_income")

    no_shock = shock.changes_nothing
    capped = _capped_figure(p, shock, spending_after, buffer_left, months)
    return ShockResult(
        account_id=account_id, shock=shock, no_shock=no_shock,
        before=Figures(p.I, p.S, p.B, p.gap, p.runway),
        after=Figures(income_after, spending_after, buffer_left, gap, runway),
        one_off=one_off, bills_added=bills_added, runway=runway, buffer_left=buffer_left, gap=gap,
        income_after=income_after, spending_after=spending_after,
        verdict_case=_verdict_case(shock, no_shock, buffer_left, gap, duration),
        duration=duration,
        bills_on_standing_orders=_bills_figure(p, shock, spending_after, income_after, buffer_left),
        if_you_adjust=_adjust_figure(p, spending_after, income_after, buffer_left),
        ei_capped=capped,
        facts=_facts(p, shock, bills_added=bills_added, one_off=one_off, buffer_left=buffer_left, raw_spending=raw_spending, months=months, capped=capped),
    )
