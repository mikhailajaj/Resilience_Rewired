"""Shock and plan: know the customer, take a shock, make a plan. Layout follows docs/design/ux/wireframes.md, regions B to H."""
import html

import streamlit as st

from app.engine import EI_WEEKLY_MAX_2026, IncomeCut, Shock, account_flows, apply_shock, get_profile, make_plan, monthly_history
from app.ui import charts, cheatsheet, plan_designer, text
from app.ui.shared import caption, md, raw

PAIRS = {  # name: (label, slider low, slider high, slider step, box low, box high)
    "income": ("Income kept (%)", 0.0, 100.0, 1.0, 0.0, 100.0),
    "months": ("Income stays lower for (months)", 1, 24, 1, 1, 120),
    "bills": ("Household bills up (%)", 0.0, 50.0, 1.0, 0.0, 500.0),
    "target": ("Emergency fund target (months of spending)", 1.0, 12.0, 1.0, 0.5, 120.0),
}
DEFAULTS = dict(income=100.0, months=6, bills=0.0, target=3.0, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0,
                ei_on=False, ei_max=float(EI_WEEKLY_MAX_2026), start="Not set")
PRESETS = (  # name, the inputs it sets. Every preset sets every shock input; only Reset turns the EI switch off.
    ("Laid off, EI 55%", dict(income=55.0, months=6, bills=0.0, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0)),
    ("Furnace dies", dict(income=100.0, months=6, bills=0.0, dollars_month=0.0, oneoff_months=1.0, oneoff_dollars=0.0)),
    ("Laid off + bills up 15%", dict(income=55.0, months=6, bills=15.0, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0)),
    ("Rent or bills up", dict(income=100.0, months=6, bills=15.0, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0)),
)
RESET_NAME = "Reset (no shock)"
RESET = dict(income=100.0, months=6, bills=0.0, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0, ei_on=False, ei_max=float(EI_WEEKLY_MAX_2026), start="Not set")
MONTH_NAMES = ["Not set", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
SINGLES = ("dollars_month", "oneoff_months", "oneoff_dollars", "ei_on", "ei_max", "start")

ss = st.session_state


def inputs():
    if "inp" not in ss:
        ss.inp = dict(DEFAULTS)
    return ss.inp


def clamp(value, low, high):
    return max(low, min(high, value))


def sync_widgets():
    """Widgets disappear from session state when not drawn, so each run sets them from the one stored value."""
    inp = inputs()
    for name, (_, s_low, s_high, _, _, _) in PAIRS.items():
        ss[f"s_{name}"] = clamp(inp[name], s_low, s_high)
        ss[f"n_{name}"] = inp[name]
    for name in SINGLES:
        ss[f"w_{name}"] = inp[name]


def from_pair(name, widget):
    value = ss[f"{widget}_{name}"]
    if value is not None:
        inputs()[name] = value


def from_single(name):
    value = ss[f"w_{name}"]
    if value is None:
        return
    inp = inputs()
    inp[name] = value
    if name == "oneoff_dollars" and value > 0:      # Last edit wins, so a typed repair doesn't add to a leftover slider.
        inp["oneoff_months"] = 0.0
    if name == "oneoff_months" and value > 0:
        inp["oneoff_dollars"] = 0.0


def apply_preset(values):
    inputs().update(values)


def selected_name():
    inp = inputs()
    for name, values in PRESETS:
        if all(inp[k] == v for k, v in values.items()):
            return name
    if all(inp[k] == RESET[k] for k in ("income", "bills", "dollars_month", "oneoff_months", "oneoff_dollars")):
        return RESET_NAME
    return None


def build_shock():
    inp = inputs()
    cut = None
    if inp["income"] < 100:
        cut = IncomeCut(keep_fraction=inp["income"] / 100, months=int(inp["months"]), ei_weekly_max=inp["ei_max"] if inp["ei_on"] else None)
    start = MONTH_NAMES.index(inp["start"]) or None
    return Shock(income_cut=cut, bills_increase_pct=inp["bills"], other_spending_change=inp["dollars_month"],
                 one_off_dollars=inp["oneoff_dollars"], one_off_spending_multiple=inp["oneoff_months"], start_month=start)


def region_b(p):
    st.subheader(f"Customer {p.account_id}", anchor=False)
    caption(f"Data from {p.first_month} to {p.last_month}. Income type: {p.income_type} (our label).")
    with st.container(key="summary"):
        md(text.summary_line(p))
    md(text.flow_line(p, account_flows(p.account_id)))
    tiles = st.columns(4)
    tiles[0].metric("Typical money in", text.money(p.I), border=True)
    tiles[1].metric("Typical spending", text.money(p.S), border=True)
    tiles[2].metric("Buffer", text.money(p.B), border=True, help="Average daily balance over the last 6 months.")
    tiles[3].metric("Runway, no shock", p.runway.label, border=True)
    row = st.columns(3)
    row[0].metric("Household bills", text.money(p.H))
    row[1].metric("Typical fixed costs (standard)", text.money(p.F))
    row[2].metric("Loan payment", text.money(p.P))
    for line in text.notes(p)[:3]:
        md(f"- {line}")


def pair(name, help_line, disabled=False):
    label, s_low, s_high, s_step, b_low, b_high = PAIRS[name]
    whole = isinstance(s_step, int)
    left, right = st.columns([3, 1], vertical_alignment="bottom")
    left.slider(label, s_low, s_high, step=s_step, key=f"s_{name}", on_change=from_pair, args=(name, "s"), disabled=disabled, format="%d" if whole else "%g")
    right.number_input(f"{label}, typed", b_low, b_high, step=1 if whole else 1.0, key=f"n_{name}", on_change=from_pair, args=(name, "n"),
                       disabled=disabled, format="%d" if whole else "%g", label_visibility="collapsed")
    caption(help_line)


def region_c(result):
    st.header("Pick a twist", anchor=False)
    caption("Or type your own sizes below.")
    with st.expander("Cheatsheet: how to type a twist card in the chat"):
        st.markdown(cheatsheet.markdown())
    inp, selected = inputs(), selected_name()
    cols = st.columns(len(PRESETS) + 1)
    for col, (name, values) in zip(cols, PRESETS):
        chosen = name == selected
        col.button(f"✓ {name}" if chosen else name, key=f"preset_{name}", type="primary" if chosen else "secondary",
                   on_click=apply_preset, args=(values,), width="stretch")
    cols[-1].button(RESET_NAME, key="preset_reset", type="tertiary", on_click=apply_preset, args=(RESET,), width="stretch")
    st.markdown(f"**Selected: {selected}**" if selected else "**Custom**")
    if selected == "Laid off + bills up 15%":
        caption(text.ASSUMED_LENGTH)

    no_cut = inp["income"] >= 100
    left, right = st.columns(2, gap="large")
    with left:
        pair("income", "100 means no change. EI pays 55%. Type any number.")
        pair("months", "Not used while income is unchanged." if no_cut else "How long the lower income lasts. Slider to 24, type up to 120.", disabled=no_cut)
        switch, amount = st.columns([3, 2], vertical_alignment="bottom")
        switch.toggle("Apply the EI weekly maximum", key="w_ei_on", on_change=from_single, args=("ei_on",), disabled=no_cut)
        amount.number_input("Weekly maximum ($)", 1.0, 5000.0, step=1.0, key="w_ei_max", on_change=from_single, args=("ei_max",), disabled=no_cut or not inp["ei_on"], format="%g")
        caption("Not used while income is unchanged." if no_cut else
                f"{'On' if inp['ei_on'] else 'Off'}. It starts off, to match the standard (judges') figures. When on, the extra runway in \"Our numbers\" caps EI at the weekly maximum. $729 a week is the 2026 maximum.")
    with right:
        pair("bills", "Percent on the customer's usual bills. Slider to 50, type up to 500.")
        st.number_input("Bills or rent up ($ a month)", 0.0, 20000.0, step=50.0, key="w_dollars_month", on_change=from_single, args=("dollars_month",), format="%g")
        caption('For a card with a dollar amount, like "rent up $300".')
        months, dollars = st.columns(2, vertical_alignment="bottom")
        months.slider("One-off cost (months of spending)", 0.0, 3.0, step=0.25, key="w_oneoff_months", on_change=from_single, args=("oneoff_months",), format="%g")
        dollars.number_input("One-off cost ($)", 0.0, 100000.0, step=100.0, key="w_oneoff_dollars", on_change=from_single, args=("oneoff_dollars",), format="%g")
        caption("Paid once, at the start. Using one clears the other.")
        line = text.oneoff_line(result)
        if line:
            md(line)
        with st.expander("More options"):
            st.selectbox("Shock starts in", MONTH_NAMES, key="w_start", on_change=from_single, args=("start",))
            caption("Optional. If the shock runs into January, a note shows this customer's typical January spending. It doesn't change any number on the page.")


def region_d_verdict(result, profile):
    v = text.verdict(result)
    key = {"ok": "verdict-ok", "bad": "verdict-bad", "neutral": "verdict"}[v.tone]
    glyph = {"ok": "✓ ", "bad": "✕ ", "neutral": ""}[v.tone]
    with st.container(key=key):
        md(glyph + v.sentence)
    if v.second_line:
        with st.container(key="summary-verdict"):
            md(v.second_line)
    for line in text.fact_lines(result, profile):
        md(line)


def region_d_cards(r):
    shocked = not r.no_shock
    before, after = st.columns(2, gap="medium")
    with before.container(key="before"):
        st.html('<div class="rr-eyebrow">Before</div>')
        with st.container(key="runway-before"):
            st.metric("Runway", r.before.runway.label)
        cols = st.columns(3)
        cols[0].metric("Money in", text.money(r.before.income))
        cols[1].metric("Spending", text.money(r.before.spending))
        cols[2].metric("Buffer", text.money(r.before.buffer))
    with after.container(key="after"):
        st.html('<div class="rr-eyebrow">After</div>')

        def metric(place, label, value, delta):
            # Words carry the direction, so there's no arrow to read as good or bad.
            place.metric(label, value, delta=delta if shocked else None, delta_color="off", delta_arrow="off")

        with st.container(key="runway-after"):
            metric(st, "Runway", r.after.runway.label, text.runway_delta(r.before.runway, r.after.runway))
        cols = st.columns(3)
        metric(cols[0], "Money in", text.money(r.after.income), text.money_delta(r.before.income, r.after.income))
        metric(cols[1], "Spending", text.money(r.after.spending), text.money_delta(r.before.spending, r.after.spending))
        metric(cols[2], "Buffer left", text.money(r.after.buffer), text.money_delta(r.before.buffer, r.after.buffer))
    raw("rr-gap rr-num", f"Monthly gap  {text.money(r.before.gap)} -> {text.money(r.after.gap)}")
    line = text.assumption_line(r)
    if line:
        caption(line)


def region_e(result, profile, plan):
    with st.container(key="ours"):
        st.subheader("Our estimates, shown beside the standard (judges') figures", anchor=False)
        caption("They never replace the standard (judges') figures.")
        rows = text.our_rows(result, profile, plan)
        cols = st.columns(3, gap="medium")
        for i, row in enumerate(rows):
            with cols[i % 3]:
                raw("rr-label", row.label)
                counterpart = f' <span class="rr-counterpart">({html.escape(row.counterpart)})</span>' if row.counterpart else ""
                st.html(f'<div class="rr-our-value rr-num">{html.escape(row.value)}{counterpart}</div>')
                for line in row.lines:
                    caption(line)


def region_f(plan):
    goal = plan.goal
    with st.container(key="plan-f", border=True):
        st.header("Goal plan: build an emergency fund", anchor=False)
        caption("Before any shock")
        pair("target", "Default 3. Type any number.")
        if goal.target_amount is not None:
            md(f"Target: **{text.money(goal.target_amount)}**")
        with st.container(key="plan-sentence"):
            lines = text.goal_lines(plan)
            md(lines[0])
        for line in lines[1:]:
            md(line)
        if goal.savings_path:
            st.markdown("**Savings path**")
            st.dataframe([{"Month": p.month, "Balance": text.money(p.balance)} for p in goal.savings_path], hide_index=True, width="stretch")


def region_g(plan):
    backup = plan.backup
    with st.container(key="plan-g", border=True):
        st.header("Backup plan: if this happens", anchor=False)
        lines = text.backup_lines(plan)
        with st.container(key="plan-sentence-g"):
            if backup.state == "no_shock":
                caption(lines[0])
            else:
                md(lines[0])
        for line in lines[1:]:
            md(line)
        if backup.steps:
            st.markdown("**Steps, in order**")
            md("\n".join(f"{s.order}. {s.action}" for s in backup.steps))


def region_h(profile):
    history = monthly_history(profile.account_id)
    with st.expander("Details: charts, tables and all notes", expanded=False):
        chart_tab, table_tab, note_tab = st.tabs(["Charts", "Tables", "Notes"])
        with chart_tab:
            when, low = charts.lowest_month_end(history)
            st.altair_chart(charts.money_in_out(history), width="stretch")
            caption(f"Line chart of money in and money out each month for customer {profile.account_id}. Lowest month-end balance was {text.money(low)} in {when:%b %Y}.")
            st.altair_chart(charts.balance(history), width="stretch")
            caption("Line chart of the account balance by month.")
        with table_tab:
            md("**Last 6 months against all months**")
            rows = [("Typical money in", profile.last_6.I, profile.I), ("Typical spending", profile.last_6.S, profile.S),
                    ("Household bills", profile.last_6.H, profile.H), ("Fixed costs", profile.last_6.F, profile.F)]
            st.dataframe([{"Measure": n, "Last 6 months": text.money(a), "All months": text.money(b)} for n, a, b in rows], hide_index=True, width="stretch")
        with note_tab:
            lines = text.notes(profile)
            md("\n".join(f"- {line}" for line in lines) if lines else "No notes for this customer.")


inputs()
sync_widgets()
account = ss.get("shown_id")
if not account:
    if not ss.get("id_error"):
        st.markdown("Enter an account ID to start. You will see their money, a shock you can change, and a plan.")
    st.stop()

profile = get_profile(account)
shock = build_shock()
through = shock.income_cut.months if shock.income_cut else None
result = apply_shock(account, shock, through_months=through)
plan = make_plan(account, shock, target_months=inputs()["target"], through_months=through)

region_b(profile)
region_c(result)
region_d_verdict(result, profile)
region_d_cards(result)
region_e(result, profile, plan)
goal, backup = st.columns(2, gap="large")
with goal:
    region_f(plan)
with backup:
    region_g(plan)
region_h(profile)
plan_designer.section(profile)
caption(text.FOOTER)
