"""Know the customer: build_profile and flags, moved from know_the_customer.ipynb with the same logic."""
import re
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from .data import END_OF_DATA, LAST_DATA_MONTH, get_dataset
from .errors import InvalidAccountIdError
from .formulas import Runway, money, runway_from

INCOME_LABELS = {"cash_deposits": "Cash deposits", "transfers_in": "Transfers in", "pension_in": "Pension", "interest_in": "Interest"}
SPEND_LABELS = {"cash_withdrawals_genuine": "Cash withdrawals", "household_bills": "Household bills", "insurance": "Insurance",
                "loan_payments": "Loan payments", "transfers_out_other": "Other transfers out",
                "card_withdrawals": "Card withdrawals", "bank_fees": "Bank fees"}


@dataclass(frozen=True)
class NoteDefinition:
    code: str
    title: str
    condition: str
    copy_key: str | None


@dataclass(frozen=True)
class AccountWarning:
    code: str
    title: str
    message: str
    condition: str
    copy_key: str | None


@dataclass(frozen=True)
class LineItem:
    key: str
    label: str
    typical: float
    share: float


@dataclass(frozen=True)
class LoanInfo:
    start: str
    amount: float
    duration_months: int
    monthly_payment: float
    status: str
    status_meaning: str


@dataclass(frozen=True)
class OrderInfo:
    purpose: str
    amount: float


@dataclass(frozen=True)
class DistrictInfo:
    name: str
    average_salary: float


@dataclass(frozen=True)
class LastSix:
    I: float
    S: float
    H: float
    F: float


@dataclass(frozen=True)
class CustomerProfile:
    account_id: int
    I: float
    S: float
    H: float
    F: float
    P: float
    B: float
    gap: float
    runway: Runway
    bills_on_standing_orders: float
    current_fixed_costs: float
    buffer_months: float | None
    lowest_balance: float
    last_6: LastSix
    income_type: str
    months_below_zero_last_6: int
    months_below_zero_last_12: int
    months_below_zero_all: int
    first_month: str
    last_month: str
    n_months: int
    opened: str
    insurance: float
    loan_median: float
    bills_hidden: bool
    leasing: float
    latest_balance: float
    income_low: float
    income_high: float
    income_sources: tuple
    spending_items: tuple
    running_loan: bool
    loan: LoanInfo | None
    standing_orders: tuple
    age: float
    home_district: DistrictInfo
    branch_district: DistrictInfo
    n_authorized: int
    cards: tuple
    warnings: tuple


@dataclass(frozen=True)
class AccountFlows:
    """What actually moved through the account, as opposed to the standard (judges') typical (median) months."""
    n_months: int
    total_in: float
    total_out: float
    total_change: float
    average_in: float
    average_out: float
    average_change: float
    median_change: float
    change_last_12: float
    change_last_6: float
    months_in_above_out: int
    months_out_above_in: int
    highest_in: float
    highest_in_month: str
    lowest_in: float
    lowest_in_month: str
    top_5_months_share_of_in: float | None      # None if the account has no money in
    lumpy_income: bool                          # The top 5 months hold at least twice their even share of money in


@dataclass(frozen=True)
class DistrictDetail:
    name: str
    region: str
    inhabitants: int
    urban_ratio_pct: float
    average_salary: float
    unemployment_rate_2022: float | None
    unemployment_rate_2023: float | None
    entrepreneurs_per_1000: float
    crimes_2022: float | None
    crimes_2023: float | None


@dataclass(frozen=True)
class PersonDetail:
    client_id: int
    role: str
    gender: str
    birth_date: str
    age: float
    home_district: str
    card_type: str | None
    card_issued: str | None


@dataclass(frozen=True)
class OrderDetail:
    purpose: str
    amount: float
    to_bank: str
    to_account: str


@dataclass(frozen=True)
class CustomerRecord:
    """Everything on file for an account beyond the numbers in CustomerProfile."""
    statement_frequency: str
    people: tuple
    home_district: DistrictDetail
    branch_district: DistrictDetail
    orders: tuple


@dataclass(frozen=True)
class AccountIdRange:
    min: int
    max: int
    count: int


@dataclass(frozen=True)
class AccountOverview:
    account_id: int
    income_type: str
    first_month: str
    last_month: str
    n_months: int
    notes: tuple


NOTES = (
    NoteDefinition("little_activity", "Little activity", "I and S are both 0", "N.zero"),
    NoteDefinition("irregular_income", "Irregular income", "I is 0 and S isn't", "N.no_income"),
    NoteDefinition("irregular_spending", "Irregular spending", "S is 0 and I isn't", "N.no_spend"),
    NoteDefinition("out_of_date", "Out of date", "The last row is before 2025-12", "N.stale"),
    NoteDefinition("no_buffer", "No buffer", "B is 0 or less", "N.neg_buf"),
    NoteDefinition("pension_income", "Pension income", "Income type is Pension", "N.pension"),
    NoteDefinition("cash_income", "Cash income", "Income type is Cash only", "N.cash"),
    NoteDefinition("high_flow", "High flow", "I is over 2x the average salary in the owner's home district", None),
    NoteDefinition("bills_missing_from_h", "Bills missing from H", "Bills on standing orders are over H x 1.1 + $1", "N.bills_gap"),
    NoteDefinition("no_regular_bills", "No regular bills visible", "H is 0 and bills aren't missing from H", "N.no_bills"),
    NoteDefinition("recent_loan_missed", "Recent loan missed by F", "The loan is running and median loan_payments is 0", "N.loan_recent"),
    NoteDefinition("finished_loan_counted", "Finished loan still counted", "The loan has finished and median loan_payments is above 0", "N.loan_done"),
    NoteDefinition("loan_in_trouble", "Loan in trouble", "Loan status is B or D", "N.loan_trouble"),
    NoteDefinition("missed_payment", "Missed payment", "The loan is running and the last row's loan_payments is 0", "N.missed"),
    NoteDefinition("went_negative", "Went negative", "Lowest balance is below 0", "N.low"),
    NoteDefinition("thin_low_point", "Thin low point", "The loan is running and the lowest balance is from $0 up to one payment", "N.thin"),
    NoteDefinition("leasing_not_counted", "Leasing not counted", "The account has a leasing standing order", "N.leasing"),
)
_NOTE_BY_CODE = {n.code: n for n in NOTES}


def note_catalogue():
    return NOTES


def account_id_range():
    ids = get_dataset().rows_by_account
    return AccountIdRange(min(ids), max(ids), len(ids))


_COMMA_GROUPED = re.compile(r"[0-9]{1,3}(,[0-9]{3})+")
_WHOLE_FLOAT = re.compile(r"[0-9]+\.0+")


def parse_account_id(value):
    text = str(value).strip()
    if isinstance(value, bool):
        digits = None
    elif _COMMA_GROUPED.fullmatch(text):
        digits = text.replace(",", "")
    elif _WHOLE_FLOAT.fullmatch(text):
        digits = text.split(".")[0]
    elif re.fullmatch(r"[0-9]+", text):
        digits = text
    else:
        digits = None
    if digits is None:
        raise InvalidAccountIdError(value, "not_digits", f"'{text[:20]}' isn't an account ID. IDs are whole numbers, like 20111.")
    # The length check keeps int() safe on absurdly long input.
    if len(digits) > 18 or int(digits) not in get_dataset().rows_by_account:
        raise InvalidAccountIdError(value, "not_found", f"Account {text[:20]} isn't in the data. IDs are whole numbers, like 20111.")
    return int(digits)


def get_profile(account_id):
    """One account's numbers. Cached, so repeat lookups return the same object."""
    return _build_profile(parse_account_id(account_id))


def flags(profile):
    """The warnings, as structured data."""
    return profile.warnings


def account_overview(account_id):
    p = get_profile(account_id)
    return AccountOverview(p.account_id, p.income_type, p.first_month, p.last_month, p.n_months, p.warnings)


def monthly_history(account_id):
    return get_dataset().rows_by_account[parse_account_id(account_id)].copy()


@lru_cache(maxsize=None)
def _build_flows(account_id):
    x = get_dataset().rows_by_account[account_id]
    change = x.money_in - x.money_out
    total_in = float(x.money_in.sum())
    share = float(x.money_in.nlargest(5).sum()) / total_in if total_in > 0 else None
    n = len(x)
    high, low = x.money_in.idxmax(), x.money_in.idxmin()
    return AccountFlows(
        n_months=n, total_in=total_in, total_out=float(x.money_out.sum()), total_change=float(change.sum()),
        average_in=float(x.money_in.mean()), average_out=float(x.money_out.mean()), average_change=float(change.mean()),
        median_change=float(change.median()), change_last_12=float(change.tail(12).mean()), change_last_6=float(change.tail(6).mean()),
        months_in_above_out=int((change > 0).sum()), months_out_above_in=int((change < 0).sum()),
        highest_in=float(x.money_in[high]), highest_in_month=str(x.month[high]),
        lowest_in=float(x.money_in[low]), lowest_in_month=str(x.month[low]),
        top_5_months_share_of_in=share, lumpy_income=share is not None and share >= min(2 * 5 / n, 1.0) and n > 5)


def account_flows(account_id):
    """Actual totals and changes. Money in minus money out equals the balance change on every row."""
    return _build_flows(parse_account_id(account_id))


def _number_or_none(value):
    return None if pd.isna(value) else float(value)


def _district_detail(row):
    return DistrictDetail(str(row["district_name"]), str(row["region"]), int(row["inhabitants"]), float(row["urban_ratio_pct"]),
                          float(row["average_salary"]), _number_or_none(row["unemployment_rate_2022"]), _number_or_none(row["unemployment_rate_2023"]),
                          float(row["entrepreneurs_per_1000"]), _number_or_none(row["crimes_2022"]), _number_or_none(row["crimes_2023"]))


def _text(value):
    return None if pd.isna(value) else str(value)


def customer_record(account_id):
    """The people, districts and orders on file for an account."""
    account_id = parse_account_id(account_id)
    d = get_dataset()
    people = []
    rows = d.people_by_account[account_id].sort_values("type", key=lambda s: s != "owner")
    for row in rows.itertuples():
        client = d.clients[row.client_id]
        people.append(PersonDetail(
            int(row.client_id), str(row.type), str(client["gender"]), f"{client['birth_date']:%Y-%m-%d}", (END_OF_DATA - client["birth_date"]).days / 365.25,
            str(d.districts[client["district_id"]]["district_name"]), d.card_by_disposition.get(row.disposition_id), d.card_issued.get(row.disposition_id)))
    owner = d.clients[rows.iloc[0].client_id]
    branch = d.branch[account_id]
    orders = d.orders_by_account.get(account_id)
    order_rows = () if orders is None else tuple(
        OrderDetail(_purpose(o.purpose), float(o.amount), _text(o.to_bank) or "n/a", _text(o.to_account) or "n/a") for o in orders.sort_values("amount", ascending=False).itertuples())
    return CustomerRecord(str(branch["frequency"]), tuple(people), _district_detail(d.districts[owner["district_id"]]),
                          _district_detail(d.districts[branch["district_id"]]), order_rows)


def _income_type(x):
    if x.pension_in.sum() > 0:
        return "Pension"
    if x.transfers_in.sum() > 0:
        return "Transfers"
    return "Cash only"


def _line_items(x, labels):
    totals = x[list(labels)].sum()
    total = float(totals.sum())
    return tuple(LineItem(c, labels[c], float(x[c].median()), float(totals[c]) / total)
                 for c in totals.sort_values(ascending=False).index if totals[c] > 0)


def _district(row):
    return DistrictInfo(str(row["district_name"]), float(row["average_salary"]))


def _purpose(value):
    return value if isinstance(value, str) else "other"


@lru_cache(maxsize=None)
def _build_profile(account_id):
    d = get_dataset()
    x = d.rows_by_account[account_id]
    last6 = x.tail(6)
    fixed = x.household_bills + x.insurance + x.loan_payments
    bills_ins = x.household_bills + x.insurance
    loan = d.loans.get(account_id)

    I, S, H = float(x.money_in.median()), float(x.money_out.median()), float(x.household_bills.median())
    F, B = float(fixed.median()), float(last6.avg_daily_balance.mean())
    running = loan is not None and loan["status"] in ("C", "D")
    P = float(loan["monthly_payment"]) if running else 0.0

    people = d.people_by_account[account_id]
    owner = people[people.type == "owner"].iloc[0]
    client = d.clients[owner.client_id]
    orders = d.orders_by_account.get(account_id)
    bill_orders = 0.0 if orders is None else float(orders.loc[orders.purpose == "household bills", "amount"].sum())
    leasing = 0.0 if orders is None else float(orders.loc[orders.purpose == "leasing", "amount"].sum())
    home = _district(d.districts[client["district_id"]])
    last_month = str(x.month.iloc[-1])
    lowest = float(last6.min_balance.min())
    income_type = _income_type(x)
    loan_median = float(x.loan_payments.median())
    bills_hidden = bill_orders > H * 1.1 + 1

    warnings = _warnings(
        I=I, S=S, H=H, B=B, P=P, last_month=last_month, income_type=income_type, salary=home.average_salary,
        bills_hidden=bills_hidden, bill_orders=bill_orders, running=running, loan=loan, loan_median=loan_median,
        last_payment=float(x.loan_payments.iloc[-1]), lowest=lowest, leasing=leasing)

    return CustomerProfile(
        account_id=account_id, I=I, S=S, H=H, F=F, P=P, B=B, gap=S - I, runway=runway_from(B, S - I),
        bills_on_standing_orders=bill_orders,
        current_fixed_costs=float(bills_ins.median()) + max(bill_orders - H, 0.0) + P,
        buffer_months=B / S if S > 0 and B > 0 else None,
        lowest_balance=lowest,
        last_6=LastSix(float(last6.money_in.median()), float(last6.money_out.median()), float(last6.household_bills.median()),
                       float((last6.household_bills + last6.insurance + last6.loan_payments).median())),
        income_type=income_type,
        months_below_zero_last_6=int((last6.days_below_zero > 0).sum()),
        months_below_zero_last_12=int((x.tail(12).days_below_zero > 0).sum()),
        months_below_zero_all=int((x.days_below_zero > 0).sum()),
        first_month=str(x.month.iloc[0]), last_month=last_month, n_months=len(x),
        opened=str(d.branch[account_id]["account_opened"]),
        insurance=float(x.insurance.median()), loan_median=loan_median, bills_hidden=bool(bills_hidden), leasing=leasing,
        latest_balance=float(x.month_end_balance.iloc[-1]),
        income_low=float(x.money_in.quantile(.1)), income_high=float(x.money_in.quantile(.9)),
        income_sources=_line_items(x, INCOME_LABELS), spending_items=_line_items(x, SPEND_LABELS),
        running_loan=running,
        loan=None if loan is None else LoanInfo(str(loan["loan_start"]), float(loan["amount"]), int(loan["duration_months"]),
                                                float(loan["monthly_payment"]), str(loan["status"]), str(loan["status_meaning"])),
        standing_orders=() if orders is None else tuple(
            OrderInfo(_purpose(o.purpose), float(o.amount)) for o in orders.sort_values("amount", ascending=False).itertuples()),
        age=(END_OF_DATA - client["birth_date"]).days / 365.25,
        home_district=home, branch_district=_district(d.districts[d.branch[account_id]["district_id"]]),
        n_authorized=int((people.type != "owner").sum()),
        cards=tuple(str(d.card_by_disposition[i]) for i in people.disposition_id if i in d.card_by_disposition),
        warnings=warnings,
    )


def _warnings(*, I, S, H, B, P, last_month, income_type, salary, bills_hidden, bill_orders, running, loan, loan_median,
              last_payment, lowest, leasing):
    out = []

    def add(code, message):
        n = _NOTE_BY_CODE[code]
        out.append(AccountWarning(n.code, n.title, message, n.condition, n.copy_key))

    if I == 0 and S == 0:
        add("little_activity", "Typical money in and spending are both $0, so most months have no movement and these numbers say little about this account.")
    elif I == 0:
        add("irregular_income", "Typical money in is $0, so most months have no income.")
    elif S == 0:
        add("irregular_spending", "Typical spending is $0, so most months have no spending. Runway will look safer than it may be.")
    if last_month != LAST_DATA_MONTH:
        add("out_of_date", f"This account's data stops at {last_month}, so every number is as of then.")
    if B <= 0:
        add("no_buffer", "The buffer is zero or negative, so runway is 0.")
    if income_type == "Pension":
        add("pension_income", "A layoff wouldn't stop this income, so a job-loss shock doesn't really fit.")
    elif income_type == "Cash only":
        add("cash_income", "Almost all money in is cash deposits, so the data can't show how much of it is pay.")
    if I > 2 * salary:
        add("high_flow", f"Typical money in is over twice the home district's average salary ({money(salary)}), so some of it may not be pay.")
    if bills_hidden:
        add("bills_missing_from_h", f"Household bills standing orders total {money(bill_orders)}, but H is only {money(H)}. This is usually because the transfers carry no bills label, though they still count in S. A bills shock based on H will be too small.")
    elif H == 0:
        add("no_regular_bills", "Typical household bills are $0, so a bills shock won't change this account's numbers.")
    if running and loan_median == 0:
        add("recent_loan_missed", f"Typical fixed costs show $0 of loan payment, but {money(P)} a month is due. Use current fixed costs.")
    if loan is not None and not running and loan_median > 0:
        add("finished_loan_counted", f"F includes {money(loan_median)} of loan payments that have ended. Use current fixed costs.")
    if loan is not None and loan["status"] in ("B", "D"):
        add("loan_in_trouble", f"Status is \"{loan['status_meaning']}\".")
    if running and last_payment == 0:
        add("missed_payment", "The loan is running, but no payment was made in the last month of data.")
    if lowest < 0:
        add("went_negative", f"The balance fell to {money(lowest)} in the last 6 months.")
    elif running and lowest < P:
        add("thin_low_point", f"The lowest balance in the last 6 months ({money(lowest)}) is under one loan payment. Before a loan, this was a strong warning sign of default.")
    if leasing > 0:
        add("leasing_not_counted", f"There's a {money(leasing)} leasing standing order, but no matching transfers in the data, so it isn't in S or F.")
    return tuple(out)
