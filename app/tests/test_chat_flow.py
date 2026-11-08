"""The chat state machine, driven by events with no Streamlit and no network: AC-1, AC-3, AC-4, AC-7, AC-8, AC-10, RU-17 to RU-21, J4.1 to J4.3."""
import socket
from dataclasses import replace

import pytest

from app.assistant import controls, flow, parse
from app.assistant.chat_text import T
from app.assistant.state import (CardAnswer, ConfirmPicked, Context, CustomerSeen, FieldPicked, FollowUpPicked, ParseResult, RangeProblem,
                                 SendApplied, TextSent, TwistPicked, ValuePicked, ValueTyped)
from app.engine import IncomeCut, InvalidShockError, Shock, apply_shock, make_plan
from app.ui import text

ID = 20111
CUT_6 = Shock(income_cut=IncomeCut(0.55, 6))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the chat must not open a socket (AC-10)")
    monkeypatch.setattr(socket, "socket", refuse)


@pytest.fixture(autouse=True)
def bare_number_reader(monkeypatch):
    """Until the real read_number lands, read a lone number simply; the real one is used as soon as it works."""
    if parse.read_number("55") is None:
        def simple(s):
            try:
                return float(s.strip().rstrip("%").lstrip("$").replace(",", ""))
            except ValueError:
                return None
        monkeypatch.setattr(parse, "read_number", simple)


def start(account=ID):
    return flow.step(flow.initial(), CustomerSeen(account))


def press(state, key, ctx=Context()):
    option = next(o for o in flow.live(state).options if o.key == key)
    return flow.step(state, option.event, ctx)


def run_card(state, twist, *keys, ctx=Context()):
    state = press(state, twist, ctx)
    for key in keys:
        state = press(state, key, ctx)
    return state


def job_6(account=ID):
    return run_card(start(account), "job", "keep_55", "months_6")


def reply(state):
    return flow.live(state).lines


def ok_reading(*answers):
    return ParseResult("ok", answers=answers)


def card(field, value, kind="job", unit="", shown=""):
    return CardAnswer(-1, kind, field, value, unit, "parsed", shown or str(value))


READING_55_6 = ok_reading(card("keep_pct", 55, unit="%", shown="55%"), card("months", 6, unit="months", shown="6 months"))


# --- AC-1 -----------------------------------------------------------------------------------------------------------

def test_ac1_buttons_run_the_card_and_say_the_engine_verdict():
    s = job_6()
    expected = apply_shock(ID, CUT_6, through_months=6)
    assert len(s.outputs) == 1 and s.phase == "result"
    out = s.outputs[0]
    assert "IncomeCut(0.55, 6)" in out.call and out.call == "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6)), through_months=6)"
    assert any("IncomeCut(0.55, 6)" in line for line in reply(s))
    assert reply(s)[0] == T.engine_call.format(call=out.call)
    assert reply(s)[1] == "✕ " + text.verdict(expected).sentence
    assert reply(s)[2] == text.verdict(expected).second_line
    assert any("3.4 months" in line for line in reply(s))
    assert out.shock == CUT_6 and out.through_months == 6 and out.runway_after == "3.4 months" and out.verdict_case == expected.verdict_case


def test_ac1_the_run_passes_the_same_inputs_as_shock_and_plan(monkeypatch):
    seen = []
    real = flow.apply_shock
    monkeypatch.setattr(flow, "apply_shock", lambda *a, **k: seen.append((a, k)) or real(*a, **k))
    job_6()
    assert seen == [((ID, CUT_6), {"through_months": 6})]


def test_open_ended_months_run_without_through_months(monkeypatch):
    seen = []
    real = flow.apply_shock
    monkeypatch.setattr(flow, "apply_shock", lambda *a, **k: seen.append((a, k)) or real(*a, **k))
    s = run_card(start(), "job", "keep_55", "months_none")
    assert seen == [((ID, Shock(income_cut=IncomeCut(0.55, None))), {"through_months": None})]
    assert s.outputs[0].call == "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, None)))"
    assert s.outputs[0].verdict_case == "income_cut_open_ended"


def test_every_accepted_event_bumps_the_turn_and_shows_the_choice_as_text():
    s = start()
    assert flow.live(s).turn == s.turn and [o.key for o in flow.live(s).options] == ["job", "bills", "repair", "mix", "type"]
    for key, label in (("job", T.b_job), ("keep_55", "55%"), ("months_6", "6 months")):
        before = s
        s = press(s, key)
        assert s.turn == before.turn + 1
        user = [m for m in s.messages[len(before.messages):] if m.role == "user"]
        assert [m.lines for m in user] == [(label,)]
        live = flow.live(s)
        assert live.role == "assistant" and live.turn == s.turn
        assert all(o.event.turn == s.turn for o in live.options)
        assert len({o.key for o in live.options}) == len(live.options)
    assert {a.field: (a.value, a.source, a.turn) for a in s.answers} == {"keep_pct": (55, "button", 3), "months": (6, "button", 4)}


# --- AC-3, RU-17 ----------------------------------------------------------------------------------------------------

def test_ac3_text_never_runs_and_run_it_runs_once(monkeypatch):
    monkeypatch.setattr(parse, "parse", lambda t: READING_55_6)
    s = flow.step(start(), TextSent(1, "laid off, EI 55% for 6 months"))
    assert s.outputs == () and s.phase == "confirm" and s.pending == READING_55_6
    assert reply(s) == (T.confirm.format(plain="income kept at 55% for 6 months"),)
    assert [o.key for o in flow.live(s).options] == ["run", "buttons"]
    done = press(s, "run")
    assert len(done.outputs) == 1 and done.phase == "result" and done.pending is None
    assert done.outputs[0].shock == CUT_6 and done.outputs[0].call.endswith("through_months=6)")
    assert reply(done)[1] == "✕ " + text.verdict(apply_shock(ID, CUT_6, through_months=6)).sentence
    assert [(a.turn, a.source) for a in done.answers] == [(done.turn, "parsed")] * 2


def test_ac3_no_use_buttons_runs_nothing(monkeypatch):
    monkeypatch.setattr(parse, "parse", lambda t: READING_55_6)
    s = press(flow.step(start(), TextSent(1, "x")), "buttons")
    assert s.outputs == () and s.phase == "greeting" and reply(s) == (T.pick,) and s.pending is None


def test_new_text_replaces_the_old_confirm(monkeypatch):
    monkeypatch.setattr(parse, "parse", lambda t: READING_55_6)
    first = flow.step(start(), TextSent(1, "a"))
    second = flow.step(first, TextSent(first.turn, "b"))
    assert second.phase == "confirm" and flow.step(second, ConfirmPicked(first.turn, True)) is second


PT_OK = [
    ("laid off, EI 55% for 6 months", Shock(income_cut=IncomeCut(0.55, 6))),
    ("laid off, EI 55% for 6 months and bills up 15%", Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15)),
    ("The furnace dies, and the repair costs a full month of their typical spending.", Shock(one_off_spending_multiple=1)),
    ("Rent or household bills go up 15%.", Shock(bills_increase_pct=15)),
    ("rent up $300 a month", Shock(other_spending_change=300)),
    ("car repair $2,500", Shock(one_off_dollars=2500)),
    ("roof repair $1.5k", Shock(one_off_dollars=1500)),
    ("EI 57% for 12 months", Shock(income_cut=IncomeCut(0.57, 12))),
    ("laid off for a year, EI 55%", Shock(income_cut=IncomeCut(0.55, 12))),
    ("laid off, EI 55% until it runs out", Shock(income_cut=IncomeCut(0.55, None))),
    ("income drops to 70% for three months", Shock(income_cut=IncomeCut(0.7, 3))),
    ("income cut by 30% for 3 months", Shock(income_cut=IncomeCut(0.7, 3))),
    ("laid off, no EI, for 3 months", Shock(income_cut=IncomeCut(0.0, 3))),
]


@pytest.mark.parametrize("sentence,shock", PT_OK)
def test_ac3_real_parser_ok_rows_wait_for_run_it(sentence, shock):
    s = flow.step(start(), TextSent(1, sentence))
    assert s.phase == "confirm" and s.outputs == () and s.pending.shock == shock
    done = press(s, "run")
    months = shock.income_cut.months if shock.income_cut else None
    assert len(done.outputs) == 1 and done.outputs[0].shock == shock
    assert done.outputs[0].verdict_case == apply_shock(ID, shock, through_months=months).verdict_case


def test_text_partial_asks_only_what_is_missing(monkeypatch):
    partial = ParseResult("partial", answers=(card("keep_pct", 55, unit="%", shown="55%"),), missing=("months",))
    monkeypatch.setattr(parse, "parse", lambda t: partial)
    s = flow.step(start(), TextSent(1, "laid off, EI 55%"))
    assert s.phase == "ask_size" and s.asking == ("months",) and s.outputs == ()
    assert reply(s) == (T.partial.format(plain="income kept at 55%", size="the length"), T.ask_months)
    done = press(s, "months_12")
    assert done.outputs[0].shock == Shock(income_cut=IncomeCut(0.55, 12))


def test_text_unsure_and_out_of_range_offer_the_twist_buttons(monkeypatch):
    monkeypatch.setattr(parse, "parse", lambda t: ParseResult("unsure", unsure="U6", month_named=True))
    s = flow.step(start(), TextSent(1, "in March"))
    assert reply(s) == (T.unsure, T.unsure_month, T.pick) and s.phase == "greeting" and s.outputs == ()
    assert [o.key for o in flow.live(s).options] == ["job", "bills", "repair", "mix", "type"]
    problem = RangeProblem("keep_pct", "150%", "income kept", "0 to 100%")
    monkeypatch.setattr(parse, "parse", lambda t: ParseResult("out_of_range", problem=problem))
    s = flow.step(s, TextSent(s.turn, "EI 150%"))
    assert reply(s)[0] == T.out_of_range.format(value="150%", size="income kept", range="0 to 100%") and s.outputs == ()


def test_free_text_never_stacks(monkeypatch):
    monkeypatch.setattr(parse, "parse", lambda t: ok_reading(card("bills_increase_pct", 15, "bills", "%", "15%")))
    s = press(job_6(), "stack")
    s = press(flow.step(s, TextSent(s.turn, "bills up 15%")), "run")
    assert s.outputs[-1].shock == Shock(bills_increase_pct=15) and not s.stacking


# --- AC-4 -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("field,typed,shown,size,rng", [
    ("keep_pct", "150", "150%", "income kept", "0 to 100%"),
    ("months", "0", "0 months", "the length", "a whole number of months from 1 to 120"),
    ("months", "121", "121 months", "the length", "a whole number of months from 1 to 120")])
def test_ac4_typed_out_of_range_stores_nothing_and_asks_again(field, typed, shown, size, rng):
    s = start()
    s = press(s, "job") if field == "keep_pct" else run_card(s, "job", "keep_55")
    before = s
    s = flow.step(s, ValueTyped(s.turn, field, typed))
    assert reply(s)[0] == T.out_of_range.format(value=shown, size=size, range=rng)
    assert s.outputs == () and s.answers == before.answers and s.draft == before.draft
    assert s.phase == "ask_size" and s.asking == before.asking and s.turn == before.turn + 1
    assert flow.live(s).other.field == field


def test_ac4_not_a_number_asks_again():
    s = press(start(), "job")
    s = flow.step(s, ValueTyped(s.turn, "keep_pct", "abc"))
    assert reply(s)[0] == T.not_number and s.answers == () and s.outputs == () and s.asking[0] == "keep_pct"


def test_typed_sizes_are_stored_as_typed_answers_and_months_are_whole_numbers():
    s = press(start(), "job")
    s = flow.step(s, ValueTyped(s.turn, "keep_pct", "40"))
    s = flow.step(s, ValueTyped(s.turn, "months", "9"))
    assert s.outputs[0].shock == Shock(income_cut=IncomeCut(0.4, 9))
    assert [(a.value, a.source, a.shown) for a in s.answers] == [(40.0, "typed", "40%"), (9, "typed", "9 months")]
    assert isinstance(s.answers[1].value, int)


def test_ac4_two_and_a_half_months_is_refused_before_the_engine():
    s = run_card(start(), "job", "keep_55")
    s = flow.step(s, ValueTyped(s.turn, "months", "2.5"))
    assert "whole number of months" in reply(s)[0] and s.outputs == ()


# --- AC-7, invariants -----------------------------------------------------------------------------------------------

def test_ac7_a_stale_event_returns_the_same_state():
    s = start()
    old = s.turn
    s2 = press(s, "job")
    for event in (TwistPicked(old, "job"), ValuePicked(old, "keep_pct", 55, "55%"), ValueTyped(old, "keep_pct", "55"), TextSent(old, "hello"),
                  ConfirmPicked(old, True), FollowUpPicked(old, "backup"), FieldPicked(old, "months"), SendApplied(old)):
        assert flow.step(s2, event) is s2


def test_ac7_an_old_button_is_dead_after_the_next_click():
    s = job_6()
    stale = flow.live(s).options[0].event
    s2 = press(s, "stack")
    assert flow.step(s2, stale) is s2


def test_blank_text_is_a_no_op():
    s = start()
    assert flow.step(s, TextSent(s.turn, "")) is s and flow.step(s, TextSent(s.turn, "  \n ")) is s


def test_events_that_do_not_fit_the_phase_change_nothing():
    s = start()
    for event in (ValuePicked(s.turn, "keep_pct", 55, "55%"), ConfirmPicked(s.turn, True), FollowUpPicked(s.turn, "backup")):
        assert flow.step(s, event) is s
    nobody = flow.initial()
    assert flow.step(nobody, TextSent(0, "hello")) is nobody


def test_step_never_mutates_the_state_it_was_given():
    s = job_6()
    snapshot = replace(s)
    press(s, "stack")
    press(s, "backup")
    assert s == snapshot


# --- AC-8, RU-20 ----------------------------------------------------------------------------------------------------

def test_ac8_a_new_customer_archives_the_old_one_and_greets_the_new():
    s = job_6()
    t = flow.step(s, CustomerSeen(20134))
    assert t.account_id == 20134 and t.phase == "greeting" and t.turn == s.turn + 1
    assert t.answers == () and t.outputs == () and t.current == () and t.pending is None
    assert reply(t)[0] == T.greet.format(id=20134)
    assert not any("20111" in line for m in t.messages for line in m.lines)
    [section] = t.archive
    assert (section.account_id, section.messages, section.answers, section.outputs) == (ID, s.messages, s.answers, s.outputs)
    u = flow.step(t, CustomerSeen(32078))
    assert [x.account_id for x in u.archive] == [ID, 20134] and u.turn == t.turn + 1


def test_the_same_customer_seen_again_changes_nothing():
    s = job_6()
    assert flow.step(s, CustomerSeen(ID)) is s
    start0 = flow.initial()
    assert flow.step(start0, CustomerSeen(None)) is start0


def test_no_customer_keeps_the_archive_and_the_turn_counting():
    s = job_6()
    t = flow.step(s, CustomerSeen(None))
    assert t.phase == "no_customer" and t.account_id is None and reply(t) == (T.no_customer,) and len(t.archive) == 1
    assert t.turn == s.turn + 1 and len(t.messages) == 1 and flow.live(t).options == ()
    u = flow.step(t, CustomerSeen(20134))
    assert len(u.archive) == 1 and u.turn == t.turn + 1


# --- RU-21 ----------------------------------------------------------------------------------------------------------

def test_ru21_a_different_kind_adds_to_the_current_shock():
    s = press(job_6(), "stack")
    assert s.phase == "greeting" and s.stacking
    s = run_card(s, "bills", "bills_15")
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15)
    assert s.outputs[-1].call == "apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15), through_months=6)"
    assert not any(T.stack_replace.split("{")[0] in line for line in reply(s)) and not s.stacking and len(s.outputs) == 2
    expected = apply_shock(ID, s.outputs[-1].shock, through_months=6)
    assert reply(s)[1] == "✕ " + text.verdict(expected).sentence


def test_ru21_the_same_kind_replaces_and_says_so():
    s = run_card(start(), "bills", "bills_15")
    s = run_card(press(s, "stack"), "bills")
    s = flow.step(s, ValueTyped(s.turn, "bills_increase_pct", "20"))
    assert s.outputs[-1].shock == Shock(bills_increase_pct=20)
    assert reply(s)[0] == T.stack_replace.format(kind=T.kind_bills, old="bills up 15%", new="bills up 20%")
    assert [a.field for a in s.current] == ["bills_increase_pct"]


def test_ru21_dollars_replace_a_percent_because_both_are_bills():
    s = run_card(start(), "bills", "bills_15")
    s = run_card(press(s, "stack"), "bills", "dollars_month")
    s = flow.step(s, ValueTyped(s.turn, "other_spending_change", "$300"))
    assert s.outputs[-1].shock == Shock(other_spending_change=300)
    assert reply(s)[0] == T.stack_replace.format(kind=T.kind_bills, old="bills up 15%", new="bills or rent up $300 a month")


def test_ru21_a_second_job_loss_replaces_the_first_whole():
    s = press(job_6(), "stack")
    s = run_card(s, "job", "keep_55", "months_12")
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 12))
    assert reply(s)[0] == T.stack_replace.format(kind=T.kind_job, old="income kept at 55% for 6 months", new="income kept at 55% for 12 months")


def test_ru21_mix_on_a_repair_adds_a_job_loss_and_bills():
    s = run_card(start(), "repair", "repair_1")
    s = run_card(press(s, "stack"), "mix", "keep_55", "months_6", "bills_15")
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15, one_off_spending_multiple=1)


# --- J4.3: change size, plans, send ---------------------------------------------------------------------------------

def test_change_size_reruns_with_exactly_one_field_changed():
    s = press(job_6(), "size")
    assert s.phase == "pick_size" and reply(s) == (T.pick_size,)
    assert [(o.key, o.label) for o in flow.live(s).options] == [("keep_pct", "Change income kept (55%)"), ("months", "Change the length (6 months)")]
    s = press(s, "months")
    assert s.phase == "ask_size" and s.asking == ("months",)
    s = press(s, "months_12")
    assert len(s.outputs) == 2 and s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 12)) and s.outputs[-1].through_months == 12
    assert [(a.field, a.value) for a in s.current] == [("keep_pct", 55), ("months", 12)]
    expected = apply_shock(ID, s.outputs[-1].shock, through_months=12)
    assert reply(s)[1] == ("✓ " if text.verdict(expected).tone == "ok" else "✕ ") + text.verdict(expected).sentence


def test_change_size_of_keep_leaves_months_alone():
    s = press(press(job_6(), "size"), "keep_pct")
    s = flow.step(s, ValueTyped(s.turn, "keep_pct", "40"))
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.4, 6))


def test_change_size_can_swap_bills_percent_for_dollars():
    s = run_card(start(), "bills", "bills_15")
    s = press(press(s, "size"), "bills_increase_pct")
    s = press(s, "dollars_month")
    s = flow.step(s, ValueTyped(s.turn, "other_spending_change", "250"))
    assert s.outputs[-1].shock == Shock(other_spending_change=250) and len(s.current) == 1


def test_backup_plan_runs_make_plan_with_the_controls_target_and_offers_the_goal_first(monkeypatch):
    seen = []
    real = flow.make_plan
    monkeypatch.setattr(flow, "make_plan", lambda *a, **k: seen.append((a, k)) or real(*a, **k))
    s = press(job_6(), "backup", Context(target_months=4))
    assert seen == [((ID, CUT_6), {"target_months": 4, "through_months": 6})]
    out = s.outputs[-1]
    assert out.function == "make_plan" and out.target_months == 4 and out.call == "make_plan(20111, Shock(income_cut=IncomeCut(0.55, 6)), target_months=4, through_months=6)"
    plan = make_plan(ID, CUT_6, target_months=4, through_months=6)
    assert reply(s)[0] == T.engine_call.format(call=out.call) and reply(s)[1] == flow.replies.plan_lines(plan, "backup")[0]
    assert (out.goal_state, out.backup_state) == (plan.goal.state, plan.backup.state)
    assert [o.key for o in flow.live(s).options][:2] == ["goal", "backup"] and s.phase == "plan"
    g = press(s, "goal", Context(target_months=4))
    assert tuple(reply(g)[1:]) == flow.replies.plan_lines(plan, "goal") and [o.key for o in flow.live(g).options][:2] == ["backup", "goal"]
    assert len(g.outputs) == 3


def test_a_plan_is_never_asked_for_without_a_shock():
    s = start()
    assert flow.step(s, FollowUpPicked(s.turn, "backup")) is s


def test_send_that_fits_hands_the_card_to_the_page_and_the_page_confirms(monkeypatch):
    monkeypatch.setattr(controls, "cant_send", lambda answers: None)
    s = press(job_6(), "send")
    assert s.phase == "sent" and s.outbox == s.current and reply(s) == (T.send_ok,)
    t = flow.step(s, SendApplied(s.turn))
    assert t.outbox is None and t.phase == "result" and t.turn == s.turn + 1 and reply(t) == (T.send_ok,)
    assert [o.key for o in flow.live(t).options][0] == "backup" and all(o.event.turn == t.turn for o in flow.live(t).options)


def test_send_that_does_not_fit_says_why_and_stays(monkeypatch):
    monkeypatch.setattr(controls, "cant_send", lambda answers: T.cant_open)
    s = press(job_6(), "send")
    assert s.phase == "result" and s.outbox is None and reply(s) == (T.send_cant.format(what=T.cant_open),)
    assert [o.key for o in flow.live(s).options][0] == "backup"


def test_new_customer_button_points_at_the_picker():
    s = press(job_6(), "new")
    assert reply(s) == (T.new,) and s.phase == "result"


# --- J4.1 3c, 6b, J4.2 2f -------------------------------------------------------------------------------------------

def test_j41_6b_an_engine_refusal_goes_back_to_that_size(monkeypatch):
    def refuse(*args, **kwargs):
        raise InvalidShockError("months", "x")
    monkeypatch.setattr(flow, "apply_shock", refuse)
    s = run_card(start(), "job", "keep_55", "months_6")
    assert s.outputs == () and s.phase == "ask_size" and s.asking == ("months",)
    assert reply(s) == (T.engine_refused.format(field="the length"), T.ask_months)
    assert [o.key for o in flow.live(s).options] == ["months_6", "months_12", "months_none"]


def test_j41_6b_the_engines_keep_fraction_is_the_keep_size(monkeypatch):
    def refuse(*args, **kwargs):
        raise InvalidShockError("keep_fraction", "x")
    monkeypatch.setattr(flow, "apply_shock", refuse)
    s = run_card(start(), "job", "keep_55", "months_6")
    assert s.asking == ("keep_pct",) and reply(s)[0] == T.engine_refused.format(field="income kept")


def test_j41_6b_a_refusal_from_shock_from_is_caught_too(monkeypatch):
    def refuse(answers):
        raise InvalidShockError("bills_increase_pct", "x")
    monkeypatch.setattr(flow, "shock_from", refuse)
    s = run_card(start(), "bills", "bills_15")
    assert s.outputs == () and s.asking == ("bills_increase_pct",) and s.phase == "ask_size"


def test_j42_2f_a_bare_number_while_asking_is_that_size():
    by_click = run_card(start(), "job", "keep_55", "months_6")
    s = press(start(), "job")
    s = flow.step(s, TextSent(s.turn, "55"))
    assert s.asking == ("months",) and s.outputs == () and s.answers[0].value == 55 and s.answers[0].source == "typed"
    s = flow.step(s, TextSent(s.turn, "6"))
    assert s.phase == "result" and s.answers[1].value == 6 and isinstance(s.answers[1].value, int)
    assert s.outputs[0].shock == by_click.outputs[0].shock and reply(s)[1:] == reply(by_click)[1:]


def test_j42_2f_a_bare_number_out_of_range_is_refused_like_the_other_box():
    s = run_card(start(), "job", "keep_55")
    s = flow.step(s, TextSent(s.turn, "121"))
    assert reply(s)[0].startswith("121 months is outside what the engine takes") and s.outputs == ()


def test_type_it_asks_for_the_card_and_keeps_the_twist_buttons():
    s = press(start(), "type")
    assert reply(s) == (T.type_prompt,) and s.phase == "greeting" and flow.live(s).options[0].event.turn == s.turn


def test_dollar_amount_button_swaps_the_repair_field():
    s = press(press(start(), "repair"), "dollar_amount")
    assert s.asking == ("one_off_dollars",) and flow.live(s).other.field == "one_off_dollars" and flow.live(s).other.placeholder == T.hint_dollars
    s = flow.step(s, ValueTyped(s.turn, "one_off_dollars", "2,500"))
    assert s.outputs[-1].shock == Shock(one_off_dollars=2500)


@pytest.mark.parametrize("twist,field,key_labels,hint", [
    ("job", "keep_pct", [("keep_55", "55%")], "0 to 100"),
    ("bills", "bills_increase_pct", [("bills_15", "+15%"), ("dollars_month", "Dollars a month")], "0 or more"),
    ("repair", "one_off_spending_multiple", [("repair_1", "1 month of spending"), ("dollar_amount", "Dollar amount")], "months of spending")])
def test_flows_section_4_size_buttons(twist, field, key_labels, hint):
    s = press(start(), twist)
    live = flow.live(s)
    assert [(o.key, o.label) for o in live.options] == key_labels and live.other.field == field and live.other.placeholder == hint
    assert live.other.button == T.use


def test_months_buttons_and_the_other_box():
    live = flow.live(run_card(start(), "job", "keep_55"))
    assert [(o.key, o.label) for o in live.options] == [("months_6", "6 months"), ("months_12", "12 months"), ("months_none", "Until it runs out")]
    assert live.other.placeholder == "1 to 120"


# --- J5.WP-C: assumed length (D2, ADR 0010, NEW-COPY-17) ------------------------------------------------------------

PT04 = "They lose their job (EI at 55%) and their household bills go up 15% in the same month."


def test_d2_pt04_confirm_says_assumed_then_the_result_ends_with_the_assumed_length_line():
    s = flow.step(start(), TextSent(1, PT04))
    assert s.phase == "confirm"
    assert reply(s) == (T.confirm.format(plain="income kept at 55% for 6 months (assumed); bills up 15%"),)
    s = press(s, "run")
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 6), bills_increase_pct=15)
    assert reply(s)[-1] == text.ASSUMED_LENGTH


def test_d2_a_stated_length_never_gets_the_assumed_line():
    s = press(flow.step(start(), TextSent(1, "laid off, EI 55% for 6 months and bills up 15%")), "run")
    assert text.ASSUMED_LENGTH not in reply(s)


def test_new_parser_6_furnace_asks_the_repair_size_and_keeps_the_length_assumed():
    s = flow.step(start(), TextSent(1, "laid off and the furnace dies, EI 55%"))
    assert s.phase == "ask_size" and s.asking == ("one_off_spending_multiple",)
    assert "for 6 months (assumed)" in reply(s)[0]
    s = press(s, "repair_1")
    assert s.outputs[-1].shock == Shock(income_cut=IncomeCut(0.55, 6), one_off_spending_multiple=1)
    assert reply(s)[-1] == text.ASSUMED_LENGTH


def test_d2_a_bare_laid_off_still_asks_the_keep_then_the_length():
    s = flow.step(start(), TextSent(1, "laid off"))
    assert s.phase == "ask_size" and s.asking == ("keep_pct", "months")
