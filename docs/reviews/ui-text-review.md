# UI text review: accuracy and clarity for a first-time user

Date: 2026-11-08. Branch: `feature/guided-chat` (commit a716c4a). Reviewer: business analyst agent.

Scope: every user-facing string in `app/streamlit_app.py`, `app/app_pages/`, `app/ui/` and `app/assistant/`. It is checked against the engine (`app/engine/`), `README.md`, `app/README.md`, `docs/engine_contract.md`, `docs/discovery.md` and `docs/adr/`. No product code was changed.

The reader in mind has never seen the app, the datathon brief or the engine.

Severity: **High** = misleading or wrong. **Medium** = likely confusion. **Low** = polish.
Type: inaccurate, vague, jargon, inconsistent, missing-help.

## Counts

| Severity | Count |
| :-- | --: |
| High | 8 |
| Medium | 36 |
| Low | 29 |
| **Total** | **73** |

---

## A. First run and navigation

### UT-01 · Medium · missing-help · `app/ui/shared.py:48-54`
- **Current:** "How long can this customer last if money gets tight?" / label "Account ID" / "Type the account number, for example 20111. Press Enter."
- **Why it misleads:** The hero asks a question but never says what the tool is or who it's for. A newcomer doesn't know which IDs exist. The valid range only appears after a wrong entry (`shared.py:38-39`), even though `account_id_range()` is available.
- **Suggested:** "Resilience Rewired shows how long a bank customer's savings would last if income fell or costs rose, and builds a plan from their own numbers. Start by typing an account ID (from {min} to {max}, for example 20111) and pressing Show customer."

### UT-02 · Medium · missing-help · `app/app_pages/shock_and_plan.py:283`, `app/app_pages/customer_profiling.py:37`, `app/assistant/chat_text.py:10`
- **Current:** "Enter an account ID to start. You will see their money, a shock you can change, and a plan." / "Enter an account ID to see everything on file..." / "Load a customer in the box above, then I can run a twist for them."
- **Why it misleads:** None of the empty states says what each page is for compared with the others. None of them says that Findings works without a customer. A newcomer can't tell where to begin.
- **Suggested:** Add one line to the Shock and plan empty state: "Not sure where to start? Findings needs no customer and shows what the data says across all 4,500 accounts. Customer profiling shows everything on file for one customer. Chat walks you through a scenario step by step."

### UT-03 · Low · missing-help · `app/streamlit_app.py:34`
- **Current:** The Findings nav item has no `help=` text. The other three pages have one.
- **Suggested:** help="What the data shows across all accounts about spending after an income drop. Needs no customer."

### UT-04 · Medium · jargon · `app/streamlit_app.py:33`, `app/app_pages/shock_and_plan.py:124`, `app/assistant/chat_text.py:13,59,62`, `app/ui/text.py:109,316`
- **Current:** "Pick a twist", "type the card", "Type the twist card, or a size", "Pick a twist to see a backup plan."
- **Why it misleads:** "Twist" and "twist card" are terms from the datathon judging script (`README.md`, "Live twist"). Nothing in the app defines them. A newcomer reads "twist" as a plot twist and "card" as a bank card. This app has bank cards too (`profile_view.py:12`, "Cards").
- **Suggested:** Use "scenario" on screen. Define it once on the Shock and plan page: "A scenario is a what-if, such as a layoff, a rent rise or a surprise repair."

### UT-05 · Medium · jargon · `app/streamlit_app.py:31`, `app/app_pages/customer_profiling.py:37,51,134-137`
- **Current:** "questions to ask the stakeholder", tab "Stakeholder questions", "Type the stakeholder's answer here."
- **Why it misleads:** It never says who the stakeholder is (the bank? the customer? the datathon organisers?). It's also unclear whether a customer could see these questions.
- **Suggested:** "Questions for the bank" (or whichever party the owner names, see OQ-7). Add: "Questions only the bank can answer. The answers change how far the numbers can be trusted."

### UT-06 · Medium · jargon · used throughout. Examples: `app/ui/text.py:107,141-142,212,221,226,237,243`, `app/app_pages/shock_and_plan.py:148,162,210-211`, `app/ui/findings_view.py:20`, `app/ui/profile_view.py:38`, `app/app_pages/customer_profiling.py:58`
- **Current:** "The judges' runway is ...", "judges': 4.2 months", "Our numbers, shown beside the judges'", "They never replace the judges' figures.", "The judges' formula holds spending flat."
- **Why it misleads:** Nobody in the app is introduced as a judge. The term traces to `README.md` ("How judges calculate the numbers"). A newcomer may think of a legal ruling or an outside authority. They can't tell that this is simply the standard formula from the brief.
- **Suggested:** Use "standard" ("the standard runway", "standard figures"). Define it once, near "Our numbers": "Standard figures use the brief's formula exactly. Figures marked 'ours' are extra estimates we added beside them." Owner decision: OQ-1.

### UT-07 · Medium · jargon · `app/ui/text.py:278,280,363-367`, `app/ui/plan_text.py:15,17,42-44,48,57,70-77`, `app/assistant/chat_text.py:28,63`
- **Current:** "(ours)" appended to sentences and labels.
- **Why it misleads:** The tag is never explained. Some sentences end in "(ours)" twice in one line (`chat_text.py:63`: "{label}: {value} ({counterpart}) (ours)"). It reads like a typo.
- **Suggested:** Define it once (see UT-06), or replace it with "(our estimate)". Never append it twice in one line.

### UT-08 · Medium · jargon · `app/app_pages/shock_and_plan.py:19,21,142,145-148`, `app/assistant/chat_text.py:14,19`, `app/ui/findings_view.py:27`, `app/ui/cheatsheet.py:37`
- **Current:** "Laid off, EI 55%", "EI pays 55%.", "Apply the EI weekly maximum", "Job loss on EI".
- **Why it misleads:** "EI" is never spelled out. Outside Canada it means nothing. The 55% is never said to be a share of the customer's usual income. The engine applies it to typical money in (`app/engine/shock.py:394`).
- **Suggested:** Expand it on first use on each page: "EI (Employment Insurance, Canada's benefit after a job loss) pays about 55% of usual income."

### UT-09 · Low · jargon · `app/ui/profile_view.py:31-32`, `app/ui/text.py:237`
- **Current:** "Typical money in (I)", "Fixed costs (F)", "judges' F: $1,234".
- **Why it misleads:** The single letters come from the README's formula table. "judges' F" on the Shock and plan page has no key at all.
- **Suggested:** Drop the letters from on-screen labels, or add a one-line key under the table: "Letters match the brief's formula: I = money in, S = spending, H = household bills, F = fixed costs, P = loan payment, B = buffer."

---

## B. Customer summary (Shock and plan region B, shared sentences)

### UT-10 · High · inaccurate · `app/ui/text.py:41,68,112`, `app/ui/plan_text.py:55,101`
- **Current:** "The balance is at or below zero, so runway is 0 months." / "Customer N has no buffer to draw on: the balance is -$120." / "The balance was already -$120 before this..." / "The balance is at or below $0, so saving starts by getting back to $0."
- **Why it misleads:** The number shown is the buffer B. B is the average daily balance over the last 6 months (`app/engine/profile.py:365`), not the balance. The latest balance is a separate figure (`profile.py:402`) and can be positive. The page shows both, so a newcomer sees "the balance is -$120" next to "Latest balance $850".
- **Suggested:** "The buffer (average balance over the last 6 months) is -$120, so runway is 0 months." Apply the same fix to all five strings.

### UT-11 · High · inaccurate · `app/ui/text.py:72`
- **Current:** "Customer N brings in about $X and spends about $Y, so money isn't running down. The buffer is $B."
- **Why it misleads:** This branch runs whenever typical money in is at least typical spending. "Money isn't running down" is a claim about the balance, and the balance can be falling. The engine flags exactly this case (`app/engine/plan.py:331-333`, `surplus_not_seen_in_balance`). Findings counts 1,038 of 3,309 such accounts whose balance didn't grow (`app/engine/findings.py:87-90`). The next line on screen (`text.py:88`) can say the balance fell. The sentence also leaves out "a month".
- **Suggested:** "Customer N brings in about $X a month and spends about $Y in a typical month, so typical months show no shortfall. The buffer is $B."

### UT-12 · Medium · inaccurate · `app/ui/text.py:75-76`, label from `app/engine/formulas.py:21-22`
- **Current:** "Customer N spends slightly more than comes in. The buffer of $B would last 120.0 months."
- **Why it misleads:** Runway is capped at 120 (`formulas.py:21`, `min(buffer_left / gap, RUNWAY_CAP)`). "120.0 months" means "120 months or more", but it reads as an exact figure. The same label appears in the tiles and cards.
- **Suggested:** "...would last at least 120 months (the longest the formula counts)." For the label, show "120+ months" when the value hits the cap.

### UT-13 · Medium · jargon · `app/ui/text.py:88`
- **Current:** "These are typical months, and medians don't add up. Over the last 12 months the balance fell $X a month on average, and it ended at $Y."
- **Why it misleads:** "Medians don't add up" assumes the reader knows that money in, spending and so on are each medians taken from different months. It sounds like an error warning.
- **Suggested:** "The figures above are typical (median) months, each taken on its own, so money in minus spending won't match what the balance did. Over the last 12 months the balance fell $X a month on average and ended at $Y."

### UT-14 · Medium · vague · `app/app_pages/shock_and_plan.py:101-108`
- **Current:** Tiles "Typical money in", "Typical spending", "Buffer", "Runway, no shock", "Household bills", "Fixed costs", "Loan payment", with dollar values only.
- **Why it misleads:** No unit or period is given ("a month"), and nothing is defined. "Buffer" in particular is a 6-month average daily balance (`profile.py:365`), not money in the bank today. "Typical" means median across all months on file (`profile.py:364`).
- **Suggested:** Add "a month" to the flow tiles, and `help=` tooltips. For example, Buffer: "Average daily balance over the last 6 months of data. Runway draws this down." Typical money in: "Median monthly money in, across all months on file."

### UT-15 · Medium · jargon · label `app/engine/formulas.py:4`, shown at `app/app_pages/shock_and_plan.py:104,184,197` and in the chat
- **Current:** "No shortfall (120+)"
- **Why it misleads:** "(120+)" is the README's notation (`README.md`, runway pseudocode). A newcomer can't tell whether it means 120 months, 120 dollars, or a score.
- **Suggested:** On screen, use "No shortfall: money in covers spending". Keep the engine label unchanged for README matching, and put "(would last 120+ months)" in the tooltip.

### UT-16 · Low · missing-help · `app/app_pages/shock_and_plan.py:109`
- **Current:** Shows only the first 3 notes, with no hint that there are more.
- **Suggested:** When there are more than 3, add "More notes under Details at the bottom of the page."

### UT-17 · Low · vague · `app/app_pages/shock_and_plan.py:96`, `app/ui/profile_view.py:11`
- **Current:** "Income type: Cash only (our label)."
- **Why it misleads:** The categories "Pension", "Transfers" and "Cash only" aren't explained. They are assigned in order: any pension deposit, then any transfer in, otherwise cash (`profile.py:332-337`).
- **Suggested:** Add a tooltip: "Pension: some pension deposits on file. Transfers: some incoming transfers, no pension. Cash only: neither."

### UT-18 · Medium · inaccurate · `app/ui/text.py:43,139`, `app/ui/findings_view.py:31`
- **Current:** "Pension income: a layoff wouldn't stop this." / "740 accounts live on a pension, where a layoff doesn't fit."
- **Why it misleads:** An account is labelled Pension if any pension deposit ever appears (`profile.py:333-334`, `x.pension_in.sum() > 0`). The pension could be a small part of the income. "Live on a pension" and "wouldn't stop this" claim it is the whole income.
- **Suggested:** "Pension deposits are on file, and a layoff wouldn't stop those." / "740 accounts receive a pension, so a layoff may not fit." Owner decision on the threshold: OQ-5.

---

## C. Shock controls (region C)

### UT-19 · High · inaccurate · `app/app_pages/shock_and_plan.py:162`
- **Current:** "Optional. Spending is higher in January and June. This never changes the judges' runway."
- **Why it misleads:** The engine uses the start month for one thing only: a note when the shock covers January (`app/engine/shock.py:328-329,361-364`; `docs/engine_contract.md:58`, "Only adds a January fact; never changes runway"). Picking June does nothing. "Never changes the judges' runway" implies other numbers do change, but none do. The June claim traces to `docs/discovery.md:121`, which describes the data, not the engine.
- **Suggested:** "Optional. If the shock runs into January, a note shows this customer's typical January spending. It doesn't change any number on the page."

### UT-20 · Medium · inaccurate · `app/ui/text.py:147`
- **Current:** "This runs into January, when spending is usually higher."
- **Why it misleads:** The engine works out this account's own January median and states it (`shock.py:363-364`). The UI replaces that with a general claim, which may be false for this customer. Their January can be lower.
- **Suggested:** Use the engine's figures: "This runs into January. This customer's typical January spending is {jan}, against {S} in a typical month."

### UT-21 · Low · inaccurate · `app/app_pages/shock_and_plan.py:142,228`
- **Current:** "100 means no change. EI pays 55%. Type any number." / "Default 3. Type any number."
- **Why it misleads:** The income box takes only 0 to 100 (`shock_and_plan.py:11`). The target box takes only 0.5 to 120 (`shock_and_plan.py:14`).
- **Suggested:** "100 means no change. EI pays 55%. Type 0 to 100." / "Default 3. Type 0.5 to 120."

### UT-22 · Medium · jargon · `app/ui/text.py:357`, shown at `app/app_pages/shock_and_plan.py:137` and in the chat
- **Current:** "The card gives no length, so this assumes 6 months, as on the first card."
- **Why it misleads:** It refers to "the card" and "the first card" from the judging script (`README.md`, example twists; ADR 0010). A newcomer has seen no cards.
- **Suggested:** "This scenario doesn't say how long, so it assumes 6 months, the same as 'Laid off, EI 55%'."

### UT-23 · Low · vague · `app/app_pages/shock_and_plan.py:147-148`
- **Current:** "Off. It starts off, to match the judges. When on, the extra runway in "Our numbers" caps EI at the weekly maximum. $729 a week is the 2026 maximum."
- **Why it misleads:** "The extra runway" doesn't say that a new row appears or that the main runway stays the same (`shock.py:257-278`).
- **Suggested:** "Off by default, so the main runway follows the brief. When on, 'Our numbers' adds a runway with EI limited to the weekly maximum ($729 a week in 2026). The main runway doesn't change."

### UT-24 · Low · inconsistent · `app/app_pages/shock_and_plan.py:22,151`
- **Current:** Preset "Rent or bills up" (sets a 15% rise on household bills) next to a box "Bills or rent up ($ a month)" (adds dollars to spending).
- **Why it misleads:** Two controls with near-identical names do different arithmetic (`shock.py:395-396`).
- **Suggested:** Preset "Bills up 15%". Box "Rent or bills up ($ a month, added to spending)".

### UT-25 · Low · vague · `app/app_pages/shock_and_plan.py:19-20`
- **Current:** "Laid off, EI 55%", "Furnace dies".
- **Why it misleads:** The names hide the sizes they set: 6 months, and 1 month of spending.
- **Suggested:** "Laid off, EI 55% for 6 months", "Furnace dies (1 month of spending)".

### UT-26 · Low · inconsistent · `app/app_pages/shock_and_plan.py:126` vs `app/assistant/chat_text.py:64`
- **Current:** "Cheatsheet: how to type a twist card in the chat" (Shock and plan) / "How to type a twist card" (Chat).
- **Why it misleads:** On Shock and plan, a typing guide for another page sits above the preset buttons, before the user has picked anything.
- **Suggested:** Use one title on both pages: "How to type a scenario in Chat". On Shock and plan, move it below the controls, or replace it with a link to Chat.

---

## D. Before and after (region D) and verdict

### UT-27 · Medium · vague · `app/app_pages/shock_and_plan.py:202`, `app/assistant/chat_text.py:27`
- **Current:** "Monthly gap  $X -> $Y" / "Runway A -> B. Monthly gap $X -> $Y."
- **Why it misleads:** "Gap" is undefined. Its sign is spending minus money in (`shock.py:400`), so a surplus shows as "-$500". A newcomer can't tell whether a negative gap is good or bad.
- **Suggested:** "Monthly shortfall (spending minus money in): $X before, $Y after. Below $0 means money in covers spending."

### UT-28 · Medium · missing-help · `app/app_pages/shock_and_plan.py:184,197`
- **Current:** Cards labelled "Runway", with no note.
- **Why it misleads:** The runway treats the shocked month as permanent (`shock.py:400-401`). It ignores "Income stays lower for (months)". The verdict above checks the chosen length separately (`shock.py:229-254`). Moving the months slider changes the verdict but not the runway, and that looks like a bug.
- **Suggested:** Caption under the cards: "Runway assumes the shocked month repeats until the buffer runs out. The line above checks the length you chose."

### UT-29 · Medium · vague · `app/app_pages/shock_and_plan.py:186-188,199-201`
- **Current:** "Money in", "Spending", "Buffer" / "Buffer left".
- **Why it misleads:** No period is given (these are monthly). "Buffer left" is the buffer after the one-off cost only (`shock.py:399`), not what's left at the end of the shock.
- **Suggested:** "Money in, a month", "Spending, a month", "Buffer after one-off cost".

### UT-30 · Low · jargon · `app/ui/text.py:128`
- **Current:** "No length was set, so there is no make-it answer."
- **Suggested:** "No length was set, so we can't say whether they last through it."

### UT-31 · Medium · vague · `app/assistant/chat_text.py:53`, `app/ui/cheatsheet.py:12`
- **Current:** Button "Until it runs out" / "laid off, EI {keep_pct}% until it runs out".
- **Why it misleads:** It reads as "until EI runs out", which is a fixed benefit period. The engine treats it as lower income with no end (`shock.py:211`, "The lower income is assumed to last the whole period"; `docs/inception/use_cases_chat.md:37`). Owner decision: OQ-2.
- **Suggested:** "No end date (lower income continues)".

---

## E. Our numbers (region E)

### UT-32 · High · inconsistent · `app/ui/text.py:215-217` vs `app/ui/profile_view.py:71`
- **Current:** Our numbers row "Bills on standing orders" with value "3.1 months". On Customer profiling, "Bills on standing orders" has value "$640".
- **Why it misleads:** The same label shows a runway on one page and a dollar amount on the other (`shock.py:291-300` vs `profile.py:390`). On Shock and plan, a reader expects dollars and gets months.
- **Suggested:** "Runway, bills rise applied to standing-order bills".

### UT-33 · High · inconsistent · `app/app_pages/shock_and_plan.py:107`, `app/ui/text.py:237,322`
- **Current:** Tile "Fixed costs" = F. Our numbers "Current fixed costs". Backup plan "Fixed costs, including bills added by the shock: $X a month".
- **Why it misleads:** One page shows three different dollar figures called fixed costs. F is the median of bills + insurance + loan payments, and can include finished loans (`profile.py:360,365`). Current fixed costs adds standing-order bills and only a running loan (`profile.py:390`). The backup figure is current fixed costs plus the bills rise (`plan.py:236`). The tile and the backup plan disagree, with no explanation.
- **Suggested:** Tile "Typical fixed costs (standard)". Backup: "Current fixed costs, plus the bills rise: $X a month". Keep "Current fixed costs" in Our numbers.

### UT-34 · Low · inaccurate · `app/ui/text.py:238`
- **Current:** "Bills, insurance and the loan payment if still running."
- **Why it misleads:** It leaves out the standing-order bills that don't show in household bills (`profile.py:390`, `max(bill_orders - H, 0)`).
- **Suggested:** "Bills (including standing-order bills not labelled as bills), insurance, and the loan payment if still running."

### UT-35 · Medium · vague · `app/ui/text.py:226`
- **Current:** "An illustration, not a forecast. In some accounts in the data, spending fell when income fell. This lowers spending that way. The judges' runway keeps spending flat."
- **Why it misleads:** "Some accounts" and "that way" don't say whose behaviour is copied or how much. The engine applies the response seen on mostly cash-only accounts, matched by buffer size (`shock.py:306,321-323`).
- **Suggested:** "An illustration, not a forecast. In past income drops in this data, mostly on cash-only accounts, spending fell too. This lowers spending by the amount seen for customers with a similar buffer. The standard runway keeps spending flat."

---

## F. Goal plan (region F)

### UT-36 · High · inaccurate · `app/ui/text.py:308`
- **Current:** "Keep the lowest balance above one loan payment ($P). It is now $L."
- **Why it misleads:** $L is the lowest daily balance in the last 6 months (`profile.py:377`; `plan.py:174-180`), not the balance now. The sentence also doesn't say why one loan payment matters. The engine note says a low point under one payment was a warning sign of default (`profile.py:457`).
- **Suggested:** "Keep the balance above one loan payment ($P) at all times. Its lowest point in the last 6 months was $L."

### UT-37 · Medium · inaccurate · `app/ui/text.py:278-279`
- **Current:** "At the actual change over the last 12 months ($604 a month, ours), 3 months of spending ($9,000) takes 8 months to save."
- **Why it misleads:** The months count only the amount still needed after the current buffer (`plan.py:141,146`, `needed = target - B`). The reader assumes the whole $9,000 is saved from zero.
- **Suggested:** "Saving $604 a month (the balance's actual average rise over the last 12 months), the remaining $4,800 to reach 3 months of spending ($9,000) takes 8 months."

### UT-38 · Medium · vague · `app/app_pages/shock_and_plan.py:236-238`
- **Current:** Heading "Savings path", with columns "Month" and "Balance".
- **Why it misleads:** The path follows the typical-month rate (I - S) from the buffer (`plan.py:160-161`). The first sentence above it leads with the actual-change rate, so the table and the headline disagree with no label. Owner decision: OQ-9.
- **Suggested:** "Savings path at the typical-month rate ($Y a month), starting from the buffer".

### UT-39 · Low · vague · `app/ui/text.py:260,263,266`
- **Current:** "That takes 15 months, more than 12 months." / "would reach $X in 12 months".
- **Why it misleads:** It doesn't say why 12 months matters. This is the plan horizon (`plan.py:324`, `horizon_months=12`).
- **Suggested:** "That takes 15 months, longer than the 12-month planning window."

### UT-40 · Medium · vague · `app/ui/text.py:366-367`, `app/ui/plan_text.py:74-75`
- **Current:** "The loan payment of $P a month isn't in the judges' typical spending yet, because the loan started recently, so the judges' figure doesn't rise when it ends in month N (ours)."
- **Why it misleads:** "The judges' figure" doesn't say which figure. It is the saving or gap, which gets no boost from the loan ending (`rates.py:94`, `bump_judges` is 0).
- **Suggested:** "This loan started recently, so its $P payment isn't in typical spending yet. When it ends in month N, the standard figures don't improve (ours)."

---

## G. Backup plan and loan end (region G)

### UT-41 · Medium · vague · `app/ui/text.py:363,368`, `app/ui/plan_text.py:42-43,70-73`
- **Current:** "Counting the loan ending in month N, the monthly gap falls by $X from then (ours)."
- **Why it misleads:** Month N is counted from the last month of data (`rates.py:18`; ADR 0006, line 13). The backup plan's months count from the start of the shock. The sentence assumes, without saying so, that the shock starts the month after the data ends. Owner decision: OQ-4.
- **Suggested:** "The loan's last payment is due in month N (counting from January 2026, the month after the data ends). From then the monthly shortfall falls by $X (ours)."

---

## H. Plan designer (region P)

### UT-42 · High · inaccurate · `app/ui/plan_text.py:17`, shown at `app/ui/plan_designer.py:79-80`
- **Current:** "Spending at its lean months (ours): +$1,200 a month"
- **Why it misleads:** The value is a saving rate: money in minus lean spending (`app/engine/rates.py:123`, `p.I - lean_spending`). It isn't a spending figure. The label tells the reader this customer spends +$1,200, which is wrong.
- **Suggested:** "Saving if other spending drops to its lean months (ours): +$1,200 a month"

### UT-43 · Medium · inconsistent · `app/ui/plan_text.py:17,36,48,57`, `app/engine/plan.py:295`
- **Current:** "lean months", "the lean-quarter level", "lean spending", "Lean budget", "the level of this account's lowest quarter of months".
- **Why it misleads:** Five names for one concept (`rates.py:63-65`, the 25th percentile of spending above fixed costs). None of them is defined where it first appears.
- **Suggested:** Pick one term, "lean months". Define it once: "Lean months: this customer's cheapest quarter of months, for spending above fixed costs."

### UT-44 · Medium · vague · `app/ui/plan_text.py:29-31`
- **Current:** "{rate}: {n} months." For example, "Actual change, last 12 months (ours): 14 months."
- **Why it misleads:** It reads as if the rate lasted 14 months. It actually means the goal is reached in month 14.
- **Suggested:** "{rate}: reached in month {n}." / "{rate}: never reached at this rate." / "{rate}: not reached within 120 months."

### UT-45 · Medium · missing-help · `app/ui/plan_text.py:46`, `app/ui/charts.py:158`
- **Current:** "Data stops in {last_month}, so month 1 is the month after." This only shows for accounts whose data ends early. The chart axis says just "Month".
- **Why it misleads:** For most customers, nothing says what month 0 or month 1 is. Month 0 is the end of the data, where the timeline starts from B minus any emergency cost (`app/engine/goals.py:144`).
- **Suggested:** Always caption: "Month 0 is now (the end of the data, {last_month}). Month 1 is the month after." Axis title: "Months from now".

### UT-46 · Medium · missing-help · `app/ui/charts.py:174-175`, `app/ui/plan_text.py:111-112`
- **Current:** The chart markers are bare letters F, G, B, O, E and L, with no key.
- **Why it misleads:** The caption names the events, but it never links them to the letters. Both "time off starts" and "time off ends" are O.
- **Suggested:** Add a key line under the chart: "F emergency fund reached · G goal reached · B goal bought · O time off starts or ends · E emergency cost · L loan paid off". Add a marker tooltip with the event name.

### UT-47 · Low · inconsistent · `app/ui/plan_text.py:21` vs `:68`
- **Current:** Checkbox "Emergency budget"; marker "Emergency cost"; input "Cost ($)".
- **Why it misleads:** The tick names a budget, but the input is a one-off cost paid at month 0 (`goals.py:39`).
- **Suggested:** Checkbox "Emergency cost today".

### UT-48 · Low · vague · `app/ui/plan_text.py:24-25`
- **Current:** "Deadline in months (optional)" (0 means none, `plan_designer.py:17`); "Interest, % a year (optional, default 0)".
- **Why it misleads:** It doesn't say that 0 turns the deadline off. It doesn't say what the interest is earned on: positive balances only, monthly (`goals.py:43`).
- **Suggested:** "Deadline in months (0 = no deadline)"; "Interest earned on savings, % a year (0 to 25)".

### UT-49 · Low · jargon · `app/ui/plan_text.py:18`, shown at `app/ui/plan_designer.py:81` and again at `app/ui/plan_text.py:317-318`
- **Current:** "Typical months come from different months, so they don't add up. The actual change is the headline."
- **Why it misleads:** "Headline" is internal language. When the rates disagree, the caption is shown twice.
- **Suggested:** "...so we lead with the actual change." Show it once.

### UT-50 · Low · vague · `app/ui/plan_text.py:77`, `app/ui/plan_designer.py:103-104`
- **Current:** "Wallets (ours)"
- **Why it misleads:** It doesn't say that the table shows month 0, at the actual-change rate only (`plan_text.py:363-365`).
- **Suggested:** "Savings pots today, at the actual change (ours)".

### UT-51 · Low · missing-help · `app/ui/plan_designer.py:76-78`
- **Current:** Shows the raw `InvalidPlanError` text, such as "target_months must be above 0, not 0." (`goals.py:200-216`).
- **Suggested:** Map each error field to a plain sentence: "The emergency fund target must be above 0 months."

### UT-52 · Low · vague · `app/ui/plan_text.py:59`
- **Current:** "Balance by month, one line per rate"
- **Suggested:** "Balance by month at each saving pace"

---

## I. Customer profiling page

### UT-53 · Medium · vague · `app/ui/profile_view.py:47`
- **Current:** "Middle month's change"
- **Why it misleads:** It reads as the change in the middle month of the data. It is the median monthly change (`profile.py:286`).
- **Suggested:** "Median monthly change (a typical month)".

### UT-54 · Medium · inconsistent · `app/ui/text.py:242`, `app/ui/profile_view.py:64` vs `app/app_pages/shock_and_plan.py:265`, `app/ui/charts.py:62`
- **Current:** "Lowest balance, last 6 months: -$310" / "Lowest month-end balance was $120 in Mar 2024." / chart label "Lowest: $120 in Mar 2024".
- **Why it misleads:** These are two different "lowest" figures: the lowest daily balance in the last 6 months (`profile.py:377`) and the lowest month-end balance in all months (`charts.py:53-56`). A newcomer sees two lowest balances that don't match.
- **Suggested:** "Lowest daily balance, last 6 months" and "Lowest month-end balance, all months".

### UT-55 · Low · vague · `app/ui/profile_view.py:65-66`
- **Current:** "Months below zero, last 6"
- **Why it misleads:** It counts months with at least one day below zero (`profile.py:396`), not months that ended below zero.
- **Suggested:** "Months with a day below $0, last 6".

### UT-56 · Low · vague · `app/app_pages/customer_profiling.py:122-124`
- **Current:** Column names generated from field names: "Cash withdrawals genuine", "Transfers out other", "Avg daily balance", "Min balance".
- **Suggested:** Explicit labels: "Cash withdrawals", "Other transfers out", "Average daily balance", "Lowest daily balance". These match the chart legend (`charts.py:14`).

### UT-57 · Low · vague · `app/ui/charts.py:104`
- **Current:** Tooltip title "Payee" for every slice, including "Left in the account".
- **Suggested:** "Where it went".

---

## J. Chat

### UT-58 · Medium · jargon · `app/assistant/chat_text.py:26`, used at `app/assistant/flow.py:127,140`
- **Current:** "⚙ engine call: `apply_shock(20111, Shock(income_cut=IncomeCut(0.55, 6)), through_months=6)`"
- **Why it misleads:** Python code appears first in every result, before the answer. A newcomer reads it as an error or debug output. Owner decision: OQ-6.
- **Suggested:** Put the answer first. Move the call into a collapsed "Show the exact calculation" line.

### UT-59 · Medium · jargon · `app/ui/cheatsheet.py:10-33,63`
- **Current:** The "Sets" column shows engine fields, such as `income_cut = IncomeCut({keep_pct}/100, {months})` and `one_off_spending_multiple = {n}`.
- **Suggested:** Replace it with a "Means" column in plain words: "Income falls to {keep_pct}% for {months} months, then stops."

### UT-60 · Medium · inaccurate · `app/ui/cheatsheet.py:50`, shown on Chat at `app/app_pages/assistant.py:59-60`
- **Current:** 'a calendar month, such as "in January" — use More options on this page'
- **Why it misleads:** On the Chat page there is no More options section. It is on Shock and plan (`shock_and_plan.py:160`). `T.unsure_month` gets this right (`chat_text.py:34`).
- **Suggested:** 'use More options on the Shock and plan page'.

### UT-61 · Medium · jargon · `app/assistant/chat_text.py:19`
- **Current:** "How much of their usual income does EI keep? The README uses 55%."
- **Why it misleads:** "The README" means nothing to a user.
- **Suggested:** "How much of their usual income does EI pay? It's usually 55%."

### UT-62 · Medium · missing-help · `app/assistant/chat_text.py:40,44`, `app/assistant/controls.py:57-59`
- **Current:** Button "Send to the controls"; then "Sent. The Shock and plan page now has these sizes."
- **Why it misleads:** It doesn't say that the button switches pages. It also doesn't say that it turns off the EI weekly maximum and clears the start month (`controls.py:57,59`). A user who had either set loses them without warning.
- **Suggested:** Button "Open on Shock and plan". Reply: "Sent to Shock and plan. The EI weekly maximum is off and the start month is cleared." Owner decision: OQ-8.

### UT-63 · Low · vague · `app/assistant/chat_text.py:17`
- **Current:** "Mix"
- **Suggested:** "Job loss + bills up". This matches `state.py:45`.

### UT-64 · Low · vague · `app/assistant/chat_text.py:24-25`
- **Current:** "{value} is outside what the engine takes..." / "The engine didn't accept {field}. Pick that size again."
- **Why it misleads:** "The engine" is internal. The second message gives no reason.
- **Suggested:** "{value} won't work: {size} must be {range}." / "That size for {field} can't be used. Pick a size or type another."

### UT-65 · Low · vague · `app/assistant/chat_text.py:39,43`
- **Current:** Button "New customer". Its reply is only "Type the new account number in the box at the top."
- **Suggested:** Button "Switch customer".

### UT-66 · Low · vague · `app/assistant/chat_text.py:60`
- **Current:** Text box label "Other"
- **Suggested:** "Or type a size"

---

## K. Findings page

### UT-67 · High · inaccurate · `app/ui/findings_view.py:18-19`
- **Current:** Metric "Below $0 after 3 months" with value "31 of 493 predicted".
- **Why it misleads:** "31 of 493" reads as 31 out of the 493 predicted cases. The two counts are independent, both over all events (`app/engine/findings.py:67`). The 31 may include events the formula didn't predict.
- **Suggested:** Label "Below $0 after 3 months: formula vs real"; value "493 predicted, 31 real".

### UT-68 · Medium · vague · `app/ui/findings_view.py:17,20,22,25`
- **Current:** "Spending kept, median", "customers kept a median of 50% of their usual spending", "Spending kept during a real income drop".
- **Why it misleads:** "Kept spending" reads as "spending they kept up". It actually means spending during the drop as a share of usual.
- **Suggested:** "Spending during the drop, % of usual (median)"; "customers spent a median of 50% of their usual amount".

### UT-69 · Medium · missing-help · `app/ui/findings_view.py:16`, `app/app_pages/findings.py:28`
- **Current:** Metric "Real income drops". The definition only appears in the evidence caption at the bottom of the page (`app/engine/response.py:113`).
- **Suggested:** Caption under the metrics: "A real income drop: deposits fell below 55% of normal for at least 3 months."

### UT-70 · Low · inconsistent · `app/ui/findings_view.py:25-26`
- **Current:** Column "Starting buffer", tiers "Under 2 months" and so on.
- **Why it misleads:** Here the buffer is month-end balance divided by recent median spending (`response.py:41`). Elsewhere in the app, Buffer is a 6-month average in dollars.
- **Suggested:** "Starting balance, in months of usual spending".

### UT-71 · Low · vague · `app/ui/findings_view.py:30`
- **Current:** "197 of 448 running loans don't show in typical spending yet, a median $2,545 a month."
- **Suggested:** "...yet. Their median payment is $2,545 a month."

### UT-72 · Low · vague · `app/ui/text.py:358-360`
- **Current:** "Method notes are in the docs folder."
- **Why it misleads:** An app user has no docs folder.
- **Suggested:** Link to the repo's `docs/` folder, as the Findings references do (`findings_view.py:35`).

---

## L. Documentation that disagrees with the app

### UT-73 · Low · inconsistent · `app/README.md:5,8`
- **Current:** "the plan designer ("If you adjust")" / "Findings: what the data shows across all accounts, with the customer's own numbers beside it."
- **Why it misleads:** On screen the plan designer is titled "Plan designer" (`plan_text.py:13`). "If you adjust" is a runway row in Our numbers (`text.py:225`). The Findings page uses no customer (`app_pages/findings.py:1`). Either the README is out of date or a planned feature is missing (OQ-10).
- **Suggested:** Fix the README to match the app, or log the missing feature.

---

## Open questions for the stakeholder

Each of these needs an owner decision. The intended meaning can't be settled from the code or docs.

1. **OQ-1. On-screen word for the brief's formula (UT-06, UT-07).** Should the app keep saying "the judges'" and "(ours)"? The `README.md` says "How judges calculate the numbers", and the demo audience is the judges. **Recommended:** use "standard" and "our estimate", with a one-line definition, because the app should make sense outside the judging room. **Blocks:** about 40 strings.
2. **OQ-2. "Until it runs out" (UT-31).** Does it mean lower income with no end, which is what the engine computes (`shock.py:211`)? Or the EI entitlement period, which would need a length (`docs/shock_sizing.md`)? **Recommended:** no end, relabelled "No end date". **Blocks:** chat button, cheatsheet, verdict wording.
3. **OQ-3. June in the start-month caption (UT-19).** Should the engine also flag June, as `docs/discovery.md:121` suggests? Or should the caption drop June? **Recommended:** drop June from the caption. Adding a June fact is an engine change. **Blocks:** UT-19 wording.
4. **OQ-4. Month numbering (UT-41, UT-45).** Is month 1 of a shock always the month after the data ends (January 2026)? The loan payoff month N assumes so (`rates.py:18`), but the Shock and plan page never says so. With a start month set, the two can disagree. **Recommended:** yes, and say so on screen. **Blocks:** loan-end lines, plan designer axis.
5. **OQ-5. Pension label threshold (UT-17, UT-18).** Should "Pension" need pension deposits to be most of the income, or any amount (current, `profile.py:333-334`)? **Recommended:** keep the engine rule, but word it as "receives a pension". **Blocks:** notes, Findings F6, questionnaire.
6. **OQ-6. Engine call line in the chat (UT-58).** Is the visible Python call meant for the live judging demo? **Recommended:** collapse it under "Show the exact calculation". **Blocks:** chat layout and transcript.
7. **OQ-7. Who the screens are for (UT-05, UT-09, UT-59).** Bank staff, a financial coach, the judges, or the customer? This decides whether "stakeholder", the formula letters and the engine field names stay. **Recommended:** bank staff. **Blocks:** tone across all pages.
8. **OQ-8. Send to controls and the EI maximum (UT-62).** Should sending from the chat keep the user's EI weekly maximum and start month, instead of resetting them (`controls.py:57-59`)? **Recommended:** keep them, or warn as suggested. **Blocks:** UT-62 wording, and possibly a behaviour change.
9. **OQ-9. Savings path rate (UT-38).** Should the Savings path table follow the actual-change rate, to match the first goal sentence? Or should it stay on the typical-month rate (`plan.py:160-161`)? **Recommended:** label it now; decide the rate later. **Blocks:** UT-38 heading.
10. **OQ-10. `app/README.md` vs the app (UT-73).** Is the Findings page meant to show the loaded customer's numbers beside the all-accounts figures? **Recommended:** fix the README if not. **Blocks:** the README and possibly the scope of Findings.
