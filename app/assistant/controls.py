"""Whether a shock fits the Shock and plan controls, and the ss.inp values that hold it (RU-22, design section 6)."""
from collections.abc import Mapping

from app.engine import EI_WEEKLY_MAX_2026
from app.ui import text

from .chat_text import T
from .state import DEFAULT_TARGET, CardAnswer

INPUT_KEYS = ("income", "months", "bills", "target", "dollars_month", "oneoff_months", "oneoff_dollars", "ei_on", "ei_max", "start")
MAX_BILLS_PCT = 500
MAX_RENT = 20000
MAX_REPAIR_MONTHS = 3
REPAIR_STEP = 0.25
MAX_REPAIR_DOLLARS = 100000


def _last(answers):
    return {a.field: a.value for a in answers}


def cant_send(answers: tuple[CardAnswer, ...]) -> str | None:
    last = _last(answers)
    what = None
    if "months" in last and last["months"] is None:
        what = T.cant_open
    elif last.get("after_ends") == "income_returns":
        what = T.cant_returns
    elif last.get("bills_increase_pct", 0) > MAX_BILLS_PCT:
        what = T.cant_bills.format(n=f"{last['bills_increase_pct']:g}")
    elif last.get("other_spending_change", 0) > MAX_RENT:
        what = T.cant_rent.format(d=text.money(last["other_spending_change"]))
    else:
        multiple = last.get("one_off_spending_multiple", 0)
        dollars = last.get("one_off_dollars", 0)
        if multiple > MAX_REPAIR_MONTHS or (multiple / REPAIR_STEP) % 1 != 0:
            what = T.cant_repair_months.format(n=f"{multiple:g}")
        elif dollars > MAX_REPAIR_DOLLARS:
            what = T.cant_repair_dollars.format(d=text.money(dollars))
        elif multiple and dollars:
            what = T.cant_two
    return what


def to_inputs(answers: tuple[CardAnswer, ...], current: Mapping | None) -> dict:
    last = _last(answers)
    current = current or {}
    months = last.get("months")
    return {
        "income": float(last["keep_pct"]) if "keep_pct" in last else 100.0,
        "months": int(months) if months is not None else current.get("months", 6),
        "bills": float(last.get("bills_increase_pct", 0.0)),
        "target": current.get("target", DEFAULT_TARGET),
        "dollars_month": float(last.get("other_spending_change", 0.0)),
        "oneoff_months": float(last.get("one_off_spending_multiple", 0.0)),
        "oneoff_dollars": float(last.get("one_off_dollars", 0.0)),
        "ei_on": False,
        "ei_max": current.get("ei_max", float(EI_WEEKLY_MAX_2026)),
        "start": "Not set",
    }
