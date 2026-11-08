"""The typed-twist cheatsheet on Shock and plan: every example is a valid Shock, and the page shows it."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.assistant.parse import parse
from app.engine import apply_shock
from app.ui import cheatsheet

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def test_every_example_is_a_shock_the_engine_runs():
    for _, _, _, shock in cheatsheet.TEMPLATES:
        through = shock.income_cut.months if shock.income_cut else None
        assert apply_shock(20111, shock, through_months=through).runway is not None


def test_every_example_parses_ok_to_its_shock():
    for _, _, example, shock in cheatsheet.TEMPLATES:
        r = parse(example)
        assert (r.status, r.shock) == ("ok", shock), example


def test_months_slot_and_the_assumed_length_row_are_documented():
    months = dict((v, allowed) for v, _, allowed in cheatsheet.VARIABLES)["{months}"]
    assert "half a year" in months and "one to twenty, tens, fifty-five" in months
    rows = [t for t, _, _, _ in cheatsheet.TEMPLATES]
    assert "lose their job (EI {keep_pct}%) and bills go up {bills_pct}%" in rows
    assert any("length assumed 6 months" in field for _, field, _, _ in cheatsheet.TEMPLATES)


def test_every_slot_in_a_template_is_explained():
    slots = {v for v, _, _ in cheatsheet.VARIABLES}
    for template, _, _, _ in cheatsheet.TEMPLATES:
        used = {part.split("}")[0].join("{}") for part in template.split("{")[1:]}
        assert used <= slots, used - slots


def test_dollars_are_escaped_outside_code_only():
    text = cheatsheet.markdown()
    assert "`rent up ${dollars} a month`" in text
    assert r"rent up \$300 a month" in text


def test_cheatsheet_shows_on_shock_and_plan():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="typed_id").set_value("20111")
    at.button(key="FormSubmitter:picker-Show customer").click().run()
    assert not at.exception
    assert any("Cheatsheet" in e.label for e in at.expander)
    assert any("{keep_pct}" in str(m.value) for m in at.markdown)
