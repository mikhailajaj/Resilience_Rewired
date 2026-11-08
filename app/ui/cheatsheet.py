"""Typed twist cheatsheet: the phrases the chat parser accepts, with {variable} slots.

Source: docs/design/ux/chat_parser.md (grammar and PT-01..PT-25). No Streamlit here, so tests can check every row.
Each row: (what to type, the engine field it sets, an example, the Shock the example means).
"""
from app.engine import IncomeCut, Shock
from app.engine.shock import MAX_MONTHS

TEMPLATES = (
    ("laid off, EI {keep_pct}% for {months} months", "income_cut = IncomeCut({keep_pct}/100, {months})",
     "laid off, EI 55% for 6 months", Shock(income_cut=IncomeCut(0.55, 6))),
    ("laid off, EI {keep_pct}% until it runs out", "income_cut.months = None (open-ended)",
     "laid off, EI 55% until it runs out", Shock(income_cut=IncomeCut(0.55, None))),
    ("laid off, EI {keep_pct}% for {months} months, then back to work", 'income_cut.after_ends = "income_returns"',
     "laid off, EI 55% for 6 months, then back to work", Shock(income_cut=IncomeCut(0.55, 6, after_ends="income_returns"))),
    ("laid off, no EI, for {months} months", "income_cut.keep_fraction = 0",
     "laid off, no EI, for 3 months", Shock(income_cut=IncomeCut(0, 3))),
    ("income drops to {keep_pct}% for {months} months", "income_cut.keep_fraction = {keep_pct}/100",
     "income drops to 70% for three months", Shock(income_cut=IncomeCut(0.7, 3))),
    ("income cut by {cut_pct}% for {months} months", "income_cut.keep_fraction = (100 − {cut_pct})/100",
     "income cut by 30% for 3 months", Shock(income_cut=IncomeCut(0.7, 3))),
    ("bills up {bills_pct}%", "bills_increase_pct = {bills_pct}",
     "rent or household bills go up 15%", Shock(bills_increase_pct=15)),
    ("rent up ${dollars} a month", "other_spending_change = {dollars}",
     "rent up $300 a month", Shock(other_spending_change=300)),
    ("{thing} repair costs {n} month(s) of their spending", "one_off_spending_multiple = {n}",
     "the furnace repair costs a full month of their typical spending", Shock(one_off_spending_multiple=1)),
    ("{thing} repair ${dollars}", "one_off_dollars = {dollars}",
     "car repair $2,500", Shock(one_off_dollars=2500)),
    ("laid off, EI {keep_pct}% for {months} months and bills up {bills_pct}%", "income cut + bills_increase_pct",
     "laid off, EI 55% for 6 months and bills up 15%", Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15)),
    ("lose their job (EI {keep_pct}%) and bills go up {bills_pct}%", "length assumed 6 months (income cut + bills_increase_pct)",
     "They lose their job (EI at 55%) and their household bills go up 15%", Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15)),
)

VARIABLES = (
    ("{keep_pct}", "Share of usual income kept, with a % sign", "0 to 100. EI pays 55"),
    ("{cut_pct}", "Share of income lost, with a % sign", "0 to 100"),
    ("{months}", "How long the lower income lasts", f"Whole number, 1 to {MAX_MONTHS}. Digits, number words (one to twenty, tens, fifty-five), \"a year\" or \"half a year\""),
    ("{bills_pct}", "Rise on the usual household bills, with a % sign", "0 or more"),
    ("{dollars}", "A dollar amount", "$2,500, 2500 dollars or $1.5k"),
    ("{n}", "Months of the customer's typical spending", "0 or more. \"a full month\" = 1"),
    ("{thing}", "Any repair word", "furnace, roof, car, surprise cost, one-off"),
)

AVOID = (
    ('"income drops 30%" — say "drops **to** 70%" or "cut **by** 30%"'),
    ('"bills down 10%" — only rises are supported'),
    ('"0.55" — write it as "55%"'),
    ('a calendar month, such as "in January" — use More options on this page'),
    ('the same kind twice, such as "bills up 15% and rent up 10%"'),
)


def _esc(cell):
    """Escape $ outside code spans, so Streamlit doesn't read it as LaTeX; inside backticks it stays literal."""
    parts = cell.split("`")
    return "`".join(p if i % 2 else p.replace("$", r"\$") for i, p in enumerate(parts))


def markdown():
    """The cheatsheet as Markdown, ready for st.markdown."""
    rows = ["| Type this | Sets | Example |", "| :-- | :-- | :-- |"]
    rows += [f"| `{t}` | `{field}` | {example} |" for t, field, example, _ in TEMPLATES]
    vars_ = ["| Slot | Means | Allowed |", "| :-- | :-- | :-- |"]
    vars_ += [f"| `{v}` | {meaning} | {allowed} |" for v, meaning, allowed in VARIABLES]
    avoid = [f"- {line}" for line in AVOID]
    out = "\n".join(rows + ["", "**Slots**", ""] + vars_ + ["", "**The chat won't guess on these; it offers the buttons instead**", ""] + avoid
                     + ["", "Join two twists with **and**. The chat always shows how it read your text before it runs anything."])
    return "\n".join(_esc(line) for line in out.split("\n"))
