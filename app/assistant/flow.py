"""The chat state machine: one event in, one new state out (ADR 0003, design section 4.2)."""
from dataclasses import replace

from app.engine import InvalidShockError, apply_shock, get_profile, make_plan

from . import controls, parse, replies
from .chat_text import T
from .state import (FIELD_KIND, KIND_FIELDS, RULES, SIZE_WORDS, CardAnswer, ChatState, ConfirmPicked, Context, CustomerSeen, Event, FieldPicked,
                    FollowUpPicked, Message, Option, OtherBox, SendApplied, Section, TextSent, TwistPicked, ValuePicked, ValueTyped, _shown,
                    check_size, shock_from)

TWISTS = ("job", "bills", "repair", "mix", "type")
KINDS = ("job", "bills", "repair")
SLOT = {"bills_increase_pct": "bills", "other_spending_change": "bills", "one_off_spending_multiple": "repair", "one_off_dollars": "repair"}
ENGINE_FIELDS = {"keep_fraction": "keep_pct"}
ASK = {"keep_pct": T.ask_keep, "months": T.ask_months, "bills_increase_pct": T.ask_bills, "other_spending_change": T.ask_bills,
       "one_off_spending_multiple": T.ask_repair, "one_off_dollars": T.ask_repair}
HINT = {"keep_pct": T.hint_keep, "months": T.hint_months, "bills_increase_pct": T.hint_pct, "other_spending_change": T.hint_dollars_month,
        "one_off_spending_multiple": T.hint_spending, "one_off_dollars": T.hint_dollars}
FOLLOW_UP_LABEL = {"backup": T.f_backup, "goal": T.f_goal, "stack": T.f_stack, "size": T.f_size, "new": T.f_new, "send": T.f_send}


def initial() -> ChatState:
    return ChatState(messages=(Message(0, "assistant", (T.no_customer,)),))


def live(state: ChatState) -> Message | None:
    return state.messages[-1] if state.messages and state.messages[-1].role == "assistant" else None


# --- Building blocks ------------------------------------------------------------------------------------------------

def _accept(state: ChatState, user_text: str, **changes) -> ChatState:
    turn = state.turn + 1
    return replace(state, turn=turn, messages=state.messages + (Message(turn, "user", (user_text,)),), **changes)


def _say(state: ChatState, lines, options=(), other=None, **changes) -> ChatState:
    return replace(state, messages=state.messages + (Message(state.turn, "assistant", tuple(lines), tuple(options), other),), **changes)


def _twist_options(turn: int) -> tuple[Option, ...]:
    return tuple(Option(k, getattr(T, f"b_{k}"), TwistPicked(turn, k)) for k in TWISTS)


def _value(turn: int, key: str, field: str, value, label: str) -> Option:
    return Option(key, label, ValuePicked(turn, field, value, label))


def _ask(turn: int, field: str, *lead: str) -> tuple[tuple[str, ...], tuple[Option, ...], OtherBox]:
    if field == "keep_pct":
        options = (_value(turn, "keep_55", field, 55, T.v_keep_55),)
    elif field == "months":
        options = (_value(turn, "months_6", field, 6, T.v_months_6), _value(turn, "months_12", field, 12, T.v_months_12),
                   _value(turn, "months_none", field, None, T.v_months_none))
    elif field == "bills_increase_pct":
        options = (_value(turn, "bills_15", field, 15, T.v_bills_15), Option("dollars_month", T.b_dollars_month, FieldPicked(turn, "other_spending_change")))
    elif field == "one_off_spending_multiple":
        options = (_value(turn, "repair_1", field, 1, T.v_repair_1), Option("dollar_amount", T.b_dollar_amount, FieldPicked(turn, "one_off_dollars")))
    else:
        options = ()
    return (*lead, ASK[field]), options, OtherBox(field, HINT[field], T.use)


def _ask_state(state: ChatState, field: str, *lead: str, **changes) -> ChatState:
    lines, options, other = _ask(state.turn, field, *lead)
    return _say(state, lines, options, other, phase="ask_size", **changes)


def _follow_ups(turn: int, first: str = "backup") -> tuple[Option, ...]:
    plans = ("backup", "goal") if first == "backup" else ("goal", "backup")
    return tuple(Option(a, FOLLOW_UP_LABEL[a], FollowUpPicked(turn, a)) for a in (*plans, "stack", "size", "new", "send"))


def _tidy(answers) -> tuple[CardAnswer, ...]:
    """One answer per field; the two ways to size bills (and the two for a repair) share one place. A later answer takes the earlier one's position."""
    out = []
    for a in answers:
        slot = SLOT.get(a.field, a.field)
        for i, b in enumerate(out):
            if SLOT.get(b.field, b.field) == slot:
                out[i] = a
                break
        else:
            out.append(a)
    return tuple(out)


def _merge(state: ChatState, draft: tuple[CardAnswer, ...]) -> tuple[tuple[CardAnswer, ...], tuple[str, ...]]:
    """The shock to run, and the T.stack_replace lines (RU-21). A draft that starts with `current` adds to it (stack) or changes one size."""
    base = state.current
    if not base or draft[:len(base)] != base:
        return _tidy(draft), ()
    new = draft[len(base):]
    if not state.stacking:
        return _tidy(base + new), ()
    kinds = {a.kind for a in new}
    lines = tuple(T.stack_replace.format(kind=getattr(T, f"kind_{k}"), old=replies.plain(tuple(a for a in base if a.kind == k)),
                                         new=replies.plain(tuple(a for a in new if a.kind == k)))
                  for k in KINDS if k in kinds and any(a.kind == k for a in base))
    return _tidy(tuple(a for a in base if a.kind not in kinds) + new), lines


def _stamp(answers, turn: int) -> tuple[CardAnswer, ...]:
    return tuple(replace(a, turn=turn) for a in answers)


# --- Engine runs ----------------------------------------------------------------------------------------------------

def _refused(state: ChatState, error, fallback: str) -> ChatState:
    field = ENGINE_FIELDS.get(error.field, error.field)
    if field not in ASK:
        field = fallback
    return _ask_state(state, field, T.engine_refused.format(field=SIZE_WORDS[field]), asking=(field,), pending=None, stacking=False)


def _run(state: ChatState, draft: tuple[CardAnswer, ...]) -> ChatState:
    answers, replaced = _merge(state, draft)
    try:
        shock = shock_from(answers)
        months = shock.income_cut.months if shock.income_cut else None
        profile = get_profile(state.account_id)
        r = apply_shock(state.account_id, shock, through_months=months)
    except (InvalidShockError, ValueError) as error:
        return _refused(state, error if isinstance(error, InvalidShockError) else InvalidShockError("keep_pct", str(error)), draft[-1].field)
    call = replies.call_text("apply_shock", state.account_id, shock, through_months=months)
    lines = (*replaced, T.engine_call.format(call=call), *replies.result_lines(r, profile, assumed_months=any(a.field == "months" and a.source == "assumed" for a in answers)))
    return _say(state, lines, _follow_ups(state.turn), phase="result", current=answers, draft=(), asking=(), pending=None, stacking=False,
                outputs=state.outputs + (replies.record(state.turn, call, r=r),))


def _plan(state: ChatState, which: str, ctx: Context) -> ChatState:
    try:
        shock = shock_from(state.current)
        months = shock.income_cut.months if shock.income_cut else None
        plan = make_plan(state.account_id, shock, target_months=ctx.target_months, through_months=months)
    except (InvalidShockError, ValueError) as error:
        return _refused(state, error if isinstance(error, InvalidShockError) else InvalidShockError("keep_pct", str(error)), state.current[-1].field)
    call = replies.call_text("make_plan", state.account_id, shock, through_months=months, target_months=ctx.target_months)
    lines = (T.engine_call.format(call=call), *replies.plan_lines(plan, which))
    return _say(state, lines, _follow_ups(state.turn, "goal" if which == "backup" else "backup"), phase="plan",
                outputs=state.outputs + (replies.record(state.turn, call, plan=plan, target_months=ctx.target_months),))


# --- Events ---------------------------------------------------------------------------------------------------------

def _seen(state: ChatState, event: CustomerSeen) -> ChatState:
    if event.account_id == state.account_id:
        return state
    archive = state.archive
    if state.account_id is not None:
        archive += (Section(state.account_id, state.messages, state.answers, state.outputs),)
    turn = state.turn + 1
    fresh = ChatState(turn=turn, archive=archive)
    if event.account_id is None:
        return _say(fresh, (T.no_customer,))
    return _say(replace(fresh, account_id=event.account_id, phase="greeting"), replies.greeting(get_profile(event.account_id)), _twist_options(turn))


def _greeting(state: ChatState, *lead: str, **changes) -> ChatState:
    return _say(state, (*lead, T.pick), _twist_options(state.turn), phase="greeting", **changes)


def _twist(state: ChatState, event: TwistPicked) -> ChatState:
    if state.phase != "greeting" or event.twist not in TWISTS:
        return state
    label = getattr(T, f"b_{event.twist}")
    if event.twist == "type":
        return _say(_accept(state, label), (T.type_prompt,), _twist_options(state.turn + 1))
    fields = KIND_FIELDS[event.twist]
    return _ask_state(_accept(state, label, asking=fields, draft=state.current if state.stacking else ()), fields[0])


def _field(state: ChatState, event: FieldPicked) -> ChatState:
    field = event.field
    if state.phase == "pick_size":
        if field == "after_ends" or all(a.field != field for a in state.current):
            return state
        shown = next(a.shown for a in state.current if a.field == field)
        st = _accept(state, T.size_button.format(size=SIZE_WORDS[field], shown=shown), asking=(field,), draft=state.current, stacking=False)
        return _ask_state(st, field)
    if state.phase == "ask_size" and field in SLOT and state.asking and SLOT.get(state.asking[0]) == SLOT[field]:
        label = T.b_dollars_month if field == "other_spending_change" else T.b_dollar_amount
        st = _accept(state, label, asking=(field, *state.asking[1:]))
        return _ask_state(st, field)
    return state


def _store(state: ChatState, field: str, value, shown: str, source: str, user_text: str) -> ChatState:
    problem = check_size(field, value)
    if problem is not None:
        return _ask_state(_accept(state, user_text), field, T.out_of_range.format(value=problem.value, size=problem.size, range=problem.range))
    if field == "months" and isinstance(value, float):
        value = int(value)
    answer = CardAnswer(state.turn + 1, FIELD_KIND[field], field, value, RULES[field].unit, source, shown)
    st = _accept(state, user_text, answers=state.answers + (answer,), draft=state.draft + (answer,), asking=state.asking[1:])
    return _ask_state(st, st.asking[0]) if st.asking else _run(st, st.draft)


def _typed(state: ChatState, field: str, text: str) -> ChatState:
    number = parse.read_number(text)
    if number is None:
        return _ask_state(_accept(state, text), field, T.not_number)
    return _store(state, field, number, _shown(field, number), "typed", text)


def _text(state: ChatState, event: TextSent) -> ChatState:
    if not event.text.strip() or state.phase == "no_customer":
        return state
    if state.phase == "ask_size" and state.asking and parse.read_number(event.text) is not None:
        return _typed(state, state.asking[0], event.text)
    result = parse.parse(event.text)
    st = _accept(state, event.text, pending=None, stacking=False, draft=(), asking=())
    if result.status == "ok":
        options = (Option("run", T.b_run, ConfirmPicked(st.turn, True)), Option("buttons", T.b_buttons, ConfirmPicked(st.turn, False)))
        return _say(st, (T.confirm.format(plain=replies.plain(result.answers)),), options, phase="confirm", pending=result)
    if result.status == "partial" and result.missing:
        stamped = _stamp(result.answers, st.turn)
        lead = (T.partial.format(plain=replies.plain(stamped), size=SIZE_WORDS[result.missing[0]]),) if stamped else ()
        return _ask_state(st, result.missing[0], *lead, asking=result.missing, draft=stamped, answers=st.answers + stamped)
    if result.status == "out_of_range" and result.problem is not None:
        p = result.problem
        return _greeting(st, T.out_of_range.format(value=p.value, size=p.size, range=p.range))
    return _greeting(st, T.unsure, *((T.unsure_month,) if result.month_named else ()))


def _confirm(state: ChatState, event: ConfirmPicked) -> ChatState:
    if state.phase != "confirm" or state.pending is None:
        return state
    if not event.run:
        return _greeting(_accept(state, T.b_buttons, pending=None))
    st = _accept(state, T.b_run, pending=None)
    answers = _stamp(state.pending.answers, st.turn)
    return _run(replace(st, answers=st.answers + answers, draft=answers), answers)


def _follow_up(state: ChatState, event: FollowUpPicked, ctx: Context) -> ChatState:
    action = event.action
    if state.phase not in ("result", "plan") or action not in FOLLOW_UP_LABEL:
        return state
    st = _accept(state, FOLLOW_UP_LABEL[action])
    if action in ("backup", "goal"):
        return _plan(st, action, ctx)
    if action == "stack":
        return _greeting(st, stacking=True, draft=(), asking=())
    if action == "size":
        options = tuple(Option(a.field, T.size_button.format(size=SIZE_WORDS[a.field], shown=a.shown), FieldPicked(st.turn, a.field))
                        for a in st.current if a.field != "after_ends")
        return _say(st, (T.pick_size,), options, phase="pick_size")
    if action == "new":
        return _say(st, (T.new,), _follow_ups(st.turn))
    reason = controls.cant_send(st.current)
    if reason is not None:
        return _say(st, (T.send_cant.format(what=reason),), _follow_ups(st.turn))
    return _say(st, (T.send_ok,), phase="sent", outbox=st.current)


def _applied(state: ChatState) -> ChatState:
    if state.phase != "sent":
        return state
    turn = state.turn + 1
    last = state.messages[-1]
    return replace(state, turn=turn, phase="result", outbox=None, messages=state.messages[:-1] + (Message(turn, "assistant", last.lines, _follow_ups(turn)),))


def step(state: ChatState, event: Event, ctx: Context = Context()) -> ChatState:
    if isinstance(event, CustomerSeen):
        return _seen(state, event)
    if event.turn != state.turn:
        return state
    if isinstance(event, TwistPicked):
        return _twist(state, event)
    if isinstance(event, FieldPicked):
        return _field(state, event)
    if isinstance(event, (ValuePicked, ValueTyped)):
        if state.phase != "ask_size" or not state.asking or event.field != state.asking[0]:
            return state
        if isinstance(event, ValuePicked):
            return _store(state, event.field, event.value, event.label, "button", event.label)
        return _typed(state, event.field, event.text)
    if isinstance(event, TextSent):
        return _text(state, event)
    if isinstance(event, ConfirmPicked):
        return _confirm(state, event)
    if isinstance(event, FollowUpPicked):
        return _follow_up(state, event, ctx)
    if isinstance(event, SendApplied):
        return _applied(state)
    return state
