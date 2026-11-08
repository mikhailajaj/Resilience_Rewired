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
        "no_buffer": "The buffer (average balance over the last 6 months) is at or below $0, so runway is 0 months.",
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
        return f"{who} has no buffer to draw on: the buffer (average balance over the last 6 months) is {money(p.B)}. Runway is 0 months."
    if p.runway.state == "no_shortfall":
        if p.I == 0 and p.S == 0:
            return f"{who} has almost no activity: typical money in and spending are both $0. The buffer is {money(p.B)}."
        return f"{who} brings in about {money(p.I)} a month and spends about {money(p.S)} in a typical month, so typical months show no shortfall. The buffer is {money(p.B)}."
    if p.I == 0:
        return f"{who} has no regular money in and spends about {money(p.S)} a month. The buffer is {money(p.B)}, so it would last {runway_words(p.runway)}."
    if p.runway.months is not None and p.runway.months >= 120:
        return f"{who} spends slightly more than comes in. The buffer of {money(p.B)} would last {p.runway.label}."
    return f"{who} brings in about {money(p.I)} a month and spends about {money(p.S)}. The buffer is {money(p.B)}, so it would last {runway_words(p.runway)}."


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
    second = f"The standard (judges') runway is {runway_words(r.runway)}." if d is not None else None
    if case == "no_shock":
        return Verdict("neutral", "No shock applied. Pick a twist to see what changes.")
    if case == "runway_zero":
        if "no_buffer_before_shock" in codes:
            return Verdict("bad", f"The buffer (average balance over the last 6 months) was already {money(r.before.buffer)} before this, so runway is 0 months whatever the shock.", second)
        if abs(r.buffer_left) < 0.5:
            return Verdict("bad", f"The one-off cost of {money(r.one_off)} uses up the whole buffer of {money(r.before.buffer)}. Nothing is left to live on.", second)
        return Verdict("bad", f"The one-off cost of {money(r.one_off)} is bigger than the buffer of {money(r.before.buffer)}. Nothing is left to live on.", second)
    if case == "no_shortfall":
        if r.income_after == 0 and r.spending_after == 0:
            return Verdict("ok", "No money in or out in a typical month, so there is nothing for the buffer to cover.", second)
        return Verdict("ok", "Income still covers spending, so the buffer isn't being used.", second)
    if case == "income_cut_makes_it":
        return Verdict("ok", f"With income at {pct}% for {months_word(d.months_asked)}, the money lasts the full {months_word(d.months_asked)}. They make it.", second)
    if case == "income_cut_runs_out":
        if d.runs_out_in_month == 0:
            return Verdict("bad", "There is no buffer before month 1, so the money is gone before the lower income starts.", second)
        short = "less than 0.1 months short" if d.months_short == 0 else f"about {months_word(d.months_short)} short"
        return Verdict("bad", f"With income at {pct}% for {months_word(d.months_asked)}, the money runs out in month {d.runs_out_in_month}, {short}.", second)
    if case == "income_cut_open_ended":
        return Verdict("neutral", f"With income at {pct}%, the buffer lasts {runway_words(r.runway)}. No length was set, so there is no make-it answer.", second)
    if r.runway.label == r.before.runway.label:
        return Verdict("neutral", f"After this, the runway is unchanged at {runway_words(r.runway)}.", second)
    after, before = r.runway.months, r.before.runway.months
    direction = "down" if after is not None and (before is None or after < before) else "up"
    return Verdict("neutral", f"After this, the buffer lasts {runway_words(r.runway)}, {direction} from {in_sentence(runway_words(r.before.runway))}.", second)


def fact_lines(r, p):
    """One plain line per fact. The verdict already says the two runway-zero facts, so they aren't repeated."""
    text = {
        "layoff_doesnt_fit_pension": "Pension income: a layoff wouldn't stop this. The numbers apply the layoff as asked.",
        "income_cut_no_income": "No regular money in, so a lower income changes nothing here.",
        "bills_shock_no_bills": "No regular bills visible, so the standard (judges') formula changes nothing for this.",
        "bills_shock_too_small": "Standing orders show more bills than the standard (judges') figure, so this rise is understated.",
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
    if d.after_ends == "income_returns":
        return f"After month {d.benefit_months} we assume income returns to its typical level."
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
    return f"{'up' if change > 0 else 'down'} {months_word(abs(change))}"


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
        return f"With the maximum, the money lasts the full {months_word(d.months_asked)}."
    line = "With the maximum, there is no buffer before month 1." if d.runs_out_in_month == 0 else f"With the maximum, they run out in month {d.runs_out_in_month}."
    if backup is not None and backup.cut_to_last:
        line += f" Lasting the full {months_word(d.months_asked)} takes {money(backup.cut_to_last)} a month less spending."
    return line


def orders_row(r):
    judges = f"standard (judges'): {r.runway.label}"
    orders = r.bills_on_standing_orders
    if orders.applies:
        return OurRow("Runway with bills from standing orders", orders.runway.label, judges, (
            "Runway if the rise applies to monthly bills set up as standing orders. Some bills don't show in typical bills, so this base can be larger.",))
    return OurRow("Bills on standing orders", "n/a", None, (REASONS.get(orders.reason, orders.note),))


def our_rows(r, p, plan):
    judges = f"standard (judges'): {r.runway.label}"
    rows = []
    adjust = r.if_you_adjust
    if adjust.applies:
        rows.append(OurRow("Runway, if you adjust", adjust.runway.label, judges, (
            "An illustration, not a forecast. In some accounts in the data, spending fell when income fell. This lowers spending that way. The standard (judges') runway keeps spending flat.",)))
    else:
        rows.append(OurRow("Runway, if you adjust", "n/a", None, (REASONS.get(adjust.reason, adjust.note),)))
    capped = r.ei_capped
    if capped.available and capped.switched_on:
        lines = [f"Same shock, with EI capped at {money(capped.weekly_max)} a week ({money(capped.monthly_max)} a month)."]
        line = _capped_line(capped, plan.backup_capped)
        if line:
            lines.append(line)
        rows.append(OurRow("Runway with EI weekly maximum", capped.runway.label, judges, tuple(lines)))
    rows.append(orders_row(r))
    rows.append(OurRow("Current fixed costs", f"{money(p.current_fixed_costs)} a month", f"standard (judges') F: {money(p.F)}", (
        "Bills, insurance and the loan payment if still running.",)))
    rows.append(OurRow("Buffer in months of spending", "n/a" if p.buffer_months is None else f"{p.buffer_months:.1f} months", None, (
        "Buffer divided by typical spending. Shows savings without how much money passes through."
        if p.buffer_months is not None else "There is no buffer or no typical spending to divide by.",)))
    rows.append(OurRow("Lowest balance, last 6 months", money(p.lowest_balance), None, ("The lowest the balance got. An average can hide it.",)))
    rows.append(OurRow("Latest balance", money(p.latest_balance), f"standard (judges') buffer: {money(p.B)}", (
        f"The balance at the end of {p.last_month}. The buffer is an average over 6 months, so the two can differ.",)))
    rows.append(OurRow("Actual change, last 12 months", f"{signed_money(plan.goal.actual_change_last_12)} a month", f"typical month: {signed_money(p.I - p.S)}", (
        "What the balance really did, on average. Typical money in minus typical spending can differ, because each is a separate median.",)))
    return rows


# --- Plans (F, G) ---------------------------------------------------------------------------------------------------

def _judges_goal_lines(g):
    """The standard (judges') sentence for the goal at I - S (the flat GoalPlan fields)."""
    if g.state == "on_track":
        start = f"To have {months_word(g.target_months)} of spending (**{money(g.target_amount)}**) saved, set aside **{money(g.monthly_amount)} a month**."
        if g.months_to_goal > 120:
            return [f"{start} That takes more than 120 months."]
        if g.reaches_within_horizon:
            return [f"{start} That takes **{months_word(g.months_to_goal)}**."]
        return [f"{start} That takes **{months_word(g.months_to_goal)}**, more than 12 months."]
    reach = g.cut_to_reach_in_horizon
    if g.cut_to_break_even < 1:
        lines = [f"Money in only just covers spending. About **{money(reach)}** a month less would reach {money(g.target_amount)} in 12 months."]
    else:
        lines = [f"Money in doesn't cover spending, so saving starts with spending about **{money(g.cut_to_break_even)}** a month less. "
                 f"About **{money(reach)}** a month less would reach {money(g.target_amount)} in 12 months."]
    if reach <= g.flexible_spending:
        lines.append(f"That fits within the {money(g.flexible_spending)} of spending above fixed costs.")
    else:
        lines.append(f"That is more than the {money(g.flexible_spending)} of spending above fixed costs.")
    return lines


def _headline_goal_line(g, h):
    """NEW-COPY-20: the goal at the actual change over the last 12 months (our estimate)."""
    if h.state == "on_track":
        n = "more than 120 months" if h.months_to_goal > 120 else months_word(h.months_to_goal)
        return (f"At the actual change over the last 12 months ({money(h.monthly)} a month, our estimate), "
                f"{months_word(g.target_months)} of spending ({money(g.target_amount)}) takes {n} to save.")
    line = f"Over the last 12 months the balance changed by {money(h.monthly)} a month (our estimate), so at that pace the fund isn't reached."
    if h.cut_to_break_even is not None and h.cut_to_break_even >= 1:
        line += f" Saving starts with spending {money(h.cut_to_break_even)} a month less."
    return line


def goal_lines(plan):
    g, low = plan.goal, plan.low_balance
    lines = []
    if g.below_zero_by > 0:
        lines.append(f"First step: get the balance back above $0 ({money(g.below_zero_by)}).")
    if g.state == "no_regular_spending":
        lines.append("Not enough regular spending to set a target.")
    elif g.state == "already_there":
        lines.append(f"Already there: the buffer covers **{g.months_covered:.1f} months**.")
    else:
        if g.headline is not None:
            lines.append(_headline_goal_line(g, g.headline))
            judges = _judges_goal_lines(g)
            judges[0] = f"On the standard (judges') typical month ({money(g.surplus)} a month): {judges[0]}"
            lines.extend(judges)
        else:
            lines.extend(_judges_goal_lines(g))
    if any(f.code == "surplus_not_seen_in_balance" for f in plan.facts):
        lines.append(f"Money in is {money(g.surplus)} above spending, but over the last 12 months the balance changed by {money(g.actual_change_last_12)} a month on average. Treat the savings figure as the most this could be.")
    if any(f.code == "balance_rose_despite_gap" for f in plan.facts):
        lines.append(f"Typical spending is {money(-g.surplus)} above typical money in, but over the last 12 months the balance rose {money(g.actual_change_last_12)} a month on average. Typical months can overstate the gap, so the cut needed may be smaller.")
    if low is not None:
        lines.append(f"Keep the balance above one loan payment ({money(low.payment)}) at all times. Its lowest point in the last 6 months was {money(low.lowest_balance)}.")
    return lines


def _backup_core(plan):
    b = plan.backup
    n = b.through_months
    if b.state == "no_shock":
        return ["Pick a twist to see a backup plan."]
    if b.state == "no_buffer":
        return [f"There is no buffer. First, **{money(b.cover_needed)}** is needed to get back to $0."]
    if b.state == "no_cuts_needed":
        return [f"No cuts needed: the buffer lasts the full {months_word(n)}." if n else "No cuts needed: income still covers spending."]
    context = [f"Spending above fixed costs: {money(b.flexible_spending)} a month.",
               f"Current fixed costs, plus the bills rise: {money(b.fixed_costs)} a month."]
    if b.state == "cuts_not_enough":
        return [f"Even with all other spending cut, the buffer lasts **{runway_words(b.runway_if_all_flexible_cut)}**, short of {months_word(n)}.", *context]
    if b.cut_to_last is not None:
        share = b.cut_to_last_share_of_spending
        size = f", about {share:.0%} of typical spending" if share is not None else ""
        return [f"To last the full {months_word(n)}, spending needs to drop by **{money(b.cut_to_last)} a month**{size}.", *context]
    return [f"To stop the buffer falling, spending needs to drop by **{money(b.cut_to_close_gap)} a month**.", *context]


def _loan_backup_lines(plan):
    check = plan.backup.loan_end
    if check is None:
        return []
    if check.reason == "not_in_spending":
        low = plan.low_balance
        return [LOAN_NOT_IN_SPENDING.format(P=money(low.payment if low is not None else check.monthly_drop), N=check.payoff_month)]
    if check.reason != "applies":
        return []
    lines = [LOAN_BACKUP.format(N=check.payoff_month, payment=money(check.monthly_drop))]
    if check.makes_it_before:
        lines.append(LOAN_BACKUP_OK)
    elif check.before is not None:
        lines.append(LOAN_BACKUP_OUT.format(m=check.before.runs_out_in_month))
    if check.scheduled_only:
        lines.append(LOAN_SCHEDULED_ONLY.format(N=check.payoff_month))
    return lines


def backup_lines(plan):
    return [*_backup_core(plan), *_loan_backup_lines(plan)]


# --- J5 wording ------------------------------------------------------------------------------------------------------

ASSUMED_LENGTH = "The card gives no length, so this assumes 6 months, as on the first card."   # D2, R7: NEW-COPY-17
FOOTER = ("Data: PKDD'99 Discovery Challenge Financial dataset, from the CTU Relational Dataset Repository (https://relational.fel.cvut.cz/dataset/Financial). "
          "EI weekly maximum: Government of Canada (https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/benefit-amount.html). "
          "Method notes are in the docs folder.")   # R2: NEW-COPY-24


LOAN_BACKUP = "Counting the loan ending in month {N}, the monthly gap falls by {payment} from then (our estimate)."       # copy §7 P.loan_backup
LOAN_BACKUP_OK = "With that, they make it (our estimate)."
LOAN_BACKUP_OUT = "They still run out in month {m} (our estimate)."
LOAN_NOT_IN_SPENDING = ("The loan payment of {P} a month isn't in the standard (judges') typical spending yet, because the loan started recently, "
                        "so the standard (judges') figure doesn't rise when it ends in month {N} (our estimate).")                 # NEW-COPY-22
LOAN_SCHEDULED_ONLY = "The loan is behind, so month {N} is the scheduled end, not a certain one."                # P.loan_d


def months_word(n):
    """"1 month" when n == 1, else f"{n:g} months" (NEW-COPY-9)."""
    return "1 month" if n == 1 else f"{n:g} months"


def runway_words(runway):
    """"under 0.1 months" when state "months" and months == 0.0, else runway.label (R11, R21). Sentences only; labels keep "0.0 months"."""
    if runway.state == "months" and runway.months == 0.0:
        return "under 0.1 months"
    return runway.label


def in_sentence(label):
    """"No shortfall (120+)" -> "no shortfall (120+)" mid-sentence (R4)."""
    return label[:1].lower() + label[1:]


def oneoff_line(r):
    """D4, R6: NEW-COPY-18; None when r.one_off == 0."""
    if r.one_off == 0:
        return None
    dollars, multiple = r.shock.one_off_dollars, r.shock.one_off_spending_multiple
    if multiple <= 0:
        return f"One-off cost: {money(r.one_off)}."
    months = f"{months_word(multiple)} of typical spending before the shock ({money(r.before.spending)} a month)"
    if dollars <= 0:
        return f"One-off cost: {money(r.one_off)}, {months}."
    return f"One-off cost: {money(r.one_off)}: {money(dollars)} plus {months}."


def after_line(r):
    """R6: NEW-COPY-19."""
    return f"After the shock: money in {money(r.income_after)} a month, spending {money(r.spending_after)} a month."
