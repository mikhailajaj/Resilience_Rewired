"""Findings figures F1 to F6 (R3, D10, D13, ADR 0009) against the notebooks' stored outputs, and the response.py refactor."""
import numpy as np
import pytest

from app.engine import (account_findings, biggest_finding, get_dataset, income_drop_events, spending_response)
from app.engine.response import find_events
from app.ui import findings_view as view
from app.ui.findings_view import F


# Captured from find_events and spending_response before income_drop_events existed (ADR 0009 decision 1).
BEFORE_SUM_BUFFER, BEFORE_SUM_PASS = 9880.231492810564, 732.2025312341339
BEFORE_TIERS = (("Under 2 months", 410, 0.6972876362842578, 0.6972876362842578),
                ("2 to 6 months", 219, 0.2701901968639057, 0.2701901968639057),
                ("6 or more months", 106, -1.210169503684295, 0.0))
BEFORE_EVIDENCE = ("735 falls in deposits below 55% of normal for at least 3 months, nearly all on cash-only accounts. "
                   "These aren't confirmed job losses.")


def test_refactor_find_events_is_unchanged():
    found = find_events(get_dataset().rows_by_account)
    assert len(found) == 735
    assert sum(b for b, _ in found) == pytest.approx(BEFORE_SUM_BUFFER, rel=1e-12)
    assert sum(p for _, p in found) == pytest.approx(BEFORE_SUM_PASS, rel=1e-12)
    events = income_drop_events()
    assert found == [(e.start_buffer_months, e.pass_through) for e in events]
    assert income_drop_events() is events


def test_refactor_spending_response_is_unchanged():
    r = spending_response()
    assert r.total_events == 735 and r.evidence == BEFORE_EVIDENCE
    for tier, (name, events, raw, clipped) in zip(r.tiers, BEFORE_TIERS):
        assert (tier.name, tier.events) == (name, events)
        assert tier.raw_pass_through == pytest.approx(raw, rel=1e-12) and tier.response_per_dollar == pytest.approx(clipped, rel=1e-12)


def test_income_drop_events_are_consistent():
    for e in income_drop_events():
        assert e.income_kept == pytest.approx(e.in_mean / e.base_in)
        assert e.spending_kept == pytest.approx(e.out_mean / e.base_out)
        assert e.predicted_end == pytest.approx(e.start_balance - 3 * (e.base_out - e.in_mean))
        assert e.start_buffer_months == pytest.approx(e.start_balance / e.base_out)


def test_f1_biggest_finding_matches_discovery_s5():
    f = biggest_finding()
    assert (f.events, f.accounts, f.predicted_below_zero, f.actually_below_zero) == (735, 480, 493, 31)
    assert round(f.income_kept_median, 2) == 0.13 and round(f.spending_kept_median, 2) == 0.50
    assert abs(f.within_10pct_share * 100 - 5) <= 0.5
    assert (f.months, f.threshold) == (3, 0.55) and len(f.spending_kept) == 735
    assert f.evidence == spending_response().evidence
    assert biggest_finding() is f


def test_f2_tiers_match_discovery_s5_and_the_response():
    f = biggest_finding()
    assert [t.events for t in f.tiers] == [410, 219, 106]
    assert [round(t.spending_kept_median * 100, 2) for t in f.tiers] == [37.43, 71.36, 246.94]
    for tier, base in zip(f.tiers, spending_response().tiers):
        assert tier.name == base.name and tier.pass_through == base.raw_pass_through


def test_f3_to_f6_account_findings_match_the_notebooks():
    a = account_findings()
    assert a.accounts == 4500
    assert (a.ei6_runs_out, a.rescued_by_cuts, a.rescued_with_lender, a.rescued_total) == (1596, 1526, 22, 1548)
    assert (a.surplus_accounts, a.surplus_not_in_balance) == (3309, 1038)
    assert (a.running_loans, a.loans_missed_by_medians) == (448, 197)
    assert a.missed_payment_median == pytest.approx(2545.40)
    assert a.pension_accounts == 740
    assert account_findings() is a


def test_view_texts_contain_the_figures():
    f, a = biggest_finding(), account_findings()
    assert view.numbers(f) == [("Real income drops", "735"), ("Spending kept, median", "50%"), ("Below $0 after 3 months: formula vs real", "493 predicted, 31 real")]
    line = view.lines(f)[0]
    assert "In 735 real drops" in line and "median of 50%" in line and "31 were below $0 after 3 months where the formula said 493" in line
    assert view.tier_rows(f) == [("Under 2 months", "410", "37%"), ("2 to 6 months", "219", "71%"), ("6 or more months", "106", "247%")]
    f3, f4, f5, f6 = view.account_lines(a)
    assert f3 == ("Of the 1,596 accounts that don't last 6 months on EI at 55%, 1,526 make it with cuts to their own spending, plus 22 more "
                  "if the lender agrees to pause the loan: 1,548 in all.")
    assert "1,038 of the 3,309" in f4 and "197 of 448" in f5 and "$2,545" in f5 and f6.startswith("740 accounts")
    assert "735" in view.alt_text(f) and "50%" in view.alt_text(f)


def test_chart_builds_with_ten_percent_bins_and_a_200_plus_bin():
    f = biggest_finding()
    bins = view._bins(f)
    assert bins.events.sum() == 735 and list(bins.start)[:2] == [0, 10] and bins.start.iloc[-1] == 200
    assert bins.events.iloc[-1] == sum(v >= 2.0 for v in f.spending_kept)
    spec = view.chart(f).to_dict()
    assert F.rule in str(spec) and F.chart_title in str(spec)


def test_chart_with_no_events_still_builds():
    empty = biggest_finding().__class__(0, 0, 0.0, 0.0, 0.0, 0, 0, 3, 0.55, (), "", biggest_finding().tiers)
    assert view._bins(empty).events.sum() == 0
    view.chart(empty).to_dict()
