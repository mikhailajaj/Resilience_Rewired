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
| K.m_fixed | Typical fixed costs (standard) | bills, insurance, loan, per month |
| K.m_loan | Loan payment | per month, if still running |

Header: `Customer {id}` and `Data from {first} to {last}`. Beside it: `Income type: {Cash only / Transfers / Pension} (our label)`.

Runway values are the engine's `runway.label`: `7.8 months`, `0 months`, `No shortfall (120+)` (gap is zero or less), `120.0 months` (buffer lasts 120 months or more).

K.flow_line, directly under the summary line on both pages: `These are typical months, and medians don't add up. Over the last 12 months the balance {fell or rose} ${x} a month on average, and it ended at ${latest}.` Accounts whose data stops early read `its last 12 months of data`. A change under 50 cents reads `stayed about the same`.

K.summary_line, by case:
- Normal: `Customer {id} brings in about ${I} a month and spends about ${S}. The buffer is ${B}, so it would last {R}.`
- Money in covers spending (`No shortfall`): `Customer {id} brings in about ${I} a month and spends about ${S} in a typical month, so typical months show no shortfall. The buffer is ${B}.`
- Capped (`120.0 months`, gap above 0): `Customer {id} spends slightly more than comes in. The buffer of ${B} would last 120.0 months.` Owner decision D5, 2026-11-07: the literal formula output. `No shortfall (120+)` only when the gap is 0 or less.
- Buffer zero or less: `Customer {id} has no buffer to draw on: the buffer (average balance over the last 6 months) is ${B}. Runway is 0 months.`

Customer notes: shown for each `profile.warnings` item, in this priority: N.neg_buf, N.zero, N.no_income, N.no_spend, N.stale, N.pension, N.no_bills, N.bills_gap, N.high_flow, the rest. Max 3 in B, all in Details. Facts, not warnings.

| Key | Engine code | Text |
| :-- | :-- | :-- |
| N.zero | little_activity | Almost no activity on this account. Most numbers are $0. |
| N.no_income | irregular_income | No regular money in. A lower income changes nothing here. |
| N.no_spend | irregular_spending | No regular spending recorded. Buffer in months of spending can't be worked out. |
| N.neg_buf | no_buffer | The buffer (average balance over the last 6 months) is at or below $0, so runway is 0 months. |
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
| K.s_start_help | Optional. If the shock runs into January, a note shows this customer's typical January spending. It doesn't change any number on the page. |

Presets: Laid off = income 55, 6 months. Furnace = one-off 1.0 month. Mix = income 55, 6 months, bills 15. Bills = bills 15. Reset = all defaults, EI switch off.

## 4. Before and after (D)

Headings: `Before`, `After`. Rows: `Runway`, `Money in`, `Spending`, `Buffer` (After: `Buffer left`), `Monthly gap`. Delta words: `down {x}`, `up {x}`, `no change`.

K.verdict is chosen by the engine's `verdict_case`. It is never worked out from the rounded runway, and never uses a ceiling on it.

| `verdict_case` | Sentence |
| :-- | :-- |
| no_shock | No shock applied. Pick a twist to see what changes. |
| runway_zero, with `no_buffer_before_shock` | The buffer (average balance over the last 6 months) was already ${B} before this, so runway is 0 months whatever the shock. |
| runway_zero, otherwise | The one-off cost of ${x} is bigger than the buffer of ${B}. Nothing is left to live on. |
| no_shortfall | Income still covers spending, so the buffer isn't being used. |
| income_cut_makes_it | With income at {pct}% for {n} months, the money lasts the full {n} months. They make it. |
| income_cut_runs_out | With income at {pct}% for {n} months, the money runs out in month {runs_out_in_month}, about {months_short} months short. |
| income_cut_runs_out, `runs_out_in_month` = 0 | There is no buffer before month 1, so the money is gone before the lower income starts. |
| income_cut_open_ended | With income at {pct}%, the buffer lasts {R}. No length was set, so there is no make-it answer. |
| cost_or_bills_only | After this, the buffer lasts {R}, down from {R0}. |

Second line when a duration exists: `The standard (judges') runway is {R}.` (so the verdict and the runway are never seen as in conflict).

Assumption line (only when `duration.assumption_applied`): `After month {n} we assume no income. A benefit ending doesn't mean a new job has started.` (This replaces "before income recovers", which the engine does not assume.)

Fact lines (K.fact.*), one plain line each, under the verdict:

| Code | Text |
| :-- | :-- |
| layoff_doesnt_fit_pension | Pension income: a layoff wouldn't stop this. The numbers apply the layoff as asked. |
| income_cut_no_income | No regular money in, so a lower income changes nothing here. |
| bills_shock_no_bills | No regular bills visible, so the standard (judges') formula changes nothing for this. |
| bills_shock_too_small | Standing orders show more bills than the standard (judges') figure, so this rise is understated. |
| one_off_zero_spending | No typical spending, so a cost in months of spending is $0. Type dollars instead. |
| no_buffer_before_shock | The buffer (average balance over the last 6 months) was already ${B} before this shock. |
| one_off_exceeds_buffer | The one-off cost is bigger than the buffer. |
| data_stops_early | Data stops in {month}. |
| little_activity | Almost no activity, so most numbers are $0. |
| spending_floored_at_zero | Spending can't go below $0, so it stops there. |
| runs_into_january | This runs into January, when spending is usually higher. |

## 5. Our numbers (E)

Heading: `Our estimates, shown beside the standard (judges') figures`. Under it: `They never replace the standard (judges') figures.`

| Key | Label | Help |
| :-- | :-- | :-- |
| K.e_adjust | Runway, if you adjust | An illustration, not a forecast. In some accounts in the data, spending fell when income fell. This lowers spending that way. The standard (judges') runway keeps spending flat. |
| K.e_cap | Runway with EI weekly maximum | Same shock, with EI capped at the weekly maximum you set. Shown only when the switch is on. |
| K.e_so | Runway with bills from standing orders | Monthly bills set up as standing orders. Some bills don't show in typical bills, so this can be larger. |
| K.e_fixed | Current fixed costs | Bills, insurance and the loan payment if still running. Differs from "Typical fixed costs" above when a loan is recent or bills are hidden. |
| K.e_months | Buffer in months of spending | Buffer divided by typical spending. Shows savings without how much money passes through. |
| K.e_low | Lowest balance, last 6 months | The lowest the balance got. An average can hide it. |
| K.e_latest | Latest balance | The balance at the end of {month}. The buffer is an average over 6 months, so the two can differ. Suffix: `(judges' buffer: {B})` |
| K.e_actual | Actual change, last 12 months | What the balance really did, on average. Typical money in minus typical spending can differ, because each is a separate median. Suffix: `(typical month: {I - S})` |

Row suffix: `(standard (judges'): {value})` where there is a counterpart.

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
- Applies: `Our adjusted runway is {Ra}, against the standard (judges') {R}. It lowers spending as income falls, as some accounts in the data did. It's an illustration.`
- n/a: `Our adjusted runway is n/a here: {reason line}. The standard (judges') {R} stands.`

## 6. Goal plan (F)

| Key | Text |
| :-- | :-- |
| K.f_head | Goal plan: build an emergency fund |
| K.f_cap | Before any shock |
| K.f_target | Emergency fund target (months of spending) |
| K.f_target_help | Default 3. Type any number. |
| K.f_on_track | To have {t} months of spending (${amt}) saved, set aside ${m} a month. That takes {n} months. |
| K.f_far | At ${m} a month this takes {n} months, more than 12 months. |
| K.f_done | Already there: the buffer covers {n} months. |
| K.f_nosurplus | Money in doesn't cover spending, so saving starts with spending about ${break_even} a month less. About ${reach} a month less would reach the target in 12 months. |
| K.f_cut_fits | That fits within the ${flex} of spending above fixed costs. |
| K.f_cut_over | That is more than the ${flex} of spending above fixed costs. |
| K.f_none | Not enough regular spending to set a target. |
| K.f_negative | First step: get the balance back above $0 (${x}). |
| K.f_low | Keep the balance above one loan payment (${P}) at all times. Its lowest point in the last 6 months was ${low}. |
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
| K.g_fixed | Current fixed costs, plus the bills rise: ${x} a month. |
| K.g_floor | Even with all other spending cut, the buffer lasts {R}, short of {n} months. |
| K.g_zero | There is no buffer. First, ${cover} is needed to get back to $0. [TBD-Owner: wording] |
| K.g_steps | Steps, in order |
| K.g_agree | Needs the lender's agreement. |
| K.g_oneoff | No cuts needed: income still covers spending. (One-off with no length and no gap; with a gap, `K.g_gap`. As built in `text.backup_lines`.) |
| P.loan_backup | Counting the loan ending in month {N}, the monthly gap falls by {payment} from then (our estimate). Then: "With that, they make it (our estimate)." or "They still run out in month {m} (our estimate)." **Gated on NEW-ADR-1** |

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
2. "Laid off, income at 55% for 6 months: the money runs out in month 4, about 2.6 months short. The standard (judges') runway is 3.4 months."
3. Adjusted runway applies: "Our adjusted runway is 4.1 months against the standard (judges') 3.4. It lowers spending as income falls, as some accounts in the data did. It's an illustration."
3b. Adjusted runway is n/a (transfer account, or a twist with no income cut): "Our adjusted runway is n/a here: this comes from cash-only accounts. The standard (judges') 83.3 months stands."
4. "To last the full 6 months, spending needs to drop by $2,178 a month, about 25%."
5. "Before any shock, a 3-month fund of $25,799 needs spending about $2,260 a month lower to start."
6. EI maximum on: "With the weekly maximum, they run out in month 4 too."

## 10. Chat (T)

The chat reuses `app/ui/text.py` for every number sentence: `summary_line`, `notes`, `verdict`, `fact_lines`, `assumption_line`, `goal_lines`, `backup_lines` and `our_rows`. Only the connecting lines below are new. `{plain}` is the shock in words, built from the card answers, such as "income kept at 55% for 6 months, then no income; bills up 15%".

| Key | Text |
| :-- | :-- |
| T.page | Chat |
| T.no_customer | Load a customer in the box above, then I can run a twist for them. |
| T.greet | Hi. I have customer {id} loaded. |
| T.range | Data from {first_month} to {last_month} ({n_months} months). |
| T.pick | Which twist? Pick one, or type the card. |
| T.b_job, T.b_bills, T.b_repair, T.b_mix, T.b_type | Job loss on EI · Bills go up · Surprise repair · Mix · Type it |
| T.ask_keep | How much of their usual income does EI keep? The README uses 55%. |
| T.ask_months | For how long? |
| T.ask_bills | How much do household bills go up? |
| T.ask_repair | How much does the repair cost? |
| T.not_number | Type a number, like 55. |
| T.out_of_range | {value} is outside what the engine takes: {size} must be {range}. Pick a size or type another. |
| T.engine_refused | The engine didn't accept {field}. Pick that size again. |
| T.engine_call | ⚙ engine call: `{call}` |
| T.change_line | Runway {R0} -> {R1}. Monthly gap {g0} -> {g1}. |
| T.ours | (our estimate) |
| T.confirm | I read this as: {plain}. Run it? |
| T.b_run, T.b_buttons | Run it · No, use buttons |
| T.partial | I read: {plain}. I still need {size}. |
| T.unsure | I'm not sure how to read that, so I won't guess. Pick a twist instead. |
| T.unsure_month | I can't set a start month here. Use More options on the Shock and plan page. |
| T.f_backup, T.f_goal, T.f_stack | Show the backup plan · Show the goal plan · Add another shock |
| T.f_size, T.f_new, T.f_send | Change the size · New customer · Send to the controls |
| T.pick_size | Which size? |
| T.stack_replace | This replaces the earlier {kind}: {old} -> {new}. |
| T.new | Type the new account number in the box at the top. |
| T.send_ok | Sent. The Shock and plan page now has these sizes. |
| T.send_cant | The controls can't hold {what}, so nothing was sent. The numbers above stand. |
| T.download | Download transcript |
| T.download_help | The chat lasts until the page is closed, so download it to keep it. |

`T.download_help` follows the questionnaire's "Answers last until the page is closed, so download them to keep them." Size buttons use the units in the [state table](flows.md#4-chat-state-machine-j4).

### Settled chat copy (NEW-COPY-1 to 10), 2026-11-07

Drafts are in [design §9](../../architecture/j4_chat.md#9-gaps-and-questions-sent-back) and [the build report](../../architecture/j4_chat_engineering.md). "As drafted" means `chat_text.py` and `state.py` keep their text.

| Item | Settled |
| :-- | :-- |
| NEW-COPY-1, NEW-COPY-5, NEW-COPY-7, NEW-COPY-8 | As drafted: `T.type_prompt`, `T.other`, `T.use`, `T.placeholder`, `T.ours_line`, `T.cheatsheet` |
| NEW-COPY-2 `{plain}` | As drafted, with the singulars of NEW-COPY-9 |
| NEW-COPY-3 `{what}` | As drafted, except `cant_open`: "a job loss with no end month" (was "until it runs out", which doesn't read after "can't hold") |
| NEW-COPY-4 | As drafted, except `after_ends`: size "what happens after the lower income ends"; range "no income, or income returns" (was the code words `no_income or income_returns`) |
| NEW-COPY-6 | `T.change_line` without the extra `$` (above). Rule for the whole deck: a `{x}` filled by `text.money` carries its own `$` and sign (`-$748`); older rows that write `${x}` mean the same |
| NEW-COPY-9 | Rule for the whole deck: a whole 1 reads "1 month", anything else "months"; a one-decimal runway always reads "months" ("1.0 months") |
| NEW-COPY-10 | Kind words as drafted. Size button: "Change {size} ({shown})", such as "Change income kept (55%)" (verbs first on buttons) |

### Consistency review of built sentences (Part 4)

Only rule breaks. The build changes `app/ui/text.py` to match; each needs a test on a 1-month or 1-target case.

| Where in `text.py` | Rule broken | Change |
| :-- | :-- | :-- |
| `verdict`: "for {n} months", "the full {n} months" | NEW-COPY-9 (`months_asked` can be 1) | "1 month" when 1 |
| `verdict`: "about {short:g} months short" | NEW-COPY-9 (`:g` turns 1.0 into "1 months") | "about 1 month short" when 1 |
| `goal_lines`: "{t} months of spending", "takes {n} months" | NEW-COPY-9 (target 1, or 1 month to goal) | Singular when 1 |
| `goal_lines` and `K.f_far`: ", more than 12." | "months" always spelled out | ", more than 12 months." |
| `backup_lines`, `_capped_line`: "the full {n} months", "short of {n} months" | NEW-COPY-9 | Singular when 1 |
| `runway_delta`: "{change:g} months" | NEW-COPY-9 | "1 month" when 1 |

## 11. Plan designer (P)

Numbers first, "(our estimate)" on our figures, `{x}` from `text.money`. Rate labels: `{rate}` is one of the three below.

| Key | Text |
| :-- | :-- |
| P.head, P.cap | Plan designer · Before any shock. Tick a plan to open it. |
| P.r_actual, P.r_judges, P.r_lean | Actual change, last 12 months (our estimate) · Typical money in minus typical spending · Saving at lean-month spending (our estimate) |
| P.r_note | Typical months come from different months, so they don't add up. The actual change is the headline. |
| P.t_goal, P.t_off, P.t_emergency | Savings goal · Time off work · Emergency budget |
| P.i_name, P.i_amount, P.i_deadline, P.i_interest | What for · Amount ($) · Deadline in months (optional) · Interest, % a year (optional, default 0) |
| P.i_months_off, P.i_cost | Months off (1 to 120) · Cost ($) |
| P.g_needed | {fund_needed} to finish the emergency fund first, then {amount} for the {goal_name}. |
| P.g_months, P.never, P.over_cap | {rate}: {n} months. · {rate}: never at this rate. · {rate}: more than 120 months. |
| P.g_now, P.g_zero | The money above the emergency fund already covers the {goal_name}, so it can be bought now. · The amount is $0, so there is nothing to save. |
| P.g_deadline, P.g_on_pace | To have it in {deadline} months, save {needed} a month. · The actual change already does that, so no cut is needed. |
| P.g_cut | That needs {cut} a month less spending: {share}% of the {flex} above fixed costs, {within or more than} the {lean_cut} the lean-quarter level would save. |
| P.g_cut_over | That is more than the {flex} above fixed costs, so cuts alone can't reach it by then. |
| P.g_cut_start | Saving starts with spending {break_even} a month less. {reach} a month less would reach it in 120 months. |
| P.g_fund_first, P.interest | This includes finishing the emergency fund first. · Includes {interest_pct}% a year interest (our estimate). |
| P.no_fund, P.month_one, P.no_shock_used | Not enough regular spending to set an emergency fund, so goals count from $0. · Data stops in {last_month}, so month 1 is the month after. · The shock above isn't used here. |
| P.o_amount | {months_off} months off at typical spending: {amount}. At lean spending: {lean_amount} (our estimate). |
| P.o_ok, P.o_out, P.o_now | With no income for {months_off} months from month {start}, the money lasts. They make it. · ..., the money runs out in month {m} of the time off. · Not saved by month 120, so this checks starting now. |
| P.e_left_ok, P.e_left_no, P.e_zero | The buffer covers it: {left} is left. · The buffer can't cover it: {left} left. · The cost is $0, so the buffer is unchanged. |
| P.e_budget, P.e_lean | Do this first, in order: · Lean budget: {lean} a month, {fixed} fixed and {other} other (our estimate). |
| P.e_rebuild | {rate}: back to {buffer} in {n} months, emergency fund in {m} months. |
| P.tl_head, P.tl_table, P.tl_none | Balance by month, one line per rate · Show as a table · No rate adds to the balance, so every line stays flat or falls. |
| P.tl_alt | Line chart of the balance over {n} months at each saving rate. Markers: {events}. |
| P.m_* | Emergency fund reached · {goal_name} reached · {goal_name} bought · Time off starts · Time off ends · Emergency cost · Loan paid off |
| P.loan_line, P.loan_never | {n} months; {n_loan} counting the loan ending in month {N} (our estimate). · never at this rate; {n_loan} months counting the loan ending in month {N} (our estimate). |
| P.loan_d | The loan is behind, so month {N} is the scheduled end, not a certain one. |

All "{n} months" follow NEW-COPY-9. Chat rows for the plan designer are stretch; none until the chat ships.

