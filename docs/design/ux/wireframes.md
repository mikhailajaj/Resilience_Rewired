# Wireframes: Resilience Rewired

Low fidelity. Streamlit parts named in [brackets]. Reading order is top to bottom, left to right. Target: readable from across a room, so the headline numbers use the largest text the app has (st.metric, or markdown at heading size); the visual designer sets the scale. All text strings live in `copy.md` and are referred to by key like `{K.title}`.

## Page structure

This file covers the Shock and plan page and, in section T, the Chat page. The Customer profiling page is described in [`customer_profiling.md`](../../customer_profiling.md). Region A sits above every page.

```
+--------------------------------------------------------------------------+
| A. Customer picker                                                        |
| B. Know the customer             (shows after a valid ID)                 |
| C. Twist: buttons and sliders                                             |
| D. Before and after              (judges' numbers, headline)              |
| E. Our numbers                   (labelled, directly below D)             |
| F. Goal plan  |  G. Backup plan                                           |
| H. Details [st.expander, closed]: charts, tables, customer notes          |
| P. Plan designer                 (bottom; ticks open each plan, J5)       |
+--------------------------------------------------------------------------+
```

Why one page and no tabs for the core: tabs hide content from a room and cost a click per section. St.tabs is used only inside H for charts vs tables. Narrow window: columns stack in the same order.

Primary action per screen: A = "Show customer". B to G = the twist buttons (C). H has none.

Branding: a neutral text wordmark ("Resilience Rewired") only. No Tangerine logo or font (RU-5).

---

## A. Customer picker (always visible, top)

```
 Resilience Rewired                         {K.subtitle}
 +-----------------------------+  [ Show customer ]
 | Account ID  [ 20111       ] |  <- [st.text_input] + [st.button] (primary)
 +-----------------------------+
 Help: {K.id_help}
 (inline error line here when invalid, plain text, no banner)
```

| Element | Label | Required | Format | Default | Validation |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Account ID | `Account ID` | Yes | digits only, as in `accounts.csv` | empty | trims spaces; digits only; must exist in data |
| Show customer | button | | | | Enter in the box does the same |

Placeholder is not a label: the label is always above. Example ID goes in help text, not only the placeholder.

Focus: page load puts the cursor in the ID box (Streamlit cannot always do this; fallback: box is the first control, so one Tab). After a result shows, focus stays on the box so the next ID can be typed over the old one.

### A1. Empty (first load)
```
 Account ID [            ]  [ Show customer ]
 Help: Type the account number the judge gave you, for example 20111.

 (rest of page: one calm line, no empty charts)
 {K.empty_page}
```
Sections B to H are not drawn. No sliders show, so nothing can be clicked with no customer.

### A2. Loading
```
 Account ID [ 20111 ]  [ Show customer ]
 Loading customer 20111...        <- [st.spinner], plain text
```
Old results are cleared first so a stale customer is never on screen with a new ID.

### A3. Invalid ID, not digits
```
 Account ID [ abc ]  [ Show customer ]
 "abc" isn't an account number. Use digits only, for example 20111.
```
Inline text under the box [st.caption], not a banner. Page below stays in the empty state.

### A4. Invalid ID, not in the data
```
 Account ID [ 12345 ]  [ Show customer ]
 No account 12345 in this data. Try another number.
```
Optionally one small line: "Account numbers here run from {min} to {max}." (engine gives min and max).

---

## B. Know the customer (J1)

Real values from the engine for account 20111 (run 2026-11-07).

```
 Customer 20111                                  Data from 2022-11 to 2025-12
 Income type: Cash only (our label)
 {K.summary_line}

 +------------------+ +------------------+ +------------------+ +------------------+
 | Typical money in | | Typical spending | | Buffer           | | Runway, no shock |
 | $6,339           | | $8,600           | | $17,612          | | 7.8 months       |
 | per month        | | per month        | | avg, last 6 mo.  | |                  |
 +------------------+ +------------------+ +------------------+ +------------------+
 Household bills  $0   |  Fixed costs  $2,330   |  Loan payment  $2,330
 Notes: Customer notes (0 to 3 plain lines; the rest are in Details)
   - No regular bills visible in the transactions.
   - The loan is behind or unpaid.
```

- Four [st.metric] in [st.columns(4)]: judges' I, S, B, runway. Then H, F, P as [st.columns(3)].
- This block holds only the judges' definitions. Income type is our addition (RU-2): it sits in the header, labelled "(our label)", outside the metric block.
- Notes come from `profile.warnings` (engine decides the condition) in the priority order in copy.md, so the wireframe never restates a condition. Plain bullets, no meaning by icon.

### B2. Hard accounts: same layout, text changes only

| State | Engine signal | What shows | Note line |
| :-- | :-- | :-- | :-- |
| Zero activity | `little_activity` | $0 money in and spending; runway per engine | N.zero |
| Irregular income | `irregular_income` | Money in $0 | N.no_income |
| Irregular spending | `irregular_spending` | Spending $0; our months-of-spending row `n/a` | N.no_spend |
| Zero or negative buffer | `no_buffer` | Buffer shown as is (e.g. -$2,513 on 32078), runway 0 months | N.neg_buf |
| Data stops early | `out_of_date` | Header range ends early | N.stale |
| Pension | `pension_income` | Normal | N.pension (repeated in D on a layoff) |
| No bills visible | `no_regular_bills` (H = 0 and bills not missing, 1,063 accounts) | H $0 | N.no_bills |
| Bills missing from H | `bills_missing_from_h` | E shows the standing-order figure | N.bills_gap |
| High flow | `high_flow` | Normal | N.high_flow |
| Went negative | `went_negative` | Lowest balance in E | N.low |

No section disappears on any of these. A short note beats a blank section.

B3 stale data = "Data stops early" above; the range is always in the header. B4 long content: notes capped at 3 in B; amounts of $1,000,000 or more read "$1.2M".

---

## C. Twist: buttons and inputs (J2)

Rule for every input: a default value plus manual entry. Where a slider helps a presenter, a number box sits beside it and the two stay in step (one `st.session_state` value). Type a number and the slider moves; move the slider and the number changes. Nothing needs a submit button.

```
 Pick a twist
 [ Laid off, EI 55% ] [ Furnace dies ] [ Laid off + bills up 15% ] [ Rent or bills up ] [ Reset (no shock) ]
 Selected: Laid off, EI 55%      (or "Custom")

 Income kept (%)            |-----------o----|  [ 55 ]   100 = no change
 Income stays lower for     |-----o----------|  [  6 ] months
 [ ] Apply the EI weekly maximum      Weekly maximum ($) [ 729 ]   (box greyed while off)
 Household bills up (%)     |--o-------------|  [ 15 ]
 Bills or rent up ($ a month)                  [  0 ]
 One-off cost (months of spending) |o---------|  [ 0.0 ]       or  One-off cost ($) [ 0 ]
 > More options  (closed [st.expander])
     Shock starts in  [ Not set v ]  (Jan to Dec)
```

| Element | Label | Control | Range / step | Default | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Twist buttons | names in copy.md | [st.button] x4 plus Reset | | none | Each sets every input below |
| Income kept | `Income kept (%)` | [st.slider] + [st.number_input] | 0 to 100, step 1 | 100 | Any whole or decimal value (57 works). Engine takes `keep_fraction` = value / 100 |
| Income lasts | `Income stays lower for (months)` | slider + number box | 1 to 24 slider, box up to 120 | 6 | Disabled while income kept is 100 |
| EI maximum switch | `Apply the EI weekly maximum` | [st.toggle] | on/off | Off | Off keeps the judges' setting |
| EI maximum amount | `Weekly maximum ($)` | [st.number_input] | $1 to $5,000, step 1 | 729 | Disabled while switch is off. $729 is the 2026 figure in shock_sizing.md |
| Bills up | `Household bills up (%)` | slider + number box | 0 to 50, step 1 | 0 | Percent of the customer's usual bills |
| Dollar rise | `Bills or rent up ($ a month)` | [st.number_input] | 0 to 20,000, step 50 | 0 | Maps to `other_spending_change`. For a card that says "rent up $300" |
| One-off, months | `One-off cost (months of spending)` | slider | 0 to 3, step 0.25 | 0 | |
| One-off, dollars | `One-off cost ($)` | [st.number_input] | 0 to 100,000, step 100 | 0 | Maps to `one_off_dollars` |
| Start month | `Shock starts in` | [st.selectbox] in a closed "More options" [st.expander] | Not set, Jan to Dec | Not set | Off the main path. Only adds a January note; never changes runway |

Behaviours
- **One-off: last edit wins.** The engine adds the two one-off fields. To keep a typed "$5,000 repair" from adding to a leftover 1.0 month, typing dollars sets the months slider to 0 and moving the slider sets dollars to 0. A line shows the total: `Total one-off: $5,000`.
- **EI maximum:** the switch changes only the labelled second runway in E (and its own make-it answer there). D's judges' numbers never change when the switch is flipped. The weekly figure becomes a monthly cap of weekly x 52 / 12 ($3,159 at $729).
- Selected twist is written as "Selected: name"; any manual edit changes it to "Custom".
- Every preset sets all inputs (Reset: 100, 6, switch off, 0, 0, 0, 0). Presets leave the EI switch where it is ; Reset turns it off.
- Narrow window: one column, same order.

### C1. No shock: inputs at defaults. D shows `{K.no_shock}`.
### C2. Out-of-range typing: the box clamps to its range and the help text states the range. No error text.
### C3. Disabled: "Income stays lower for" and the EI switch are disabled while Income kept = 100, with the caption `Not used while income is unchanged.`

---

## D. Before and after, the judges' numbers (headline)

Real engine values, account 20111, "Laid off, EI 55%":

```
 They run out in month 4 of 6, about 2.6 months short.        <- verdict, from the engine
 The judges' runway is 3.4 months.
 +------------------------------+  +------------------------------+
 | BEFORE                       |  | AFTER                        |
 | Runway     7.8 months        |  | Runway     3.4 months (down 4.4) |
 | Money in   $6,339            |  | Money in   $3,487  (down $2,852) |
 | Spending   $8,600            |  | Spending   $8,600  (no change) |
 | Buffer     $17,612           |  | Buffer left $17,612 (no change) |
 +------------------------------+  +------------------------------+
 Monthly gap   $2,260  ->  $5,113
 After month 6 we assume no income, because a benefit ending doesn't mean a new job.   <- duration.assumption, only when it applies
```

- [st.columns(2)] with [st.metric]; deltas also written in words.
- The verdict comes only from `verdict_case`, `duration.verdict` and `duration.runs_out_in_month`. The UI never compares the rounded runway to the length and never rounds up. (Example: 5.96 shows "6.0 months" yet runs out in month 6.)
- Runway shows `runway.label`: `7.8 months`, `0 months`, `No shortfall (120+)` (gap is zero or less, nothing else) or `120.0 months` (a gap exists but the buffer lasts 120 months or more, as for 20134 with no shock). The cap is not "no shortfall".
- Every `facts` item prints as one plain line under the verdict, using the copy in copy.md section 4.

### D states, one per `verdict_case` (same order the engine checks)

| `verdict_case` | What the verdict line says | Extra |
| :-- | :-- | :-- |
| `no_shock` | No shock applied | Before = After, deltas hidden |
| `runway_zero` | Two wordings, below | After runway `0 months`, buffer left may be negative |
| `no_shortfall` | Income still covers spending | After runway `No shortfall (120+)`. Never routed to "runs out" |
| `income_cut_makes_it` | They make it | |
| `income_cut_runs_out` | Runs out in month N, about X months short | N = `runs_out_in_month`; N = 0 reads "no buffer before month 1" |
| `income_cut_open_ended` | Buffer lasts R months; no length given | |
| `cost_or_bills_only` | Buffer lasts R months, down from R0 | |

`runway_zero` has two wordings. If `no_buffer_before_shock` is in `facts`, the line says the buffer was already at or below zero and does not blame the cost (32078 with the furnace twist: buffer already -$2,513). Otherwise the cost is named.

Fact lines under the verdict (all optional): `layoff_doesnt_fit_pension` (pension), `income_cut_no_income`, `bills_shock_no_bills` (20111 bills result), `bills_shock_too_small`, `one_off_zero_spending`, `one_off_exceeds_buffer`, `no_buffer_before_shock`, `data_stops_early`, `little_activity`, `spending_floored_at_zero`, `runs_into_january`.

---

## E. Our numbers (directly below D, labelled)

Real values, 20111 with the layoff twist:

```
 Our numbers, shown beside the judges'. They never replace them.
 +----------------------------------------------------------------+
 | Runway, if you adjust        4.1 months    (judges': 3.4)  (i) |
 | Runway with EI weekly max    3.2 months    (judges': 3.4)  (i) |  <- only when the switch is on
 | Bills on standing orders     n/a  (no bills shock)             |
 | Current fixed costs          $2,330 a month (judges' F: $2,330)|
 | Buffer in months of spending 2.0 months                        |
 | Lowest balance, last 6 mo.   $10,418                           |
 +----------------------------------------------------------------+
```

- The EI-maximum runway row (from the engine's `ei_capped`: $729 x 52 / 12 = $3,159 caps income at $3,159 against $3,487, gap $5,441, runway 3.2) shows only when the switch is on. It has its own make-it line, plus the cut from `backup_capped`: `With the maximum, they run out in month 4. Lasting the full 6 months takes $2,505 a month less spending.` The judges' runway stays in D as the headline.
- "Bills on standing orders" rows: `n/a` with the engine's `reason` (`no_bills_shock`, `bills_not_missing`) turned into words by the table in copy.md. With a bills shock and `bills_missing_from_h` it shows the figure.
- "If you adjust" has a designed n/a path. `applies = False` happens for `pension_income`, `transfers_income`, `no_income_lost` and `no_typical_spending`, so it is n/a on transfer accounts and on every twist with no income cut (20134 on any twist; 20111 on the furnace twist). The row reads `n/a` and the reason line from copy.md sits under it. It is never blank or zero. The row stays on screen so the presenter has one sentence ready.
- The cheat sheet in copy.md has the matching n/a sentence.
- "Current fixed costs" is the contract's `current_fixed_costs` (bills + insurance + running loan payment). Do not label it F.
- Built below D at every width, with rows in three columns. Beside D, the 72px runway overflowed its card at 1440px.

---

## F. Goal plan: emergency fund (J3)

Always before any shock (captioned "Before any shock"). Real values, 20111, target 3 months:

```
 Goal plan: build an emergency fund                       Before any shock
 Emergency fund target (months of spending)  |--o----------|  [ 3 ]   = $25,799
 {goal sentence}
 Money in doesn't cover spending, so saving starts with spending about $2,260 a month less.
 $2,942 a month less would reach the target in 12 months. That is within the $6,269 of spending above fixed costs.
 Keep the lowest balance above one loan payment ($2,330). It is now $10,418.
 Savings path [st.dataframe, up to 6 rows]
```

Target: default 3 (owner), slider 1 to 12 plus number box (any value).

| `goal.state` | Shows |
| :-- | :-- |
| `already_there` | Buffer already covers {months_covered} months. No steps |
| `on_track` | Save `monthly_amount` a month for `months_to_goal` months; if `reaches_within_horizon` is False, say it is more than 12 months |
| `no_surplus` | Cut to break even, cut to reach in 12 months, and whether that fits in flexible spending (`cut_is_possible`) |
| `no_regular_spending` | Not enough regular spending to set a target |

- `below_zero_by` > 0 puts "First step: get the balance back above $0 ($X)" above everything.
- **Fact `surplus_not_seen_in_balance`:** printed directly under the plan sentence as a plain line. Example, account 20189: money in is $1,796 above spending, but the balance fell $1,344 a month on average over the last 12 months. The savings figure then reads "the most this could be".
- Low-balance line only when a loan is running (`low_balance` not None).

## G. Backup plan: if the shock hits (J3)

| `backup.state` | Shows |
| :-- | :-- |
| `no_shock` | Pick a twist to see a backup plan |
| `no_cuts_needed` | No cuts needed: the buffer lasts the full N months |
| `cuts_needed` | Cut `cut_to_last` a month (share of spending, share of flexible spending) to last N months. Without a length (furnace): `cut_to_close_gap` to stop the buffer falling |
| `cuts_not_enough` | With all flexible spending cut, runway is `runway_if_all_flexible_cut`, short of N |
| `no_buffer` | Buffer is gone: `cover_needed` first, then the steps |

```
 Backup plan: if this happens                   (20111, layoff, 6 months)
 To last the full 6 months, spending needs to drop by $2,178 a month, about 25% of typical spending.
 Spending above fixed costs: $6,269 a month.   Fixed costs, with bills added by the shock: $2,330.
 Steps in order:
  1. Bring other spending down to $3,405 a month, the level of this account's lowest quarter. Saves $2,864 a month.
```

- Step text is the engine's `BackupStep.action`, printed as is, in `order`. A step with `needs_agreement` reads "needs the lender's agreement" (words, not colour).
- `fixed_costs` is current fixed costs plus bills added by the shock, so it can differ from F (CON-4). Label it as such.
- 20134 with the layoff + bills twist is `cuts_not_enough`: needs $1,692 a month, only $1,582 is flexible, and the runway with all flexible spending cut is 5.8 months.
- Runway 0 on 32078 (furnace): `no_buffer`, cover $5,480 first.

---

## H. Details (closed [st.expander])

```
 v Details
   [Charts] [Tables] [Notes]    <- [st.tabs]
   Charts: money in vs out by month; balance with lowest point marked
   Tables: last 6 months vs lifetime medians [st.dataframe]
   Notes: all customer notes in full, plain list
```

- Closed by default so the projected screen stays clean.
- Charts: [st.line_chart] with text labels; no meaning by colour alone (lines named in a legend and directly in the caption).
- Last 6 months vs all-time table is where "stale medians" show as plain numbers.

---

## P. Plan designer (J5)

Below H, above the footer. No shock (RU-11). Keys are in [copy §11](copy.md#11-plan-designer-p); use-case steps in [`use_cases_plan.md`](../../inception/use_cases_plan.md). Values: 20111, from the inception script.

### P1. Rates and checkboxes (J5 1 to 3)

```
 Plan designer                                   {P.cap}
 {P.rates}   Actual change, last 12 months   -$748 a month   (headline)
             Judges' typical month (I - S)   -$2,260 a month
             Lean months (ours)              +$604 a month
 [ ] Savings goal   [ ] Time off work   [ ] Emergency budget   [st.checkbox x3]
```

### P2. Savings goal open (J5.1)

```
 [x] Savings goal   Name [ car ]  Amount [ 60000 ]  Deadline, months [ 24 ]  Interest % a year [ 0 ]
 {P.g_needed}  $8,187 to finish the emergency fund first, then $60,000 for the car.
 {P.g_months}  Actual change: never at this rate. 115 months counting the loan ending in month 36 (ours).
               Judges' typical month: never at this rate.   Lean months (ours): 113 months; 52 counting the loan.
 {P.g_deadline} To have it in 24 months, save $2,841 a month.
 {P.g_cut}     That needs $3,589 a month less spending: 57% of the $6,269 above fixed costs, more than the
               $2,864 the lean-quarter level would save.
```

### P3. Time off and emergency open (J5.2, J5.3)

```
 [x] Time off work   Months off [ 24 ]
 {P.o_amount}  24 months off at typical spending: $206,391. At lean spending: $137,643 (ours).
 {P.o_now}     Not saved by month 120, so this checks starting now.
 {P.o_out}     With no income for 24 months from month 0, the money runs out in month 3 of the time off.
 [x] Emergency budget   Cost [ 10000 ]
 {P.e_left_ok} The buffer covers it: $7,612 is left.
```

32078, cost $10,000 (instant budget): `{P.e_left_no}` "The buffer can't cover it: -$12,513 left." then `{P.e_budget}` with the backup steps (1. find $12,513 to get back to $0) and "Lean budget: $1,346 a month", then `{P.e_rebuild}` per rate.

### P4. Timeline (J5.4)

```
 {P.tl_head}
 $ |            ___/  lean (ours)          markers: F fund reached, G goal reached, B bought,
   |   ___/----'                           O time off start/end, E emergency, L loan paid off
   |--+---------L-----------------> month  [st.altair_chart, one line per rate, up to 120]
 [ Show as a table ]  {P.tl_table}         [st.dataframe: Month, one column per rate, Event]
```

### P5. Loan lines (J5.1 5d, 5e; J3 5b)

```
 {P.loan_line}   113 months; 52 counting the loan ending in month 36 (ours).
 {P.loan_d}      (status D only) The loan is behind, so month N is scheduled, not certain.
```

| Element | Use-case steps |
| :-- | :-- |
| Rates block | J5 1; J5.1 5, 5a, 5b |
| Checkboxes and inputs | J5 2, 2a; J5.1 1, 2, 2a to 2c; J5.2 1, 1a; J5.3 1, 1a |
| Goal lines | J5.1 4 to 6, 4a to 4c, 5c to 5h, 6a to 6c, 7a |
| Time-off lines | J5.2 2 to 4, 3a, 4a, 4b |
| Emergency lines | J5.3 2, 3, 2a, 3a, 3b |
| Timeline, table | J5 4; J5.4 1 to 3, 1a, 2a, 2b; J5.1 7 |
| Plain lines under P1 | J5 1b to 1d, 3a, 4b |
| Loan lines | J5 4a; J5.1 5d, 5e; J3 5b |

Accessibility: the table view holds every charted value and marker; markers are letters as well as colours.

## Accessibility behaviour (all screens)

| Topic | Behaviour |
| :-- | :-- |
| Focus order | ID box, Show customer, twist buttons left to right, sliders top to bottom, then the page text, Details |
| After submit | Focus stays in the ID box; results appear below it |
| After invalid ID | Error text sits directly under the box and is tied to it (shown as caption text, not removed on next keypress) |
| Keyboard | Enter submits ID; Tab reaches every button and slider; arrow keys move sliders |
| Announcements | The verdict sentence is plain page text near the top of D; Streamlit re-renders it on change; screen-reader users reach it by heading |
| Status without colour | Words ("down", "Selected", "runs out in month 4"), not colour, carry the status |
| Targets | Buttons full-width in their column, so large touch/click areas |
| Projection | Body text no smaller than st.metric label; headline numbers largest on the page |

---

## T. Chat page (J4)

A third page in [st.navigation], `{T.page}`, below region A. Messages are [st.chat_message] ("assistant" and "user"), history is in session state, and the text box is [st.chat_input]. Only the latest assistant message has live buttons (RU-19). Sample figures are the engine's output for 20111 on 2026-11-07.

```
+--------------------------------------------------------------------------+
| A. Customer picker (shared)                                               |
| Chat                                         [ Download transcript ]      |
| (bot) {T.greet} {K.summary_line}                                          |
|       {T.range}: Data from 2022-11 to 2025-12 (38 months).                |
|       - No regular bills visible in the transactions.   (up to 3 notes)   |
|       {T.pick}                                                            |
|       [Job loss on EI] [Bills go up] [Surprise repair] [Mix] [Type it]    |
| ...                                                                       |
| [ Type the twist card, or a size ...                              ] [>]   |
+--------------------------------------------------------------------------+
```

States, each drawn in the message area above:

```
T1 No customer   (bot) {T.no_customer}         no buttons; picker shows any error
T2 Greeting      as drawn above
T3 In progress   (you) Job loss on EI   (you) 55%
                 (bot) {T.ask_months}  [6 months] [12 months] [Until it runs out]
                       Other: [ 1 to 120 ] [Use]
T4 Result        (bot) ⚙ engine call: apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6)))
                       ✕ With income at 55% for 6 months, the money runs out in month 4,
                         about 2.6 months short.  The judges' runway is 3.4 months.
                       Runway 7.8 months -> 3.4 months. Monthly gap $2,260 -> $5,113.
                       (fact lines, assumption line, one "(ours)" line if it applies)
                       [Show the backup plan] [Show the goal plan] [Add another shock]
                       [Change the size] [New customer] [Send to the controls]
T5 Parse confirm (you) laid off, EI 55% for 6 months and bills up 15%
                 (bot) {T.confirm}  [Run it] [No, use buttons]
T6 Error         (bot) {T.out_of_range} | {T.not_number} | {T.unsure} | {T.send_cant}
                       then the buttons of the step being asked
```

| Element | Use-case steps |
| :-- | :-- |
| T1 no-customer line | J4 1a, J4.1 1b, J4.3 1d, 1d1 |
| T2 greeting, notes, twist buttons | J4 1, 1b, 1c, 1d, 4a; J4.1 1, 1a, 6a; J4.2 4a; J4.4 1a, 1c |
| T3 size question and buttons | J4.1 2, 3, 4; J4.2 2a, 2f; J4.3 1b, 1c |
| T4 engine call line | J4.1 5, 6; J4.3 2 |
| T4 result sentences | J4.1 7, 3c, 7a to 7h; J4.2 5a |
| T4 plan lines | J4.3 3, 3a, 3b, 3c, 1a, 1a1, 1a2, 1e |
| T4 follow-up buttons | J4.1 8; J4.3 1, 4 |
| T5 confirm | J4.2 3, 4, 4b |
| T6 error line | J4 2a; J4.1 3a, 3b, 3d, 6b; J4.2 2b, 2c, 2d; J4.3 1e1 |
| Download button | J4.4 1, 2 |

No screen: J4.2 2e (blank text is ignored) and J4.4 1b (inside the file). Focus: after each click, focus goes to [st.chat_input]. Buttons wrap onto a second row on a narrow window.
