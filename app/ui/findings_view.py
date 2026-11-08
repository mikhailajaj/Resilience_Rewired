"""The Findings page's sentences, table rows and chart, from NEW-COPY-25 and NEW-COPY-31. No Streamlit here."""
import altair as alt
import numpy as np
import pandas as pd

from .charts import BLUE, INK, ORANGE, _configure
from .text import money

BIN = 10          # percent
LAST_BIN = 200    # percent: the last bin is "200%+"


class F:
    page = "Findings"
    head = "Biggest finding: spending doesn't stay flat after a shock"
    n_events = "Real income drops"
    n_kept = "Spending kept, median"
    n_below = "Below $0 after {months} months: formula vs real"
    below_value = "{predicted} predicted, {actual} real"
    line = ("The standard (judges') formula holds spending flat. In {events} real drops in money in, customers kept a median of {pct}% of their usual "
            "spending, so {actual} were below $0 after {months} months where the formula said {predicted}.")
    chart_title = "Spending kept during a real income drop"
    rule = "The formula assumes 100%"
    alt = "Histogram of spending kept in {events} income drops. The median is {pct}%."
    tier_head = "Spending kept, by starting buffer"
    tier_cols = ("Starting buffer", "Events", "Spending kept")
    f3 = ("Of the {fail} accounts that don't last 6 months on EI at 55%, {cuts} make it with cuts to their own spending, plus {lender} more "
          "if the lender agrees to pause the loan: {total} in all.")
    f4 = "{n} of the {m} accounts with more money in than spending on paper didn't grow their balance over the last 12 months."
    f5 = "{n} of {m} running loans don't show in typical spending yet, a median {P} a month."
    f6 = "{n} accounts live on a pension, where a layoff doesn't fit."
    spinner = "Working out the figures across all 4,500 accounts. This takes about a minute the first time."
    pointer = "More findings, with their limits, are in the notebooks below."
    refs_head = "References: the notebooks behind these findings"
    repo = "https://github.com/mikhailajaj/Resilience_Rewired/blob/main/"
    notebooks = (
        ("Discovery", "discovery.ipynb", "Tests the runway formula against what customers really did after an income drop."),
        ("Know the customer", "know_the_customer.ipynb", "Income, bills, fixed costs, buffer and runway for one account, and where the medians mislead."),
        ("Make a plan", "make_a_plan.ipynb", "The goal plan and the backup plan, built from each customer's own numbers."),
    )


def reference_lines():
    """One Markdown bullet per notebook, linked to the public repo on GitHub."""
    return [f"- [{name}]({F.repo}{path}): {about}" for name, path, about in F.notebooks]


def _pct(value):
    return f"{value * 100:.0f}"


def numbers(f):
    return [(F.n_events, f"{f.events:,}"), (F.n_kept, f"{_pct(f.spending_kept_median)}%"),
            (F.n_below.format(months=f.months), F.below_value.format(actual=f.actually_below_zero, predicted=f.predicted_below_zero))]


def lines(f):
    return [F.line.format(events=f.events, pct=_pct(f.spending_kept_median), actual=f.actually_below_zero, months=f.months,
                          predicted=f.predicted_below_zero)]


def tier_rows(f):
    return [(t.name, f"{t.events:,}", f"{_pct(t.spending_kept_median)}%") for t in f.tiers]


def account_lines(a):
    return [F.f3.format(fail=f"{a.ei6_runs_out:,}", cuts=f"{a.rescued_by_cuts:,}", lender=f"{a.rescued_with_lender:,}", total=f"{a.rescued_total:,}"),
            F.f4.format(n=f"{a.surplus_not_in_balance:,}", m=f"{a.surplus_accounts:,}"),
            F.f5.format(n=f"{a.loans_missed_by_medians:,}", m=f"{a.running_loans:,}", P=money(a.missed_payment_median)),
            F.f6.format(n=f"{a.pension_accounts:,}")]


def alt_text(f):
    return F.alt.format(events=f.events, pct=_pct(f.spending_kept_median))


def _bins(f):
    start = np.minimum(np.floor(np.asarray(f.spending_kept) * 100 / BIN) * BIN, LAST_BIN).astype(int)
    counts = pd.Series(start).value_counts().reindex(range(0, LAST_BIN + BIN, BIN), fill_value=0)
    return pd.DataFrame({"start": counts.index, "end": counts.index + BIN, "events": counts.to_numpy()})


def chart(f):
    bars = alt.Chart(_bins(f), title=F.chart_title).mark_bar(color=BLUE, stroke="white", strokeWidth=1).encode(
        x=alt.X("start:Q", title="Spending kept, % of usual", scale=alt.Scale(domain=[0, LAST_BIN + BIN], nice=False),
                axis=alt.Axis(values=list(range(0, LAST_BIN + BIN, 40)) + [LAST_BIN], grid=False, labelAngle=0,
                              labelExpr=f"datum.value >= {LAST_BIN} ? '{LAST_BIN}%+' : datum.value + '%'")),
        x2="end:Q", y=alt.Y("events:Q", title="Income drops", axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip("start:Q", title="From %"), alt.Tooltip("events:Q", title="Income drops")])
    mark = pd.DataFrame({"x": [100], "label": [F.rule]})
    rule = alt.Chart(mark).mark_rule(color=ORANGE, strokeWidth=2, strokeDash=[6, 4]).encode(x="x:Q")
    label = alt.Chart(mark).mark_text(align="left", dx=6, dy=-4, baseline="bottom", color=INK, fontSize=16, fontWeight=600).encode(
        x="x:Q", y=alt.value(0), text="label:N")
    return _configure(alt.layer(bars, rule, label))
