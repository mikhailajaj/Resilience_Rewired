# Use cases: J5 Design a plan

User-goal use cases under the [J5 summary](use_cases.md#j5-design-a-plan). Screens P1 to P5 are in [wireframes P](../design/ux/wireframes.md#p-plan-designer-j5), `P.*` keys in [copy §11](../design/ux/copy.md#11-plan-designer-p). Author: the inception agent; the area owner is TBD ([OI-9](scope.md#open-items-for-the-owner)). Example values are from a read-only script over the CSVs on 2026-11-07; the engine is the source once built.

## J5.1 Plan a savings goal

| Field | Value |
| :-- | :-- |
| ID, type | J5.1, user goal |
| Traces to | BR-19, BR-23 |
| Rules | RU-1, RU-2, RU-9, RU-11, RU-23, RU-24, RU-25, RU-26, RU-27 |
| Actors | Presenter (primary), judge (supporting), customer (offstage) |
| Preconditions | A valid customer is on Shock and plan (J1 1, 2) |
| Trigger | A judge names a goal, such as "a $60,000 car in 24 months" |

**Main flow**

1. The presenter ticks `P.t_goal` (P1). The tool opens its inputs.
2. The presenter types `{goal_name}`, `{amount}` and, optionally, `{deadline_months}` and `{interest_pct}` (P2).
3. The tool runs the plan designer's engine function with no shock (RU-11).
4. The tool shows what's needed: the fund still needed (J3's target less B), then the amount (RU-24): `P.g_needed`.
5. The tool shows the months to reach it at each rate, the headline first: `P.g_months` (RU-23, RU-26).
6. With a deadline, the tool shows the monthly saving needed, the cut needed against the headline rate, and that cut as a share of flexible spending and against the lean-quarter cut: `P.g_deadline`, `P.g_cut`.
7. The tool adds "reached" and "bought" markers to the timeline (J5.4).

**Postcondition:** every figure comes from the engine; no judges' number changed. For 20111 and a $60,000 car, the headline rate (−$748) never gets there, and the lean rate ($604, ours) takes 113 months, or 52 counting the loan ending in month 36.

**Extensions**

| Step | Condition (accounts) | Behaviour | Screen |
| :-- | :-- | :-- | :-- |
| 2a | Amount is 0 | `P.g_zero`; no marker | P2 |
| 2b | Amount below 0, or deadline outside 1 to 120 | The box holds its range and says it (as C2); no run | P2 |
| 2c | Interest given | Applied as RU-25; `P.interest` (ours) | P2 |
| 4a | B ≤ 0 (23) | `K.f_negative` first; the amount needed includes getting back to $0 | P2 |
| 4b | S is 0 (77) | No fund target (`P.no_fund`); the goal counts from $0 | P2 |
| 4c | Money above the fund already covers it (1 account for $60,000) | `P.g_now`; bought at month 0 | P2 |
| 5a | A rate is 0 or below (judges' 1,191; actual 1,607; lean 98) | `P.never`, plus the cut to start saving and the cut to reach it in 120 months: `P.g_cut_start` | P2 |
| 5b | Judges' rate and actual change differ in sign (622 and 1,038) | Both shown; the existing plan fact shows once | P2 |
| 5c | Reached after month 120 | `P.over_cap` (RU-26) | P2 |
| 5d | Running loan ends inside the horizon (448) | `P.loan_line` (ours), worded as the brief's "31 months; 22 counting the loan ending in month 9 (ours)" | P5 |
| 5e | Loan status D (45) | `P.loan_d` under 5d | P5 |
| 5f | Pension income (740) | Shown as normal | P2 |
| 5g | Data stops early (76) | `P.month_one` | P2 |
| 5h | Short history | Lean rate from few months. **Gated on OI-12**; fallback: the data range only | P2 |
| 6a | Monthly saving needed ≤ the headline rate | `P.g_on_pace`; no cut | P2 |
| 6b | Cut needed > flexible spending (deadline shorter than possible) | `P.g_cut_over`; no fix claimed | P2 |
| 6c | Deadline arrives before the fund is reached | The needed saving includes the fund first (RU-24): `P.g_fund_first` | P2 |
| 7a | More than one goal | Each goal starts after the one before is bought (RU-24) | P4 |

## J5.2 Plan time off work

Outline; full dress in the next pass. Traces to BR-20, BR-23. Rules RU-23, RU-24, RU-26, RU-27, RU-29.

1. The presenter ticks `P.t_off` and types `{months_off}` (P3).
2. The tool shows the amount needed, `months_off` × S, and at lean spending (ours): `P.o_amount`.
3. The tool shows the months to save it after the fund, at each rate: `P.g_months`.
4. The tool runs `IncomeCut(0, months_off)` on the projected balance at the start and says whether they make it: `P.o_ok` or `P.o_out` (RU-29). For 20111 and 24 months: $206,391 needed, never at the headline rate, so the check starts now and runs out in month 3.

Extensions: 1a `months_off` above 120: `T.out_of_range` wording, no run (P3). 3a not saved by month 120: `P.o_now`; the check starts now, as J2 would (OI-17). 4a pension (740): `fact_lines` pension line, applied as asked. 4b loan ends during the time off: the gap falls (RU-27).

## J5.3 Budget for an emergency

Outline. Traces to BR-21. Rules RU-7, RU-23, RU-26, RU-30.

1. The presenter ticks `P.t_emergency` and types `{cost}` (P3).
2. The tool applies `Shock(one_off_dollars=cost)` and shows the buffer left: `P.e_left_ok` or `P.e_left_no`. For 20111 and $10,000: $7,612.
3. If the buffer left is 0 or less, the tool shows the instant budget: the backup plan's steps in order, the lean monthly budget and the months to rebuild the buffer and the fund at each rate: `P.e_budget`, `P.e_rebuild`. For 32078: buffer left −$12,513, step 1 `cover_buffer`, lean budget $1,346 a month.

Extensions: 1a cost 0: `P.e_zero`. 2a B already ≤ 0 (23): the no-buffer sentence, cost not blamed (CON-5). 3a a rate is 0 or below: `P.never` for rebuilding. 3b running loan: `ask_lender` marked as needing agreement (J3 5a).

## J5.4 Read the combined timeline

Outline. Traces to BR-19, BR-20, BR-21, BR-22, BR-23. Rules RU-23, RU-24, RU-25, RU-26, RU-27.

1. The tool draws the balance month by month from B, one line per rate, up to the longest plan horizon and at most 120 months (P4).
2. The tool marks fund reached, each goal reached and bought, time off start and end, the emergency cost and loan paid off.
3. The presenter opens the table view, with the same values by month: `P.tl_table`.

Extensions: 1a no rate above 0 and nothing ticked: the lines are flat or falling; `P.tl_none`. 2a two markers in one month: one label lists both. 2b a marker past month 120: listed under the chart as "after month 120".
