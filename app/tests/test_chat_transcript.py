"""transcript.py: the download, from stored records only (ADR 0005, J4.4)."""
import inspect
from dataclasses import replace

import pytest

import app.engine as engine
from app.assistant import flow, transcript
from app.assistant.state import CardAnswer, ChatState, CustomerSeen, EngineOutput, Message, Section, TwistPicked, ValuePicked
from app.engine import Shock


def output(turn, account_id, call, **kw):
    base = dict(function="apply_shock", shock=Shock(), through_months=6, target_months=None, verdict_case="C2", runway_before="4.0 months",
                runway_after="1.5 months", gap_before=100.0, gap_after=1234567.0, fact_codes=("F1", "F2"), goal_state=None, backup_state=None)
    base.update(kw)
    return EngineOutput(turn, account_id, call=call, **base)


ANSWER = CardAnswer(2, "job", "keep_pct", 55, "%", "button", "55%")
OLD = Section(7, (Message(1, "assistant", ("Old hello",)), Message(2, "user", ("Old reply",))),
              (CardAnswer(2, "bills", "bills_increase_pct", 15, "%", "typed", "15%"),), (output(3, 7, "apply_shock(old)"),))


def hand_state(**kw):
    msgs = (Message(1, "assistant", ("Hi. I have customer 9 loaded.", "Which twist? Pick one | or type"), ),
            Message(2, "user", ("Job loss on EI",)), Message(3, "assistant", ("Runway 4.0 -> 1.5", "second line")))
    out = (output(3, 9, "apply_shock(a|b)", goal_state="reached", backup_state="none"),)
    return ChatState(9, "result", 3, msgs, (ANSWER,), out, **kw)


def test_chat_messages_verbatim_with_roles():
    md = transcript.to_markdown(hand_state())
    assert md.startswith("# Chat transcript")
    for line in ("Hi. I have customer 9 loaded.", "Which twist? Pick one | or type", "Job loss on EI", "Runway 4.0 -> 1.5", "second line"):
        assert line in md
    assert md.index("**Assistant:**") < md.index("**You:**")
    assert "## Customer 9" in md and "### Conversation" in md


def test_chat_answers_and_outputs_in_tables():
    md = transcript.to_markdown(hand_state())
    assert "| 2 | job | keep_pct | 55 | % | button | 55% |" in md
    assert "apply_shock(a\\|b)" in md
    assert "4.0 months -> 1.5 months" in md and "$100 -> $1.2M" in md and "F1, F2" in md
    assert "goal: reached" in md and "backup: none" in md and "C2" in md


def test_chat_archive_comes_first():
    md = transcript.to_markdown(hand_state(archive=(OLD,)))
    assert md.index("## Customer 7") < md.index("## Customer 9")
    assert md.index("Old hello") < md.index("## Customer 9")
    assert "apply_shock(old)" in md and "| 2 | bills | bills_increase_pct | 15 | % | typed | 15% |" in md


def test_chat_file_name():
    assert transcript.file_name(hand_state()) == "chat_transcript_9.md"


def test_chat_greeting_only_has_no_rows_j44_1a():
    state = flow.step(flow.initial(), CustomerSeen(20111))
    md = transcript.to_markdown(state)
    for m in state.messages:
        for line in m.lines:
            assert line in md
    assert md.count("None yet.") == 2 and "| Turn |" not in md


def test_chat_no_customer_state():
    assert "No customer yet." in transcript.to_markdown(ChatState())


def engine_names():
    names = [(engine, n) for n, v in vars(engine).items() if callable(v) and not n.startswith("__")]
    names += [(flow, n) for n, v in vars(flow).items() if callable(v) and getattr(v, "__module__", "").startswith("app.engine")]
    return names


def test_chat_transcript_needs_no_engine(monkeypatch):
    state = flow.step(flow.initial(), CustomerSeen(20111))                     # a real run: job loss, 55%, 6 months (AC-1)
    for pick in (lambda t: TwistPicked(t, "job"), lambda t: ValuePicked(t, "keep_pct", 55, "55%"), lambda t: ValuePicked(t, "months", 6, "6 months")):
        state = flow.step(state, pick(state.turn))
    assert len(state.outputs) == 1
    state = replace(state, archive=(OLD,))
    before = transcript.to_markdown(state)
    for line in (l for m in state.messages for l in m.lines):
        assert line in before
    assert state.outputs[0].call in before and "IncomeCut(0.55, 6)" in before

    def boom(*a, **k):
        raise AssertionError("engine called")

    for mod, name in engine_names():
        monkeypatch.setattr(mod, name, boom, raising=False)
    assert transcript.to_markdown(state) == before
    assert transcript.file_name(state) == "chat_transcript_20111.md"


def test_chat_transcript_imports_no_engine_function():
    src = inspect.getsource(transcript)
    assert "app.engine" not in src
