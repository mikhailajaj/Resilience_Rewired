import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import engine
from app.engine import InvalidAccountIdError, account_id_range, account_overview, get_profile, monthly_history, note_catalogue, to_dict
from app.tests.raw import judges

ROOT = Path(__file__).resolve().parents[2]


def test_20111_known_values():
    p = get_profile(20111)
    assert (round(p.I), round(p.S), round(p.H), round(p.F), round(p.P), round(p.B)) == (6339, 8600, 0, 2330, 2330, 17612)
    assert p.runway.months == 7.8 and p.runway.state == "months"
    assert round(p.current_fixed_costs) == 2330
    assert round(p.buffer_months, 1) == 2.0
    assert round(p.gap) == 2260
    assert {w.title for w in p.warnings} == {"Cash income", "No regular bills visible", "Loan in trouble"}


def test_32078_no_buffer():
    p = get_profile(32078)
    assert round(p.B) == -2513
    assert p.runway.state == "no_buffer" and p.runway.months == 0.0
    assert p.buffer_months is None


def test_20176_no_shortfall_with_bills_on_orders():
    p = get_profile(20176)
    assert p.runway.state == "no_shortfall" and p.runway.months is None
    assert p.runway.label == "No shortfall (120+)"
    assert round(p.bills_on_standing_orders) == 1189
    assert round(p.current_fixed_costs) == 1189
    assert p.income_type == "Pension"


def test_21132_no_activity():
    p = get_profile(21132)
    assert p.I == 0 and p.S == 0
    assert p.buffer_months is None
    assert "little_activity" in {w.code for w in p.warnings}


@pytest.mark.parametrize("account_id", [20111, 20176, 20208, 32078, 21132])
def test_matches_a_separate_stdlib_calculation(account_id):
    p, raw = get_profile(account_id), judges(account_id)
    for key, value in raw.items():
        assert getattr(p, key) == pytest.approx(value, abs=1e-6), key


@pytest.mark.parametrize("bad,reason", [
    ("abc", "not_digits"), ("", "not_digits"), (None, "not_digits"), (True, "not_digits"), (20111.0, "not_digits"),
    ("20_111", "not_digits"), ("-20111", "not_digits"), ("٢٠١١١", "not_digits"),
    (12345, "not_found"), ("12345", "not_found"), (0, "not_found"),
])
def test_invalid_ids_raise_a_typed_error(bad, reason):
    with pytest.raises(InvalidAccountIdError) as e:
        get_profile(bad)
    assert e.value.reason == reason and e.value.value == bad and str(e.value)
    assert isinstance(e.value, ValueError)


def test_id_forms_that_work():
    assert get_profile(" 20111 ").account_id == 20111
    assert get_profile("20111") is get_profile(20111)    # cached, so lookups are near-instant


def test_days_below_zero_is_int():
    assert monthly_history(20111).days_below_zero.dtype.kind == "i"


def test_months_below_zero():
    x = monthly_history(32078)
    p = get_profile(32078)
    assert p.months_below_zero_last_6 == int((x.tail(6).days_below_zero > 0).sum())
    assert p.months_below_zero_last_12 == int((x.tail(12).days_below_zero > 0).sum())
    assert p.months_below_zero_all == int((x.days_below_zero > 0).sum())
    assert p.months_below_zero_last_6 > 0


def test_monthly_history_is_a_copy():
    history = monthly_history(20111)
    history.loc[:, "money_in"] = -1.0
    assert history.money_in.max() == -1
    assert monthly_history(20111).money_in.min() >= 0


def test_lookup_helpers():
    r = account_id_range()
    assert r.count == 4500 and r.min <= 20111 <= r.max
    o = account_overview(20111)
    assert (o.income_type, o.last_month) == ("Cash only", "2025-12") and o.n_months == 38
    assert [n.code for n in o.notes] == [w.code for w in get_profile(20111).warnings]
    assert all(n.condition for n in o.notes)
    catalogue = note_catalogue()
    assert len(catalogue) == 17 and len({n.code for n in catalogue}) == 17 and all(n.condition for n in catalogue)


def test_profile_is_json_safe():
    json.dumps(to_dict(get_profile(20111)), allow_nan=False)


def test_runs_from_any_working_directory(tmp_path):
    code = "from app.engine import get_profile; print(get_profile(20111).runway.months)"
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env={"PYTHONPATH": str(ROOT)},
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "7.8"


def test_engine_has_no_ui_imports():
    for path in Path(engine.__file__).parent.glob("*.py"):
        text = path.read_text()
        for name in ("streamlit", "matplotlib", "IPython"):
            assert f"import {name}" not in text and f"from {name}" not in text, path
