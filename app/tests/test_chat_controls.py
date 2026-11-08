"""controls.py: what the Shock and plan controls hold (design section 6, RU-22)."""
import ast
from pathlib import Path

import pytest

from app.assistant import controls
from app.assistant.chat_text import T
from app.assistant.state import DEFAULT_TARGET, CardAnswer
from app.engine import EI_WEEKLY_MAX_2026

KINDS = {"keep_pct": "job", "months": "job", "after_ends": "job", "bills_increase_pct": "bills", "other_spending_change": "bills",
         "one_off_spending_multiple": "repair", "one_off_dollars": "repair"}


def card(**values):
    return tuple(CardAnswer(1, KINDS[f], f, v, "", "button", str(v)) for f, v in values.items())


def refusal(what):
    return what


def test_chat_fitting_card_sends():
    assert controls.cant_send(card(keep_pct=55, months=6, after_ends="no_income", bills_increase_pct=15, other_spending_change=300,
                                   one_off_spending_multiple=1)) is None
    assert controls.cant_send(()) is None


def test_chat_months_open_ended_refused():
    assert controls.cant_send(card(keep_pct=55, months=None)) == refusal(T.cant_open)


def test_chat_income_returns_refused():
    assert controls.cant_send(card(keep_pct=55, months=6, after_ends="income_returns")) == refusal(T.cant_returns)


def test_chat_bills_limit_boundary():
    assert controls.cant_send(card(bills_increase_pct=500)) is None
    assert controls.cant_send(card(bills_increase_pct=500.01)) == refusal(T.cant_bills.format(n="500.01"))
    assert controls.cant_send(card(bills_increase_pct=600)) == refusal(T.cant_bills.format(n="600"))


def test_chat_rent_limit_boundary():
    assert controls.cant_send(card(other_spending_change=20000)) is None
    assert controls.cant_send(card(other_spending_change=20001)) == refusal(T.cant_rent.format(d="$20,001"))


@pytest.mark.parametrize("value", [0, 0.25, 1, 2.75, 3])
def test_chat_repair_months_fit(value):
    assert controls.cant_send(card(one_off_spending_multiple=value)) is None


@pytest.mark.parametrize("value,shown", [(3.25, "3.25"), (0.3, "0.3"), (4, "4"), (1.1, "1.1")])
def test_chat_repair_months_refused(value, shown):
    assert controls.cant_send(card(one_off_spending_multiple=value)) == refusal(T.cant_repair_months.format(n=shown))


def test_chat_repair_dollars_boundary():
    assert controls.cant_send(card(one_off_dollars=100000)) is None
    assert controls.cant_send(card(one_off_dollars=100001)) == refusal(T.cant_repair_dollars.format(d="$100,001"))


def test_chat_two_one_offs_refused():
    assert controls.cant_send(card(one_off_spending_multiple=1, one_off_dollars=500)) == refusal(T.cant_two)
    assert controls.cant_send(card(one_off_spending_multiple=0, one_off_dollars=500)) is None


def test_chat_first_problem_wins():
    answers = card(keep_pct=55, months=None, after_ends="income_returns", bills_increase_pct=900)
    assert controls.cant_send(answers) == refusal(T.cant_open)


def test_chat_last_answer_per_field_wins():
    answers = card(bills_increase_pct=900) + card(bills_increase_pct=10)
    assert controls.cant_send(answers) is None
    assert controls.cant_send(card(bills_increase_pct=10) + card(bills_increase_pct=900)) is not None


def test_chat_to_inputs_values_and_types():
    out = controls.to_inputs(card(keep_pct=55, months=6, bills_increase_pct=15, other_spending_change=200, one_off_dollars=900), None)
    assert out["income"] == 55.0 and isinstance(out["income"], float)
    assert out["months"] == 6 and isinstance(out["months"], int)
    assert out["bills"] == 15.0 and out["dollars_month"] == 200.0 and out["oneoff_dollars"] == 900.0 and out["oneoff_months"] == 0.0
    assert all(isinstance(out[k], float) for k in ("bills", "dollars_month", "oneoff_months", "oneoff_dollars"))
    assert out["ei_on"] is False and out["start"] == "Not set"
    assert set(out) == set(controls.INPUT_KEYS)


def test_chat_to_inputs_defaults_without_current():
    out = controls.to_inputs((), None)
    assert out == dict(income=100.0, months=6, bills=0.0, target=DEFAULT_TARGET, dollars_month=0.0, oneoff_months=0.0, oneoff_dollars=0.0,
                       ei_on=False, ei_max=float(EI_WEEKLY_MAX_2026), start="Not set")


def test_chat_to_inputs_keeps_target_ei_max_and_months_from_current():
    current = dict(income=70.0, months=9, bills=5.0, target=4.5, ei_on=True, ei_max=700.0, start="2025-03")
    out = controls.to_inputs(card(bills_increase_pct=15), current)
    assert out["target"] == 4.5 and out["ei_max"] == 700.0 and out["months"] == 9
    assert out["ei_on"] is False and out["start"] == "Not set" and out["income"] == 100.0
    assert current["ei_on"] is True


def test_chat_input_keys_match_page_defaults():
    tree = ast.parse((Path(__file__).parents[1] / "app_pages" / "shock_and_plan.py").read_text())
    calls = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "DEFAULTS" for t in n.targets)]
    assert len(calls) == 1 and isinstance(calls[0], ast.Call)
    assert set(controls.INPUT_KEYS) == {k.arg for k in calls[0].keywords}
