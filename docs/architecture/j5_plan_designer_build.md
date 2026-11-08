# Build plan: J5 plan designer, loan end, and the README review fixes

Status: proposed, 2026-11-07; revised 2026-11-08 (owner answers, brief Parts 6 to 8). The design is [`j5_plan_designer.md`](j5_plan_designer.md); decisions are [ADR 0006 to 0010](../adr/README.md). This file holds the increment scope, the test map, the work packages for parallel sr-dev agents, the plan hand-off and the risks. Branch: `feature/guided-chat`. Run every test with `.venv/bin/python -m pytest app/tests -q -p no:cacheprovider` (Streamlit 1.67.0). There is no `slow` marker: the owner asked for one command, with the tests fixed and added where needed and focused on the engine (NEW-SCOPE-6).

## Changes from v1 (2026-11-07)

| § | Change | Source |
| :-- | :-- | :-- |
| 1 | S1 acceptance adds the wallet and the second deadline cut; S5 becomes F1 to F6 with the rescued count in the app; the live rescued count leaves "Deferred"; fixture IDs add 95548, 60630, 66505 | WL-3, WL-8, NEW-SCOPE-5, NEW-SCOPE-7 |
| 2 | `test_rates.py`: per-rate rise LE-1 to LE-4 on 95548, 60630, 66505 and 20111 and the population counts, replacing "every bump 0 on the 197". `test_goals.py`: both deadline cuts, the wallet split, the emergency split, the interest cap. Sweep: wallet and cut invariants. `test_findings.py`, `test_findings_ui.py`, `test_warm_up.py`: F2 to F6, live and cached at first use. `test_plan_text.py`, `test_plan_designer_ui.py`: new branches. No `slow` marker | LE-1 to LE-6, WL-1 to WL-9, NEW-SCOPE-3, 5, 6, 7 |
| 3 | T0 scaffold adds `Wallet`, `wallets_at`, `FindingTier`, `AccountFindings`, `account_findings` and the new `DeadlineAnswer`/`EmergencyResult` fields. WP rows updated; file ownership unchanged and non-overlapping | Design §3 changes |
| 4 | Estimates raised for WP-E1, WP-E2, WP-T, WP-UI and WP-F | as above |
| 5, 6 | R-J5-3, 4, 5 updated; R-J5-11 and R-J5-12 added; exit criteria updated for the closed NEW-SCOPE items | Parts 6 to 8 |

## 1. Increment scope

The architecturally significant story is **S1, the savings goal on the timeline**. It crosses every layer: page → `plan_designer` → `goals.design_plan` → `rates` (with the loan end) → `plan_text` and `charts` → page. It also proves the projection, the three rates and the loan end at once. Build and demo it first, on 20111.

| Story | Use case | Wireframe | Collaboration | Acceptance |
| :-- | :-- | :-- | :-- | :-- |
| S1 Savings goal on the timeline | [J5.1](../inception/use_cases_plan.md#j51-plan-a-savings-goal), [J5.4](../inception/use_cases_plan.md#j54-read-the-combined-timeline) | P1, P2, P4, P5 (wallet rows and the second cut: NEW-WF-3) | [design §6.1](j5_plan_designer.md#61-tick--engine--timeline-j51-to-j54-ac-11-to-ac-16) | AC-11, AC-12, AC-15, AC-16, AC-17, AC-19; the wallet split and both deadline cuts (ADR 0008 decisions 5 and 7) |
| S2 Time off | [J5.2](../inception/use_cases_plan.md#j52-plan-time-off-work) | P3 | §6.1 (the time-off branch) | AC-13, AC-16 |
| S3 Emergency budget | [J5.3](../inception/use_cases_plan.md#j53-budget-for-an-emergency) | P3 | §6.1 (the emergency branch) | AC-14, AC-16 |
| S4 Loan end in the backup plan | [J3 5b](../inception/use_cases.md#j3-make-a-plan) | G, P5 | [§6.2](j5_plan_designer.md#62-loan-payoff-inside-the-backup-plans-duration-check-j3-5b-ru-28-adr-0006) | AC-17, AC-18 |
| S5 Findings page | NEW-USECASES-1 | none yet (design §4.5; NEW-WF-3) | [§6.3](j5_plan_designer.md#63-findings-view-r3-d10-adr-0009) | R3, D10, D13; F1 to F6 equal the notebooks' stored outputs (ADR 0009 decision 4) |
| S6 README review fixes | n/a (D1 to D13, R1 to R22) | B, C, D, F, G | design §5 | AC-6, AC-20, R1 to R22 |

**Deferred:**

- plan designer in the chat, and its cheatsheet rows (stretch);
- more than one goal on the page (the engine takes up to 4);
- time off with a chosen start month (OI-17);
- the sourced "Realistic layoff" preset (D11);
- the notebook-only findings: income paradox correlations, the lowest-balance AUC, seasonality, district data (ADR 0009 decision 4);
- a precomputed Findings file (rejected, NEW-SCOPE-7);
- the short-history note (OI-12).

**Construction rules:**

- Follow the existing style: a module docstring, no comments that restate the code, `from app.engine import ...`.
- Everything is pure except the pages and `ui/plan_designer.py`.
- Use real fixture IDs (20111, 32078, 20134, 49637, 21271, 49900, 32179, and for the loan end 95548, 60630, 66505) in tests written against stubs. This is the J4 lesson in [`lessons.md`](../knowledge/lessons.md).
- Assert full formatted sentences at the call site, not prefixes.

## 2. Test map

"Sweep" means all 4,500 accounts. The owner is the work package that writes the test **first**, against the frozen contract.

| Test file | Owner | What it proves | Maps to |
| :-- | :-- | :-- | :-- |
| `test_judges_parity.py` (new) | WP-0 | An **independent oracle**, rewritten in the repo from the QA oracle. It reads the CSVs with `csv` and `statistics.median` and imports nothing from `app.engine.data`, `formulas` or `profile`. It checks I, F, S, B, H and P (to 1e-6) and the before-runway label on every account. Then, on 13 shocks, it checks `income_after`, `spending_after`, `one_off`, `buffer_left`, `gap` (1e-6) and the exact `runway.label`. The 13 shocks are: none, EI 55%, EI 55% + bills 15%, bills 15%, one-off 1×S, EI 40%, income to 0, bills +50%, bills +100%, one-off 2×S, one-off $10,000, rent +$300, and EI 55% + bills 15% + one-off 1×S with `through_months=6`. **R15:** every status A (203) and B (31) loan has P = 0, and C and D (403, 45) have P = the monthly payment. The 28 MB QA vector file is not committed; the test recomputes | R18, R15, AC-18, fixed rule "judges' numbers never change" |
| `test_rates.py` (new) | WP-E1 | 20111: actual −$748, judges −$2,260, lean +$604, lean cut $2,864, flexible $6,269, N = 36, status D. 32078: lean budget $1,346, fixed $0. Sweep: `actual.monthly == account_flows(id).change_last_12 == make_plan(id).goal.actual_change_last_12`; lean cut equals the backup steps' `cancel_other_orders` + `lean_months` saving wherever both exist; `lean_above_fixed` equals the old value (a pinned 20-account sample). **AC-17:** N for all 448 running loans equals an independent date computation from `loans.csv`; the counts within 6, 12, 24 and 36 months are 60, 125, 235 and 335; N ranges 1 to 60; 197 have `in_typical_spending False` with every bump 0 (D12); 45 have `scheduled_only`. **Per-rate rise (LE-1 to LE-4, rerun 2026-11-08):** 95548 actual $447.37 → `at(42, 42)` $1,925.53, judges bump 0.00, lean bump $2,956.31, `paid_rows` 6, `in_typical_spending False`; 60630 actual bump $366.97, judges 0, lean $597.81 (S caps); 66505 actual $815.23 → $2,798.06, judges −$950.62 → $1,032.22, lean $1,982.83, N 17; 20111 actual −$747.89 → $1,193.83 (bump $1,941.72), judges +$2,330.06, lean +$2,330.19, N 36. All to the cent (`pytest.approx(abs=0.01)`). **Populations:** on the 197, `bump_actual > 0` on all 197, `bump_judges == 0` on all 197, `bump_lean` full P on 166, part on 29, 0 on 2 (38528, 52185); `paid_rows < 12` on 156 (ADR 0007 limit); `paid_rows == 12` on 41 of the 197 and 225 of the other 251 (count rows, don't compare `bump_actual == P`: `loan_payments` and `monthly_payment` differ by cents). On the other 251, `bump_lean` is the full P on 250 (22609 is $0.13 short). With no running loan (status A or B), `loan_end(id) is None` and every `loan_bump == 0` (LE-4, R15) | RU-23, RU-27, AC-17, D12, LE-1 to LE-5 |
| `test_loan_end.py` (new) | WP-E1 | `duration_with_loan_end` with drop 0, or payoff after the months asked, returns `duration_path`'s fields exactly, on all accounts × 5 presets. A hand-worked example: buffer 1,000, gap 400 a month, drop 300 from month 2, 6 months asked → balances 600, 500, 400, 300, 200, 100, so it makes it (without the drop it runs out in month 3, 3.5 months short). `LoanEndCheck.reason` per case; `not_in_spending` on all 197 (LE-6). **AC-18 snapshots:** for all accounts × 5 presets, a Counter of `verdict_case`, of `backup.state`, and the rescued split (1,526 `cuts_needed` that make it after the steps, plus 22 `cuts_not_enough` that make it only with `ask_lender`) equal the pinned values. `makes_it_after_steps` is unchanged where `loan_end.reason == "applies"`. RU-28 population: EI 6 months, runs out, loan ends within 6 → 44 accounts; the number that make it counting the loan end is pinned from the first green run, and the inception script's 6 is the expected value | RU-28, AC-18, ADR 0006 |
| `test_plan.py` (changed) | WP-E1 | D8 wording of `cancel_other_orders` and `all_flexible` (NEW-COPY-21). **D7 sweep:** `goal.headline.monthly == actual_change_last_12`, and `goal.judges` equals the flat fields (state, months, cuts) on every account | R8, R9, D7, D8 |
| `test_qa_gaps.py` (new) | WP-E1 | **R16:** 20111 at keep 0.30 → `ei_capped.income_after == 1901.82` (to the cent), with both flat-below-the-cap and cap-binding cases. **R17 (engine):** a spy on `app.engine.plan.apply_shock` records `through_months` passed equal to `make_plan`'s argument, and `None` stays `None`. **R22:** `formulas.money(-0.3) == "$0"`, `money(-0.5)` per Python rounding, `money(-1) == "-$1"` | R16, R17, R22 |
| `test_account_id.py` (new) | WP-E1 | **R13:** "20,111", " 20111 ", "20111.0" and the float 20111.0 → 20111. "20,11", "2,0111", "20111.5", "1e4", "-20111" and "" → `not_digits`. "99,999" → `not_found` | R13 |
| `test_goals.py` (new) | WP-E2 | **AC-11:** 20111, $60,000 car, no deadline: lean `reached` 113, with the loan end 52; judges `never` with no loan and `over_cap` with it; actual `never` with no loan and 115 with it. **AC-12:** deadline 24 → need $68,188, monthly $2,841, cut $3,589, share 0.57, `within_lean False`. **AC-13:** 24 months off → $206,391 and $137,643; the check started now equals `apply_shock(20111, Shock(IncomeCut(0, 24)), through_months=24).duration`, running out in month 3. **AC-14:** $10,000: 20111 leaves $7,612 covered; 32078 leaves −$12,513, step 1 `cover_buffer`, lean budget $1,346, both equal to `apply_shock` and `make_plan`. **AC-15:** `start == B`, `balance[0] == B − cost`, three lines, horizon ≤ 120, events sorted. Order rules (RU-24): two goals in tick order; the time off waits for the fund; a goal is never bought below the fund. Interest: 0 gives the same as no interest; 6% shortens `months` on a positive-rate account and leaves `never` on a negative balance. Each `InvalidPlanError.field`. **Deadline, both cuts (WL-7, WL-8):** 20111 deadline 24 → `counts_loan_end False`, `cut_with_loan None` (N 36 > 24); deadline 48 → `cut_needed` $2,168.45, `cut_with_loan` $1,642.57, `payoff_month` 36; 66505 $60,000 car, deadline 36 → need $93,200, monthly $2,588.89, `cut_needed` $1,773.66, `cut_with_loan` $672.08; actual reach `month` 45, `month_no_loan` 115; fund reached month 24, or 41 without the loan. An account with no running loan → `cut_with_loan None`. With 6% interest the with-loan cut is the smallest to the cent (one cent less misses `need` by D). **Wallets (WL-1 to WL-4, WL-9):** 20111 actual line, month 35: fund wallet −$8,564 (to the dollar), car `waiting`; 66505 actual line: car `filling` from month 24, `accomplished` with `month_accomplished` 45, $0 from month 45; `wallets_at(…, horizon + 1)` raises `InvalidPlanError("month")`; S = 0 (77 accounts' shape, for example 20578) → no fund wallet. **Emergency split:** 66505 (B $45,648, fund $78,848) with $10,000 → `from_wallet` 0, `from_fund` $10,000; an account with B above fund + cost → `from_wallet == cost`. **Interest cap (NEW-SCOPE-3):** `MAX_INTEREST_PCT == 25.0` (owner value; the test names it so a change is deliberate); 25.0 accepted, 25.01 and −0.01 raise `InvalidPlanError("interest_pct")`; the default `PlanRequest().interest_pct == 0.0` | AC-11 to AC-15, RU-24 to RU-26, RU-29, RU-30, OI-17 to OI-19, WL-1 to WL-9 |
| `test_plan_designer_sweep.py` (new) | WP-E2 | Sweep × 2 requests: A = car $60,000 with deadline 24, 24 months off and a $10,000 emergency; B = amount 0, deadline 1, 120 months off and cost 0. Engine invariants: no exception; every balance is finite; `len(balance) == horizon + 1`; a reached month ≤ 120; no item reached before the item ahead of it; after each `goal_bought`, the balance ≥ fund. **Wallets:** at every month of every line with a fund target, `sum(w.amount) == balance[month]` (1e-6), and at most one wallet is `filling` or `spending`. **Cuts:** where `counts_loan_end`, `cut_with_loan <= cut_needed` and `payoff_month <= months`; elsewhere `cut_with_loan is None`. Then `plan_text` (WP-T) lines for the design contain no "None", "nan", "{", "$$", "-$0" or "1 months". **AC-16** edge populations reach their line: amount 0, `now` (1 account at $60,000), 121 months off rejected, B ≤ 0 (23), S = 0 (77) with `fund_target None`, deadline shorter than possible (`over_flexible`). Budget about 90 s | AC-16, AC-20 (plan half) |
| `test_text_fixes.py` (new) | WP-T | **R1/D1:** 21271 EI 6 → "less than 0.1 months short"; a sweep of all × `job_loss_ei` finds no "about 0 months short" (18 accounts). **R4:** 20111 bills 15%, 50% and 100% → "unchanged at 7.8 months"; an account with H > 0 → "down from"; no "down from No shortfall". **R10:** target 1 and length 1 → "1 month". **R11/R21:** 49637 summary and 32179 at EI 40% read "under 0.1 months" while the label stays "0.0 months"; I = S = 0 → NEW-COPY-14/15. **R14:** `income_returns` → NEW-COPY-16. **R19:** 49900 → no "slightly more". **R20:** 20111 with `one_off_dollars = p.B` (exactly $17,611.86…) → "uses up the whole buffer". **D5/AC-6:** `summary_line(20134)` contains "120.0 months" and no "No shortfall" or "120 months or more". **D4/R6:** `oneoff_line` and `after_line` forms. D7 `goal_lines` lead with the headline (20111) | R1, R4, R10, R11, R14, R19, R20, R21, D4, D5, D7, AC-6 |
| `test_ui.py` (changed) | WP-T | The existing `test_every_sentence_on_every_account` gains the bans "about 0 months short", "1 months", "$$" and "down from X" where before equals after, and one more key, `length_one_target_one` (`IncomeCut(0.55, 1)`, `target_months=1`). Other existing AppTest asserts are updated to the new wording | AC-20, R1, R4, R10 sweep |
| `test_plan_text.py` (new) | WP-T | **AC-19:** a hand-built `PlanDesign` with sentinel numbers (for example 12,345.67 → "$12,346") comes back in the lines, so no number is computed in `plan_text`. Every P.* branch: never, over_cap, now, zero, deadline on pace or cut or over, fund first, interest, `o_ok`, `o_out`, `o_now`, `e_left_ok`, `e_left_no`, `e_zero`, `loan_line`, `loan_never`, `loan_over`, `loan_d` (status D), D12 reworded for the judges' rate (NEW-COPY-22), after-cap, two markers in one month. **New 2026-11-08:** NEW-COPY-27 cut and on-pace forms appear only when `counts_loan_end`, after the cautious cut; `wallet_rows` states (filling, full, waiting, spending, accomplished, negative fund) and the emergency split line (NEW-COPY-30); `table_rows` has one wallet column per item. Copy rows in copy §11 without "…" equal `P` constants | AC-19, J5.1 to J5.4 extensions |
| `test_chat_parse.py` (changed) | WP-C | NEW-PARSER-1 to 6; PT-04 changed (`assumed` source); the other PT rows unchanged; `read_number("fifteen") == 15`; the fuzz still passes | R5, D2, R7 |
| `test_chat_replies.py` (changed) | WP-C | `result_lines` holds the one-off dollars on the furnace on 20111 ("$8,600"), "before the shock" and `after_line`. With `assumed_months=True` it holds `ASSUMED_LENGTH`. The AC-6 assertion becomes "120.0 months". **Sweep:** `greeting` and `result_lines` on every account × 5 presets with the bans of `test_ui.py` | R6, R7, AC-6, Part 5 "result_lines and greeting swept" |
| `test_chat_flow.py`, `test_chat_text.py`, `test_cheatsheet.py`, `test_chat_imports.py` (changed) | WP-C | Flow: PT-04 text → confirm → run gives `IncomeCut(0.55, 6)` and the assumed line. Text: `cant_open`, `size_button` as settled. Cheatsheet: the new slot words and row parse `ok`. Imports: rules E1 to E3 (design §2) | R5, R7, NEW-COPY-3, NEW-COPY-10, AC-10 |
| `test_findings.py` (new) | WP-F | **F1:** `biggest_finding()` = 735 events, 480 accounts, income kept 13%, spending kept 50%, within 10% 5%, 493 predicted and 31 actual (the discovery notebook asserts). **F2:** `tiers` = 410, 219, 106 events with spending kept medians 0.37, 0.71, 2.47 (discovery §5 tier table, 37.43%, 71.36%, 246.94%) and pass-through equal to `spending_response()`. `find_events` output and `spending_response()` tiers are identical before and after the refactor. **F3 to F6:** `account_findings()` = 4,500 accounts; 1,596 run out on `job_loss_ei` over 6 months, 1,526 by cuts, 22 with the lender, 1,548 in all (equal to the `test_loan_end.py` snapshot); 1,038 of 3,309; 197 of 448, median $2,545.40; 740 pension. A second call returns the same object (cached). `findings_view.numbers/lines/tier_rows/account_lines/alt_text` contain those figures, and F3 uses D13's wording; `chart` builds. About a minute cold, less when other sweeps have already warmed the profiles in the same process; no `slow` marker | R3, D10, D13, ADR 0009 |
| `test_findings_ui.py` (new) | WP-F | AppTest: Findings is in the navigation; the page shows the three metrics, the sentence and the tier table with no customer loaded; with `account_findings` stubbed by a monkeypatch (the engine test covers the real figures), the F3 to F6 lines appear; Shock and plan is still the default page | R3, D13 |
| `test_warm_up.py` (new) | WP-F | In a fresh subprocess, `warm_up()` finishes within 15 s (ours). Then `biggest_finding()` and `spending_response()` return in under 50 ms (cache hit), and `account_findings.cache_info().currsize == 0` (not computed at startup) | Part 5 "warm_up timing", ADR 0009 decision 3 |
| `test_plan_designer_ui.py` (new) | WP-UI | AppTest on 20111: P appears below Details; nothing ticked → rates only; tick goal → `P.g_needed` with $8,187 or $8,188 as engine-formatted; the deadline lines; the chart is present; the table toggle shows a 121-row-or-fewer dataframe whose values equal the lines; tick order goal → off, then off → goal, changes the order; a customer change keeps the ticks (J5 4b); a shock on the page doesn't change P (RU-11). The interest box's max equals `goals.MAX_INTEREST_PCT` and its default is 0. On 66505 with a 36-month deadline, both cuts show ($1,774 and $672). The wallet rows show under the goal lines. The footer has the CTU link and canada.ca | AC-15, AC-19, R2 (footer), J5, NEW-SCOPE-3 |
| `test_call_sites_ui.py` (new) | WP-UI | **R17 (page):** spies on `app.engine.apply_shock` and `make_plan` during an AppTest run record `through_months=6` for the EI preset and `None` for the furnace. The D2 caption shows for "Laid off + bills up 15%" only; the D4 line shows "$8,600" on the furnace for 20111 | R17, R7, D4 |
| `test_submission.py` (new) | WP-D | `project_dev-post.md` has "Sources" and "Credits" headings, "Biggest finding", the CTU and canada.ca URLs, "1,526", "22 more if the lender agrees", "1,548", "1,038 of 3,309", the current test count (read from a constant the lead sets after the final run), "four pages" and no "three pages". The root `requirements.txt` starts `-r app/requirements.txt`; `app/.streamlit/config.toml` has `gatherUsageStats = false` | R2, R12, D9, D13 |

**Suite time (NEW-SCOPE-6).** No `slow` marker. New tests are engine tests first; the AppTest files stay at the states listed. Per-file budgets: parity about 2.5 min, design sweep 120 s, `test_findings.py` about 1 min cold. The lead records the full-run time after WP-UI and sends it to WP-D.

AC-1 to AC-10 stay covered by the J4 files ([J4 build §2](j4_chat_build.md#2-test-strategy)). Only AC-6 changes (above). AC-10's network-off half is still GO-10.

## 3. Work packages

### Freeze first: T0, the software-engineer lead, within 45 minutes

The lead commits these before any package starts:

1. **`test_judges_parity.py`**, green on the current engine. It is the safety net for every engine change.
2. **`app/engine/rates.py`, `goals.py` and `findings.py`** with every dataclass and constant of [design §3](j5_plan_designer.md#3-frozen-interfaces) verbatim, and stub functions:
   - `saving_rates` returns the three rates with no loan;
   - `design_plan` returns an empty timeline of 12 months at B;
   - `biggest_finding` returns zeros and three empty tiers;
   - `account_findings` returns zeros (2026-11-08);
   - `wallets_at` returns `()` (2026-11-08);
   - `duration_with_loan_end` delegates to `duration_path`.
3. **`plan.py`**: the `GoalAtRate` and `LoanEndCheck` classes and the three defaulted fields.
4. **`engine/__init__.py`** with all exports and `warm_up`.
5. **`ui/plan_text.py`**: class `P` with every string, and signature stubs that return `[]`.
6. **`state.py`**: `Source` gains `"assumed"`, and `ASSUMED_MONTHS = 6`.
7. **`text.py`**: the new names `months_word`, `runway_words`, `in_sentence`, `oneoff_line`, `after_line`, `ASSUMED_LENGTH` and `FOOTER`, as stubs that return the label or `None`.

After T0 these names are frozen. Each file's ownership then passes to the package below.

| WP | Owns (only these files) | Codes against (frozen at T0) | Tests first | Done when |
| :-- | :-- | :-- | :-- | :-- |
| **WP-0** Lead scaffold and parity | T0 files above (until handed over); `app/tests/test_judges_parity.py` (keeps it) | none | `test_judges_parity.py` | Green on the unchanged engine in about 2.5 min; the T0 scaffold imports and the existing 829 tests still pass |
| **WP-E1** Engine: rates, loan end, D7, D8, QA gaps | `app/engine/rates.py`, `plan.py`, `profile.py` (R13 only), `formulas.py` (R22 only); `test_rates.py`, `test_loan_end.py`, `test_plan.py`, `test_qa_gaps.py`, `test_account_id.py`, `test_sweep.py` (pins only) | design §3.1, §3.3 | AC-17 counts, delegation equality, the AC-18 snapshots (pinned on the **unchanged** engine first), R16, R13, R22, D7 mirror; then the per-rate rise LE-1 to LE-4 on 95548, 60630, 66505, 20111 and the population counts | All its files pass; `test_judges_parity.py` and `test_shock.py` unchanged and green; `plan._lean_above_fixed` callers moved to `rates.lean_above_fixed` |
| **WP-E2** Engine: plan designer | `app/engine/goals.py`; `test_goals.py`, `test_plan_designer_sweep.py` | design §3.2, §4.3; `rates` (stubbed until WP-E1 lands, then real); `plan_text` stub for the sweep's text half | AC-11 to AC-16 with real IDs; the order rules; `cut_with_loan` (66505, 20111 at 24 and 48); `wallets_at` and the emergency split; the interest cap | Both pass with the real `rates` and `plan_text`; sweep ≤ 120 s with the wallet and cut invariants |
| **WP-T** Copy and text | `app/ui/text.py`, `app/ui/plan_text.py`; `test_text_fixes.py`, `test_plan_text.py`, `test_ui.py` | design §3.6, §5; `PlanDesign` and `Wallet` built by hand | R1, R4, R10, R11, R14, R19 to R21, D5, D7 lines, then AC-19 sentinels; NEW-COPY-22 (reworded), 27 (replaced), 30 | Its files pass; `test_ui.py`'s sweep has the new bans and is green; every P.* branch has a test |
| **WP-C** Parser and chat | `app/assistant/parse.py`, `state.py` (after T0), `replies.py`, `flow.py` (the `assumed_months` kwarg only), `chat_text.py`; `app/ui/cheatsheet.py`; `docs/design/ux/chat_parser.md` (NEW-PARSER rows and PT-04, as placeholders for the UX owner to number); `test_chat_parse.py`, `test_chat_replies.py`, `test_chat_flow.py`, `test_chat_text.py`, `test_cheatsheet.py`, `test_chat_imports.py` | design §5 (parser), `text.oneoff_line`/`after_line`/`ASSUMED_LENGTH` (T0 stubs) | NEW-PARSER-1 to 6, the PT-04 change, R6 lines, the greeting and result sweep | All chat tests pass; the PT-01 to PT-25 rows other than PT-04 are unchanged; the fuzz shows no regex over 50 ms |
| **WP-UI** Page, plan designer section, chart | `app/app_pages/shock_and_plan.py`, `app/ui/plan_designer.py`, `app/ui/charts.py`; `test_plan_designer_ui.py`, `test_call_sites_ui.py` | `design_plan` (stub, then real), `plan_text` (stub, then real), `text.FOOTER`/`ASSUMED_LENGTH`/`oneoff_line` | `request_from` unit cases, the AppTest P1 to P4 states, R17 spies; the interest box bound read from `goals.MAX_INTEREST_PCT`; the wallet rows | Both files pass with the real modules; a manual run on 20111, 32078, 20134 and 49637 with the network off |
| **WP-F** Findings | `app/engine/response.py`, `app/engine/findings.py` (after T0), `app/ui/findings_view.py`, `app/app_pages/findings.py`, `app/streamlit_app.py` (one `st.Page` line); `test_findings.py`, `test_findings_ui.py`, `test_warm_up.py` | design §3.4, §4.5; `findings_view` copy NEW-COPY-25 and 31 | The tier and event equality before and after the refactor, then 735/480/50%/493/31, the tiers, then `account_findings` (1,526 + 22, 1,038 of 3,309, 197 of 448, 740) | All three pass; `test_shock.py` green; startup measured; the first Findings open timed on the laptop and recorded |
| **WP-D** Submission and config | `project_dev-post.md`, `app/README.md`, root `requirements.txt`, `app/.streamlit/config.toml`; `docs/inception/scope.md` (the test-count figures in the status line and GO-2 only); `test_submission.py` | D9, D10, D13, R2, R12; the final test count from the lead | `test_submission.py` | It passes, and the counts match the final full run. Runs **last** |

**Files no package owns:** `app/engine/shock.py`, `data.py`, `errors.py`, `app/assistant/controls.py`, `transcript.py`, `app/app_pages/assistant.py`, `customer_profiling.py` and every other doc. If a package needs one of them changed, it asks the lead.

**Cross-package seams (assert the full sentence at the call site):**

- WP-C's result-line tests need WP-T's `oneoff_line` and `after_line`.
- WP-E2's sweep needs WP-T's `plan_text`.
- WP-UI needs WP-E2 and WP-T.
- AC-6 is asserted in both `test_text_fixes.py` (WP-T) and `test_chat_replies.py` (WP-C).

**Critical path:** T0 → WP-E1 `rates.py` (`saving_rates`, `loan_end`, `duration_with_loan_end`) → WP-E2 `design_plan` → WP-UI integration → full suite → WP-D counts.

- WP-T, WP-C and WP-F run in parallel off T0.
- WP-E2 is the largest package, and its sweep is the gate.
- If the time runs short, ship S1 and S6 first. S4 (the backup loan line) and S5 (Findings) are independent and can follow.

## 4. Plan hand-off for `pm-planner`

Points use the planner's scale. Hours are estimates; actuals stay blank until the work is done.

| Item | Points | Dev tasks | Estimate (h) | Actual (h) | Risk notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| WP-0 Scaffold and parity | 2 | T0 stubs; oracle test over 13 shocks | 1.5 | | The parity test runs about 2.5 min |
| WP-E1 Rates, loan end, D7, D8, QA gaps | 5 | rates; payoff; per-rate rise LE-1 to LE-4 and `paid_rows`; drop path; LoanEndCheck; GoalAtRate; R13, R16, R17, R22; snapshots | 4.5 (was 4.0) | | Snapshots must be pinned **before** the change |
| WP-E2 Plan designer engine | 8 | request checks and the interest cap; simulation; reach; deadline with both cuts; wallets_at; time off; emergency and its split; horizon; facts; sweep | 7.0 (was 6.0) | | Critical path; order and edge rules |
| WP-T Copy and text | 5 | 13 text fixes; plan_text branches incl. wallet rows and the second cut; sweep bans | 4.5 (was 4.0) | | Wording churn across existing AppTests |
| WP-C Parser and chat | 3 | number words; half a year; D2 assumed; R6 lines; cheatsheet; PT rows | 2.5 | | Regex backtracking; PT-04 meaning change |
| WP-UI Page and section | 5 | plan_inp sync; widgets (interest bound from the constant); chart; table with wallet columns; wallet rows; notes; footer; AppTests | 4.5 (was 4.0) | | AppTest with conditional widgets |
| WP-F Findings | 5 (was 3) | events refactor; finding and tiers; account_findings; view; page with spinner; warm_up test | 3.5 (was 2.5) | | Exact equality with three notebooks; a minute-long first open |
| WP-D Submission | 1 | Devpost sections; counts; requirements; config | 1.0 | | Waits for the final test count |
| Rehearsal (GO-11, GO-1, GO-10) | 1 | AC-11 to AC-20 by hand, network off | 0.5 | | Needs the demo laptop |

Split: the brief's "plan designer" becomes S1 to S3 (the wallet and the second cut stay inside S1; they change no month, so they aren't split out). "Fixes" becomes S4 and S6. R3 becomes S5.

## 5. Risks and open items

| ID | Risk | Response |
| :-- | :-- | :-- |
| R-J5-1 | A judges' number moves silently | `test_judges_parity.py` (independent oracle, 13 shocks) lands first; there are no edits to `shock.py` or `formulas.runway_from`; snapshots are pinned before WP-E1 |
| R-J5-2 | The plan designer's numbers and the backup plan's drift apart | One `rates` module feeds both. The lean cut equals the backup steps (`test_rates.py`) |
| R-J5-3 | The loan end overstates or understates savings on recent loans | Each rate rises by the part of P it contains (LE-1 to LE-3): 0 on the judges' rate for the 197, so nothing double-counts; `test_rates.py` pins four accounts and the populations |
| R-J5-4 | Status D payoff isn't certain | `scheduled_only` → `P.loan_d`; the cautious deadline cut is always shown first, and the cut counting the loan end only beside it (ADR 0008 decision 5) |
| R-J5-5 | Suite time about doubles (parity × 13, design sweeps, the Findings sweep) | No `slow` marker (owner, NEW-SCOPE-6); budgets per file; profiles are cached once per process, so the Findings sweep is cheap after the other sweeps; the lead records the run time |
| R-J5-6 | Startup slows with Findings | One shared events pass (ADR 0009); `test_warm_up.py` |
| R-J5-7 | Session state for conditional widgets is lost on rerun | The `ss.plan_inp` single-store pattern, already proven on the page |
| R-J5-8 | Copy changes break existing AppTests | WP-T owns `test_ui.py` and updates its asserts in the same change |
| R-J5-9 | The parser's assumed length is read as guessing | Mandatory confirm (ADR 0004) plus the stated line (ADR 0010); only card 3's shape |
| R-J5-10 | Cloud deploy reads the root `requirements.txt` (unknown) | **verify** in the Community Cloud settings before GO-9 |
| R-J5-11 | The first Findings open takes about a minute (50 s of cold profiles, measured on the laptop; Cloud speed **verify**), and a process restart loses the cache | Spinner with NEW-COPY-31's message; the owner opens Findings once before judging (NEW-SCOPE-7); F1 and F2 don't wait for it; GO-11 rehearsal checks it |
| R-J5-12 | The actual rate before payoff overstates the forward saving on 156 part-paid recent loans | Known limit in ADR 0007; D7 keeps the literal change; `paid_rows` exposes it if the owner later wants a note |

Open items are cited, not copied: OI-5 (fund target), OI-9 (owners), OI-12 (short history), OI-14 to OI-21 (built with their defaults, D12 and D13 where those settle them), and NEW-SCOPE-1 to 7 (closed 2026-11-08), NEW-USECASES-1, NEW-GLOSSARY-1, NEW-WF-2 and NEW-WF-3 in [design §9](j5_plan_designer.md#9-gaps-and-questions-sent-back).

## 6. Exit review

Elaboration for J5 is done when all of these hold:

- T0 is committed and frozen, and `test_judges_parity.py` is green on the unchanged engine;
- S1 runs end to end on 20111 with AC-11, AC-12 and AC-15 passing;
- the AC-18 snapshots are pinned and green after WP-E1;
- ADR 0006 to 0010 are accepted or revised by the owner;
- NEW-COPY-11 to 29 and NEW-PARSER-1 to 6 are numbered or answered by the UX owner;
- NEW-SCOPE-1 to 7 are answered (done 2026-11-08) and the ADR revisions reviewed by the owner;
- NEW-WF-3 is drawn or answered by the UX owner.
