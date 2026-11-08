"""Page call sites: R17 (through_months), D2/R7 (assumed length caption), D4/R6 (one-off line)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import app.engine as engine
from app.engine import apply_shock
from app.ui import text

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def page(at):
    return "\n".join(str(e.value) for group in (at.markdown, at.caption, at.text, at.subheader, at.header) for e in group).replace("\\$", "$")


def show(at, account):
    at.text_input(key="typed_id").set_value(str(account))
    at.button(key="FormSubmitter:picker-Show customer").click().run()
    assert not at.exception
    return at


def spy(monkeypatch, name, calls):
    real = getattr(engine, name)

    def wrapper(*args, **kwargs):
        calls.append(kwargs.get("through_months", "missing"))
        return real(*args, **kwargs)

    monkeypatch.setattr(engine, name, wrapper)


@pytest.mark.parametrize("preset,expected", [("Laid off, EI 55%", 6), ("Furnace dies", None)])
def test_R17_both_engine_calls_get_through_months(monkeypatch, preset, expected):
    shocks, plans = [], []
    spy(monkeypatch, "apply_shock", shocks)
    spy(monkeypatch, "make_plan", plans)
    at = show(AppTest.from_file(APP, default_timeout=60).run(), 20111)
    shocks.clear()
    plans.clear()
    at.button(key=f"preset_{preset}").click().run()
    assert not at.exception
    assert shocks and plans
    assert set(shocks) == {expected} and set(plans) == {expected}


def test_D2_caption_only_for_the_laid_off_and_bills_preset():
    at = show(AppTest.from_file(APP, default_timeout=60).run(), 20111)
    assert text.ASSUMED_LENGTH not in page(at)
    for name in ("Laid off, EI 55%", "Furnace dies", "Rent or bills up"):
        at.button(key=f"preset_{name}").click().run()
        assert text.ASSUMED_LENGTH not in page(at)
    at.button(key="preset_Laid off + bills up 15%").click().run()
    assert not at.exception
    assert text.ASSUMED_LENGTH in page(at)


def test_D4_furnace_shows_the_oneoff_line():
    at = show(AppTest.from_file(APP, default_timeout=60).run(), 20111)
    at.button(key="preset_Furnace dies").click().run()
    assert not at.exception
    from app.engine import Shock
    result = apply_shock(20111, Shock(one_off_spending_multiple=1.0))
    line = text.oneoff_line(result)
    assert line is not None, "WP-T has not filled oneoff_line yet"
    assert line in page(at) and "$8,600" in line
