"""Findings page through AppTest (R3, D13): navigation, the head from the warm cache, and F3 to F6 with account_findings stubbed."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.engine import AccountFindings
from app.engine import findings as findings_engine

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
STUB = AccountFindings(4500, 100, 80, 5, 85, 300, 90, 40, 12, 1500.0, 7)


def text(at):
    return "\n".join(str(e.value) for group in (at.markdown, at.caption, at.header, at.subheader) for e in group).replace("\\$", "$")


def test_shock_and_plan_is_still_the_default_and_findings_is_last():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "Enter an account ID to start" in text(at)


def test_findings_page_shows_head_sentence_and_tiers_with_no_customer(monkeypatch):
    monkeypatch.setattr(findings_engine, "account_findings", lambda: STUB)
    monkeypatch.setattr("app.engine.account_findings", lambda: STUB)
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.switch_page("app_pages/findings.py").run()
    assert not at.exception
    assert [m.label.replace("\\$", "$") for m in at.metric] == ["Real income drops", "Spending kept, median", "Below $0 after 3 months: formula vs real"]
    values = [m.value for m in at.metric]
    assert values == ["735", "50%", "493 predicted, 31 real"]
    body = text(at)
    assert "Biggest finding: spending doesn't stay flat after a shock" in body
    assert "31 were below $0 after 3 months where the formula said 493" in body
    assert "Histogram of spending kept in 735 income drops. The median is 50%." in body
    assert at.table[0].value.values.tolist() == [["Under 2 months", "410", "37%"], ["2 to 6 months", "219", "71%"], ["6 or more months", "106", "247%"]]
    assert "85 in all" in body and "90 of the 300" in body and "12 of 40" in body and "$1,500" in body and "7 accounts live on a pension" in body
    assert "More findings, with their limits, are in the notebooks below." in body


def test_notebook_references_link_to_the_public_repo():
    from app.ui import findings_view as view
    lines = view.reference_lines()
    assert len(lines) == 3
    for name in ("discovery.ipynb", "know_the_customer.ipynb", "make_a_plan.ipynb"):
        assert any(f"https://github.com/mikhailajaj/Resilience_Rewired/blob/main/{name})" in line for line in lines)
        assert (Path(__file__).resolve().parents[2] / name).exists()
