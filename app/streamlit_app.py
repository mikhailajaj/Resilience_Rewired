"""Resilience Rewired. Run from this folder with `streamlit run streamlit_app.py`.

This file holds what both pages share: the theme CSS, the engine start-up and the customer picker. Numbers come only from the engine.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.assistant.chat_text import T
from app.engine import warm_up
from app.ui.findings_view import F
from app.ui.shared import picker
from app.ui.style import CSS


@st.cache_resource(show_spinner="Loading the bank data...")
def start_engine():
    warm_up()


st.set_page_config(layout="wide")
st.html(CSS)
start_engine()
page = st.navigation([
    st.Page("app_pages/shock_and_plan.py", title="Shock and plan", icon=":material/bolt:", default=True,
            help="Know the customer, apply a shock of any size, and see the goal plan and backup plan."),
    st.Page("app_pages/customer_profiling.py", title="Customer profiling", icon=":material/person_search:",
            help="Everything on file for the customer, and questions to ask the stakeholder, with room for answers."),
    st.Page("app_pages/assistant.py", title=T.page, icon=":material/chat:",
            help="Pick a twist in a short conversation, or type it, and see the engine's result in plain words."),
    st.Page("app_pages/findings.py", title=F.page, icon=":material/insights:"),
], position="top")
picker()
page.run()
