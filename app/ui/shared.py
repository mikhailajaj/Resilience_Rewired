"""What both pages use: text helpers and the customer picker, which keeps one customer across pages."""
import html

import streamlit as st

from app.engine import InvalidAccountIdError, account_id_range, get_profile

ss = st.session_state


def md(line):
    """Markdown with literal dollar signs, which would otherwise start LaTeX."""
    st.markdown(line.replace("$", r"\$"))


def caption(line):
    st.caption(line.replace("$", r"\$"))


def raw(tag_class, line):
    st.html(f'<div class="{tag_class}">{html.escape(line)}</div>')


def load_customer(typed):
    """Checks the typed ID. A new customer starts with no shock."""
    ss.id_error = None
    typed = typed.strip()
    if not typed:
        ss.shown_id = None
        return
    try:
        profile = get_profile(typed)
    except InvalidAccountIdError as error:
        ss.shown_id = None
        if error.reason == "not_digits":
            ss.id_error = f'"{typed[:30]}" isn\'t an account number. Use digits only, for example 20111.'
        else:
            bounds = account_id_range()
            ss.id_error = f"No account {typed} in this data. Try another number. Account numbers here run from {bounds.min} to {bounds.max}."
        return
    if ss.get("shown_id") != profile.account_id:
        ss.pop("inp", None)
    ss.shown_id = profile.account_id


def picker():
    with st.container(key="hero"):
        st.title("Resilience Rewired", anchor=False)
        st.markdown("How long can this customer last if money gets tight?")
    with st.form("picker", border=False):
        box, button = st.columns([4, 1], vertical_alignment="bottom")
        typed = box.text_input("Account ID", key="typed_id", autocomplete="off")
        submitted = button.form_submit_button("Show customer", type="primary", width="stretch")
    caption("Type the account number, for example 20111. Press Enter.")
    if submitted:
        load_customer(typed)
    if ss.get("id_error"):
        with st.container(key="id-error"):
            st.text("✕ " + ss.id_error)
