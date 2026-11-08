# ADR 0007: Three saving rates, with the actual 12-month change first

Status: proposed, 2026-11-07; revised 2026-11-08 (consequences only). Sources: brief Part 1, D7, RU-23, OI-14, R8, [design §4.1 and §4.4](../architecture/j5_plan_designer.md#41-saving-rates-adr-0007).

## Context

The judges' surplus I − S is a difference of two medians from different months, and the two don't add up. 20111 shows −$2,260 a month while its balance actually fell $748 a month over the last year. On 1,038 of the 3,309 accounts with a positive I − S, the balance didn't grow. The brief wants three rates side by side, and the owner chose the actual change as the headline for the new plan designer and for the existing goal plan (D7). The lean rate's base wasn't fixed (OI-14).

## Decisions

1. **The rates are, in display order:**
   - **actual**: `account_flows(id).change_last_12`, the headline, ours;
   - **judges**: I − S, labelled as the judges' figure;
   - **lean**: I − (S − lean cut), ours.

   The lean cut is `max(flexible − lean_above, 0)`. That's the saving the backup plan's `cancel_other_orders` and `lean_months` steps give, so the plan designer and the backup plan agree ($2,864 on 20111; lean rate $604).
2. **One module, `engine/rates.py`, computes them.** `LEAN_QUANTILE` and `lean_above_fixed` move there. `plan.py` imports them, so they can't drift.
3. **The goal plan (J3) gains `GoalPlan.headline` (actual) and `GoalPlan.judges` (I − S).** The existing flat fields keep the judges' meaning, so the chat's records and existing tests stay valid. The wording leads with the headline.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Lean = actual change + lean cut (20111: $2,117) | Mixes a 12-month mean with a median-based cut, and disagrees with the backup step |
| Keep I − S as the headline | D7; its sign disagrees with the actual change on 1,660 accounts (622 + 1,038) |
| Replace the flat goal fields with the actual rate | Breaks the chat's `EngineOutput.goal_state` meaning and existing tests |

## Consequences

- A sweep asserts `headline.monthly == actual_change_last_12`, and that `judges` mirrors the flat fields on every account.
- Every rate is labelled. Only "judges" lacks "(ours)".
- **Known limit (brief Part 7, limit 1):** 156 of the 197 recent-loan accounts paid the loan in fewer than 12 of the last 12 rows. On these, the actual rate **before** payoff overstates the saving going forward by P × (12 − k) ÷ 12, where k is the number of paid rows, because the loan is now paid every month (95548: k = 6, so $1,478 a month). Decision 1 keeps the literal 12-month change (D7), so nothing changes. `LoanEnd.paid_rows` exposes k, and `test_rates.py` pins the 156.
- Revisit if the owner picks a different lean base (OI-14), or asks the plan to note the 31 loans whose start month may hold the loan being paid out (brief Part 7, limit 2; still open, low).

## Changes

| Date | Change | Source |
| :-- | :-- | :-- |
| 2026-11-08 | Consequences gain the 156-account known limit and the open limit-2 question. No decision changes | Brief Part 7 Q1 known limits |
