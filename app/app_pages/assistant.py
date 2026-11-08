"""Chat: a guided conversation that runs a twist on the loaded customer. All logic is in app/assistant; this page only draws it."""
import streamlit as st

from app.assistant import controls, flow, transcript
from app.assistant.chat_text import T
from app.assistant.state import DEFAULT_TARGET, Context, CustomerSeen, SendApplied, TextSent, ValueTyped
from app.ui import cheatsheet
from app.ui.shared import md

ss = st.session_state


def ctx():
    return Context(target_months=ss.get("inp", {}).get("target", DEFAULT_TARGET))


def dispatch(event):
    ss.chat = flow.step(ss.chat, event, ctx())


def on_text():
    dispatch(TextSent(ss.chat.turn, ss.chat_text))


def on_other(field):
    dispatch(ValueTyped(ss.chat.turn, field, ss[f"chat_{ss.chat.turn}_other"]))


state = ss.get("chat") or flow.initial()
if ss.get("shown_id") != state.account_id:
    state = flow.step(state, CustomerSeen(ss.get("shown_id")), ctx())
ss.chat = state
if state.outbox is not None:
    ss.inp = controls.to_inputs(state.outbox, ss.get("inp"))
    ss.chat = flow.step(state, SendApplied(state.turn), ctx())
    st.switch_page("app_pages/shock_and_plan.py")

head, download = st.columns([3, 2], vertical_alignment="center")
head.subheader(T.page, anchor=False)
download.download_button(T.download, transcript.to_markdown(state), file_name=transcript.file_name(state), mime="text/markdown",
                         on_click="ignore", key="chat_download", disabled=state.account_id is None)
st.caption(T.download_help)

for m in state.messages:
    with st.chat_message(m.role):
        for line in m.lines:
            md(line)

live = flow.live(state)
if live is not None:
    if live.options:
        with st.container(horizontal=True):         # wraps onto a second row on a narrow window (wireframe T)
            for option in live.options:
                st.button(option.label, key=f"chat_{live.turn}_{option.key}", on_click=dispatch, args=(option.event,))
    if live.other:
        st.text_input(T.other, key=f"chat_{live.turn}_other", placeholder=live.other.placeholder)
        st.button(live.other.button, key=f"chat_{live.turn}_use", on_click=on_other, args=(live.other.field,))

with st.expander(T.cheatsheet):
    st.markdown(cheatsheet.markdown())
st.chat_input(T.placeholder, key="chat_text", on_submit=on_text, disabled=state.account_id is None)
