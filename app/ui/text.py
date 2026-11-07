"""Every sentence on the page, from docs/design/ux/copy.md. No Streamlit here, so it can all be tested on every account."""
from dataclasses import dataclass

LAST_DATA_MONTH = "2025-12"


def money(value):
    if value is None:
        return "n/a"
    size = abs(value)
    text = f"${size / 1_000_000:.1f}M" if size >= 999_950 else f"${size:,.0f}"
    return f"-{text}" if value < 0 and text not in ("$0",) else text


def signed_money(value):
    """A change in dollars, always with its direction."""
    if abs(value) < 0.5:
        return "$0"
    return f"{'+' if value > 0 else '-'}{money(abs(value))}"


def number(value):
    return f"{value:g}"


def month_label(month):
    return str(month)


# --- Customer (B) ---------------------------------------------------------------------------------------------------

NOTE_PRIORITY = ("no_buffer", "little_activity", "irregular_income", "irregular_spending", "out_of_date", "pension_income",
                 "no_regular_bills", "bills_missing_from_h", "high_flow")


def _note_text(warning, p):
    return {
        "little_activity": "Almost no activity on this account. Most numbers are $0.",
        "irregular_income": "No regular money in. A lower income changes nothing here.",
        "irregular_spending": "No regular spending recorded. Buffer in months of spending can't be worked out.",
        "no_buffer": "The balance is at or below zero, so runway is 0 months.",
        "out_of_date": f"Data stops in {month_label(p.last_month)}. Figures are as of then.",
        "pension_income": "Pension income: a layoff wouldn't stop this.",
        "cash_income": "Income is cash deposits. The data can't show which are pay.",
        "high_flow": f"Typical money in is over twice the home district's average salary ({money(p.home_district.average_salary)}), so some of it may not be pay.",
        "no_regular_bills": "No regular bills visible in the transactions.",
        "bills_missing_from_h": f"Standing orders show {money(p.bills_on_standing_orders)} a month in bills; transactions show {money(p.H)}.",
        "recent_loan_missed": f"The loan is recent: {money(p.P)} a month isn't in typical fixed costs.",
        "finished_loan_counted": "A finished loan still counts in typical fixed costs.",
        "loan_in_trouble": "The loan is behind or unpaid.",
        "missed_payment": "No loan payment last month.",
        "went_negative": f"The balance went below zero in {p.months_below_zero_last_6} of the last 6 months.",
        "thin_low_point": "The lowest balance was under one loan payment.",
        "leasing_not_counted": "A leasing payment is on record but isn't counted.",
    }.get(warning.code, warning.message)


def notes(p):
    """All customer notes, most important first."""
    rank = {code: i for i, code in enumerate(NOTE_PRIORITY)}
    ordered = sorted(p.warnings, key=lambda w: rank.get(w.code, len(rank)))
    return [_note_text(w, p) for w in ordered]


def summary_line(p):
    who = f"Customer {p.account_id}"
    if p.B <= 0:
        return f"{who} has no buffer to draw on: the balance is {money(p.B)}. Runway is 0 months."
    if p.runway.state == "no_shortfall":
        return f"{who} brings in about {money(p.I)} and spends about {money(p.S)}, so money isn't running down. The buffer is {money(p.B)}."
    if p.runway.months is not None and p.runway.months >= 120:
        return f"{who} spends slightly more than comes in, but the buffer of {money(p.B)} lasts 120 months or more."
    return f"{who} brings in about {money(p.I)} a month and spends about {money(p.S)}. The buffer is {money(p.B)}, so it would last {p.runway.label}."


def flow_line(p, flows):
    """Typical months aren't what the balance does, so this says what it did."""
    change = flows.change_last_12
    period = "the last 12 months" if p.last_month == LAST_DATA_MONTH else "its last 12 months of data"
    if abs(change) < 0.5:
        moved = "stayed about the same"
    else:
        moved = f"{'rose' if change > 0 else 'fell'} {money(abs(change))} a month on average"
    return f"These are typical months, and medians don't add up. Over {period} the balance {moved}, and it ended at {money(p.latest_balance)}."


# --- Before and after (D) -------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    tone: str        # "neutral", "ok" or "bad"
    sentence: str
    second_line: str | None = None


def verdict(r):
    """Chosen only from the engine's verdict_case and duration, never from the rounded runway."""
    case = r.verdict_case
    codes = {f.code for f in r.facts}
    cut = r.shock.income_cut
    pct = number(round(cut.keep_fraction * 100, 2)) if cut else None
    d = r.duration
    second = f"The judges' runway is {r.runway.label}." if d is not None else None
    if case == "no_shock":
        return Verdict("neutral", "No shock applied. Pick a twist to see what changes.")
    if case == "runway_zero":
        if "no_buffer_before_shock" in codes:
            return Verdict("bad", f"The balance was already {money(r.before.buffer)} before this, so runway is 0 months whatever the shock.", second)
        return Verdict("bad", f"The one-off cost of {money(r.one_off)} is bigger than the buffer of {money(r.before.buffer)}. Nothing is left to live on.", second)
    if case == "no_shortfall":
        return Verdict("ok", "Income still covers spending, so the buffer isn't being used.", second)
    if case == "income_cut_makes_it":
        return Verdict("ok", f"With income at {pct}% for {d.months_asked} months, the money lasts the full {d.months_asked} months. They make it.", second)
    if case == "income_cut_runs_out":
        if d.runs_out_in_month == 0:
            return Verdict("bad", "There is no buffer before month 1, so the money is gone before the lower income starts.", second)
        return Verdict("bad", f"With income at {pct}% for {d.months_asked} months, the money runs out in month {d.runs_out_in_month}, about {d.months_short:g} months short.", second)
    if case == "income_cut_open_ended":
        return Verdict("neutral", f"With income at {pct}%, the buffer lasts {r.runway.label}. No length was set, so there is no make-it answer.", second)
    return Verdict("neutral", f"After this, the buffer lasts {r.runway.label}, down from {r.before.runway.label}.", second)


def fact_lines(r, p):
    """One plain line per fact. The verdict already says the two runway-zero facts, so they aren't repeated."""
    text = {
        "layoff_doesnt_fit_pension": "Pension income: a layoff wouldn't stop this. The numbers apply the layoff as asked.",
        "income_cut_no_income": "No regular money in, so a lower income changes nothing here.",
        "bills_shock_no_bills": "No regular bills visible, so the judges' formula changes nothing for this.",
        "bills_shock_too_small": "Standing orders show more bills than the judges' figure, so this rise is understated.",
        "one_off_zero_spending": "No typical spending, so a cost in months of spending is $0. Type dollars instead.",
        "data_stops_early": f"Data stops in {month_label(p.last_month)}.",
        "little_activity": "Almost no activity, so most numbers are $0.",
        "spending_floored_at_zero": "Spending can't go below $0, so it stops there.",
        "runs_into_january": "This runs into January, when spending is usually higher.",
    }
    skip = {"no_buffer_before_shock", "one_off_exceeds_buffer", "ei_weekly_max_applied"}
    return [text.get(f.code, f.message) for f in r.facts if f.code not in skip]


def assumption_line(r):
    d = r.duration
    if d is None or not d.assumption_applied:
        return None
    return f"After month {d.benefit_months} we assume no income. A benefit ending doesn't mean a new job has started."


def money_delta(before, after):
    change = after - before
    if abs(change) < 0.5:
        return "no change"
    return f"{'up' if change > 0 else 'down'} {money(abs(change))}"


def runway_delta(before, after):
    if before.months is None or after.months is None:
        return "no change" if before.label == after.label else None
    change = round(after.months - before.months, 1)
    if change == 0:
        return "no change"
    return f"{'up' if change > 0 else 'down'} {abs(change):g} months"


# --- Our numbers (E) ------------------------------------------------------------------------------------------------

REASONS = {
    "pension_income": "This comes from cash-only accounts, and a pension isn't lost with a layoff.",
    "transfers_income": "This comes from cash-only accounts, so it doesn't apply to transfer income.",
    "no_income_lost": "No income is lost in this twist.",
    "no_typical_spending": "There is no typical spending to adjust.",
    "no_bills_shock": "No bills rise is set.",
    "bills_not_missing": "Standing orders match the bills already counted.",
}


@dataclass(frozen=True)
class OurRow:
    label: str
    value: str
    counterpart: str | None
    lines: tuple


def _capped_line(c, backup):
    """The maximum's own make-it answer, plus the cut it would take."""
    d = c.duration
    if d is None:
        return None
    if d.verdict == "makes_it":
        return f"With the maximum, the money lasts the full {d.months_asked} months."
    line = "With the maximum, there is no buffer before month 1." if d.runs_out_in_month == 0 else f"With the maximum, they run out in month {d.runs_out_in_month}."
    if backup is not None and backup.cut_to_last:
        line += f" Lasting the full {d.months_asked} months takes {money(backup.cut_to_last)} a month less spending."
    return line


def our_rows(r, p, plan):
    judges = f"judges': {r.runway.label}"
    rows = []
    adjust = r.if_you_adjust
    if adjust.applies:
        rows.append(OurRow("Runway, if you adjust", adjust.runway.label, judges, (
            "An illustration, not a forecast. In some accounts in the data, spending fell when income fell. This lowers spending that way. The judges' runway keeps spending flat.",)))
    else:
        rows.append(OurRow("Runway, if you adjust", "n/a", None, (REASONS.get(adjust.reason, adjust.note),)))
    capped = r.ei_capped
    if capped.available and capped.switched_on:
        lines = [f"Same shock, with EI capped at {money(capped.weekly_max)} a week ({money(capped.monthly_max)} a month)."]
        line = _capped_line(capped, plan.backup_capped)
        if line:
            lines.append(line)
        rows.append(OurRow("Runway with EI weekly maximum", capped.runway.label, judges, tuple(lines)))
    orders = r.bills_on_standing_orders
    if orders.applies:
        rows.append(OurRow("Bills on standing orders", orders.runway.label, judges, (
            "Runway if the rise applies to monthly bills set up as standing orders. Some bills don't show in typical bills, so this base can be larger.",)))
    else:
        rows.append(OurRow("Bills on standing orders", "n/a", None, (REASONS.get(orders.reason, orders.note),)))
    rows.append(OurRow("Current fixed costs", f"{money(p.current_fixed_costs)} a month", f"judges' F: {money(p.F)}", (
        "Bills, insurance and the loan payment if still running.",)))
    rows.append(OurRow("Buffer in months of spending", "n/a" if p.buffer_months is None else f"{p.buffer_months:.1f} months", None, (
        "Buffer divided by typical spending. Shows savings without how much money passes through."
        if p.buffer_months is not None else "There is no buffer or no typical spending to divide by.",)))
    rows.append(OurRow("Lowest balance, last 6 months", money(p.lowest_balance), None, ("The lowest the balance got. An average can hide it.",)))
    rows.append(OurRow("Latest balance", money(p.latest_balance), f"judges' buffer: {money(p.B)}", (
        f"The balance at the end of {p.last_month}. The buffer is an average over 6 months, so the two can differ.",)))
    rows.append(OurRow("Actual change, last 12 months", f"{signed_money(plan.goal.actual_change_last_12)} a month", f"typical month: {signed_money(p.I - p.S)}", (
        "What the balance really did, on average. Typical money in minus typical spending can differ, because each is a separate median.",)))
    return rows


# --- Plans (F, G) ---------------------------------------------------------------------------------------------------

def goal_lines(plan):
    g, low = plan.goal, plan.low_balance
    lines = []
    if g.below_zero_by > 0:
        lines.append(f"First step: get the balance back above $0 ({money(g.below_zero_by)}).")
    if g.state == "no_regular_spending":
        lines.append("Not enough regular spending to set a target.")
    elif g.state == "already_there":
        lines.append(f"Already there: the buffer covers **{g.months_covered:.1f} months**.")
    elif g.state == "on_track":
        start = f"To have {number(g.target_months)} months of spending (**{money(g.target_amount)}**) saved, set aside **{money(g.monthly_amount)} a month**."
        if g.months_to_goal > 120:
            lines.append(f"{start} That takes more than 120 months.")
        elif g.reaches_within_horizon:
            lines.append(f"{start} That takes **{g.months_to_goal} months**.")
        else:
            lines.append(f"{start} That takes **{g.months_to_goal} months**, more than 12.")
    else:
        reach = g.cut_to_reach_in_horizon
        if g.cut_to_break_even < 1:
            lines.append(f"Money in only just covers spending. About **{money(reach)}** a month less would reach {money(g.target_amount)} in 12 months.")
        else:
            lines.append(f"Money in doesn't cover spending, so saving starts with spending about **{money(g.cut_to_break_even)}** a month less. "
                         f"About **{money(reach)}** a month less would reach {money(g.target_amount)} in 12 months.")
        if reach <= g.flexible_spending:
            lines.append(f"That fits within the {money(g.flexible_spending)} of spending above fixed costs.")
        else:
            lines.append(f"That is more than the {money(g.flexible_spending)} of spending above fixed costs.")
    if any(f.code == "surplus_not_seen_in_balance" for f in plan.facts):
        lines.append(f"Money in is {money(g.surplus)} above spending, but over the last 12 months the balance changed by {money(g.actual_change_last_12)} a month on average. Treat the savings figure as the most this could be.")
    if any(f.code == "balance_rose_despite_gap" for f in plan.facts):
        lines.append(f"Typical spending is {money(-g.surplus)} above typical money in, but over the last 12 months the balance rose {money(g.actual_change_last_12)} a month on average. Typical months can overstate the gap, so the cut needed may be smaller.")
    if low is not None:
        lines.append(f"Keep the lowest balance above one loan payment ({money(low.payment)}). It is now {money(low.lowest_balance)}.")
    return lines


def backup_lines(plan):
    b = plan.backup
    n = b.through_months
    if b.state == "no_shock":
        return ["Pick a twist to see a backup plan."]
    if b.state == "no_buffer":
        return [f"There is no buffer. First, **{money(b.cover_needed)}** is needed to get back to $0."]
    if b.state == "no_cuts_needed":
        return [f"No cuts needed: the buffer lasts the full {n} months." if n else "No cuts needed: income still covers spending."]
    context = [f"Spending above fixed costs: {money(b.flexible_spending)} a month.",
               f"Fixed costs, including bills added by the shock: {money(b.fixed_costs)} a month."]
    if b.state == "cuts_not_enough":
        return [f"Even with all other spending cut, the buffer lasts **{b.runway_if_all_flexible_cut.label}**, short of {n} months.", *context]
    if b.cut_to_last is not None:
        share = b.cut_to_last_share_of_spending
        size = f", about {share:.0%} of typical spending" if share is not None else ""
        return [f"To last the full {n} months, spending needs to drop by **{money(b.cut_to_last)} a month**{size}.", *context]
    return [f"To stop the buffer falling, spending needs to drop by **{money(b.cut_to_close_gap)} a month**.", *context]
