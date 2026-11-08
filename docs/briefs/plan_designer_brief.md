# Brief: Plan designer, loan-end event, fixes and copy refinement

Owner's brief, 2026-11-07. Branch `feature/guided-chat`; nothing is committed. Pipeline: inception, then validation by the main session, then elaboration, then a build team (software-engineer with sr-devs). Every stage reads this file first.

## Fixed rules (unchanged from the project)

- The judges' numbers (I, F, S, B, H, P, runway) never change. An independent check on 2026-11-07 matched the engine to the README definitions on all 4,500 accounts and on 5 shocks, with 0 mismatches. Keep it that way.
- Everything new is labelled "ours" and sits beside the judges' numbers.
- Every number comes from the engine. The UI and the chat only display.
- `app/engine/` stays free of Streamlit. `app/assistant/` stays free of Streamlit, network and language-model code.
- Keep the current page structure. Add new sections; don't rework existing ones.

## Part 1: Plan designer (new feature)

At the **bottom of the Shock and plan page**, add a "Plan designer" section with a checkbox for each plan. Ticking one opens its inputs. Below the plans is one combined timeline.

| Plan | Inputs (the `{slots}` follow the cheatsheet style) | Answers |
| :-- | :-- | :-- |
| Savings goal | `{goal_name}` (for example "car"), `{amount}` (for example $60,000), optional `{deadline_months}` | Months to save at each savings rate (see below). If there's a deadline: the monthly saving needed, the cut needed, and that cut as a share of flexible spending and against the lean-quarter level. If the rate is 0 or below: never at the current rate, plus the cut needed |
| Time off work | `{months_off}` (for example 24) | Amount needed = `months_off` × S, also shown at lean spending. Months to save it. Then a check with the engine's existing shock, `IncomeCut(0, months_off)`, on the projected balance at the start of the time off: do they make it? |
| Emergency budget | `{cost}` (for example $10,000) | Reuse the one-off shock: buffer left. If the buffer can't cover it, the instant budget: the backup plan's ordered steps, the lean monthly budget, and the months to rebuild the buffer and the emergency fund |

**Savings rates** are shown side by side and labelled:
1. The judges' median surplus, I − S.
2. The actual balance change over the last 12 months. This is the **headline**, because the medians come from different months and don't add up.
3. Savings with cuts down to the customer's lean quarter. This reuses `LEAN_QUANTILE` from `plan.py`.

Owner defaults (marked as changeable):
- **Interest** is 0%, with an optional `{interest_pct}` a year.
- **The order is fixed:** the emergency fund (the existing goal plan target) comes first, then the goals in the order they're ticked. A goal is never paid for out of the safety net.

**Timeline:** month-by-month balance from B, for at least the longest plan horizon, up to 120 months. It has markers for:
- emergency fund reached;
- each goal reached and bought (the balance drops);
- time off start and end;
- the emergency cost;
- loan paid off (Part 2).

Each line is one savings rate. There's a table view for accessibility.

**Edge cases to cover:**
- no surplus;
- B ≤ 0;
- short history;
- pension income;
- `data_stops_early`;
- deadline shorter than possible;
- amount 0;
- goal already affordable from the money above the emergency fund;
- a time off length beyond the 120-month cap.

**Chat:** page only for now. The chat ("save $60k for a car in 2 years") is **stretch**. Design the engine function so the chat can call it later, and add cheatsheet rows only if the chat ships.

## Part 2: Loan-end event (fix)

Today the plans assume a running loan's payment P lasts for ever. Of the 448 running loans (status C or D):
- 60 end within 6 months of 2025-12;
- 125 end within 12 months;
- 235 end within 24 months;
- 335 end within 36 months.

The median payment is $2,438. The payoff month is `loan_start + duration_months`, compared with the last data month.

- In the plan designer and the timeline, monthly saving rises by P from the payoff month. Show a "loan paid off in month N" marker, and a line such as "31 months; 22 counting the loan ending in month 9 (ours)".
- The backup plan's month-by-month duration check takes account of the shortfall falling by P after the payoff month. This is **ours** and doesn't change the judges' runway (the README runway doesn't use P).
- Status D (running, in debt): the payoff month is the scheduled one, not guaranteed. Add a note.
- Decide whether this needs a new ADR (it changes what the backup plan's verdict means) or an amendment to ADR 0001.

## Part 3: Fixes carried over from the J4 build

- **AC-6 conflict:** AC-6 expects the chat to greet 20134 with "120.0 months", but the chat uses `summary_line`, which says "lasts 120 months or more". Recommend one, align AC-6 or the copy, and keep "No shortfall" off capped runways.
- **ADR status word:** 0001 and the ADR index rules say "accepted"; 0002 to 0005 say "approved". Pick one word for all.
- **Out-of-date counts:** the tests now number 829, not 232 or 236. Update `scope.md` GO-2 and the status line, `app/README.md`, and the Devpost draft (`project_dev-post.md`).
- **Devpost "rescued" count:** the draft says 1,526 accounts; the engine gives 1,548. The 22 `no_buffer` accounts are rescued after `cover_buffer`. Pick one definition and use it in the app and on Devpost.
- **Missing copy row:** `K.g_oneoff` (cited in J3 4e) has no row in the copy deck.

## Part 4: Text refinement (copy pass)

- Settle NEW-COPY-1 to NEW-COPY-10 (`docs/architecture/j4_chat.md` §9 and the J4 build report):
  - the `{plain}` and `{what}` phrases;
  - the `${g0}` double dollar sign in `T.change_line`;
  - the singular forms ("for 1 month", "1 month of spending");
  - the `T.stack_replace` kind words;
  - the change-size button label "{size}: {shown}";
  - "what happens after".
- Write the copy for the whole plan designer and the loan-end lines in the existing copy-deck style: short, plain, numbers first, and "(ours)" on our figures.
- Review the existing on-screen sentences for consistency, plurals and the dollar format. Only change wording where a rule is broken, and list every change.

## Deliverables by stage

- **Inception:** requirements and rules (new IDs), summary and fully dressed use cases, domain and glossary, wireframes for the plan designer and its states, the copy deck for Parts 1, 2 and 4, data feasibility checked against the CSVs, MVP and stretch, acceptance criteria, and updates to the out-of-date docs for Part 3. List the open questions.
- **Elaboration:** engine modules (for example `engine/goals.py` and the loan-end change in `plan.py`), frozen interfaces, sequence diagrams, ADRs, a test map (including a sweep over all accounts), and work packages for parallel sr-devs with no file overlap.
- **Build:** tests first. Run the full suite with `.venv/bin/python -m pytest app/tests -q -p no:cacheprovider`, and every test must pass. No commits.

## Part 5: README review fixes and owner decisions (2026-11-07)

Source: the BA and QA reviews of `README.md`, verified by the main session. The owner accepted every recommendation.

### Owner decisions (settled)

| # | Question | Decision |
| :-- | :-- | :-- |
| D1 | Twist 1: "about 0 months short" next to a judges' runway of 6.0 (18 accounts, for example 21271, unrounded 5.956) | Keep the verdict exact (unrounded path). When the rounded shortfall is 0.0, the copy reads **"less than 0.1 months short"** |
| D2 | Twist 3 gives no length | Assume **6 months, as on card 1**, and **say so on screen and in the chat** ("assumed 6 months, as on the first card") |
| D3 | "In the same month" | Both changes start together. **No calendar start month** |
| D4 | Furnace "a full month of typical spending" in a mix | **S before the shock**. State it on screen and in the chat, with the dollar amount |
| D5 | Capped runway, gap > 0 (225 accounts) | Show **"120.0 months"**, the literal formula output. **This overrides inception's AC-6 change**: AC-6 and `summary_line` copy must say 120.0 months. "No shortfall (120+)" only when gap ≤ 0 |
| D6 | "Bills" in Know the customer | **H** (the judges' figure), with the standing-order figure beside it, labelled ours. This is already built |
| D7 | Existing goal plan's saving rate | **Lead with the actual 12-month change**. Keep I − S beside it, labelled as the judges' figure. This is consistent with Part 1 |
| D8 | Unlabelled standing orders and transfers in the backup plan | Still cuttable. Word the step "**if these aren't rent or bills**" |
| D9 | Devpost Sources | **Only what the product uses**: the CTU dataset (https://relational.fel.cvut.cz/dataset/Financial) and the canada.ca EI benefit-amount page. Add StatCan only if a sourced preset ships |
| D10 | The one "biggest finding" for the pitch and write-up | **Spending doesn't stay flat after a shock** (735 income drops; customers kept a median of 50% of their spending; the formula predicted 493 below $0 after 3 months; 31 were) |
| D11 | Sourced "Realistic layoff" preset | **No** (stretch only, if time allows) |
| D12 | OI-15: 197 running loans have $0 of P in typical spending | Add P back at payoff **only where P is already in typical spending**. On the 197 accounts, show **descriptive text**: the loan payment isn't in their typical spending yet (the loan started recently), so the payoff doesn't raise their savings in the plan. Label it ours |
| D13 | "Rescued" count | **1,526 by cuts, plus 22 more if the lender agrees** to pause the loan (`ask_lender`), 1,548 in all. Verified by the main session. Use this wording in the app and on Devpost |

### Fixes to build

| # | Severity | Fix | Where (from the reviews) |
| :-- | :-- | :-- | :-- |
| R1 | High | D1 copy: "less than 0.1 months short" | `app/ui/text.py:117`; the chat via `replies.result_lines` |
| R2 | High | Submission: Sources and Credits sections, a "Biggest finding" heading (D10), stale lines (three pages, 829 tests, D13 count, "If you adjust" is built, the "40% of savers" basis stated: 1,038 of 3,309 accounts with a surplus). The footer credit names PKDD with the CTU link, plus GoC for the EI maximum | `project_dev-post.md`, `app/app_pages/shock_and_plan.py` footer |
| R3 | High | A small **Findings** panel or page for the 1-minute pitch, showing D10 from existing engine or discovery numbers. MVP is one chart plus three numbers | New, in the elaboration design |
| R4 | Medium | "X months, down from X months" when nothing changed (551 times; 20111 with bills up). Copy: "unchanged at X". Also "down from No shortfall" with a capital N mid-sentence | `app/ui/text.py:120` |
| R5 | Medium | Parser: "half a year" → 6 months (today it gives 12); number words above twelve ("fifteen percent"). Add both to the PT table and the cheatsheet slots | `app/assistant/parse.py:19`, `docs/design/ux/chat_parser.md` |
| R6 | Medium | The chat result states the one-off in dollars and that it's based on spending before the shock (D4), plus income and spending after the shock | `app/assistant/replies.py:52-65` |
| R7 | Medium | D2 note on the page and in the chat whenever the length was assumed | page region C/D, chat replies |
| R8 | Medium | D7 for the existing goal plan | `app/engine/plan.py:126-151`, `text.py` goal lines |
| R9 | Medium | D8 wording on backup step 2 and on the flexible-spending step | `plan.py:231-234`, `text.py` |
| R10 | Low | Plurals: "1 months" | `text.py:113, 117, 251, 282` |
| R11 | Low | Explain "0.0 months" (positive B, under 0.05 months) vs "0 months" (B ≤ 0). "Income still covers spending" when I = S = 0 should read as no activity | `text.py` |
| R12 | Low | Pin the root `requirements.txt` to `app/requirements.txt`. Set `gatherUsageStats = false` in `.streamlit/config.toml` | root, `app/.streamlit/config.toml` |
| R13 | Low | Accept "20,111" (strip commas) as a typed ID | `app/engine/profile.py:216` (`parse_account_id`) |
| R14 | Low | `assumption_line` always says "we assume no income", even for `income_returns`. Fix it even though no UI path reaches it yet | `text.py` ~143 |

Tests to add, with the review's list:
- a sentence sweep over all accounts × presets that bans "about 0 months short", "1 months" and "down from X" when before equals after;
- parser cases for "half a year" and "fifteen percent";
- `result_lines` contains the one-off dollars;
- `result_lines` and `greeting` swept over every account;
- 49637 (runway rounds to 0.0 but isn't 0);
- typed IDs "20,111" and "20111.0";
- a `warm_up` timing test;
- bills up 50% and 100% sentence checks.

### Part 5b: specialized QA additions (2026-11-07)

The oracle matched all 4,500 accounts on 13 shocks, with 0 mismatches. The mutation check caught 11 of 16 mutants. Oracle and vectors: `/private/tmp/claude-501/-Users-mikha2il3ajaj-Projects-datathon-Tangerine/e61e5f6a-f979-4c28-9acf-134c93200464/scratchpad/qa2/`.

| # | Severity | Fix |
| :-- | :-- | :-- |
| R15 | Major (test gap) | Add a test that P = 0 for finished loans (status A or B). Today a mutant that treats A or B as running passes all tests (31 B and 203 A loans exist) |
| R16 | Major (test gap) | Add a test for the EI-max capped income. Example: 20111 at keep 0.30, where `ei_capped.income_after` = $1,901.82. A mutant that uses `p.I` survives |
| R17 | Major (test gap) | Pin `through_months` at the call sites. Add kwargs tests for the page's `apply_shock`/`make_plan` and for `plan.py`. Three call-site mutants survive, because `apply_shock` falls back to `cut.months` |
| R18 | Major (coverage) | Turn the QA oracle into the permanent judges-parity test over all accounts × 13 shocks: the 5 base shocks plus EI 40%, income to 0, bills +50% and +100%, one-off 2×S and $10,000, rent +$300, and the triple mix |
| R19 | Minor | `summary_line` says "spends slightly more than comes in" when I = 0 (for example 49900). Word it for no income |
| R20 | Minor | When the one-off equals B exactly (20111 with $17,612), the copy reads "bigger than the buffer". Write "uses up the whole buffer" |
| R21 | Minor | "Lasts 0.0 months" when the buffer is positive (41 cases, for example 32179 at EI 40%, buffer $120). Write "under 0.1 months" in the sentence and keep the label (merge with R11) |
| R22 | Minor, latent | `formulas.money(-0.3)` returns "-$0". Make it "$0" (used in the engine's warning and fact messages) |

## Part 6: owner answers to the elaboration questions (2026-11-08)

| Question | Owner answer | Status |
| :-- | :-- | :-- |
| NEW-SCOPE-1: do the rates rise at loan payoff on the 197 recent-loan accounts? | "Logically, if the loan is paid off it should raise their saving." The BA is analysing this against D12 | **Pending the BA** (Part 7) |
| NEW-SCOPE-2: do deadline figures ignore the loan end? | Reframed as a **savings-wallet concept**: a goal is a wallet that fills up, and when it reaches the target the plan is accomplished. The BA is analysing it | **Pending the BA** (Part 7) |
| NEW-SCOPE-3: interest cap | Cap **25% a year, modifiable** (a named constant the owner can change). The **default rate is 0%** | Settled |
| NEW-SCOPE-4: limit D2's "assume 6 months" to card 3's shape? | **No.** "Job loss = laid off, or possibly EI = 0; nothing needs to change." The BA confirms the parser reading | **Pending the BA** (Part 7) |
| NEW-SCOPE-5: Findings as a fourth page? | **Yes.** Build it from the knowledge in `discovery.ipynb`, `know_the_customer.ipynb` and `make_a_plan.ipynb` | Settled |
| NEW-SCOPE-6: test suite time | Fix the tests that need it and add new ones where needed, **focused on the engine**. No `slow` marker requested | Settled |
| NEW-SCOPE-7: rescued count, precomputed or live? | **Computed live in the app** (cached after the first run). The owner warms the app before judging, so no precomputed file | Settled |

## Part 7: BA analysis (2026-11-08)

Source: the BA's analysis of the three pending owner answers in Part 6 (NEW-SCOPE-1, 2 and 4). Data: `data/monthly_summary.csv` and `data/loans.csv` through the engine's `get_profile` and `account_flows`. Running = status C or D (448 loans). Payoff month N = `loan_start` month + `duration_months` − the account's last data month (ADR 0006). Scratch scripts: `/private/tmp/claude-501/-Users-mikha2il3ajaj-Projects-datathon-Tangerine/e61e5f6a-f979-4c28-9acf-134c93200464/scratchpad/ba3/`.

### Summary

| # | Question | Result | Status |
| :-- | :-- | :-- | :-- |
| Q1 | Does paying off the loan raise savings on the 197 recent-loan accounts? | **There's no conflict.** The owner is right for the actual and lean rates, because the money really leaves the account now. D12 is right only for the judges' I − S, because S never contained P. Each rate rises by the part of P it already contains. D12's "doesn't raise their savings in the plan" narrows to "doesn't raise the judges' rate" | Settled by logic and data. The owner confirms only |
| Q2 | Savings wallet | Each goal is a wallet, filled in the fixed order with the fund first. Reached = accomplished = bought in that month. The wallet is a way of presenting ADR 0008's single balance, so it changes no months. **The loan bonus flows into the wallet, so months-to-goal and the deadline cut both count the loan end**, shown beside the figure without it. This reverses ADR 0008 decision 5 | Recommended. One question for the owner |
| Q3 | Layoff with no EI given | Recommend reading (a): keep the parser and ADR 0010 as designed | Stakeholder question, one word |

### Q1. Loan payoff and the three saving rates

**What each rate already contains.**

| Rate | Built from | Is P inside it? | Rise from month N |
| :-- | :-- | :-- | :-- |
| actual (headline) | mean of `money_in − money_out` over the last 12 rows. `loan_payments` is part of `money_out` (README) | Yes, for every month of the last 12 that had a payment. Inside = mean of `loan_payments` over the last 12 rows | `bump_actual = min(P, mean of loan_payments over the last 12 rows)` on **every** running loan, the 197 included |
| judges | I − S, where S = median `money_out` over the whole history | Only as far as the lifetime median holds it. Proxy: `loan_median` | `bump_judges = min(P, loan_median)`. That's 0 on the 197, because their S was taken mostly from months before the loan |
| lean (ours) | I − (S − lean_cut), with lean_cut = max(flexible − lean_above, 0). flexible = max(S − current_fixed_costs, 0), and current_fixed_costs includes P. lean_above excludes loan payments | Yes, P comes in through current_fixed_costs, so lean spending = min(S, Fx + P + L) | `bump_lean = min(S, Fx + P + L) − min(S, Fx + L)`, where Fx = current_fixed_costs − P and L = lean_above (the hidden-bills-adjusted value from ADR 0007). That's P unless S caps it |

**Data: months of loan payments in the last 12 rows.** Every paying month in these rows paid exactly P.

| Group | Accounts | Months with a payment in the last 12 rows | Actual rate holds all of P | Last row pays P | Judges rise | Lean rise |
| :-- | --: | :-- | --: | --: | :-- | :-- |
| `loan_median == 0` (the 197) | 197 | 1:15, 2:7, 3:14, 4:12, 5:8, 6:17, 7:22, 8:16, 9:9, 10:12, 11:24, 12:41. **All 197 have at least 1**; the median share of P inside is 0.67 | 41 | 187 | 0 on all 197 | full P on 166, part of P on 29, 0 on 2 (38528 and 52185, where S is below fixed costs) |
| other running loans | 251 | 12 of 12 on 225; 3 to 11 on 26 | 225 | 249 | full P on 235, part on 16 | full P on 251 (22609 is $0.13 short, which is rounding) |

The loans in the 197 started 0 to 31 months before the last data month (median 8). For the other 251 it's 7 to 59 months (median 25).

**Conclusion.** D12 was written as if "not in typical spending" meant "not in any rate". That holds only for S. The actual 12-month change has P inside it on all 197, fully on 41 and partly on 156. Lean spending is built bottom-up from current fixed costs, which carry P. If the rate doesn't rise at payoff, it understates the saving the customer will really have. If it rises by the full P, it double-counts on the judges' rate. So both statements hold, each for different rates.

**Rule (testable).**

- **LE-1:** For a running loan, from month N, `actual` rises by min(P, the mean of `loan_payments` over the last `actual_months` rows). This includes the 197.
- **LE-2:** `judges` rises by min(P, `loan_median`). On the 197 that's exactly 0.
- **LE-3:** `lean` rises by `min(S, Fx + P + L) − min(S, Fx + L)`. It's always between 0 and P.
- **LE-4:** With no running loan (status A or B, or no loan), every rise is 0 (R15).
- **LE-5:** On the 197, the D12 line is shown, reworded for the judges' rate only. Draft: "The loan payment of {P} a month isn't in the judges' typical spending yet, because the loan started recently, so the judges' figure doesn't rise when it ends in month {N} (ours)."
- **LE-6:** The backup plan's loan-end check keeps `bump_judges`, because the shocked gap is built from S (ADR 0006 decision 3). It stays `not_in_spending` on the 197, and the D13 count is unchanged.

| Account | Group | P, N | actual → from month N | judges → from N | lean rise |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 95548 (C) | one of the 197; 6 of 12 rows paid | $2,956.31, 42 | $447.37 → **$1,925.53** (+$1,478.16) | −$101.63 → −$101.63 (+$0) | +$2,956.31 |
| 60630 (C) | one of the 197; 2 of 12 paid; S caps lean | $2,201.82, 11 | $1,324.87 → $1,691.84 (+$366.97) | +$0 | +$597.81 |
| 66505 (C) | other; 12 of 12 paid | $1,982.83, 17 | $815.23 → $2,798.06 (+$1,982.83) | −$950.62 → $1,032.22 (+$1,982.83) | +$1,982.83 |
| 20111 (D) | other; 10 of 12 paid | $2,330.19, 36 | −$747.89 → $1,193.83 (+$1,941.72) | −$2,260.22 → +$69.84 (+$2,330.06) | +$2,330.19 |

**Known limits.** These are notes, not changes:

1. On the 156 of the 197 whose loans have fewer than 12 paid rows, the actual rate **before** payoff overstates the saving going forward by P × (12 − k) ÷ 12, where k is the number of paid rows. The loan is now paid every month. D7 keeps the literal 12-month change, so no change is proposed.
2. For 31 of the 158 loans that started within the last 12 rows, the start month's money in is at least half the loan amount. It may be the loan being paid out, which would lift the actual rate. Question for the owner (low): should the plan note this?

### Q2. The savings-wallet model

**Sources:**

- Part 6: "a goal is a wallet that fills up, and when it reaches the target the plan is accomplished".
- Part 1: "each goal reached and bought (the balance drops)", the fund first, "never paid for out of the safety net".
- Part 2: "In the plan designer and the timeline, monthly saving rises by P from the payoff month".

**Rule (WL-1 to WL-9):**

- **WL-1:** There is one wallet per item, in the fixed order: the emergency fund (target = `target_months` × S), then the items in tick order. A time off's wallet target is `months_off` × S.
- **WL-2:** Each month's saving (the rate, plus the Q1 rise from month N, plus interest on a positive balance) goes into the first wallet that isn't full. Month 0 puts B − the emergency cost in, in the same order. So money above the fund goes straight to goal 1, which covers the "already affordable" edge case.
- **WL-3:** A wallet is shown as the one balance split up. The fund wallet = min(balance, fund target), which may be negative. The wallet in progress = max(balance − fund target, 0). Wallets later in the order show $0, and goals already bought show $0 and "accomplished". **The months are exactly ADR 0008's**; the wallet is presentation only.
- **WL-4:** A goal is **accomplished** in the month its wallet reaches the target. It's bought in the same month: the wallet empties, and the balance drops by the amount (Part 1 isn't overridden). Contributions move to the next wallet from the next month.
- **WL-5:** The time-off wallet is spent over the time off: no income, spending S less `bump_judges` after N. Later wallets wait until it ends (unchanged).
- **WL-6:** **The loan bonus flows in.** Months-to-goal count the loan end. The timeline line is the with-loan run, and the figure without the loan end is shown beside it ("31 months; 22 counting the loan ending in month 9 (ours)"). Status D adds `P.loan_d`.
- **WL-7:** The **monthly saving needed for a deadline D** is the level monthly amount into savings that fills this wallet by month D, the earlier wallets first. At 0% interest it's `need ÷ D`, with `need = max(fund + earlier amounts + amount − (B − cost), 0)`. That's unchanged, and it doesn't depend on the loan.
- **WL-8:** The **cut needed** is shown twice when N ≤ D: without the loan end, `max(need ÷ D − rate, 0)` (unchanged), and **counting it**, `max((need − Σ_{t=1..D} rate.at(t, N)) ÷ D, 0)`. With interest, it's the smallest level cut that reaches `need` by D on the with-loan run, to the cent. When N > D, only one figure is shown. This replaces ADR 0008 decision 5 and NEW-COPY-27.
- **WL-9:** **Shocks.** `design_plan` takes no shock (RU-11). The only cost inside the plan is the emergency at month 0 (OI-18). By WL-3 it shows as coming out of the wallet in progress first, then the fund. Either way of splitting it gives the same months, because the fund must be whole before any goal wallet fills.

**Consequences:**

- Every months-to-goal and timeline figure is unchanged.
- Deadline answers gain a second cut figure.
- The page gains wallet amounts and an "accomplished" state.
- The cautious reading (no loan in the deadline) is still visible, as the first figure.

**Worked examples** (headline actual rate, 0% interest, 3-month fund, a $60,000 car):

| Account | B, fund target | Rate → after N | Fund wallet full | Car accomplished | Deadline | Needed a month | Cut: no loan · counting the loan |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 66505 (C, N 17) | $45,648; $78,848 | $815.23 → $2,798.06 | month 41; **24** counting the loan | month 115; **45** counting the loan | 36 months | $2,588.89 (need $93,200) | $1,773.66 · **$672.08** |
| 20111 (D, N 36) | $17,612; $25,799 | −$747.89 → $1,193.83 | never; **64** counting the loan | never; **115** counting the loan | 24 months (AC-12) | $2,841.12 (need $68,188) | $3,589.01 · $3,589.01 (N > D, one figure) |
| 20111, deadline 48 | | | | | 48 months | $1,420.56 | $2,168.45 · **$1,642.57** |

On 20111 the fund wallet goes negative, to −$8,564 at month 35, before the loan ends. WL-3 shows it as a negative fund wallet. A cut is needed in every case.

**Question for the owner:** "Deadline cut: show it counting the loan end too, beside the cautious figure (recommended), or keep only the cautious figure?"

### Q3. Layoff with no EI given (NEW-SCOPE-4)

Owner's words: "**No.** Job loss = laid off, or possibly EI = 0; nothing needs to change."

| Reading | Meaning | PT-04 (card 3) | PT-12 "laid off" | PT-19 "laid off, no EI, for 3 months" | What judges see |
| :-- | :-- | :-- | :-- | :-- | :-- |
| (a) as built | The sentence lists what counts as a job loss. The parser already counts "laid off" and "no EI" as one (`_JOB_KW`, `_NO_INCOME`). "Nothing needs to change" = keep ADR 0010 | `ok` `IC(0.55, 6)`, assumed, shown "(assumed)" | `partial`: asks the keep %, then the months | `ok` `IC(0, 3)` | Card 3 runs at once with a stated assumption. A bare "laid off" gets two short questions |
| (b) EI defaults to 0 | "Laid off" with no EI = income to $0 | unchanged (EI given) | asks the months only. If "No" also means the 6 months is assumed for every job loss, it's `ok` `IC(0, 6)` assumed | unchanged | A bare "laid off" runs at once at $0 income, harsher than card 1's 55%. It's a silent default, which ADR 0004 avoids. It needs a new PT row and an ADR 0010 change |

**Recommendation: (a).** "Nothing needs to change" literally rules out a change. The "No" answers "should we narrow anything?". The EI = 0 case is already PT-19. **Stakeholder question (one word):** "A bare 'laid off' with no EI: *ask* (as now) or *zero*?"

### Records to change after the owner confirms

| Record | Change |
| :-- | :-- |
| ADR 0006 | Decision 2: actual and lean rise on the 197 (LE-1, LE-3), and lean = the capped formula, not P. D12 applies to judges only (LE-5). Close the "Revisit (NEW-SCOPE-1)" line. Decision 3 is unchanged |
| ADR 0007 | No decision change. Add the known limit for the 156 part-paid recent loans to Consequences |
| ADR 0008 | Decision 5 reversed (WL-8). Decision 3 is confirmed as "accomplished = bought" (WL-4). Add the wallet presentation (WL-3). Remove the "Count the loan end in deadlines" alternative |
| ADR 0010 | Unchanged under (a). Under (b), decision 1 and the alternatives table change |
| `j5_plan_designer.md` | §3.1 `LoanEnd` comments: `bump_actual` and `bump_lean`, no 0 on `in_typical_spending=False`. §3.2 `DeadlineAnswer`: add the with-loan cut. §4.2 D12 bullet. §4.3 deadline line and wallet split. §5 NEW-COPY-22 reworded, NEW-COPY-27 replaced. §9 NEW-SCOPE-1, 2 and 4 closed |
| Brief Part 5 D12 | Narrowed by LE-5 (this part) |

## Part 8: owner answers to the Part 7 questions (2026-11-08)

- **Deadline cut: both.** Show the figure that counts the loan ending beside the cautious one (when the payoff month N ≤ the deadline D). This adopts Part 7 Q2 in full: the wallet model, and ADR 0008 decision 5 reversed.
- **A bare "laid off" with no EI given: ask.** This is reading (a): the parser stays as built. PT-12 asks for the keep % and then the months. PT-19 "no EI" gives `IC(0, …)`. PT-04 (card 3) is assumed to be `IC(0.55, 6)` per ADR 0010. ADR 0010 is unchanged.
- **Q1, loan payoff:** Part 7 rules LE-1 to LE-6 are adopted. From the payoff month, the actual rate and the lean rate rise. The judges' rate rises only by the part of P already in S (0 on the 197 accounts). The backup plan uses the judges' rise, so the 1,526 + 22 count is unchanged.
