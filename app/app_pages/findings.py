"""Findings: what the data shows about spending after a shock, and four more findings across all accounts. Needs no customer."""
import pandas as pd
import streamlit as st

from app.engine import account_findings, biggest_finding
from app.ui import findings_view as view
from app.ui.findings_view import F
from app.ui.shared import caption, md

st.header(F.page, anchor=False)
st.subheader(F.head, anchor=False)

finding = biggest_finding()
for column, (label, value) in zip(st.columns(3), view.numbers(finding)):
    column.metric(label.replace("$", r"\$"), value)
for line in view.lines(finding):
    md(line)
st.altair_chart(view.chart(finding), width="stretch")
caption(view.alt_text(finding))

st.markdown(f"**{F.tier_head}**")
st.table(pd.DataFrame(view.tier_rows(finding), columns=list(F.tier_cols)), hide_index=True, alt=F.tier_head)

with st.spinner(F.spinner):
    accounts = account_findings()
for line in view.account_lines(accounts):
    md(f"- {line}")
caption(finding.evidence)
caption(F.pointer)

st.markdown(f"**{F.refs_head}**")
st.markdown("\n".join(view.reference_lines()))
