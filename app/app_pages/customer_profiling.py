"""Customer profiling: everything on file for one customer, and the questions to ask the stakeholder."""
import pandas as pd
import streamlit as st

from app.engine import account_flows, customer_record, get_profile, make_plan, monthly_history
from app.ui import charts, profile_view as view, questionnaire, text
from app.ui.shared import caption, md

ss = st.session_state


def table(rows, alt):
    """A small static table, from (label, value) pairs or from dicts."""
    pairs = bool(rows) and isinstance(rows[0], tuple)
    frame = pd.DataFrame(rows, columns=["Measure", "Value"] if pairs else None).astype(str).replace(r"\$", r"\\$", regex=True)
    st.table(frame, hide_index=True, hide_header=pairs, alt=alt)


def answer_box(question):
    st.text_area("Answer", key=f"answer_{account}_{question.id}", persist_state="session", height=100,
                 placeholder="Type the stakeholder's answer here.")


def show_questions(questions):
    for number, question in enumerate(questions, 1):
        with st.container(border=True):
            md(f"**{number}. {question.question}**")
            caption(f"{question.topic}. Why we ask: {question.why}")
            caption(f"What the answer changes: {question.changes}")
            answer_box(question)


st.header("Customer profiling", anchor=False)
account = ss.get("shown_id")
if not account:
    if not ss.get("id_error"):
        st.markdown("Enter an account ID to see everything on file for this customer, and the questions to ask the stakeholder.")
    st.stop()

profile = get_profile(account)
flows = account_flows(account)
record = customer_record(account)
plan = make_plan(account)
history = monthly_history(account)

st.subheader(f"Customer {account}", anchor=False)
md(text.summary_line(profile))
md(text.flow_line(profile, flows))

who, money_tab, balance_tab, debts, months, questions_tab = st.tabs(
    ["Who they are", "Money in and out", "Balance", "Costs and loan", "Month by month", "Stakeholder questions"], key="profile_tabs")

with who:
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Account", anchor=False)
        table(view.account_rows(profile, record), f"Account details for customer {account}.")
        st.subheader("The standard (judges') numbers", anchor=False)
        table(view.judges_rows(profile), "The standard (judges') numbers for this customer.")
    with right:
        st.subheader("Districts", anchor=False)
        table(view.district_rows(record), "Facts about the customer's home and branch districts.")
    st.subheader("People", anchor=False)
    table(view.people_rows(record), "The people on this account.")
    st.subheader("All notes", anchor=False)
    notes = text.notes(profile)
    md("\n".join(f"- {line}" for line in notes) if notes else "No notes for this customer.")

with money_tab:
    st.subheader("Typical months against what happened", anchor=False)
    table(view.flow_rows(profile, flows), "Money in, money out and the difference for a typical month, an average month and in total.")
    if float(history.money_in.sum()) + float(history.money_out.sum()) > 0:
        st.altair_chart(charts.payee_pie(history), alt="Pie chart of where this customer's money in went, by payee type, with any amount left in the account.")
        caption("Payees are grouped by type, because the data doesn't name who received the money.")
    st.altair_chart(charts.monthly_in_out(history), alt="Bar chart with two columns for each month. Money in is split by type. Money out is split by payee type, with loan payments at the bottom.")
    loan_note = ", with loan payments at the bottom" if history.loan_payments.sum() > 0 else ""
    caption(f"In each month, the left column is money in and the right column is money out{loan_note}. Every figure is in the Month by month tab.")
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Actual changes", anchor=False)
        table(view.flow_detail_rows(flows), "Actual changes in the balance and the range of money in.")
    with right:
        st.subheader("Last 6 months against all months", anchor=False)
        table(view.recent_rows(profile), "Typical figures for the last 6 months and for all months.")
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Where money comes from", anchor=False)
        if profile.income_sources:
            table(view.line_item_rows(profile.income_sources), "Sources of money in.")
        else:
            st.markdown("No money in is recorded.")
    with right:
        st.subheader("Where money goes", anchor=False)
        if profile.spending_items:
            table(view.line_item_rows(profile.spending_items), "Items of money out.")
        else:
            st.markdown("No money out is recorded.")

with balance_tab:
    table(view.balance_rows(profile), "Balance measures for this customer.")
    st.altair_chart(charts.balance(history), alt="Line chart of the balance at the end of each month.")

with debts:
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Costs", anchor=False)
        table(view.cost_rows(profile), "Fixed costs for this customer.")
    with right:
        st.subheader("Loan", anchor=False)
        if profile.loan is not None:
            table(view.loan_rows(profile), "Loan details.")
        else:
            st.markdown("No loan on this account.")
    st.subheader("Standing orders", anchor=False)
    if record.orders:
        table(view.order_rows(record), "Standing orders on this account.")
    else:
        st.markdown("No standing orders on this account.")

with months:
    st.altair_chart(charts.money_in_out(history), alt="Line chart of money in and money out each month.")
    money_columns = ["money_in", "money_out", "month_end_balance", "min_balance", "avg_daily_balance", "cash_deposits", "transfers_in", "pension_in", "interest_in",
                     "household_bills", "insurance", "loan_payments", "bank_fees", "cash_withdrawals_genuine", "card_withdrawals", "transfers_out_other"]
    config = {c: st.column_config.NumberColumn(c.replace("_", " ").capitalize(), format="dollar") for c in money_columns}
    config["month"] = st.column_config.TextColumn("Month")
    config["days_below_zero"] = st.column_config.NumberColumn("Days below zero")
    st.dataframe(history.drop(columns="account_id").iloc[::-1], hide_index=True, column_config=config, alt="Every monthly figure on file for this customer, newest first.")

with questions_tab:
    specific, general = questionnaire.build_questions(profile, flows, record)
    answers = {q.id: ss.get(f"answer_{account}_{q.id}") or "" for q in specific + general}
    answered = sum(1 for value in answers.values() if value.strip())
    head, download = st.columns([3, 1], vertical_alignment="bottom")
    head.markdown(f"**{answered} of {len(specific) + len(general)} answered.** Type answers as you go, then download them.")
    download.download_button("Download questions", questionnaire.to_markdown(profile, specific, general, answers), file_name=f"stakeholder_questions_{account}.md",
                             mime="text/markdown", icon=":material/download:", on_click="ignore", width="stretch")
    caption("Answers last until the page is closed, so download them to keep them.")
    st.subheader("About this customer", anchor=False)
    caption("These come from this customer's own numbers.")
    show_questions(specific)
    st.subheader("About every customer", anchor=False)
    show_questions(general)
