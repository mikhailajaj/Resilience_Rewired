"""Questions to ask the stakeholder about one customer. No Streamlit here, so every account can be tested.

Each customer question fires only when that account's numbers raise it, and quotes those numbers. General questions apply to every customer.
"""
from dataclasses import dataclass

from .text import money, signed_money

TOPICS = ("Income", "Spending and bills", "Balance and buffer", "Loan", "The account", "Rules for the plan", "The data")


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    question: str
    why: str
    changes: str


def _share(profile, key):
    for item in profile.income_sources:
        if item.key == key:
            return item.share
    return 0.0


def customer_questions(p, flows, record):
    """The questions this account's numbers raise, in topic order."""
    warning = {w.code for w in p.warnings}
    actual, gap = flows.change_last_12, p.gap
    q = []

    def add(id, topic, question, why, changes):
        q.append(Question(id, topic, question, why, changes))

    # Income
    if flows.lumpy_income:
        add("lumpy_income", "Income", "What are this customer's largest deposits: pay, business income, loan money, or money moved from their own accounts?",
            f"The 5 largest months hold {flows.top_5_months_share_of_in:.0%} of all money in. Monthly money in ranges from {money(flows.lowest_in)} to {money(flows.highest_in)}.",
            "Whether typical money in is a fair stand-in for income, and how much a layoff would really remove.")
    if "cash_income" in warning:
        add("cash_income", "Income", "Can the bank tell which cash deposits are pay?",
            f"Cash makes up {_share(p, 'cash_deposits'):.0%} of money in, and nothing in the data labels a deposit as pay.",
            "Whether a job-loss twist applies to all of this income or only part of it.")
    if p.income_type == "Transfers":
        add("transfer_income", "Income", "Are this customer's incoming transfers pay from an employer, or something else?",
            f"Transfers make up {_share(p, 'transfers_in'):.0%} of money in, and the data doesn't name the sender.",
            "Whether a job loss is the right shock for this customer.")
    if "pension_income" in warning:
        add("pension_income", "Income", "A layoff wouldn't stop a pension. Which shock is realistic for this customer instead?",
            f"Typical money in is {money(p.I)}, and pension income is on the account. The customer is {p.age:.0f}.",
            "Which twist we lead with for pension customers.")
    if "high_flow" in warning:
        add("high_flow", "Income", "Does this much money passing through mean two earners, a business, or something else?",
            f"Typical money in is {money(p.I)}, over twice the {money(p.home_district.average_salary)} average salary in {p.home_district.name}.",
            "Whether to treat this flow as household income, and how much the EI maximum matters here.")
    if "irregular_income" in warning:
        add("irregular_income", "Income", "This customer has no money in during a typical month. How do they receive income?",
            f"Typical money in is $0, but {money(flows.total_in)} came in over {flows.n_months} months.",
            "Whether a lower-income shock means anything for this account.")

    # Spending and bills
    if gap > 0 and actual > -0.5 * gap:
        add("gap_vs_actual", "Spending and bills", "Typical months and actual balance changes disagree for this customer. Which should a real plan be based on?",
            f"Typical spending is {money(gap)} above typical money in, but the balance actually changed by {signed_money(actual)} a month over the last 12 months.",
            "The size of the cut the plan asks for. The judges' formula stays as defined either way.")
    if p.gap < 0 and actual <= 0:
        add("surplus_not_kept", "Spending and bills", "Where does this customer's apparent surplus go?",
            f"Typical money in is {money(-gap)} above typical spending, but the balance changed by {signed_money(actual)} a month over the last 12 months.",
            "Whether the savings figure in the goal plan can be reached.")
    if "bills_missing_from_h" in warning:
        add("bills_missing", "Spending and bills", "Should bills on standing orders count as household bills, even when their transfers carry no bills label?",
            f"Standing orders show {money(p.bills_on_standing_orders)} a month in bills, against typical household bills of {money(p.H)}.",
            "How much a rent or bills shock adds for this customer.")
    if "no_regular_bills" in warning:
        add("no_bills", "Spending and bills", "Where does this customer pay rent and bills: in cash, from another bank, or not at all?",
            "No regular bills show in the transactions or the standing orders.",
            "Whether a bills shock can be shown for this customer, and how much spending can really be cut.")
    if "leasing_not_counted" in warning:
        add("leasing", "Spending and bills", "Is this customer's leasing payment paid from this account?",
            f"A {money(p.leasing)} a month leasing order is on record, but no matching transfer appears.",
            "Whether fixed costs and spending are understated.")
    if "irregular_spending" in warning:
        add("irregular_spending", "Spending and bills", "This customer has no spending in a typical month. Is this account used for day-to-day money?",
            f"Typical spending is $0, but {money(flows.total_out)} went out over {flows.n_months} months.",
            "Whether a target in months of spending means anything here.")

    # Balance and buffer
    if p.B > 1.25 * max(p.latest_balance, 1):
        add("buffer_vs_latest", "Balance and buffer", "Which balance should a real plan start from: the 6-month average or the latest balance?",
            f"The buffer is {money(p.B)}, but the balance ended {p.last_month} at {money(p.latest_balance)}.",
            "How long the money really lasts. The judges' runway keeps using the average.")
    if "no_buffer" in warning:
        add("no_buffer", "Balance and buffer", "What can the bank offer a customer who starts with no buffer?",
            f"The buffer is {money(p.B)}, so runway is 0 months whatever the shock.",
            "What the backup plan says first for this customer.")
    if "went_negative" in warning:
        add("overdraft", "Balance and buffer", "Does this customer have an overdraft limit, and what does going below zero cost?",
            f"The balance went below zero in {p.months_below_zero_last_6} of the last 6 months and {p.months_below_zero_all} of {p.n_months} overall.",
            "Whether a $0 balance is really where the money runs out.")

    # Loan
    if p.loan is not None and "loan_in_trouble" in warning:
        add("loan_status", "Loan", "What does this loan's status mean in practice: how far behind is the customer, and what happens next?",
            f"Status {p.loan.status}: {p.loan.status_meaning}. The payment is {money(p.loan.monthly_payment)} a month.",
            "Whether the plan should deal with the loan first, before any saving.")
    if p.running_loan:
        add("lender_pause", "Loan", "Can the bank really pause or reduce this customer's loan payment during a shock?",
            f"The payment is {money(p.P)} a month, and the backup plan can name asking the lender as a last step.",
            "Whether that step stays in the plan, and how it's worded.")
    if "recent_loan_missed" in warning:
        add("recent_loan", "Loan", "Should fixed costs use the current loan payment instead of the historical figure?",
            f"The {money(p.P)} a month payment isn't in typical fixed costs of {money(p.F)}, because the loan is recent.",
            "How much of this customer's spending counts as fixed.")
    if "finished_loan_counted" in warning:
        add("finished_loan", "Loan", "Should a finished loan drop out of this customer's fixed costs?",
            f"Typical fixed costs of {money(p.F)} still include a loan payment of {money(p.loan_median)}.",
            "How much of this customer's spending counts as fixed.")
    if "missed_payment" in warning:
        add("missed_payment", "Loan", "Is the missing loan payment last month a real missed payment, or a timing or data issue?",
            f"No loan payment appears in {p.last_month}, and the loan is still running.",
            "Whether to treat this customer as already in trouble.")
    if "thin_low_point" in warning:
        add("thin_low_point", "Loan", "Is one loan payment the right safety line for this customer?",
            f"The lowest balance in the last 6 months was {money(p.lowest_balance)}, under one payment of {money(p.P)}.",
            "Whether the plan keeps that line as a goal. It was chosen on the same data it was tested on.")

    # The account
    if "out_of_date" in warning:
        add("out_of_date", "The account", "Why does this account's data stop early: is it closed, moved or just quiet?",
            f"The last month of data is {p.last_month}.",
            "Whether a plan for this customer makes sense at all.")
    if "little_activity" in warning:
        add("little_activity", "The account", "Is this the customer's main account, or one they rarely use?",
            f"Typical money in and spending are both $0, over {flows.n_months} months.",
            "Whether to show a plan or say there's too little to go on.")
    if len(record.people) > 1:
        add("second_person", "The account", "Does the second person on this account earn income, and would a layoff affect one income or both?",
            f"{len(record.people)} people are on this account.",
            "How much income a single job loss removes.")
    if p.age >= 60 and p.income_type != "Pension":
        add("near_retirement", "The account", "Should a plan treat this customer as close to retirement?",
            f"The customer is {p.age:.0f} with no pension income on this account yet.",
            "Whether a layoff or retirement is the shock to plan for, and how long a fund should last.")
    return q


def general_questions():
    """Questions that apply to every customer."""
    return [
        Question("other_accounts", "Rules for the plan", "Can we assume this account is all of a customer's money?",
                 "Customers may hold savings or earn income elsewhere, and the data only shows this bank.",
                 "How far to trust runway and how we word it."),
        Question("fund_target", "Rules for the plan", "What emergency fund target does the bank recommend: 3 months of spending, 6, or something else?",
                 "The plan defaults to 3 months, and any value can be typed.",
                 "The default target and how many customers already meet it."),
        Question("after_ei", "Rules for the plan", "When EI ends, should a plan assume no income or a return to work?",
                 "The plan assumes $0 after the lower income ends, because a benefit ending doesn't mean a new job has started.",
                 "Whether long shocks show the money running out."),
        Question("ei_eligibility", "Rules for the plan", "Can we treat typical money in as insurable earnings, and every customer as eligible for EI?",
                 "The data shows no insurable hours or tax. Much of the flow may not be pay.",
                 "How much EI a customer really receives, and how far to rely on the weekly maximum figure."),
        Question("advice_limits", "Rules for the plan", "May a plan name specific cuts, such as cancelling a standing order, or would that count as advice?",
                 "The backup plan lists steps in order, using the customer's own numbers.",
                 "How the steps are worded, and whether they can be shown to customers."),
        Question("traits", "The data", "May age and gender appear in a customer view, and must they stay out of any recommendation?",
                 "Both are on file. This page shows them, but no plan or runway uses gender, and age only prompts a question.",
                 "What this page may show."),
        Question("income_drops", "The data", "What do falls in deposits mean in real life: job losses, a business slowing down, or money moving elsewhere?",
                 "Real drops show spending falling too, but nothing confirms they were job losses.",
                 "How much weight the \"if you adjust\" runway can carry."),
        Question("december", "The data", "Why is December 2025 spending so low across accounts?",
                 "December is in the 6 months behind the buffer, so it affects every customer's starting point.",
                 "Whether the buffer needs a note about the last month."),
    ]


def build_questions(p, flows, record):
    """Customer questions first, grouped by topic, then the general ones."""
    order = {topic: i for i, topic in enumerate(TOPICS)}
    return sorted(customer_questions(p, flows, record), key=lambda q: order[q.topic]), general_questions()


def to_markdown(p, specific, general, answers):
    """The questionnaire as a Markdown file, with any answers typed so far."""
    lines = [f"# Stakeholder questions: customer {p.account_id}", "",
             f"Data from {p.first_month} to {p.last_month}. Income type: {p.income_type}.", ""]

    def section(title, questions):
        if not questions:
            return
        lines.extend([f"## {title}", ""])
        for number, q in enumerate(questions, 1):
            lines.extend([f"### {number}. {q.question}", "", f"- **Topic:** {q.topic}", f"- **Why we ask:** {q.why}",
                          f"- **What the answer changes:** {q.changes}", f"- **Answer:** {answers.get(q.id, '').strip() or '(not answered)'}", ""])

    section("About this customer", specific)
    section("About every customer", general)
    return "\n".join(lines)
