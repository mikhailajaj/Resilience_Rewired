"""UI tests: the live flow through Streamlit's AppTest, and every sentence on every account."""
import re
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.engine import (EI_WEEKLY_MAX_2026, account_flows, apply_shock, customer_record, get_preset, get_profile, list_presets, make_plan, monthly_history)
from app.ui import charts, profile_view, questionnaire, text

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
IDS = sorted(pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "accounts.csv").account_id)


def page(at):
    return "\n".join(str(e.value) for group in (at.markdown, at.caption, at.text, at.subheader, at.header) for e in group).replace("\\$", "$")


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    return at


def show(at, account):
    at.text_input(key="typed_id").set_value(str(account))
    at.button(key="FormSubmitter:picker-Show customer").click().run()
    assert not at.exception
    return at


def preset(at, name):
    at.button(key=f"preset_{name}").click().run()
    assert not at.exception
    return at


def test_empty_page_shows_only_the_picker(app):
    assert "Enter an account ID to start" in page(app)
    assert not app.metric and not app.slider


@pytest.mark.parametrize("typed,expected", [("abc", '"abc" isn\'t an account number'), ("12345", "No account 12345 in this data")])
def test_invalid_ids_explain_themselves(app, typed, expected):
    show(app, typed)
    assert expected in page(app)
    assert not app.metric


def test_know_the_customer_uses_the_judges_numbers(app):
    show(app, 20111)
    values = {m.label: m.value for m in app.metric}
    assert values["Typical money in"] == "$6,339" and values["Typical spending"] == "$8,600"
    assert values["Buffer"] == "$17,612" and values["Runway, no shock"] == "7.8 months"
    assert "No shock applied" in page(app)


def test_layoff_verdict_and_plan_on_20111(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    body = page(app)
    assert "the money runs out in month 4, about 2.6 months short" in body
    assert "The standard (judges') runway is 3.4 months." in body
    assert "Selected: Laid off, EI 55%" in body
    assert "spending needs to drop by **$2,178 a month**" in body


def test_ei_maximum_changes_our_row_and_not_the_judges(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    before = [m.value for m in app.metric]
    assert "Runway with EI weekly maximum" not in str([h.proto for h in app.get("html")])
    app.toggle(key="w_ei_on").set_value(True).run()
    assert not app.exception
    assert [m.value for m in app.metric] == before
    html_text = str([h.proto for h in app.get("html")])
    assert "Runway with EI weekly maximum" in html_text and "3.2 months" in html_text
    assert "they run out in month 4" in page(app)


def test_typed_income_and_length_are_used(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    app.number_input(key="n_income").set_value(57.0).run()
    app.number_input(key="n_months").set_value(9).run()
    assert not app.exception
    body = page(app)
    assert "income at 57% for 9 months" in body and "**Custom**" in body
    assert app.slider(key="s_income").value == 57.0 and app.slider(key="s_months").value == 9


def test_typed_months_beyond_the_slider_stay_in_the_box(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    app.number_input(key="n_months").set_value(60).run()
    assert not app.exception
    assert "for 60 months" in page(app)
    assert app.slider(key="s_months").value == 24 and app.number_input(key="n_months").value == 60


def test_dollar_repair_clears_the_months_slider(app):
    show(app, 20111)
    preset(app, "Furnace dies")
    assert "One-off cost: $8,600, 1 month of typical spending before the shock ($8,600 a month)." in page(app)
    app.number_input(key="w_oneoff_dollars").set_value(5000.0).run()
    assert not app.exception
    body = page(app)
    assert "One-off cost: $5,000." in body and "Total one-off" not in body and "the buffer lasts 5.6 months, down from 7.8 months" in body
    assert app.slider(key="w_oneoff_months").value == 0


def test_dollar_rise_in_rent(app):
    show(app, 20111)
    app.number_input(key="w_dollars_month").set_value(300.0).run()
    assert not app.exception
    assert {m.value for m in app.metric} >= {"$8,900"}


def test_target_box_changes_goal_only(app):
    show(app, 20111)
    app.number_input(key="n_target").set_value(6.0).run()
    assert not app.exception
    assert f"Target: **{text.money(6 * get_profile(20111).S)}**" in page(app)


def test_new_customer_starts_with_no_shock(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    show(app, 20134)
    assert "No shock applied" in page(app)
    assert app.number_input(key="n_income").value == 100


def test_reset_clears_everything(app):
    show(app, 20111)
    preset(app, "Laid off + bills up 15%")
    app.toggle(key="w_ei_on").set_value(True).run()
    preset(app, "reset")
    assert "No shock applied" in page(app)
    assert app.toggle(key="w_ei_on").value is False and app.number_input(key="n_bills").value == 0


def test_hard_accounts_draw_the_whole_page(app):
    for account in (32078, 21132, 20176, 21755):
        show(app, account)
        preset(app, "Furnace dies")
        preset(app, "Laid off + bills up 15%")
        assert "Goal plan: build an emergency fund" in page(app)
        assert "Backup plan: if this happens" in page(app)


def test_negative_buffer_does_not_blame_the_cost(app):
    show(app, 32078)
    preset(app, "Furnace dies")
    assert "The buffer (average balance over the last 6 months) was already -$2,513 before this" in page(app)


def test_bills_twist_on_account_with_no_bills_says_why(app):
    show(app, 20111)
    preset(app, "Rent or bills up")
    assert "the standard (judges') formula changes nothing for this" in page(app)


def test_start_month_never_changes_the_numbers(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    before = [m.value for m in app.metric]
    app.selectbox(key="w_start").select("November").run()
    assert not app.exception
    assert [m.value for m in app.metric] == before
    assert "runs into January" in page(app)


def test_money_format():
    assert text.money(1234.4) == "$1,234" and text.money(-3200) == "-$3,200" and text.money(1_234_000) == "$1.2M"
    assert text.money(-0.2) == "$0" and text.money(None) == "n/a"


def test_verdict_never_comes_from_rounding():
    """The worst case the contract names: a runway that rounds to the length but doesn't last it."""
    for a in IDS[:1500]:
        r = apply_shock(a, get_preset("job_loss_ei"))
        v = text.verdict(r)
        if r.verdict_case == "income_cut_runs_out" and r.duration.runs_out_in_month:
            assert f"month {r.duration.runs_out_in_month}," in v.sentence
        if r.verdict_case == "income_cut_makes_it":
            assert "They make it" in v.sentence


@pytest.mark.parametrize("key", [p.key for p in list_presets()] + ["ei_max", "repair_and_rent", "length_one_target_one"])
def test_every_sentence_on_every_account(key):
    """No account and twist can leave a blank, a None or an unfilled slot on screen."""
    shock = {"ei_max": lambda: get_preset("job_loss_ei", ei_weekly_max=EI_WEEKLY_MAX_2026),
             "repair_and_rent": lambda: get_preset("no_shock", one_off_dollars=5000, other_spending_change=300),
             "length_one_target_one": lambda: get_preset("job_loss_ei", months=1)}.get(key, lambda: get_preset(key))()
    through = shock.income_cut.months if shock.income_cut else None
    for a in IDS:
        p = get_profile(a)
        r = apply_shock(a, shock, through_months=through)
        plan = make_plan(a, shock, through_months=through, target_months=1.0 if key == "length_one_target_one" else 3.0)
        v = text.verdict(r)
        lines = [text.summary_line(p), v.sentence, v.second_line or "", text.assumption_line(r) or "", *text.notes(p), *text.fact_lines(r, p),
                 *text.goal_lines(plan), *text.backup_lines(plan), text.oneoff_line(r) or "", text.after_line(r)]
        for row in text.our_rows(r, p, plan):
            lines += [row.label, row.value, row.counterpart or "", *row.lines]
        for line in lines:
            assert "None" not in line and "nan" not in line and "{" not in line and "-$0" not in line, (a, key, line)
            assert "about 0 months short" not in line and "$$" not in line, (a, key, line)
            assert not re.search(r"(?<![\d.])1 months\b", line), (a, key, line)
            down = re.search(r"lasts (.+?), (?:down|up) from (.+?)\.", line)
            assert not down or down.group(1) != down.group(2), (a, key, line)
            assert "down from No shortfall" not in line, (a, key, line)
        assert text.backup_lines(plan), (a, key)
        assert text.goal_lines(plan), (a, key)


def test_flow_line_on_20111(app):
    show(app, 20111)
    assert "These are typical months, and medians don't add up. Over the last 12 months the balance fell $748 a month on average, and it ended at $10,863." in page(app)


def test_our_numbers_show_latest_balance_and_actual_change(app):
    show(app, 20111)
    html_text = str([h.proto for h in app.get("html")])
    assert "Latest balance" in html_text and "$10,863" in html_text and "standard (judges&#x27;) buffer: $17,612" in html_text
    assert "Actual change, last 12 months" in html_text and "-$748 a month" in html_text and "typical month: -$2,260" in html_text


def test_reverse_note_shows_only_when_the_balance_rose(app):
    show(app, 20160)
    assert "the balance rose" in page(app) and "the cut needed may be smaller" in page(app)
    show(app, 20111)
    assert "the cut needed may be smaller" not in page(app)


def test_reverse_note_population_matches_the_investigation():
    codes = [{f.code for f in make_plan(a).facts} for a in IDS]
    assert sum("balance_rose_despite_gap" in c for c in codes) == 616
    assert sum("surplus_not_seen_in_balance" in c for c in codes) == 1038
    assert not any(len(c & {"balance_rose_despite_gap", "surplus_not_seen_in_balance"}) > 1 for c in codes)


def test_flows_reconcile_to_the_balance_on_every_account():
    for a in IDS:
        f, x = account_flows(a), monthly_history(a)
        assert abs(f.total_change - x.month_end_balance.iloc[-1]) < 6  # Accounts open at $0.
        assert abs(f.change_last_12 * 12 - (x.month_end_balance.iloc[-1] - x.month_end_balance.iloc[-13] if len(x) > 12 else f.total_change)) < 1


def profiling(at):
    at.switch_page("app_pages/customer_profiling.py").run()
    assert not at.exception
    return at


def test_profiling_page_is_empty_until_a_customer_is_shown(app):
    profiling(app)
    assert "Enter an account ID to see everything on file" in page(app)


def test_profiling_page_keeps_the_customer_and_shows_the_record(app):
    show(app, 20111)
    profiling(app)
    body = page(app)
    assert "Customer 20111" in body and "the balance fell $748" in body
    tables = " ".join(t.value.to_string() for t in app.table).replace("\\$", "$")
    for expected in ("Rokycany", "west Bohemia", "8035546", "D: running, client in debt", "75490885", "$139,811", "41%", "$286"):
        assert expected in tables, expected
    assert len(app.dataframe) == 1 and len(app.dataframe[0].value) == 38


def test_changing_customer_on_the_profiling_page(app):
    show(app, 20111)
    profiling(app)
    show(app, 32078)
    assert "Customer 32078" in page(app)


def test_questions_use_the_customers_own_numbers():
    specific, general = questionnaire.build_questions(get_profile(20111), account_flows(20111), customer_record(20111))
    by_id = {q.id: q for q in specific}
    assert {"lumpy_income", "cash_income", "gap_vs_actual", "buffer_vs_latest", "loan_status", "lender_pause", "no_bills"} <= set(by_id)
    assert "41%" in by_id["lumpy_income"].why and "$63,751" in by_id["lumpy_income"].why
    assert "$2,260" in by_id["gap_vs_actual"].why and "-$748" in by_id["gap_vs_actual"].why
    assert "$17,612" in by_id["buffer_vs_latest"].why and "$10,863" in by_id["buffer_vs_latest"].why
    assert len(general) == 8
    pension = {q.id for q in questionnaire.customer_questions(get_profile(20176), account_flows(20176), customer_record(20176))}
    assert "pension_income" in pension and "cash_income" not in pension


def test_answers_survive_a_page_switch_and_reach_the_download(app):
    show(app, 20111)
    profiling(app)
    key = "answer_20111_lumpy_income"
    app.text_area(key=key).set_value("Mostly business income.").run()
    assert not app.exception
    assert "1 of" in page(app)
    app.switch_page("app_pages/shock_and_plan.py").run()
    assert not app.exception
    profiling(app)
    assert app.text_area(key=key).value == "Mostly business income."
    specific, general = questionnaire.build_questions(get_profile(20111), account_flows(20111), customer_record(20111))
    file = questionnaire.to_markdown(get_profile(20111), specific, general, {"lumpy_income": "Mostly business income."})
    assert "**Answer:** Mostly business income." in file and "(not answered)" in file and file.startswith("# Stakeholder questions: customer 20111")


def test_shock_inputs_survive_a_page_switch(app):
    show(app, 20111)
    preset(app, "Laid off, EI 55%")
    profiling(app)
    app.switch_page("app_pages/shock_and_plan.py").run()
    assert not app.exception
    assert app.number_input(key="n_income").value == 55 and "runs out in month 4" in page(app)


def test_every_account_builds_a_profile_and_questions():
    """No account can leave a blank, a None or a bad value on the profiling page, or leave its questions without numbers."""
    for a in IDS:
        p, f, r = get_profile(a), account_flows(a), customer_record(a)
        lines = [text.flow_line(p, f)]
        for rows in (profile_view.account_rows(p, r), profile_view.people_rows(r), profile_view.district_rows(r), profile_view.judges_rows(p), profile_view.flow_rows(p, f),
                     profile_view.flow_detail_rows(f), profile_view.recent_rows(p), profile_view.balance_rows(p), profile_view.cost_rows(p), profile_view.loan_rows(p),
                     profile_view.order_rows(r), profile_view.line_item_rows(p.income_sources), profile_view.line_item_rows(p.spending_items)):
            for row in rows:
                lines += [str(v) for v in (row.values() if isinstance(row, dict) else row)]
        specific, general = questionnaire.build_questions(p, f, r)
        for q in specific + general:
            lines += [q.question, q.why, q.changes]
        assert len({q.id for q in specific + general}) == len(specific) + len(general), a
        assert p.age >= 0 and r.people[0].role == "owner", a
        for line in lines:
            assert line != "" and "None," not in line and "nan" not in line.lower().replace("finance", "") and "{" not in line and "-$0" not in line, (a, line)


def test_pie_on_20111_adds_up_to_money_in():
    total_in, total_out, frame = charts.payee_split(monthly_history(20111))
    assert round(total_in) == 462327 and round(total_out) == 451464
    assert abs(frame.amount.sum() - total_in) < 0.01
    kept = frame[frame.item == "Left in the account"].iloc[0]
    assert round(kept.amount) == 10863 and kept.label == "Left in the account, 2%"
    assert frame.colour.is_unique


def test_pie_shares_never_round_to_0_or_100():
    assert [charts._share_text(s) for s in (0.004, 0.42, 0.996, 1.0)] == ["under 1%", "42%", "over 99%", "100%"]


def test_monthly_stacks_put_the_loan_at_the_bottom():
    history = monthly_history(20111)
    out = charts.monthly_stacks(history, charts.MONEY_OUT, "Money out")
    assert out.sort_values("order").item.iloc[0] == "Loan payments"
    december = out[out.month_label == "Dec 2025"]
    assert abs(december.amount.sum() - history.money_out.iloc[-1]) < 0.01


def test_charts_add_up_and_build_on_every_account():
    for a in IDS:
        history = monthly_history(a)
        total_in, total_out, frame = charts.payee_split(history)
        assert abs(frame.amount.sum() - max(total_in, total_out)) < 0.01, a
        assert (frame.amount > 0).all(), a
        stacked_in = charts.monthly_stacks(history, charts.MONEY_IN, "Money in").groupby("month_label").amount.sum()
        stacked_out = charts.monthly_stacks(history, charts.MONEY_OUT, "Money out").groupby("month_label").amount.sum()
        assert abs(stacked_in.sum() - total_in) < 0.01 and abs(stacked_out.sum() - total_out) < 0.01, a
    for a in (20111, 32078, 21132, 20176):
        assert charts.payee_pie(monthly_history(a)).to_dict() and charts.monthly_in_out(monthly_history(a)).to_dict()
