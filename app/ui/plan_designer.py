"""Region P, the plan designer: tick a plan, see the lines and one timeline. Every figure comes from design_plan and is worded by plan_text."""
import streamlit as st

from app.engine import EmergencyCost, InvalidPlanError, PlanRequest, SavingsGoal, TimeOff, design_plan
from app.engine.goals import MAX_INTEREST_PCT
from app.ui import charts, plan_text
from app.ui.plan_text import P
from app.ui.shared import caption, md

ss = st.session_state

PLAN_DEFAULTS = dict(goal_on=False, goal_name="car", amount=60000.0, deadline=0, interest=0.0,
                     off_on=False, months_off=24, em_on=False, cost=10000.0, order=[], table=False)


def request_from(values, target_months):
    """The request for the ticked plans, in tick order. A deadline of 0 means none; a blank name becomes "goal"."""
    ticked = {"goal": values["goal_on"], "off": values["off_on"]}
    items = []
    for kind in values["order"]:
        if not ticked.get(kind):
            continue
        if kind == "goal":
            deadline = int(values["deadline"])
            items.append(SavingsGoal(name=(values["goal_name"] or "").strip() or "goal", amount=float(values["amount"]),
                                     deadline_months=deadline if deadline > 0 else None))
        else:
            items.append(TimeOff(months_off=int(values["months_off"])))
    emergency = EmergencyCost(cost=float(values["cost"])) if values["em_on"] else None
    return PlanRequest(items=tuple(items), emergency=emergency, target_months=target_months, interest_pct=float(values["interest"]))


def plan_inputs():
    if "plan_inp" not in ss:
        ss.plan_inp = {**PLAN_DEFAULTS, "order": []}
    return ss.plan_inp


def sync_widgets():
    """Widgets disappear from session state when not drawn, so each run sets them from the one stored value."""
    inp = plan_inputs()
    for name in PLAN_DEFAULTS:
        if name != "order":
            ss[f"pd_{name}"] = inp[name]


def from_widget(name):
    value = ss[f"pd_{name}"]
    if value is not None:
        plan_inputs()[name] = value


def from_tick(name, kind):
    inp = plan_inputs()
    inp[name] = ss[f"pd_{name}"]
    if kind is None:
        return
    if inp[name] and kind not in inp["order"]:
        inp["order"].append(kind)
    elif not inp[name] and kind in inp["order"]:
        inp["order"].remove(kind)


def number(label, name, low, high, step, whole=False):
    st.number_input(label, low, high, step=step, key=f"pd_{name}", on_change=from_widget, args=(name,), format="%d" if whole else "%g")


def section(profile):
    inp = plan_inputs()
    sync_widgets()
    with st.container(key="plan-designer"):
        st.header(P.head, anchor=False)
        caption(P.cap)
        try:
            design = design_plan(profile.account_id, request_from(inp, inputs_target()))
        except InvalidPlanError as error:
            st.markdown(str(error))
            return
        for label, value, headline in plan_text.rate_rows(design.rates):
            md(f"**{label}: {value}**" if headline else f"{label}: {value}")
        caption(P.r_note)

        ticks = st.columns(3)
        ticks[0].checkbox(P.t_goal, key="pd_goal_on", on_change=from_tick, args=("goal_on", "goal"))
        ticks[1].checkbox(P.t_off, key="pd_off_on", on_change=from_tick, args=("off_on", "off"))
        ticks[2].checkbox(P.t_emergency, key="pd_em_on", on_change=from_tick, args=("em_on", None))

        if inp["goal_on"]:
            cols = st.columns(4, vertical_alignment="bottom")
            with cols[0]:
                st.text_input(P.i_name, key="pd_goal_name", max_chars=40, on_change=from_widget, args=("goal_name",))
            with cols[1]:
                number(P.i_amount, "amount", 0.0, 10_000_000.0, 1000.0)
            with cols[2]:
                number(P.i_deadline, "deadline", 0, 120, 1, whole=True)
            with cols[3]:
                number(P.i_interest, "interest", 0.0, float(MAX_INTEREST_PCT), 0.1)
            for goal in design.goals:
                for line in plan_text.goal_lines(design, goal):
                    md(line)
            rows = plan_text.wallet_rows(design)
            if rows:
                md(f"**{P.w_head}**")
                st.dataframe([{"Wallet": a, "Saved": b, "State": c} for a, b, c in rows], hide_index=True, width="stretch")
        if inp["off_on"]:
            number(P.i_months_off, "months_off", 1, 120, 1, whole=True)
            for line in plan_text.time_off_lines(design):
                md(line)
        if inp["em_on"]:
            number(P.i_cost, "cost", 0.0, 1_000_000.0, 100.0)
            for line in plan_text.emergency_lines(design):
                md(line)
        for line in (*plan_text.loan_lines(design), *plan_text.fact_lines(design)):
            md(line)

        st.subheader(P.tl_head, anchor=False)
        labels = {key: plan_text.rate_label(key) for key in ("actual", "judges", "lean")}
        st.altair_chart(charts.plan_timeline(design.timeline, labels, plan_text.MARKER_LETTER), width="stretch")
        caption(plan_text.timeline_alt(design))
        after = plan_text.after_cap_line(design)
        if after:
            caption(after)
        st.toggle(P.tl_table, key="pd_table", on_change=from_widget, args=("table",))
        if inp["table"]:
            st.dataframe(plan_text.table_rows(design), hide_index=True)


def inputs_target():
    """The J3 fund target the page already holds (the same box as the goal plan), never a shock input."""
    return ss.inp["target"]
