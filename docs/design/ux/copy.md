# Copy deck: Resilience Rewired

Rules: short, plain, no jargon. Verbs first on buttons. Amounts as `$1,234`, runway with one decimal, "months" always spelled out. Judges' terms are used exactly: Typical money in, Typical spending, Buffer, Runway. Our additions are always labelled "our" or carry "if you adjust". No banner copy anywhere: every message is plain inline text. `{x}` is filled by the engine. Nothing here is legal or reason-code text, so none needs an approved set.

Wordmark: neutral text "Resilience Rewired". No Tangerine logo or font.

Words to avoid on screen: AUC, median (say "typical"), shortfall (say "gap"), liquidity, stress test, runway without "months" beside it. Never state as fact that customers cut spending when income falls: discovery.md calls that one reading of the data. Say "in some accounts in the data" and "illustration".

Where the engine gives a `message` or `note`, the deck wording below is shown and the engine text is the fallback.

## 1. Page and picker (A)

| Key | Text |
| :-- | :-- |
| K.title | Resilience Rewired |
| K.subtitle | How long can this customer last if money gets tight? |
| K.id_label | Account ID |
| K.id_help | Type the account number, for example 20111. Press Enter. |
| K.id_button | Show customer |
| K.loading | Loading customer {id}... |
| K.empty_page | Enter an account ID to start. You will see their money, a shock you can change, and a plan. |
| K.err_not_digits | "{input}" isn't an account number. Use digits only, for example 20111. (engine reason `not_digits`) |
| K.err_not_found | No account {id} in this data. Try another number. (engine reason `not_found`) |
| K.err_range_hint | Account numbers here run from {min} to {max}. |
| K.no_shock | No shock applied. Pick a twist to see what changes. |

## 2. Know the customer (B)

| Key | Label | Caption |
| :-- | :-- | :-- |
| K.m_in | Typical money in | per month |
| K.m_out | Typical spending | per month |
| K.m_buf | Buffer | average balance, last 6 months |
| K.m_run | Runway, no shock | months the buffer lasts |
| K.m_bills | Household bills | per month, typical |
| K.m_fixed | Fixed costs | bills, insurance, loan, per month |
| K.m_loan | Loan payment | per month, if still running |

Header: `Customer {id}` and `Data from {first} to {last}`. Beside it: `Income type: {Cash only / Transfers / Pension} (our label)`.

Runway values are the engine's `runway.label`: `7.8 months`, `0 months`, `No shortfall (120+)` (gap is zero or less), `120.0 months` (buffer lasts 120 months or more).

K.flow_line, directly under the summary line on both pages: `These are typical months, and medians don't add up. Over the last 12 months the balance {fell or rose} ${x} a month on average, and it ended at ${latest}.` Accounts whose data stops early read `its last 12 months of data`. A change under 50 cents reads `stayed about the same`.

K.summary_line, by case:
- Normal: `Customer {id} brings in about ${I} a month and spends about ${S}. The buffer is ${B}, so it would last {R}.`
- Money in covers spending (`No shortfall`): `Customer {id} brings in about ${I} and spends about ${S}, so money isn't running down. The buffer is ${B}.`
- Capped (`120.0 months`): `Customer {id} spends slightly more than comes in, but the buffer of ${B} lasts 120 months or more.`
- Buffer zero or less: `Customer {id} has no buffer to draw on: the balance is ${B}. Runway is 0 months.`

Customer notes: shown for each `profile.warnings` item, in this priority: N.neg_buf, N.zero, N.no_income, N.no_spend, N.stale, N.pension, N.no_bills, N.bills_gap, N.high_flow, the rest. Max 3 in B, all in Details. Facts, not warnings.

| Key | Engine code | Text |
| :-- | :-- | :-- |
| N.zero | little_activity | Almost no activity on this account. Most numbers are $0. |
| N.no_income | irregular_income | No regular money in. A lower income changes nothing here. |
| N.no_spend | irregular_spending | No regular spending recorded. Buffer in months of spending can't be worked out. |
| N.neg_buf | no_buffer | The balance is at or below zero, so runway is 0 months. |
| N.stale | out_of_date | Data stops in {month}. Figures are as of then. |
| N.pension | pension_income | Pension income: a layoff wouldn't stop this. |
| N.cash | cash_income | Income is cash deposits. The data can't show which are pay. |
| N.high_flow | high_flow | Typical money in is over twice the home district's average salary (${avg}), so some of it may not be pay. |
| N.no_bills | no_regular_bills | No regular bills visible in the transactions. |
| N.bills_gap | bills_missing_from_h | Standing orders show ${x} a month in bills; transactions show ${H}. |
| N.loan_recent | recent_loan_missed | The loan is recent: ${P} a month isn't in typical fixed costs. |
| N.loan_done | finished_loan_counted | A finished loan still counts in typical fixed costs. |
| N.loan_trouble | loan_in_trouble | The loan is behind or unpaid. |
| N.missed | missed_payment | No loan payment last month. |
| N.low | went_negative | The balance went below zero in {n} of the last 6 months. (`months_below_zero_last_6`) |
| N.thin | thin_low_point | The lowest balance was under one loan payment. |
| N.leasing | leasing_not_counted | A leasing payment is on record but isn't counted. |

## 3. Twist (C)

| Key | Text |
| :-- | :-- |
| K.twist_head | Pick a twist |
| K.twist_sub | Or type your own sizes below. |
| K.b_layoff | Laid off, EI 55% |
| K.b_furnace | Furnace dies |
| K.b_mix | Laid off + bills up 15% |
| K.b_bills | Rent or bills up |
| K.b_reset | Reset (no shock) |
| K.b_selected | Selected: {name} |
| K.b_custom | Custom |
| K.s_income | Income kept (%) |
| K.s_income_help | 100 means no change. EI pays 55%. Type any number. |
| K.s_months | Income stays lower for (months) |
| K.s_months_help | How long the lower income lasts. |
| K.s_disabled | Not used while income is unchanged. |
| K.s_cap | Apply the EI weekly maximum |
| K.s_cap_help | Off by default, to match the judges. When on, the extra runway in "Our numbers" caps EI at the weekly maximum. |
| K.s_cap_amt | Weekly maximum ($) |
| K.s_cap_amt_help | $729 a week is the 2026 maximum. Change it if the card says otherwise. |
| K.s_bills | Household bills up (%) |
| K.s_bills_help | Percent on the customer's usual bills. |
| K.s_dollar | Bills or rent up ($ a month) |
| K.s_dollar_help | For a card with a dollar amount, like "rent up $300". |
| K.s_oneoff_m | One-off cost (months of spending) |
| K.s_oneoff_m_help | Paid once, at the start. 1 means one month of typical spending. |
| K.s_oneoff_d | One-off cost ($) |
| K.s_oneoff_d_help | Type the repair cost, for example 5000. Typing here clears the months slider. |
| K.oneoff_total | Total one-off: ${x} |
| K.more | More options |
| K.s_start | Shock starts in |
| K.s_start_help | Optional. Spending is higher in January and June. This never changes the judges' runway. |

Presets: Laid off = income 55, 6 months. Furnace = one-off 1.0 month. Mix = income 55, 6 months, bills 15. Bills = bills 15. Reset = all defaults, EI switch off.

## 4. Before and after (D)

Headings: `Before`, `After`. Rows: `Runway`, `Money in`, `Spending`, `Buffer` (After: `Buffer left`), `Monthly gap`. Delta words: `down {x}`, `up {x}`, `no change`.

K.verdict is chosen by the engine's `verdict_case`. It is never worked out from the rounded runway, and never uses a ceiling on it.

| `verdict_case` | Sentence |
| :-- | :-- |
| no_shock | No shock applied. Pick a twist to see what changes. |
| runway_zero, with `no_buffer_before_shock` | The balance was already ${B} before this, so runway is 0 months whatever the shock. |
| runway_zero, otherwise | The one-off cost of ${x} is bigger than the buffer of ${B}. Nothing is left to live on. |
| no_shortfall | Income still covers spending, so the buffer isn't being used. |
| income_cut_makes_it | With income at {pct}% for {n} months, the money lasts the full {n} months. They make it. |
| income_cut_runs_out | With income at {pct}% for {n} months, the money runs out in month {runs_out_in_month}, about {months_short} months short. |
| income_cut_runs_out, `runs_out_in_month` = 0 | There is no buffer before month 1, so the money is gone before the lower income starts. |
| income_cut_open_ended | With income at {pct}%, the buffer lasts {R}. No length was set, so there is no make-it answer. |
| cost_or_bills_only | After this, the buffer lasts {R}, down from {R0}. |

Second line when a duration exists: `The judges' runway is {R}.` (so the verdict and the runway are never seen as in conflict).

Assumption line (only when `duration.assumption_applied`): `After month {n} we assume no income. A benefit ending doesn't mean a new job has started.` (This replaces "before income recovers", which the engine does not assume.)

Fact lines (K.fact.*), one plain line each, under the verdict:

| Code | Text |
| :-- | :-- |
| layoff_doesnt_fit_pension | Pension income: a layoff wouldn't stop this. The numbers apply the layoff as asked. |
| income_cut_no_income | No regular money in, so a lower income changes nothing here. |
| bills_shock_no_bills | No regular bills visible, so the judges' formula changes nothing for this. |
| bills_shock_too_small | Standing orders show more bills than the judges' figure, so this rise is understated. |
| one_off_zero_spending | No typical spending, so a cost in months of spending is $0. Type dollars instead. |
| no_buffer_before_shock | The balance was already ${B} before this shock. |
| one_off_exceeds_buffer | The one-off cost is bigger than the buffer. |
| data_stops_early | Data stops in {month}. |
| little_activity | Almost no activity, so most numbers are $0. |
| spending_floored_at_zero | Spending can't go below $0, so it stops there. |
| runs_into_january | This runs into January, when spending is usually higher. |

## 5. Our numbers (E)

Heading: `Our numbers, shown beside the judges'`. Under it: `They never replace the judges' figures.`

| Key | Label | Help |
| :-- | :-- | :-- |
| K.e_adjust | Runway, if you adjust | An illustration, not a forecast. In some accounts in the data, spending fell when income fell. This lowers spending that way. The judges' runway keeps spending flat. |
| K.e_cap | Runway with EI weekly maximum | Same shock, with EI capped at the weekly maximum you set. Shown only when the switch is on. |
| K.e_so | Bills on standing orders | Monthly bills set up as standing orders. Some bills don't show in typical bills, so this can be larger. |
| K.e_fixed | Current fixed costs | Bills, insurance and the loan payment if still running. Differs from "Fixed costs" above when a loan is recent or bills are hidden. |
| K.e_months | Buffer in months of spending | Buffer divided by typical spending. Shows savings without how much money passes through. |
| K.e_low | Lowest balance, last 6 months | The lowest the balance got. An average can hide it. |
| K.e_latest | Latest balance | The balance at the end of {month}. The buffer is an average over 6 months, so the two can differ. Suffix: `(judges' buffer: {B})` |
| K.e_actual | Actual change, last 12 months | What the balance really did, on average. Typical money in minus typical spending can differ, because each is a separate median. Suffix: `(typical month: {I - S})` |

Row suffix: `(judges': {value})` where there is a counterpart.

### n/a path for "if you adjust" (engine `applies = False`)

The row reads `n/a` and the reason line below it. Same pattern for the other extra rows.

| Engine `reason` | Line shown |
| :-- | :-- |
| pension_income | n/a. This comes from cash-only accounts, and a pension isn't lost with a layoff. |
| transfers_income | n/a. This comes from cash-only accounts, so it doesn't apply to transfer income. |
| no_income_lost | n/a. No income is lost in this twist. |
| no_typical_spending | n/a. There is no typical spending to adjust. |
| no_bills_shock (bills row) | n/a. No bills rise is set. |
| bills_not_missing (bills row) | n/a. Standing orders match the bills already counted. |
| no value (other rows) | n/a, with the reason in the help |

Sentence to read (K.e_sentence):
- Applies: `Our adjusted runway is {Ra}, against the judges' {R}. It lowers spending as income falls, as some accounts in the data did. It's an illustration.`
- n/a: `Our adjusted runway is n/a here: {reason line}. The judges' {R} stands.`

## 6. Goal plan (F)

| Key | Text |
| :-- | :-- |
| K.f_head | Goal plan: build an emergency fund |
| K.f_cap | Before any shock |
| K.f_target | Emergency fund target (months of spending) |
| K.f_target_help | Default 3. Type any number. |
| K.f_on_track | To have {t} months of spending (${amt}) saved, set aside ${m} a month. That takes {n} months. |
| K.f_far | At ${m} a month this takes {n} months, more than 12. |
| K.f_done | Already there: the buffer covers {n} months. |
| K.f_nosurplus | Money in doesn't cover spending, so saving starts with spending about ${break_even} a month less. About ${reach} a month less would reach the target in 12 months. |
| K.f_cut_fits | That fits within the ${flex} of spending above fixed costs. |
| K.f_cut_over | That is more than the ${flex} of spending above fixed costs. |
| K.f_none | Not enough regular spending to set a target. |
| K.f_negative | First step: get the balance back above $0 (${x}). |
| K.f_low | Keep the lowest balance above one loan payment (${P}). It is now ${low}. |
| K.f_table | Savings path |

Fact `surplus_not_seen_in_balance` (shown under the plan sentence): `Money in is ${surplus} above spending, but over the last 12 months the balance changed by {change} a month on average. Treat the savings figure as the most this could be.`

Fact `balance_rose_despite_gap` (same place): `Typical spending is ${gap} above typical money in, but over the last 12 months the balance rose ${change} a month on average. Typical months can overstate the gap, so the cut needed may be smaller.`

## 7. Backup plan (G)

| Key | Text |
| :-- | :-- |
| K.g_head | Backup plan: if this happens |
| K.g_none | Pick a twist to see a backup plan. |
| K.g_ok | No cuts needed: the buffer lasts the full {n} months. |
| K.g_cut | To last the full {n} months, spending needs to drop by ${x} a month, about {pct}% of typical spending. |
| K.g_gap | To stop the buffer falling, spending needs to drop by ${x} a month. |
| K.g_flex | Spending above fixed costs: ${flex} a month. |
| K.g_fixed | Fixed costs, including bills added by the shock: ${x} a month. |
| K.g_floor | Even with all other spending cut, the buffer lasts {R}, short of {n} months. |
| K.g_zero | There is no buffer. First, ${cover} is needed to get back to $0. [TBD-Owner: wording] |
| K.g_steps | Steps, in order |
| K.g_agree | Needs the lender's agreement. |

Step wording is the engine's `BackupStep.action`, printed as is.

## 8. Details (H) and footer

| Key | Text |
| :-- | :-- |
| K.h_expander | Details: charts, tables and all notes |
| K.h_tab_charts | Charts |
| K.h_tab_tables | Tables |
| K.h_tab_notes | Notes |
| K.h_chart_alt | Line chart of money in and money out each month for customer {id}. Lowest balance was ${x} in {month}. |
| K.h_chart2_alt | Line chart of the account balance by month. |
| K.h_table_cap | Last 6 months against all months |
| K.footer | Data: PKDD'99 Discovery Challenge Financial dataset. Method notes are in the docs folder. |

## 9. Sentences the presenter reads (cheat sheet), with real 20111 values

1. "Customer 20111 brings in $6,339 a month and spends $8,600. The buffer is $17,612: that's 7.8 months."
2. "Laid off, income at 55% for 6 months: the money runs out in month 4, about 2.6 months short. The judges' runway is 3.4 months."
3. Adjusted runway applies: "Our adjusted runway is 4.1 months against the judges' 3.4. It lowers spending as income falls, as some accounts in the data did. It's an illustration."
3b. Adjusted runway is n/a (transfer account, or a twist with no income cut): "Our adjusted runway is n/a here: this comes from cash-only accounts. The judges' 83.3 months stands."
4. "To last the full 6 months, spending needs to drop by $2,178 a month, about 25%."
5. "Before any shock, a 3-month fund of $25,799 needs spending about $2,260 a month lower to start."
6. EI maximum on: "With the weekly maximum, they run out in month 4 too."
