"""Plan designer UI (region P): J5.1 to J5.4, AC-11 to AC-16, RU-11, OI-19 (interest cap)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.engine import SavingsGoal, TimeOff, design_plan
from app.engine.goals import MAX_INTEREST_PCT
from app.ui import plan_text, text
from app.ui.plan_designer import PLAN_DEFAULTS, request_from
from app.ui.plan_text import P

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def page(at):
    return "\n".join(str(e.value) for group in (at.markdown, at.caption, at.text, at.subheader, at.header) for e in group).replace("\\$", "$")


def show(account):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="typed_id").set_value(str(account))
    at.button(key="FormSubmitter:picker-Show customer").click().run()
    assert not at.exception
    return at


def tick(at, key, value=True):
    at.checkbox(key=key).set_value(value).run()
    assert not at.exception
    return at


def values(**changes):
    return {**PLAN_DEFAULTS, "order": [], **changes}


# --- request_from (pure) -------------------------------------------------------------------------------------------

def test_request_from_nothing_ticked_is_empty_AC11():
    r = request_from(values(), 3.0)
    assert r.items == () and r.emergency is None and r.target_months == 3.0 and r.interest_pct == 0.0


def test_request_from_goal_deadline_zero_means_none_and_blank_name_is_goal_J5_1():
    r = request_from(values(goal_on=True, order=["goal"], goal_name="  "), 3.0)
    assert r.items == (SavingsGoal("goal", 60000.0, None),)
    r = request_from(values(goal_on=True, order=["goal"], deadline=24, goal_name=" car "), 3.0)
    assert r.items == (SavingsGoal("car", 60000.0, 24),)


def test_request_from_follows_the_tick_order_RU24():
    goal_first = request_from(values(goal_on=True, off_on=True, order=["goal", "off"]), 3.0)
    off_first = request_from(values(goal_on=True, off_on=True, order=["off", "goal"]), 3.0)
    assert [type(i) for i in goal_first.items] == [SavingsGoal, TimeOff]
    assert [type(i) for i in off_first.items] == [TimeOff, SavingsGoal]


def test_request_from_emergency_is_outside_the_order_and_interest_passes_through_OI18():
    r = request_from(values(em_on=True, cost=500.0, interest=4.5, order=[]), 6.0)
    assert r.items == () and r.emergency.cost == 500.0 and r.interest_pct == 4.5 and r.target_months == 6.0


def test_request_from_ignores_unticked_entries_in_the_order():
    assert request_from(values(order=["goal", "off"]), 3.0).items == ()


# --- the page ------------------------------------------------------------------------------------------------------

def test_header_comes_after_the_details_expander_AC11():
    at = show(20111)
    assert [e.label for e in at.expander][-1].startswith("Details")
    headers = [h.value for h in at.header]
    assert P.head in headers and headers.index(P.head) == len(headers) - 1
    assert P.head in page(at)


def test_nothing_ticked_shows_the_rate_rows_only_AC11():
    at = show(20111)
    body = page(at)
    for label, value, _ in plan_text.rate_rows(design_plan(20111).rates):
        assert f"{label}: {value}" in body
    assert all(n.key != "pd_amount" for n in at.number_input)
    assert [c.value for c in at.checkbox if c.key.startswith("pd_")] == [False, False, False]


def test_savings_goal_lines_all_appear_AC12():
    at = show(20111)
    tick(at, "pd_goal_on")
    request = request_from(values(goal_on=True, order=["goal"]), 3.0)
    design = design_plan(20111, request)
    body = page(at)
    lines = plan_text.goal_lines(design, design.goals[0])
    assert lines and all(line in body for line in lines)
    assert "$8,187" in body or "$8,188" in body


def test_deadline_lines_and_chart_and_table_AC12_AC15():
    at = show(20111)
    tick(at, "pd_goal_on")
    at.number_input(key="pd_deadline").set_value(24).run()
    assert not at.exception
    request = request_from(values(goal_on=True, order=["goal"], deadline=24), 3.0)
    design = design_plan(20111, request)
    body = page(at)
    for line in plan_text.goal_lines(design, design.goals[0]):
        assert line in body
    assert len(at.get("vega_lite_chart")) >= 3
    assert plan_text.timeline_alt(design) in body
    at.toggle(key="pd_table").set_value(True).run()
    assert not at.exception
    frames = at.dataframe
    table = [f for f in frames if "Month" in f.value.columns]
    assert table and len(table[-1].value) <= 121


def test_tick_order_changes_the_request_RU24():
    at = show(20111)
    tick(at, "pd_goal_on")
    tick(at, "pd_off_on")
    assert at.session_state["plan_inp"]["order"] == ["goal", "off"]
    tick(at, "pd_goal_on", False)
    tick(at, "pd_goal_on")
    assert at.session_state["plan_inp"]["order"] == ["off", "goal"]


def test_unticking_removes_the_item():
    at = show(20111)
    tick(at, "pd_off_on")
    tick(at, "pd_off_on", False)
    assert at.session_state["plan_inp"]["order"] == []


def test_a_customer_change_keeps_the_ticks():
    at = show(20111)
    tick(at, "pd_goal_on")
    at.text_input(key="typed_id").set_value("66505")
    at.button(key="FormSubmitter:picker-Show customer").click().run()
    assert not at.exception
    assert at.checkbox(key="pd_goal_on").value is True
    assert at.session_state["plan_inp"]["order"] == ["goal"]


def test_a_shock_preset_does_not_change_the_plan_lines_RU11():
    at = show(20111)
    tick(at, "pd_goal_on")
    request = request_from(values(goal_on=True, order=["goal"]), 3.0)
    design = design_plan(20111, request)
    lines = plan_text.goal_lines(design, design.goals[0])
    before = page(at)
    at.button(key="preset_Laid off, EI 55%").click().run()
    assert not at.exception
    after = page(at)
    assert all(line in after for line in lines if line in before)


def test_interest_box_is_capped_and_defaults_to_zero_OI19():
    at = show(20111)
    tick(at, "pd_goal_on")
    box = at.number_input(key="pd_interest")
    assert box.max == MAX_INTEREST_PCT and box.value == 0 and box.step == 0.1


def test_66505_both_deadline_cuts_show_AC12():
    at = show(66505)
    tick(at, "pd_goal_on")
    at.number_input(key="pd_deadline").set_value(36).run()
    assert not at.exception
    body = page(at)
    assert "$1,774" in body and "$672" in body


def test_smoke_a_savings_goal_on_20111_and_66505():
    for account in (20111, 66505):
        at = show(account)
        tick(at, "pd_goal_on")
        tick(at, "pd_off_on")
        tick(at, "pd_em_on")
        assert not at.exception


def test_footer_has_the_source_links_R2():
    body = page(show(20111))
    assert "relational.fel.cvut.cz" in body and "canada.ca" in body and text.FOOTER.replace("$", "") [:20] in body
