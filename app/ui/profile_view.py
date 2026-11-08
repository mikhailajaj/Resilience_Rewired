"""The rows on the Customer profiling page. No Streamlit here, so every account can be tested."""
from .text import money, number, signed_money


def _or_na(value, fmt="{:,.2f}"):
    return "n/a" if value is None else fmt.format(value)


def account_rows(p, record):
    return [("Account ID", str(p.account_id)), ("Opened", p.opened), ("Statements", record.statement_frequency),
            ("Data range", f"{p.first_month} to {p.last_month} ({p.n_months} months)"), ("Income type (our label)", p.income_type),
            ("People on the account", str(len(record.people))), ("Cards", ", ".join(p.cards) or "None")]


def people_rows(record):
    return [{"Role": c.role.title(), "Client ID": str(c.client_id), "Gender": c.gender, "Born": c.birth_date, "Age": f"{c.age:.0f}",
             "Home district": c.home_district, "Card": c.card_type or "None", "Card issued": c.card_issued or "n/a"} for c in record.people]


def district_rows(record):
    home, branch = record.home_district, record.branch_district
    fields = [("District", lambda d: d.name), ("Region", lambda d: d.region), ("Inhabitants", lambda d: f"{d.inhabitants:,}"),
              ("Urban share", lambda d: f"{d.urban_ratio_pct:g}%"), ("Average salary", lambda d: money(d.average_salary)),
              ("Unemployment, 2022", lambda d: _or_na(d.unemployment_rate_2022, "{:g}%")), ("Unemployment, 2023", lambda d: _or_na(d.unemployment_rate_2023, "{:g}%")),
              ("Entrepreneurs per 1,000", lambda d: f"{d.entrepreneurs_per_1000:g}"), ("Crimes, 2022", lambda d: _or_na(d.crimes_2022, "{:,.0f}")),
              ("Crimes, 2023", lambda d: _or_na(d.crimes_2023, "{:,.0f}"))]
    return [{"Measure": label, "Home district": get(home), "Branch district": get(branch)} for label, get in fields]


def judges_rows(p):
    return [("Typical money in (I)", money(p.I)), ("Typical spending (S)", money(p.S)), ("Household bills (H)", money(p.H)),
            ("Fixed costs (F)", money(p.F)), ("Loan payment (P)", money(p.P)), ("Buffer (B)", money(p.B)), ("Runway, no shock", p.runway.label)]


def flow_rows(p, flows):
    """Typical months against what actually happened."""
    return [
        {"Measure": "Typical month (standard (judges') I and S)", "Money in": money(p.I), "Money out": money(p.S), "Difference": signed_money(p.I - p.S)},
        {"Measure": "Average month", "Money in": money(flows.average_in), "Money out": money(flows.average_out), "Difference": signed_money(flows.average_change)},
        {"Measure": f"Total, {flows.n_months} months", "Money in": money(flows.total_in), "Money out": money(flows.total_out), "Difference": signed_money(flows.total_change)},
    ]


def flow_detail_rows(flows):
    share = flows.top_5_months_share_of_in
    return [("Actual change, last 12 months", f"{signed_money(flows.change_last_12)} a month"), ("Actual change, last 6 months", f"{signed_money(flows.change_last_6)} a month"),
            ("Middle month's change", signed_money(flows.median_change)), ("Months money in beat money out", f"{flows.months_in_above_out} of {flows.n_months}"),
            ("Months money out beat money in", f"{flows.months_out_above_in} of {flows.n_months}"),
            ("Highest money in", f"{money(flows.highest_in)} in {flows.highest_in_month}"), ("Lowest money in", f"{money(flows.lowest_in)} in {flows.lowest_in_month}"),
            ("Share of money in from the 5 largest months", "n/a" if share is None else f"{share:.0%}")]


def line_item_rows(items):
    return [{"Item": i.label, "Typical month": money(i.typical), "Share of total": f"{i.share:.0%}"} for i in items]


def recent_rows(p):
    last, rows = p.last_6, [("Typical money in", "I", "I"), ("Typical spending", "S", "S"), ("Household bills", "H", "H"), ("Fixed costs", "F", "F")]
    return [{"Measure": label, "Last 6 months": money(getattr(last, a)), "All months": money(getattr(p, b))} for label, a, b in rows]


def balance_rows(p):
    return [("Buffer, average of the last 6 months", money(p.B)), ("Latest balance", f"{money(p.latest_balance)} at the end of {p.last_month}"),
            ("Lowest balance, last 6 months", money(p.lowest_balance)), ("Buffer in months of spending", "n/a" if p.buffer_months is None else f"{p.buffer_months:.1f} months"),
            ("Months below zero, last 6", str(p.months_below_zero_last_6)), ("Months below zero, last 12", str(p.months_below_zero_last_12)),
            ("Months below zero, all", f"{p.months_below_zero_all} of {p.n_months}")]


def cost_rows(p):
    return [("Current fixed costs (our figure)", money(p.current_fixed_costs)), ("Insurance, typical month", money(p.insurance)),
            ("Bills on standing orders", money(p.bills_on_standing_orders)), ("Leasing on standing orders", money(p.leasing)),
            ("Loan payments, typical month", money(p.loan_median))]


def loan_rows(p):
    if p.loan is None:
        return []
    loan = p.loan
    return [("Started", loan.start), ("Amount", money(loan.amount)), ("Length", f"{number(loan.duration_months)} months"), ("Payment", f"{money(loan.monthly_payment)} a month"),
            ("Status", f"{loan.status}: {loan.status_meaning}"), ("Still running", "Yes" if p.running_loan else "No")]


def order_rows(record):
    return [{"Purpose": o.purpose.title(), "Amount a month": money(o.amount), "To bank": o.to_bank, "To account": o.to_account} for o in record.orders]
