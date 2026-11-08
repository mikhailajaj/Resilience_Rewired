"""Every plan designer sentence, marker label and table row, from docs/design/ux/copy.md §11. No Streamlit and no arithmetic beyond formatting (AC-19)."""
from app.engine import get_profile
from app.engine.goals import wallets_at
from app.engine.rates import RATE_KEYS

from . import text
from .text import money, months_word, signed_money


class P:
    """Copy §11 plus NEW-COPY-22, 26, 27, 28 and 30. `{x}` money values come from text.money. Rows match copy §11 literally;
    "{n} months" rows follow NEW-COPY-9, so WP-T adds singular forms beside them where n can be 1."""
    head = "Plan designer"
    cap = "Before any shock. Tick a plan to open it."
    r_actual = "Actual change, last 12 months (our estimate)"
    r_judges = "Typical money in minus typical spending"
    r_lean = "Saving at lean-month spending (our estimate)"
    r_note = "Typical months come from different months, so they don't add up. The actual change is the headline."
    t_goal = "Savings goal"
    t_off = "Time off work"
    t_emergency = "Emergency budget"
    i_name = "What for"
    i_amount = "Amount ($)"
    i_deadline = "Deadline in months (optional)"
    i_interest = "Interest, % a year (optional, default 0)"
    i_months_off = "Months off (1 to 120)"
    i_cost = "Cost ($)"
    g_needed = "{fund_needed} to finish the emergency fund first, then {amount} for the {goal_name}."
    g_months = "{rate}: {n} months."
    never = "{rate}: never at this rate."
    over_cap = "{rate}: more than 120 months."
    g_now = "The money above the emergency fund already covers the {goal_name}, so it can be bought now."
    g_zero = "The amount is $0, so there is nothing to save."
    g_deadline = "To have it in {deadline} months, save {needed} a month."
    g_on_pace = "The actual change already does that, so no cut is needed."
    g_cut = "That needs {cut} a month less spending: {share}% of the {flex} above fixed costs, {within} the {lean_cut} the lean-quarter level would save."
    g_cut_within = "within"
    g_cut_more = "more than"
    g_cut_over = "That is more than the {flex} above fixed costs, so cuts alone can't reach it by then."
    g_cut_start = "Saving starts with spending {break_even} a month less. {reach} a month less would reach it in 120 months."
    g_fund_first = "This includes finishing the emergency fund first."
    g_cut_loan = "Counting the loan ending in month {N}, spend {cut_with_loan} a month less (our estimate)."        # NEW-COPY-27
    g_on_pace_loan = "Counting the loan ending in month {N}, the current pace is enough (our estimate)."          # NEW-COPY-27
    interest = "Includes {interest_pct}% a year interest (our estimate)."
    no_fund = "Not enough regular spending to set an emergency fund, so goals count from $0."
    month_one = "Data stops in {last_month}, so month 1 is the month after."
    no_shock_used = "The shock above isn't used here."
    o_amount = "{months_off} months off at typical spending: {amount}. At lean spending: {lean_amount} (our estimate)."
    o_ok = "With no income for {months_off} months from month {start}, the money lasts. They make it."
    o_out = "With no income for {months_off} months from month {start}, the money runs out in month {m} of the time off."
    o_now = "Not saved by month 120, so this checks starting now."
    e_left_ok = "The buffer covers it: {left} is left."
    e_left_no = "The buffer can't cover it: {left} left."
    e_zero = "The cost is $0, so the buffer is unchanged."
    e_neg = "The buffer (average balance over the last 6 months) was already {B}, so the cost isn't what empties the buffer."                    # NEW-COPY-29
    e_budget = "Do this first, in order:"
    e_lean = "Lean budget: {lean} a month, {fixed} fixed and {other} other (our estimate)."
    e_rebuild = "{rate}: back to {buffer} in {n} months, emergency fund in {m} months."
    tl_head = "Balance by month, one line per rate"
    tl_table = "Show as a table"
    tl_none = "No rate adds to the balance, so every line stays flat or falls."
    tl_alt = "Line chart of the balance over {n} months at each saving rate. Markers: {events}."
    m_fund_reached = "Emergency fund reached"
    m_goal_reached = "{goal_name} reached"
    m_goal_bought = "{goal_name} bought"
    m_time_off_start = "Time off starts"
    m_time_off_end = "Time off ends"
    m_emergency_cost = "Emergency cost"
    m_loan_paid_off = "Loan paid off"
    loan_line = "{n} months; {n_loan} counting the loan ending in month {N} (our estimate)."
    loan_never = "never at this rate; {n_loan} months counting the loan ending in month {N} (our estimate)."
    loan_over = "never at this rate, and more than 120 months counting the loan ending in month {N} (our estimate)."   # NEW-COPY-26
    loan_d = "The loan is behind, so month {N} is the scheduled end, not a certain one."
    loan_not_in_spending = ("The loan payment of {P} a month isn't in the standard (judges') typical spending yet, because the loan started recently, "
                            "so the standard (judges') figure doesn't rise when it ends in month {N} (our estimate).")                     # NEW-COPY-22
    after_cap = "After month 120: {events}."                                                              # NEW-COPY-28
    w_head = "Wallets (our estimate)"                                                                             # NEW-COPY-30
    w_row = "{item}: {amount} of {target}"
    w_fund = "Emergency fund"
    w_time_off = "Time off"
    w_filling = "filling"
    w_full = "full"
    w_waiting = "waiting for {previous}"
    w_spending = "spending during the time off"
    w_accomplished = "accomplished in month {m}"
    w_negative_fund = "Emergency fund: {amount} of {target}, below $0 before the loan ends"
    w_emergency = "The {cost} cost comes out of {from_wallet} saved for {item}, then {from_fund} of the emergency fund."
    w_column = "{item} wallet"
    loan_backup = text.LOAN_BACKUP                                                                       # copy §7
    loan_backup_ok = text.LOAN_BACKUP_OK
    loan_backup_out = text.LOAN_BACKUP_OUT
    # New wording (not yet in copy §11; the copy owner files it):
    g_months_never_over = "more than 120 months; {n_loan} counting the loan ending in month {N} (our estimate)."
    g_cut_plain = "That needs {cut} a month less spending."
    o_out_zero = "With no income for {months_off} months from month {start}, there is no money before month 1."
    o_loan = "This counts the loan ending in month {N} (our estimate)."
    item_time_off = "time off"
    w_negative_state = "below $0 before the loan ends"
    w_below_zero = "below $0"
    pension_time_off = "Pension income: time off wouldn't stop it. The check still uses no income, as asked."
    no_buffer = "The buffer (average balance over the last 6 months) is at or below $0, so saving starts by getting back to $0."
    tl_no_markers = "none"
    rebuild_never = "never at this rate"
    rebuild_over = "in more than 120 months"
    rebuild_now = "now"


RATE_SHORT = {"actual": "actual change", "judges": "typical month", "lean": "lean months"}


MARKER_LETTER = {"fund_reached": "F", "goal_reached": "G", "goal_bought": "B", "time_off_start": "O", "time_off_end": "O",
                 "emergency_cost": "E", "loan_paid_off": "L"}


def _fmt(template, **values):
    """Fill a template; "{key} months" becomes "{key} month" for a whole 1 (NEW-COPY-9)."""
    for key, value in values.items():
        if value == 1 and not isinstance(value, bool):
            template = template.replace(f"{{{key}}} months", f"{{{key}}} month")
    return template.format(**values)


def rate_label(key: str) -> str:
    return {"actual": P.r_actual, "judges": P.r_judges, "lean": P.r_lean}[key]


def rate_rows(rates) -> list[tuple[str, str, bool]]:
    """(label, "+$604 a month", is_headline), headline first."""
    return [(rate_label(r.key), f"{signed_money(r.monthly)} a month", r.is_headline) for r in rates.ordered]


def _loan_month(design):
    loan = design.rates.loan_end
    return None if loan is None else loan.payoff_month


def _reach_line(label, reach, payoff):
    """One rate's line: months with and without the loan end, 'never', or 'more than 120 months'."""
    differs = payoff is not None and (reach.state, reach.month) != (reach.state_no_loan, reach.month_no_loan)
    plain, counted = reach.state_no_loan, reach.state
    if differs and plain == "reached" and counted == "reached":
        return f"{label}: " + _fmt(P.loan_line, n=reach.month_no_loan, n_loan=reach.month, N=payoff)
    if differs and plain == "never" and counted == "reached":
        return f"{label}: " + _fmt(P.loan_never, n_loan=reach.month, N=payoff)
    if differs and plain == "never" and counted == "over_cap":
        return f"{label}: " + P.loan_over.format(N=payoff)
    if differs and plain == "over_cap" and counted == "reached":
        return f"{label}: " + _fmt(P.g_months_never_over, n_loan=reach.month, N=payoff)
    if counted == "never":
        return P.never.format(rate=label)
    if counted == "over_cap":
        return P.over_cap.format(rate=label)
    return _fmt(P.g_months, n=reach.month or 0, rate=label)


def _reach_lines(design, reach):
    payoff = _loan_month(design)
    return [_reach_line(rate_label(r.rate), r, payoff) for r in reach]


def _cut_start_lines(reach):
    lines = []
    for r in reach:
        if r.cut_to_start is not None and r.cut_to_reach_by_cap is not None:
            lines.append(f"{rate_label(r.rate)}: " + P.g_cut_start.format(break_even=money(r.cut_to_start), reach=money(r.cut_to_reach_by_cap)))
    return lines


def _deadline_lines(design, goal):
    d = goal.deadline
    lines = [_fmt(P.g_deadline, deadline=d.months, needed=money(d.monthly_needed))]
    if d.includes_fund:
        lines.append(P.g_fund_first)
    if d.on_pace:
        lines.append(P.g_on_pace)
    else:
        if d.cut_share_of_flexible is None:
            lines.append(P.g_cut_plain.format(cut=money(d.cut_needed)))
        else:
            within = P.g_cut_within if d.within_lean else P.g_cut_more
            lines.append(P.g_cut.format(cut=money(d.cut_needed), share=format(d.cut_share_of_flexible, ".0%").rstrip("%"),
                                        flex=money(d.flexible_spending), within=within, lean_cut=money(d.lean_cut)))
        if d.over_flexible:
            lines.append(P.g_cut_over.format(flex=money(d.flexible_spending)))
    if d.counts_loan_end:
        if d.on_pace_with_loan:
            lines.append(P.g_on_pace_loan.format(N=d.payoff_month))
        else:
            lines.append(P.g_cut_loan.format(N=d.payoff_month, cut_with_loan=money(d.cut_with_loan)))
    return lines


def goal_lines(design, goal) -> list[str]:
    name = goal.goal.name
    if goal.state == "zero":
        return [P.g_zero]
    if goal.state == "now":
        return [P.g_now.format(goal_name=name)]
    lines = []
    if goal.fund_needed > 0:
        lines.append(P.g_needed.format(fund_needed=money(goal.fund_needed), amount=money(goal.goal.amount), goal_name=name))
    lines.extend(_reach_lines(design, goal.reach))
    lines.extend(_cut_start_lines(goal.reach))
    if goal.deadline is not None:
        lines.extend(_deadline_lines(design, goal))
    return lines


def _check_lines(check, months_off, payoff):
    lines = []
    if check.started_now:
        lines.append(P.o_now)
    d = check.duration
    if d.verdict == "makes_it":
        lines.append(_fmt(P.o_ok, months_off=months_off, start=check.start_month))
    elif d.runs_out_in_month == 0:
        lines.append(_fmt(P.o_out_zero, months_off=months_off, start=check.start_month))
    else:
        lines.append(_fmt(P.o_out, months_off=months_off, start=check.start_month, m=d.runs_out_in_month))
    if check.counts_loan_end and payoff is not None:
        lines.append(P.o_loan.format(N=payoff))
    return lines


def time_off_lines(design) -> list[str]:
    t = design.time_off
    if t is None:
        return []
    n = t.time_off.months_off
    lines = [_fmt(P.o_amount, months_off=n, amount=money(t.amount), lean_amount=money(t.lean_amount))]
    lines.extend(_reach_lines(design, t.reach))
    payoff = _loan_month(design)
    per_rate = [(rate_label(c.rate), _check_lines(c, n, payoff)) for c in t.checks]
    if all(lines_ == per_rate[0][1] for _, lines_ in per_rate):
        lines.extend(per_rate[0][1])
    else:
        lines.extend(f"{label}: {line}" for label, lines_ in per_rate for line in lines_)
    return lines


def _reach_phrase(reach):
    if reach.state == "never":
        return P.rebuild_never
    if reach.state == "over_cap":
        return P.rebuild_over
    if reach.month == 0:
        return P.rebuild_now
    return f"in {months_word(reach.month)}"


def _rebuild_line(rebuild, buffer):
    label = rate_label(rebuild.rate)
    b, f = rebuild.to_buffer, rebuild.to_fund
    if f is not None and b.state in ("reached", "now") and f.state in ("reached", "now"):
        return _fmt(P.e_rebuild, rate=label, buffer=buffer, n=b.month, m=f.month)
    line = f"{label}: back to {buffer} {_reach_phrase(b)}"
    if f is not None:
        line += f", emergency fund {_reach_phrase(f)}"
    return line + "."


def emergency_lines(design) -> list[str]:
    e = design.emergency
    if e is None:
        return []
    if e.cost == 0:
        return [P.e_zero]
    if e.buffer_before <= 0:
        lines = [P.e_neg.format(B=money(e.buffer_before))]
    elif e.covered:
        lines = [P.e_left_ok.format(left=money(e.buffer_left))]
    else:
        lines = [P.e_left_no.format(left=money(e.buffer_left))]
    if design.fund_target is not None and design.request.items:
        working = [w for w in wallets_at(design, "actual", 0) if w.state in ("filling", "spending")]
        first = design.request.items[0]
        item = working[0].item if working else getattr(first, "name", "time_off")
        name = P.item_time_off if item == "time_off" else item
        lines.append(P.w_emergency.format(cost=money(e.cost), from_wallet=money(e.from_wallet), item=name, from_fund=money(e.from_fund)))
    if not e.covered:
        lines.append(P.e_budget)
        if e.backup is not None:
            lines.extend(f"{step.order}. {step.action}" for step in e.backup.steps)
        lines.append(P.e_lean.format(lean=money(e.lean_budget), fixed=money(e.lean_fixed), other=money(e.lean_other)))
        buffer = money(max(e.buffer_before, 0.0))
        lines.extend(_rebuild_line(r, buffer) for r in e.rebuild)
    return lines


def loan_lines(design) -> list[str]:
    """P.loan_d for status D, then the D12 line (NEW-COPY-22) where the payment isn't in the standard (judges') typical spending."""
    loan = design.rates.loan_end
    if loan is None:
        return []
    lines = []
    if loan.scheduled_only:
        lines.append(P.loan_d.format(N=loan.payoff_month))
    if not loan.in_typical_spending:
        lines.append(P.loan_not_in_spending.format(P=money(loan.payment), N=loan.payoff_month))
    return lines


def fact_lines(design) -> list[str]:
    """Plain lines for the design's facts. The two loan facts are read in loan_lines."""
    codes = {f.code for f in design.facts}
    lines = []
    if "no_fund_target" in codes:
        lines.append(P.no_fund)
    if "no_buffer" in codes:
        lines.append(P.no_buffer)
    if "data_stops_early" in codes:
        lines.append(P.month_one.format(last_month=text.month_label(get_profile(design.account_id).last_month)))
    if "interest_applied" in codes:
        lines.append(P.interest.format(interest_pct=f"{design.request.interest_pct:g}"))
    if "pension_time_off" in codes:
        lines.append(P.pension_time_off)
    if "rates_disagree" in codes:
        lines.append(P.r_note)
    return lines


def marker_label(event) -> str:
    """P.m_* with {goal_name}."""
    template = {"fund_reached": P.m_fund_reached, "goal_reached": P.m_goal_reached, "goal_bought": P.m_goal_bought,
                "time_off_start": P.m_time_off_start, "time_off_end": P.m_time_off_end, "emergency_cost": P.m_emergency_cost,
                "loan_paid_off": P.m_loan_paid_off}.get(event.code)
    return event.code if template is None else template.format(goal_name=event.item)


def _unique_events(events):
    seen, out = set(), []
    for e in events:
        key = (e.month, e.code, e.item)
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def timeline_alt(design) -> str:
    """P.tl_alt: the markers of the headline line, plus those every line shares."""
    t = design.timeline
    events = _unique_events(e for e in t.events if e.rate in (None, RATE_KEYS[0]))
    listed = "; ".join(f"{marker_label(e)} in month {e.month}" for e in events) or P.tl_no_markers
    return _fmt(P.tl_alt, n=t.horizon, events=listed)


def after_cap_line(design) -> str | None:
    """NEW-COPY-28."""
    after = design.timeline.after_cap
    if not after:
        return None
    labels = list(dict.fromkeys(marker_label(e) for e in after))
    return P.after_cap.format(events="; ".join(labels))


def _wallet_label(wallet):
    if wallet.item == "fund":
        return P.w_fund
    return P.w_time_off if wallet.item == "time_off" else wallet.item


def wallet_rows(design, month: int = 0) -> list[tuple[str, str, str]]:
    """(wallet label, "$x of $y", state label) from wallets_at(design, "actual", month)."""
    wallets = wallets_at(design, "actual", month)
    has_loan = design.rates.loan_end is not None
    rows = []
    for i, w in enumerate(wallets):
        if w.state == "accomplished":
            state = P.w_accomplished.format(m=w.month_accomplished)
        elif w.state == "waiting":
            state = P.w_waiting.format(previous=_wallet_label(wallets[i - 1]) if i else "")
        elif w.state == "spending":
            state = P.w_spending
        elif w.item == "fund" and w.amount < 0:
            state = P.w_negative_state if has_loan else P.w_below_zero
        else:
            state = P.w_full if w.state == "full" else P.w_filling
        rows.append((_wallet_label(w), f"{money(w.amount)} of {money(w.target)}", state))
    return rows


def table_rows(design) -> list[dict]:
    """{"Month": m, <three rate labels>: money, <one column per wallet, headline line>: money, "Events": "; ".join(labels)}."""
    t = design.timeline
    by_month = {}
    rates_of = {}
    for e in t.events:
        rates_of.setdefault((e.month, e.code, e.item), set()).add(e.rate)
    for e in _unique_events(t.events):
        every = rates_of[(e.month, e.code, e.item)]
        label = marker_label(e)
        if e.rate is not None and len(every) < len(RATE_KEYS):
            label += f" ({', '.join(RATE_SHORT[k] for k in RATE_KEYS if k in every)})"
        by_month.setdefault(e.month, []).append(label)
    rows = []
    for m in range(t.horizon + 1):
        row = {"Month": m}
        for line in t.lines:
            row[rate_label(line.rate)] = money(line.balance[m])
        for w in wallets_at(design, "actual", m):
            row[P.w_column.format(item=_wallet_label(w))] = money(w.amount)
        row["Events"] = "; ".join(by_month.get(m, []))
        rows.append(row)
    return rows
