"""The chat's reply lines: call text, results, plans, plain words, and the sweep of every account by every preset through flow.step (AC-1, AC-2, AC-5, AC-6, RU-16)."""
import re
from pathlib import Path

import pandas as pd
import pytest

from app.assistant import flow, replies
from app.assistant.chat_text import T
from app.assistant.state import CardAnswer, CustomerSeen, ValuePicked, TwistPicked
from app.engine import IncomeCut, Shock, apply_shock, get_profile, list_presets, make_plan
from app.ui import text

IDS = sorted(pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "accounts.csv").account_id)
GLYPH = {"ok": "✓ ", "bad": "✕ ", "neutral": ""}


# --- call_text ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("function,shock,kwargs,expected", [
    ("apply_shock", Shock(), {}, "apply_shock(20111, Shock())"),
    ("apply_shock", Shock(income_cut=IncomeCut(0.55, 6)), {"through_months": 6}, "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6)), through_months=6)"),
    ("apply_shock", Shock(income_cut=IncomeCut(0.55, None)), {}, "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, None)))"),
    ("apply_shock", Shock(income_cut=IncomeCut(0.55, 6, "income_returns")), {"through_months": 6},
     'apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6, after_ends="income_returns")), through_months=6)'),
    ("apply_shock", Shock(bills_increase_pct=15.0), {}, "apply_shock(20111, Shock(bills_increase_pct=15))"),
    ("apply_shock", Shock(bills_increase_pct=7.5), {}, "apply_shock(20111, Shock(bills_increase_pct=7.5))"),
    ("apply_shock", Shock(other_spending_change=300), {}, "apply_shock(20111, Shock(other_spending_change=300))"),
    ("apply_shock", Shock(one_off_dollars=2500), {}, "apply_shock(20111, Shock(one_off_dollars=2500))"),
    ("apply_shock", Shock(one_off_spending_multiple=0.25), {}, "apply_shock(20111, Shock(one_off_spending_multiple=0.25))"),
    ("apply_shock", Shock(income_cut=IncomeCut(1.0, 3)), {"through_months": 3}, "apply_shock(20111, Shock(income_cut=IncomeCut(1, 3)), through_months=3)"),
    ("apply_shock", Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15, one_off_spending_multiple=1), {"through_months": 6},
     "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15, one_off_spending_multiple=1), through_months=6)"),
    ("make_plan", Shock(income_cut=IncomeCut(0.55, 6)), {"target_months": 3.0, "through_months": 6},
     "make_plan(20111, Shock(income_cut=IncomeCut(0.55, 6)), target_months=3, through_months=6)"),
    ("make_plan", Shock(), {"target_months": 2.5}, "make_plan(20111, Shock(), target_months=2.5)"),
])
def test_call_text_forms(function, shock, kwargs, expected):
    assert replies.call_text(function, 20111, shock, **kwargs) == expected


# --- results --------------------------------------------------------------------------------------------------------

def expected_result(account, shock, months):
    r = apply_shock(account, shock, through_months=months)
    p = get_profile(account)
    v = text.verdict(r)
    lines = [GLYPH[v.tone] + v.sentence]
    lines += [v.second_line] if v.second_line else []
    lines.append(f"Runway {r.before.runway.label} -> {r.after.runway.label}. Monthly gap {text.money(r.before.gap)} -> {text.money(r.after.gap)}.")
    lines.append(text.after_line(r))
    if text.oneoff_line(r) is not None:
        lines.append(text.oneoff_line(r))
    lines += text.fact_lines(r, p)
    if text.assumption_line(r):
        lines.append(text.assumption_line(r))
    return r, lines


def test_ac5_no_buffer_account_says_the_balance_was_already_negative_and_never_blames_the_cost():
    s = flow.step(flow.initial(), CustomerSeen(32078))
    s = flow.step(s, TwistPicked(s.turn, "repair"))
    s = flow.step(s, flow.live(s).options[0].event)
    lines = flow.live(s).lines
    assert lines[1] == "✕ The buffer (average balance over the last 6 months) was already -$2,513 before this, so runway is 0 months whatever the shock."
    assert not any("one-off cost" in line for line in lines)
    assert s.outputs[0].verdict_case == "runway_zero" and "no_buffer_before_shock" in s.outputs[0].fact_codes
    assert [o.key for o in flow.live(s).options][0] == "backup"


def test_ac6_a_runway_at_the_cap_never_reads_as_no_shortfall():
    p = get_profile(20134)
    lines = replies.greeting(p)
    assert text.summary_line(p) in lines and "120.0 months" in lines[1]
    assert not any("No shortfall" in line for line in lines)
    r = apply_shock(20134, Shock())
    assert r.runway.label == "120.0 months"
    assert not any("No shortfall" in line or "runs out" in line for line in replies.result_lines(r, p))


def test_greeting_lines():
    ID = 20111
    p = get_profile(ID)
    lines = replies.greeting(p)
    assert lines[0] == T.greet.format(id=ID) and lines[1] == text.summary_line(p)
    assert lines[2] == T.range.format(first_month=p.first_month, last_month=p.last_month, n_months=p.n_months)
    assert list(lines[3:-1]) == ["- " + n for n in text.notes(p)[:3]] and lines[-1] == T.pick


def test_result_lines_have_the_glyph_the_second_line_and_the_change_line():
    r, expected = expected_result(20111, Shock(income_cut=IncomeCut(0.55, 6)), 6)
    lines = replies.result_lines(r, get_profile(20111))
    assert list(lines) == expected and lines[0].startswith("✕ ") and lines[2] == "Runway 7.8 months -> 3.4 months. Monthly gap $2,260 -> $5,113."
    assert lines[3] == text.after_line(r) and lines[3].startswith("After the shock: money in ")
    neutral = replies.result_lines(apply_shock(20111, Shock()), get_profile(20111))
    assert neutral[0] == "No shock applied. Pick a twist to see what changes."


def test_the_ours_line_appears_only_when_standing_orders_apply_and_ends_with_ours():
    with_orders, without = 20176, 20111
    shock = Shock(bills_increase_pct=15)
    r = apply_shock(with_orders, shock)
    assert r.bills_on_standing_orders.applies
    lines = replies.result_lines(r, get_profile(with_orders))
    row = text.orders_row(r)
    assert lines[-1] == f"{row.label} (our estimate): {row.value} ({row.counterpart})" and lines[-1].count("(our estimate)") == 1
    assert sum("(our estimate)" in line for line in lines) == 1
    r2 = apply_shock(without, shock)
    assert not r2.bills_on_standing_orders.applies
    assert not any("(our estimate)" in line for line in replies.result_lines(r2, get_profile(without)))
    assert text.orders_row(r2).value == "n/a"


def test_orders_row_is_the_row_our_rows_shows():
    for account in (20176, 20111):
        r = apply_shock(account, Shock(bills_increase_pct=15))
        rows = text.our_rows(r, get_profile(account), make_plan(account, Shock(bills_increase_pct=15)))
        assert text.orders_row(r) in rows


# --- plans ----------------------------------------------------------------------------------------------------------

def test_plan_lines_backup_lists_the_steps_in_order_and_goal_is_goal_lines():
    shock = Shock(income_cut=IncomeCut(0.55, 6))
    plan = make_plan(20111, shock, target_months=3, through_months=6)
    backup = replies.plan_lines(plan, "backup")
    assert list(backup[:len(text.backup_lines(plan))]) == text.backup_lines(plan)
    assert list(backup[len(text.backup_lines(plan)):]) == [f"{s.order}. {s.action}" for s in plan.backup.steps] and plan.backup.steps
    assert replies.plan_lines(plan, "goal") == tuple(text.goal_lines(plan))


# --- plain ----------------------------------------------------------------------------------------------------------

def a(field, value, kind="job"):
    return CardAnswer(1, kind, field, value, "", "button", str(value))


@pytest.mark.parametrize("answers,expected", [
    ((), ""),
    ((a("keep_pct", 55),), "income kept at 55%"),
    ((a("keep_pct", 55), a("months", 6)), "income kept at 55% for 6 months"),
    ((a("keep_pct", 55), a("months", 1)), "income kept at 55% for 1 month"),
    ((a("keep_pct", 55), a("months", None)), "income kept at 55% until it runs out"),
    ((a("keep_pct", 55), a("months", 6), a("after_ends", "no_income")), "income kept at 55% for 6 months, then no income"),
    ((a("keep_pct", 55), a("months", 6), a("after_ends", "income_returns")), "income kept at 55% for 6 months, then income returns"),
    ((a("bills_increase_pct", 15, "bills"),), "bills up 15%"),
    ((a("other_spending_change", 300, "bills"),), "bills or rent up $300 a month"),
    ((a("one_off_spending_multiple", 1, "repair"),), "a one-off cost of 1 month of spending"),
    ((a("one_off_spending_multiple", 2.5, "repair"),), "a one-off cost of 2.5 months of spending"),
    ((a("one_off_dollars", 2500, "repair"),), "a one-off cost of $2,500"),
    ((a("bills_increase_pct", 15, "bills"), a("keep_pct", 55), a("months", 6)), "income kept at 55% for 6 months; bills up 15%"),
    ((a("keep_pct", 55), a("keep_pct", 40)), "income kept at 40%"),
])
def test_plain_per_field(answers, expected):
    assert replies.plain(answers) == expected


# --- record ---------------------------------------------------------------------------------------------------------

def test_record_copies_from_the_result_and_from_the_plan():
    shock = Shock(income_cut=IncomeCut(0.55, 6))
    r = apply_shock(20111, shock, through_months=6)
    out = replies.record(4, "CALL", r=r)
    assert (out.turn, out.account_id, out.function, out.call, out.shock, out.through_months, out.target_months) == (4, 20111, "apply_shock", "CALL", shock, 6, None)
    assert (out.verdict_case, out.runway_before, out.runway_after, out.gap_before, out.gap_after) == (
        r.verdict_case, r.before.runway.label, r.after.runway.label, r.before.gap, r.after.gap)
    assert out.fact_codes == tuple(f.code for f in r.facts) and out.goal_state is None and out.backup_state is None
    plan = make_plan(20111, shock, target_months=4, through_months=6)
    out = replies.record(5, "CALL", plan=plan, target_months=4)
    assert (out.function, out.shock, out.through_months, out.target_months, out.goal_state, out.backup_state) == (
        "make_plan", shock, 6, 4, plan.goal.state, plan.backup.state)
    assert out.verdict_case is None and out.runway_after is None and out.fact_codes == tuple(f.code for f in plan.facts)
    with pytest.raises(ValueError):
        replies.record(1, "CALL")


# --- Sweep: every account by every preset, through flow.step ---------------------------------------------------------

def preset_card(shock):
    """The twist and the ValuePicked events a presenter would click for this shock."""
    cut = shock.income_cut
    sizes = []
    if cut:
        sizes += [("keep_pct", round(cut.keep_fraction * 100, 6)), ("months", cut.months)]
    if shock.bills_increase_pct:
        sizes.append(("bills_increase_pct", shock.bills_increase_pct))
    if shock.one_off_spending_multiple:
        sizes.append(("one_off_spending_multiple", shock.one_off_spending_multiple))
    twist = "mix" if cut and shock.bills_increase_pct else "job" if cut else "bills" if shock.bills_increase_pct else "repair"
    return twist, sizes


SWEEP = [p for p in list_presets() if p.key != "no_shock"]


def test_sweep_every_account_by_every_preset_through_the_buttons():
    assert len(IDS) == 4500 and {p.key for p in SWEEP} == {"job_loss_ei", "furnace_repair", "job_loss_bills", "bills_up"}
    for account in IDS:
        greeted = flow.step(flow.initial(), CustomerSeen(account))
        for preset in SWEEP:
            twist, sizes = preset_card(preset.shock)
            s = flow.step(greeted, TwistPicked(greeted.turn, twist))
            for field, value in sizes:
                s = flow.step(s, ValuePicked(s.turn, field, value, str(value)))
            months = preset.shock.income_cut.months if preset.shock.income_cut else None
            r, expected = expected_result(account, preset.shock, months)
            lines = list(flow.live(s).lines)
            assert s.phase == "result" and len(s.outputs) == 1, (account, preset.key)
            assert lines[0] == T.engine_call.format(call=s.outputs[0].call), (account, preset.key)
            body = lines[1:]
            if r.bills_on_standing_orders.applies:
                assert "(our estimate):" in body.pop(), (account, preset.key)
            assert body == expected, (account, preset.key)
            out = s.outputs[0]
            assert out.shock == preset.shock and out.through_months == months and out.account_id == account, (account, preset.key)
            assert (out.verdict_case, out.runway_before, out.runway_after, out.gap_before, out.gap_after) == (
                r.verdict_case, r.before.runway.label, r.after.runway.label, r.before.gap, r.after.gap), (account, preset.key)
            assert out.fact_codes == tuple(f.code for f in r.facts), (account, preset.key)


def test_r6_d4_result_lines_carry_the_after_line_and_the_one_off_line_after_the_change_line():
    shock = Shock(one_off_spending_multiple=1)
    r = apply_shock(20111, shock)
    lines = replies.result_lines(r, get_profile(20111))
    assert text.oneoff_line(r) in lines and text.after_line(r) in lines
    assert lines.index(text.after_line(r)) == lines.index(text.oneoff_line(r)) - 1
    assert lines[lines.index(text.after_line(r)) - 1].startswith("Runway ")


def test_d4_the_furnace_on_20111_shows_the_one_off_in_dollars_before_the_shock():
    r = apply_shock(20111, Shock(one_off_spending_multiple=1))
    body = " ".join(replies.result_lines(r, get_profile(20111)))
    assert "$8,600" in body and "before the shock" in body


def test_r6_no_one_off_means_no_one_off_line():
    r = apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6)), through_months=6)
    assert text.oneoff_line(r) is None
    assert not any(line.startswith("One-off cost") for line in replies.result_lines(r, get_profile(20111)))


def test_d2_assumed_months_appends_the_assumed_length_line_and_only_then():
    r = apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15), through_months=6)
    p = get_profile(20111)
    assert replies.result_lines(r, p, assumed_months=True)[-1] == text.ASSUMED_LENGTH
    assert replies.result_lines(r, p, assumed_months=True)[:-1] == replies.result_lines(r, p)
    assert text.ASSUMED_LENGTH not in replies.result_lines(r, p)


def test_d2_plain_says_assumed_on_the_months_part_only_for_an_assumed_answer():
    assumed = CardAnswer(1, "job", "months", 6, "months", "assumed", "6 months (assumed)")
    assert replies.plain((a("keep_pct", 55), assumed)) == "income kept at 55% for 6 months (assumed)"
    assert replies.plain((a("keep_pct", 55), a("months", 6))) == "income kept at 55% for 6 months"


BANS = re.compile(r"about 0 months short|(?<![\d.])1 months|\$\$|None|nan")


def test_sweep_greeting_and_result_lines_hold_no_banned_text_for_every_account_and_preset():
    presets = list_presets()
    assert len(presets) == 5
    for account in IDS:
        p = get_profile(account)
        for line in replies.greeting(p):
            assert not BANS.search(line), (account, line)
        for preset in presets:
            cut = preset.shock.income_cut
            r = apply_shock(account, preset.shock, through_months=cut.months if cut else None)
            for line in replies.result_lines(r, p):
                assert not BANS.search(line), (account, preset.key, line)
