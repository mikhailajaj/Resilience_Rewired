"""The plan designer: savings goals, time off and an emergency cost on one month-by-month timeline. Ours throughout (ADR 0008)."""
import math
from dataclasses import dataclass
from numbers import Integral, Real

from .errors import InvalidPlanError
from .formulas import money
from .plan import BackupPlan, make_plan
from .profile import get_profile, parse_account_id
from .rates import RATE_KEYS, SavingRates, duration_with_loan_end, saving_rates
from .shock import LAST_DATA_MONTH, MAX_MONTHS, DurationResult, Fact, Shock, apply_shock

MAX_ITEMS = 4                     # ours; the page sends at most one goal and one time off (MVP)
MAX_INTEREST_PCT = 25.0           # owner-set upper bound for {interest_pct}, % a year; change it here only (the page reads it). NEW-SCOPE-3
MARKER_CODES = ("fund_reached", "goal_reached", "goal_bought", "time_off_start", "time_off_end", "emergency_cost", "loan_paid_off")


@dataclass(frozen=True)
class SavingsGoal:
    name: str                     # {goal_name}: stripped, 1..40 characters; the page sends "goal" when blank
    amount: float                 # {amount} >= 0
    deadline_months: int | None = None    # {deadline_months}: whole 1..120


@dataclass(frozen=True)
class TimeOff:
    months_off: int               # {months_off}: whole 1..120 (RU-29)


@dataclass(frozen=True)
class EmergencyCost:
    cost: float                   # {cost} >= 0 (RU-30)


Item = SavingsGoal | TimeOff


@dataclass(frozen=True)
class PlanRequest:
    items: tuple[Item, ...] = ()            # in tick order (RU-24); 0..MAX_ITEMS
    emergency: EmergencyCost | None = None  # always at month 0 (OI-18)
    target_months: float = 3.0              # J3's fund target (OI-5); same validation as make_plan
    interest_pct: float = 0.0               # % a year, 0..MAX_INTEREST_PCT, default 0 (owner); monthly at /12 on a positive balance only (OI-19, RU-25)


@dataclass(frozen=True)
class Reach:
    """When one item is reached on one rate."""
    rate: str                     # one of RATE_KEYS
    state: str                    # "now" (month 0) | "reached" | "over_cap" | "never", counting the loan end
    month: int | None             # month reached, 0..120; None unless now or reached
    state_no_loan: str            # the same, without the loan end
    month_no_loan: int | None
    cut_to_start: float | None    # -rate.monthly when rate.monthly <= 0 (P.g_cut_start), else None
    cut_to_reach_by_cap: float | None   # -rate.monthly + need / 120 when rate.monthly <= 0, else None (no loan end, no interest)


@dataclass(frozen=True)
class DeadlineAnswer:
    months: int
    need: float                   # max(fund_value + earlier items + amount - (B - cost), 0)
    monthly_needed: float         # need / months when interest is 0; else the smallest level saving that reaches need, to the cent
    headline_rate: float          # rates.actual.monthly
    cut_needed: float             # the cautious cut, without the loan end: max(monthly_needed - headline_rate, 0); shown first
    on_pace: bool                 # cut_needed == 0 (P.g_on_pace)
    flexible_spending: float
    cut_share_of_flexible: float | None   # cut_needed / flexible, None when flexible is 0
    lean_cut: float
    within_lean: bool             # cut_needed <= lean_cut
    over_flexible: bool           # cut_needed > flexible_spending (P.g_cut_over)
    includes_fund: bool           # the fund is still to finish (P.g_fund_first)
    counts_loan_end: bool         # a running loan with payoff_month <= months and rates.actual.loan_bump > 0: the second cut is shown (WL-8)
    payoff_month: int | None      # N when counts_loan_end, else None
    cut_with_loan: float | None   # counting the loan end: max((need - sum(actual.at(t, N) for t in 1..months)) / months, 0);
                                  # with interest, the smallest level cut reaching need by `months` on the with-loan run, to the cent.
                                  # None unless counts_loan_end
    on_pace_with_loan: bool | None    # cut_with_loan == 0; None unless counts_loan_end


@dataclass(frozen=True)
class GoalResult:
    goal: SavingsGoal
    position: int                 # 1-based in request.items
    fund_needed: float            # max(fund_value - (B - cost), 0) when position is 1, else 0.0 (P.g_needed)
    total_needed: float           # fund_needed + amount
    state: str                    # "zero" (amount 0, P.g_zero) | "now" (every rate at month 0, P.g_now) | "planned"
    reach: tuple[Reach, Reach, Reach]     # actual, judges, lean
    deadline: DeadlineAnswer | None


@dataclass(frozen=True)
class TimeOffCheck:
    rate: str
    started_now: bool             # not saved by month 120, so checked from month 0 on B (P.o_now, OI-17)
    start_month: int
    start_balance: float
    duration: DurationResult      # from duration_with_loan_end(start_balance, S, S, m, m, "no_income", ...)
    counts_loan_end: bool         # the payoff falls inside the time off and bump_judges > 0


@dataclass(frozen=True)
class TimeOffResult:
    time_off: TimeOff
    position: int
    amount: float                 # months_off * S (P.o_amount)
    lean_amount: float            # months_off * lean_spending (our estimate)
    reach: tuple[Reach, Reach, Reach]     # saved when the balance >= fund + amount
    checks: tuple[TimeOffCheck, TimeOffCheck, TimeOffCheck]


@dataclass(frozen=True)
class Rebuild:
    rate: str
    to_buffer: Reach              # back to max(B, 0)
    to_fund: Reach | None         # None when there is no fund target


@dataclass(frozen=True)
class EmergencyResult:
    cost: float
    buffer_before: float          # B
    buffer_left: float            # apply_shock(id, Shock(one_off_dollars=cost)).buffer_left (AC-14)
    covered: bool                 # buffer_left > 0
    backup: BackupPlan | None     # from make_plan(id, Shock(one_off_dollars=cost)) when not covered
    lean_budget: float            # rates.lean_spending
    lean_fixed: float             # min(rates.fixed_costs, lean_budget)
    lean_other: float             # lean_budget - lean_fixed
    rebuild: tuple[Rebuild, Rebuild, Rebuild]
    from_wallet: float            # min(cost, max(B - fund_value, 0)): out of the wallet in progress first (WL-9)
    from_fund: float              # cost - from_wallet: then out of the fund wallet, which may go negative


@dataclass(frozen=True)
class TimelineEvent:
    month: int | None             # None only in Timeline.after_cap
    code: str                     # one of MARKER_CODES
    rate: str | None              # None for emergency_cost and loan_paid_off (the same on every line)
    item: str | None              # the goal name for goal_*; None otherwise


@dataclass(frozen=True)
class TimelineLine:
    rate: str
    balance: tuple[float, ...]    # months 0..horizon; [0] = B - cost (after the month-0 emergency)


@dataclass(frozen=True)
class Timeline:
    horizon: int                  # 12..120 (RU-26)
    start: float                  # B, the point before month 0's emergency cost (AC-15)
    lines: tuple[TimelineLine, TimelineLine, TimelineLine]   # actual, judges, lean
    events: tuple[TimelineEvent, ...]       # month <= horizon, sorted by (month, RATE_KEYS order, MARKER_CODES order)
    after_cap: tuple[TimelineEvent, ...]    # items not reached by month 120 (J5.4 2b)


@dataclass(frozen=True)
class PlanDesign:
    account_id: int
    request: PlanRequest
    rates: SavingRates
    fund_target: float | None     # target_months * S; None when S <= 0 (P.no_fund)
    goals: tuple[GoalResult, ...]
    time_off: TimeOffResult | None
    emergency: EmergencyResult | None
    timeline: Timeline
    facts: tuple[Fact, ...]       # shock.Fact codes: no_fund_target, no_buffer, data_stops_early, loan_scheduled_only,
                                  # loan_not_in_spending, interest_applied, pension_time_off, rates_disagree


@dataclass(frozen=True)
class Wallet:
    """One wallet on one line at one month: a split of that line's balance, presentation only (ADR 0008 decision 7)."""
    item: str                     # "fund", the goal name, or "time_off"
    position: int                 # 0 for the fund, else 1-based in request.items
    target: float                 # fund_value; the goal amount; months_off * S
    amount: float                 # fund: min(balance, fund_value), may be negative; in progress: max(balance - fund_value, 0); else 0.0
    state: str                    # "filling" | "full" (fund only) | "waiting" | "spending" (time off running) | "accomplished"
    month_accomplished: int | None    # the line's reached month (goal: bought the same month; time off: its end); None if not by 120


def _is_number(value):
    return not isinstance(value, bool) and isinstance(value, Real) and math.isfinite(value)


def _is_whole(value, low, high):
    return not isinstance(value, bool) and isinstance(value, Integral) and low <= value <= high


def _validate(request):
    if not isinstance(request, PlanRequest):
        raise InvalidPlanError("items", "request must be a PlanRequest.")
    items = request.items
    if not isinstance(items, (tuple, list)) or len(items) > MAX_ITEMS:
        raise InvalidPlanError("items", f"items must be a tuple of at most {MAX_ITEMS} plans.")
    if sum(isinstance(x, TimeOff) for x in items) > 1:
        raise InvalidPlanError("items", "at most one time off can be planned.")
    for item in items:
        if isinstance(item, SavingsGoal):
            if not isinstance(item.name, str) or not 1 <= len(item.name.strip()) <= 40:
                raise InvalidPlanError("name", "name must be 1 to 40 characters.")
            if not _is_number(item.amount) or item.amount < 0:
                raise InvalidPlanError("amount", f"amount must be a finite number of at least 0, not {item.amount!r}.")
            if item.deadline_months is not None and not _is_whole(item.deadline_months, 1, MAX_MONTHS):
                raise InvalidPlanError("deadline_months", f"deadline_months must be a whole number from 1 to {MAX_MONTHS}, not {item.deadline_months!r}.")
        elif isinstance(item, TimeOff):
            if not _is_whole(item.months_off, 1, MAX_MONTHS):
                raise InvalidPlanError("months_off", f"months_off must be a whole number from 1 to {MAX_MONTHS}, not {item.months_off!r}.")
        else:
            raise InvalidPlanError("items", f"each plan must be a SavingsGoal or a TimeOff, not {type(item).__name__}.")
    if request.emergency is not None:
        if not isinstance(request.emergency, EmergencyCost) or not _is_number(request.emergency.cost) or request.emergency.cost < 0:
            raise InvalidPlanError("cost", "cost must be a finite number of at least 0.")
    if not _is_number(request.interest_pct) or not 0 <= request.interest_pct <= MAX_INTEREST_PCT:
        raise InvalidPlanError("interest_pct", f"interest_pct must be from 0 to {MAX_INTEREST_PCT:g}, not {request.interest_pct!r}.")
    if not _is_number(request.target_months) or request.target_months <= 0:
        raise InvalidPlanError("target_months", f"target_months must be above 0, not {request.target_months!r}.")


@dataclass(frozen=True)
class _Step:
    kind: str                     # "fund" | "goal" | "off"
    name: str | None
    target: float                 # the balance that settles it
    amount: float                 # what leaves the balance (goal) or the time off's total spending
    months: int = 0               # time off length


@dataclass
class _Run:
    balance: list
    events: list                  # (month, code, item)
    reached: dict                 # step index -> month
    start_balance: dict           # time-off step index -> balance when it starts
    ends: dict                    # time-off step index -> month it ends (may pass 120)
    head_balance: dict
    blocked: int                  # first step not reached by month 120
    net_at_cap: float


def _simulate(steps, rate, payoff, bump, bal0, spending, i):
    bal = bal0
    events, reached, start_balance, ends, head_balance = [], {}, {}, {}, {0: bal0}
    state = {"pos": 0, "off_end": None}

    def settle(t):
        nonlocal bal
        while state["pos"] < len(steps) and state["off_end"] is None:
            pos = state["pos"]
            step = steps[pos]
            if bal < step.target:
                return
            reached[pos] = t
            if step.kind == "fund":
                events.append((t, "fund_reached", None))
            elif step.kind == "goal":
                events.append((t, "goal_reached", step.name))
                events.append((t, "goal_bought", step.name))
                bal -= step.amount
            else:
                events.append((t, "time_off_start", None))
                start_balance[pos] = bal
                ends[pos] = t + step.months
                state["off_end"] = t + step.months
            state["pos"] = pos + 1
            head_balance[pos + 1] = bal

    settle(0)
    balance = [bal]
    for t in range(1, MAX_MONTHS + 1):
        interest = bal * i if bal > 0 else 0.0
        if state["off_end"] is not None:
            flow = -(spending - (bump if payoff is not None and t >= payoff else 0.0))
        else:
            flow = rate.at(t, payoff)
        bal += interest + flow
        if state["off_end"] == t:
            events.append((t, "time_off_end", None))
            state["off_end"] = None
            head_balance[state["pos"]] = bal
        settle(t)
        balance.append(bal)
    net = rate.at(MAX_MONTHS, payoff) + (bal * i if bal > 0 else 0.0)
    return _Run(balance, events, reached, start_balance, ends, head_balance, state["pos"], net)


def _state(run, index):
    if index in run.reached:
        month = run.reached[index]
        return ("now" if month == 0 else "reached"), month
    if run.net_at_cap <= 0 and run.balance[MAX_MONTHS] <= run.head_balance[run.blocked]:
        return "never", None
    return "over_cap", None


def _reach(rate, index, need, runs):
    state, month = _state(runs[0], index)
    state_no_loan, month_no_loan = _state(runs[1], index)
    stuck = rate.monthly <= 0
    return Reach(rate.key, state, month, state_no_loan, month_no_loan,
                 -rate.monthly + 0.0 if stuck else None,
                 -rate.monthly + need / MAX_MONTHS if stuck else None)


def _reaches(bal0, target, flows, extra, i):
    bal = bal0
    for flow in flows:
        bal += (bal * i if bal > 0 else 0.0) + flow + extra
    return bal >= target - 1e-9


def _smallest_level(bal0, target, flows, i):
    """The smallest level amount, to the cent, added to every month's `flows` that reaches `target` (0 when none is needed)."""
    if _reaches(bal0, target, flows, 0.0, i):
        return 0.0
    high = math.ceil(max((target - bal0 - sum(flows)) / len(flows), 0.0) * 100)
    while not _reaches(bal0, target, flows, high / 100, i):
        high += 1
    low = 0
    while high - low > 1:
        mid = (low + high) // 2
        if _reaches(bal0, target, flows, mid / 100, i):
            high = mid
        else:
            low = mid
    return high / 100


def _deadline(rates, months, target, bal0, i, includes_fund):
    need = max(target - bal0, 0.0)
    actual, loan = rates.actual, rates.loan_end
    monthly_needed = need / months if i == 0 else _smallest_level(bal0, target, [0.0] * months, i)
    cut_needed = max(monthly_needed - actual.monthly, 0.0)
    flexible = rates.flexible_spending
    counts = loan is not None and loan.payoff_month <= months and actual.loan_bump > 0
    cut_with_loan = None
    if counts:
        flows = [actual.at(t, loan.payoff_month) for t in range(1, months + 1)]
        cut_with_loan = max((need - sum(flows)) / months, 0.0) if i == 0 else _smallest_level(bal0, target, flows, i)
    return DeadlineAnswer(
        months=months, need=need, monthly_needed=monthly_needed, headline_rate=actual.monthly, cut_needed=cut_needed,
        on_pace=cut_needed == 0, flexible_spending=flexible,
        cut_share_of_flexible=cut_needed / flexible if flexible > 0 else None, lean_cut=rates.lean_cut,
        within_lean=cut_needed <= rates.lean_cut, over_flexible=cut_needed > flexible, includes_fund=includes_fund,
        counts_loan_end=counts, payoff_month=loan.payoff_month if counts else None, cut_with_loan=cut_with_loan,
        on_pace_with_loan=cut_with_loan == 0 if counts else None)


def _facts(p, rates, request, fund_target):
    out = []
    if fund_target is None:
        out.append(Fact("no_fund_target", "Not enough regular spending to set an emergency fund, so goals count from $0."))
    if p.B <= 0:
        out.append(Fact("no_buffer", f"The balance was already {money(p.B)}, so every goal starts below $0."))
    if p.last_month != LAST_DATA_MONTH:
        out.append(Fact("data_stops_early", f"Data stops in {p.last_month}. Figures are as of then."))
    end = rates.loan_end
    if end is not None and end.scheduled_only:
        out.append(Fact("loan_scheduled_only", f"The loan is behind, so month {end.payoff_month} is the scheduled end, not a certain one."))
    if end is not None and not end.in_typical_spending:
        out.append(Fact("loan_not_in_spending", f"The loan payment of {money(end.payment)} a month isn't in the standard (judges') typical spending yet, so the standard (judges') figure doesn't rise when it ends."))
    if request.interest_pct > 0:
        out.append(Fact("interest_applied", f"Includes {request.interest_pct:g}% a year interest (our estimate)."))
    if p.income_type == "Pension" and any(isinstance(x, TimeOff) for x in request.items):
        out.append(Fact("pension_time_off", "Pension income: time off work wouldn't stop it. The check still assumes no income."))
    if (rates.actual.monthly > 0) != (rates.judges.monthly > 0):
        out.append(Fact("rates_disagree", "The actual change and the standard (judges') typical figures point different ways, because typical months come from different months."))
    return tuple(out)


def design_plan(account_id, request: PlanRequest | None = None) -> PlanDesign:
    """No shock is used (RU-11). Raises InvalidPlanError(field) with field in
    items, name, amount, deadline_months, months_off, cost, interest_pct, target_months."""
    account_id = parse_account_id(account_id)
    request = PlanRequest() if request is None else request
    _validate(request)
    p = get_profile(account_id)
    rates = saving_rates(account_id)
    loan = rates.loan_end
    payoff = loan.payoff_month if loan else None
    bump = loan.bump_judges if loan else 0.0
    i = request.interest_pct / 1200
    fund_target = p.S * request.target_months if p.S > 0 else None
    fund_value = fund_target or 0.0
    cost = float(request.emergency.cost) if request.emergency else 0.0
    bal0 = p.B - cost

    steps, index_of, needs, earlier = [], {}, {}, 0.0
    if fund_value > 0:
        steps.append(_Step("fund", None, fund_value, 0.0))
    for position, item in enumerate(request.items, 1):
        if isinstance(item, SavingsGoal):
            amount = float(item.amount)
            steps.append(_Step("goal", item.name, fund_value + amount, amount))
        else:
            amount = item.months_off * p.S
            steps.append(_Step("off", None, fund_value + amount, amount, item.months_off))
        index_of[position] = len(steps) - 1
        needs[position] = (fund_value + earlier + amount, max(fund_value + earlier + amount - bal0, 0.0))
        earlier += amount

    runs = {(r.key, flag): _simulate(steps, r, payoff if flag else None, bump, bal0, p.S, i)
            for r in rates.ordered for flag in (True, False)}

    def reach_for(rate, index, need):
        return _reach(rate, index, need, (runs[rate.key, True], runs[rate.key, False]))

    goals, time_off = [], None
    for position, item in enumerate(request.items, 1):
        index = index_of[position]
        target, need = needs[position]
        reach = tuple(reach_for(r, index, need) for r in rates.ordered)
        if isinstance(item, SavingsGoal):
            fund_needed = max(fund_value - bal0, 0.0) if position == 1 and fund_target is not None else 0.0
            deadline = None
            if item.deadline_months is not None:
                deadline = _deadline(rates, item.deadline_months, target, bal0, i, max(fund_value - bal0, 0.0) > 0)
            state = "zero" if item.amount == 0 else "now" if all(x.state == "now" for x in reach) else "planned"
            goals.append(GoalResult(item, position, fund_needed, fund_needed + item.amount, state, reach, deadline))
        else:
            checks = []
            for r in rates.ordered:
                run = runs[r.key, True]
                started_now = index not in run.reached
                start = 0 if started_now else run.reached[index]
                start_balance = bal0 if started_now else run.start_balance[index]
                m = item.months_off
                inside = loan is not None and loan.bump_judges > 0 and start < loan.payoff_month <= start + m
                duration = duration_with_loan_end(
                    start_balance, p.S, p.S, m, m, "no_income",
                    payoff_month=max(loan.payoff_month - start, 1) if loan else None, monthly_drop=bump)
                checks.append(TimeOffCheck(r.key, started_now, start, start_balance, duration, inside))
            time_off = TimeOffResult(item, position, item.months_off * p.S, item.months_off * rates.lean_spending, reach, tuple(checks))

    emergency = None
    if request.emergency is not None:
        shock = Shock(one_off_dollars=cost)
        left = apply_shock(account_id, shock).buffer_left
        covered = left > 0
        backup = None if covered else make_plan(account_id, shock).backup
        lean_fixed = min(rates.fixed_costs, rates.lean_spending)
        rebuild = []
        for r in rates.ordered:
            pair = []
            for target in (max(p.B, 0.0), fund_target):
                if target is None:
                    pair.append(None)
                    continue
                one = [_simulate([_Step("fund", None, target, 0.0)], r, flag, bump, bal0, p.S, i) for flag in (payoff, None)]
                pair.append(_reach(r, 0, max(target - bal0, 0.0), one))
            rebuild.append(Rebuild(r.key, pair[0], pair[1]))
        from_wallet = min(cost, max(p.B - fund_value, 0.0))
        emergency = EmergencyResult(cost, p.B, left, covered, backup, rates.lean_spending, lean_fixed, rates.lean_spending - lean_fixed,
                                    tuple(rebuild), from_wallet, cost - from_wallet)

    events, after_cap = [], []
    for r in rates.ordered:
        run = runs[r.key, True]
        events.extend(TimelineEvent(month, code, r.key, item) for month, code, item in run.events)
        for index, step in enumerate(steps):
            names = {"fund": ("fund_reached",), "goal": ("goal_reached", "goal_bought"), "off": ("time_off_start", "time_off_end")}[step.kind]
            if index not in run.reached:
                after_cap.extend(TimelineEvent(None, code, r.key, step.name) for code in names)
            elif step.kind == "off" and run.ends[index] > MAX_MONTHS:
                after_cap.append(TimelineEvent(None, "time_off_end", r.key, None))
    if request.emergency is not None and cost > 0:
        events.append(TimelineEvent(0, "emergency_cost", None, None))
    if loan is not None and loan.payoff_month <= MAX_MONTHS:
        events.append(TimelineEvent(loan.payoff_month, "loan_paid_off", None, None))
    deadlines = [g.goal.deadline_months for g in goals if g.goal.deadline_months is not None]
    horizon = MAX_MONTHS if after_cap else min(MAX_MONTHS, max([12, *deadlines, *(e.month for e in events)]))
    order = {k: n for n, k in enumerate(RATE_KEYS)}
    events.sort(key=lambda e: (e.month, order.get(e.rate, -1), MARKER_CODES.index(e.code)))
    lines = tuple(TimelineLine(r.key, tuple(runs[r.key, True].balance[:horizon + 1])) for r in rates.ordered)
    timeline = Timeline(horizon, p.B, lines, tuple(events), tuple(after_cap))
    return PlanDesign(account_id, request, rates, fund_target, tuple(goals), time_off, emergency, timeline,
                      _facts(p, rates, request, fund_target))


def wallets_at(design: PlanDesign, rate: str, month: int) -> tuple[Wallet, ...]:
    """The wallets of design.timeline's `rate` line at `month` (0..horizon), the fund first (omitted when fund_target
    is None), then the items in tick order. At most one wallet is "filling" or "spending"; none when all are accomplished.
    With a fund target, sum(w.amount) == the line's balance[month]; once every item is accomplished the fund wallet holds
    the rest of the balance. Raises InvalidPlanError("month") outside 0..horizon."""
    if isinstance(month, bool) or not isinstance(month, int) or not 0 <= month <= design.timeline.horizon:
        raise InvalidPlanError("month", f"month must be a whole number from 0 to {design.timeline.horizon}, not {month!r}.")
    if rate not in RATE_KEYS:
        raise InvalidPlanError("rate", f"rate must be one of {RATE_KEYS}, not {rate!r}.")
    k = RATE_KEYS.index(rate)
    balance = design.timeline.lines[k].balance[month]
    fund_value = design.fund_target or 0.0
    items = []
    for g in design.goals:
        reached = g.reach[k].month
        items.append((g.position, g.goal.name, float(g.goal.amount), reached, reached, False))
    if design.time_off is not None:
        t = design.time_off
        start = t.reach[k].month
        end = start + t.time_off.months_off if start is not None and start + t.time_off.months_off <= MAX_MONTHS else None
        items.append((t.position, "time_off", float(t.amount), start, end, True))
    items.sort(key=lambda x: x[0])
    current = next((n for n, x in enumerate(items) if x[4] is None or month < x[4]), None)
    running = current is not None and items[current][5] and items[current][3] is not None and month >= items[current][3]
    fund_full = balance >= fund_value
    out = []
    if design.fund_target is not None:
        amount = balance if current is None else min(balance, fund_value)
        out.append(Wallet("fund", 0, fund_value, amount, "full" if fund_full else "waiting" if running else "filling", None))
    for n, (position, name, target, start, end, is_off) in enumerate(items):
        if current is None or n < current:
            out.append(Wallet(name, position, target, 0.0, "accomplished", end))
        elif n > current:
            out.append(Wallet(name, position, target, 0.0, "waiting", end))
        else:
            state = "spending" if running else "filling" if fund_full else "waiting"
            out.append(Wallet(name, position, target, max(balance - fund_value, 0.0), state, end))
    return tuple(out)
