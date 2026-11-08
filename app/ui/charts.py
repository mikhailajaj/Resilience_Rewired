"""The charts, from docs/design/visual/charts.md."""
import altair as alt
import pandas as pd

from .text import money

BLUE, ORANGE, INK, MUTED, GRID = "#006BCE", "#F2691D", "#3A3835", "#716B60", "#E9E8E5"
HEIGHT = 320

# (columns, label, colour), bottom of the stack first. Validated as two palettes in this order.
MONEY_IN = ((("cash_deposits",), "Cash deposits", "#006BCE"), (("transfers_in",), "Transfers in", "#1baf7a"),
            (("interest_in",), "Interest", "#5598e7"), (("pension_in",), "Pension", "#008300"))
MONEY_OUT = ((("loan_payments",), "Loan payments", "#e34948"), (("household_bills",), "Household bills", "#eda100"),
             (("cash_withdrawals_genuine",), "Cash withdrawals", "#6250d6"), (("transfers_out_other",), "Other transfers out", "#F2691D"),
             (("insurance", "bank_fees"), "Insurance and bank fees", "#8F5A12"), (("card_withdrawals",), "Card withdrawals", "#e87ba4"))
KEPT_COLOUR = "#8B857B"


def _configure(chart):
    return (chart.properties(height=HEIGHT, padding={"right": 16, "top": 8, "left": 8, "bottom": 8})
            .configure_view(stroke=None)
            .configure(background="transparent", font="Figtree")
            .configure_axis(labelFont="Figtree", titleFont="Figtree", labelFontSize=18, titleFontSize=18, labelColor=INK, titleColor=INK,
                            gridColor=GRID, gridWidth=1, domainColor=MUTED, tickColor=MUTED)
            .configure_axisY(domain=False, ticks=False, labelPadding=8)
            .configure_legend(labelFont="Figtree", labelFontSize=18, labelColor=INK, symbolType="stroke", symbolStrokeWidth=3,
                              orient="top", title=None)
            .configure_title(font="Figtree", fontSize=20, fontWeight=700, color=INK, anchor="start"))


def _months(history):
    frame = history.copy()
    frame["date"] = pd.to_datetime(frame["month"].astype(str))
    return frame


def _x():
    return alt.X("date:T", title=None, axis=alt.Axis(format="%b %Y", tickCount={"interval": "month", "step": 6}, labelAngle=0, grid=False))


def money_in_out(history):
    frame = _months(history).rename(columns={"money_in": "Money in", "money_out": "Money out"})
    long = frame.melt(id_vars="date", value_vars=["Money in", "Money out"], var_name="series", value_name="amount")
    lines = alt.Chart(long, title="Money in and money out by month").mark_line(strokeWidth=2).encode(
        x=_x(),
        y=alt.Y("amount:Q", title=None, axis=alt.Axis(format="$,.0f", tickCount=5)),
        color=alt.Color("series:N", scale=alt.Scale(domain=["Money in", "Money out"], range=[BLUE, ORANGE])),
        tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"), alt.Tooltip("series:N", title="Series"), alt.Tooltip("amount:Q", title="Amount", format="$,.0f")],
    )
    return _configure(lines)


def lowest_month_end(history):
    frame = _months(history)
    row = frame.loc[frame["month_end_balance"].idxmin()]
    return row["date"], float(row["month_end_balance"])


def balance(history):
    frame = _months(history)
    when, low = lowest_month_end(history)
    label = f"Lowest: {money(low)} in {when:%b %Y}"
    line = alt.Chart(frame, title="Balance at the end of each month").mark_line(strokeWidth=2, color=BLUE).encode(
        x=_x(),
        y=alt.Y("month_end_balance:Q", title=None, axis=alt.Axis(format="$,.0f", tickCount=5)),
        tooltip=[alt.Tooltip("date:T", title="Month", format="%b %Y"), alt.Tooltip("month_end_balance:Q", title="Balance", format="$,.0f")],
    )
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=MUTED, strokeWidth=1).encode(y="y:Q")
    point_data = pd.DataFrame({"date": [when], "amount": [low], "label": [label]})
    point = alt.Chart(point_data).mark_circle(size=140, color=INK, stroke="white", strokeWidth=2, opacity=1).encode(x="date:T", y="amount:Q")
    share = (when - frame["date"].min()) / max(frame["date"].max() - frame["date"].min(), pd.Timedelta(days=1))
    text = alt.Chart(point_data).mark_text(fontSize=18, color=INK, font="Figtree", dy=-16, align="right" if share > 0.5 else "left").encode(x="date:T", y="amount:Q", text="label:N")
    return _configure(zero + line + point + text)


def _share_text(share):
    """Never rounds a small share to 0%, or a share that isn't the whole to 100%."""
    if 0 < share < 0.01:
        return "under 1%"
    return "over 99%" if 0.99 < share < 1 else f"{share:.0%}"


def payee_split(history):
    """Where money in went: one row per payee, plus what stayed in the account. Shares are of money in, or of money out if that's larger."""
    total_in, total_out = float(history.money_in.sum()), float(history.money_out.sum())
    whole = max(total_in, total_out)
    rows = [(label, colour, float(history[list(columns)].sum().sum())) for columns, label, colour in MONEY_OUT]
    rows.append(("Left in the account", KEPT_COLOUR, max(total_in - total_out, 0.0)))
    kept = [(label, colour, amount) for label, colour, amount in rows if amount >= 0.005]
    frame = pd.DataFrame([{"item": label, "colour": colour, "amount": amount, "share": amount / whole, "order": i,
                           "label": f"{label}, {_share_text(amount / whole)}", "amount_text": money(amount)}
                          for i, (label, colour, amount) in enumerate(kept)])
    return total_in, total_out, frame


def payee_pie(history):
    total_in, total_out, frame = payee_split(history)
    title = f"Where the {money(total_in)} of money in went" if total_in >= total_out else f"Where {money(total_out)} went: {money(total_out - total_in)} more than came in"
    pie = alt.Chart(frame, title=title).mark_arc(stroke="white", strokeWidth=2).encode(
        theta=alt.Theta("amount:Q", stack=True),
        order=alt.Order("order:Q"),
        color=alt.Color("label:N", sort=frame["label"].tolist(), scale=alt.Scale(domain=frame["label"].tolist(), range=frame["colour"].tolist()),
                        legend=alt.Legend(orient="right", title=None, symbolType="square", labelLimit=320)),
        tooltip=[alt.Tooltip("item:N", title="Payee"), alt.Tooltip("amount_text:N", title="Total"), alt.Tooltip("share:Q", title="Share", format=".1%")],
    )
    return _configure(pie).properties(height=340)


def monthly_stacks(history, series, side):
    """One row per month and type, in stacking order."""
    frame = _months(history)
    frame["month_label"] = frame["date"].dt.strftime("%b %Y")
    rows = []
    for order, (columns, label, _) in enumerate(series):
        amounts = frame[list(columns)].sum(axis=1)
        if amounts.sum() <= 0:
            continue
        rows.append(pd.DataFrame({"month_label": frame["month_label"], "side": side, "item": label, "amount": amounts, "order": order}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["month_label", "side", "item", "amount", "order"])


def monthly_in_out(history):
    """Two columns a month: money in by type on the left, money out on the right with the loan at the bottom."""
    labels = _months(history)["date"].dt.strftime("%b %Y").tolist()
    x = alt.X("month_label:N", title=None, sort=labels, scale=alt.Scale(domain=labels, paddingInner=0.25),
              axis=alt.Axis(values=labels[::6], labelAngle=0, grid=False, ticks=False))

    def layer(series, side, legend_columns):
        frame = monthly_stacks(history, series, side)
        shown = [(label, colour) for _, label, colour in series if label in set(frame["item"])]
        return alt.Chart(frame).mark_bar(stroke="white", strokeWidth=1).encode(
            x=x,
            xOffset=alt.XOffset("side:N", scale=alt.Scale(domain=["Money in", "Money out"])),
            y=alt.Y("amount:Q", title=None, stack="zero", axis=alt.Axis(format="$,.0f", tickCount=5)),
            order=alt.Order("order:Q"),
            color=alt.Color("item:N", sort=[s[0] for s in shown], scale=alt.Scale(domain=[s[0] for s in shown], range=[s[1] for s in shown]),
                            legend=alt.Legend(title=side, orient="bottom", direction="horizontal", titleFont="Figtree", titleFontSize=18, titleFontWeight=700,
                                              titleColor=INK, titleOrient="left", symbolType="square", columns=legend_columns, labelLimit=320)),
            tooltip=[alt.Tooltip("month_label:N", title="Month"), alt.Tooltip("side:N", title="Column"), alt.Tooltip("item:N", title="Type"),
                     alt.Tooltip("amount:Q", title="Amount", format="$,.0f")],
        )

    chart = alt.layer(layer(MONEY_IN, "Money in", 2), layer(MONEY_OUT, "Money out", 3), title="Money in and money out by month").resolve_scale(color="independent")
    return _configure(chart).properties(height=430)


PLAN_COLOURS = {"actual": BLUE, "judges": MUTED, "lean": ORANGE}
PLAN_DASH = {"actual": [1, 0], "judges": [6, 4], "lean": [1, 0]}


def plan_timeline(timeline, rate_labels, marker_letter):
    """One line per saving rate, month 0 to the horizon, with a letter marker on the line where each event happens."""
    rows = [{"month": m, "rate": rate_labels[line.rate], "balance": float(b)} for line in timeline.lines for m, b in enumerate(line.balance)]
    frame = pd.DataFrame(rows)
    domain = [rate_labels[line.rate] for line in timeline.lines]
    colour = alt.Color("rate:N", sort=domain, scale=alt.Scale(domain=domain, range=[PLAN_COLOURS[line.rate] for line in timeline.lines]),
                       legend=alt.Legend(orient="top", title=None, symbolType="stroke", labelLimit=420))
    x = alt.X("month:Q", title="Month", axis=alt.Axis(grid=False, tickMinStep=1, format="d"), scale=alt.Scale(domain=[0, timeline.horizon], nice=False))
    y = alt.Y("balance:Q", title=None, axis=alt.Axis(format="$,.0f", tickCount=5))
    lines = alt.Chart(frame).mark_line(strokeWidth=2).encode(
        x=x, y=y, color=colour, strokeDash=alt.StrokeDash("rate:N", sort=domain, legend=None,
                                                          scale=alt.Scale(domain=domain, range=[PLAN_DASH[line.rate] for line in timeline.lines])),
        tooltip=[alt.Tooltip("month:Q", title="Month"), alt.Tooltip("rate:N", title="Rate"), alt.Tooltip("balance:Q", title="Balance", format="$,.0f")])
    by_rate = {line.rate: line.balance for line in timeline.lines}
    marks = []
    for event in timeline.events:
        if event.month is None:
            continue
        balance = by_rate[event.rate or "actual"]
        marks.append({"month": event.month, "balance": float(balance[event.month]), "letter": marker_letter[event.code], "code": event.code})
    layers = [lines]
    if marks:
        data = pd.DataFrame(marks)
        layers.append(alt.Chart(data).mark_circle(size=170, color=INK, stroke="white", strokeWidth=2, opacity=1).encode(x="month:Q", y="balance:Q"))
        layers.append(alt.Chart(data).mark_text(fontSize=14, fontWeight=700, color=INK, dy=-16, font="Figtree").encode(x="month:Q", y="balance:Q", text="letter:N"))
    return _configure(alt.layer(*layers))
