# ADR 0006: A scheduled loan end, counted beside the judges' numbers

Status: proposed, 2026-11-07; revised 2026-11-08 (decision 2, consequences). Numbers the inception placeholder NEW-ADR-1. Sources: brief Part 2, D12, brief Part 7 (LE-1 to LE-6) and Part 8, BR-23, RU-27, RU-28, OI-15, OI-16, AC-17, AC-18, [ADR 0001](0001-engine-shock-semantics.md), [design §4.2 and §6.2](../architecture/j5_plan_designer.md#42-loan-end-adr-0006).

## Context

The plans treat a running loan's payment P as lasting for ever. Of 448 running loans (status C or D), 335 end within 36 months of the last data month. The README runway doesn't use P, so the judges' numbers can't count a loan end. But the plan designer and the backup plan's "do they make it?" check should count it. 197 of the loans have $0 of P in typical spending, because the loan started recently (D12). Status D loans are behind, so their end is only scheduled.

An amendment to ADR 0001 isn't allowed, because accepted records are immutable. In any case 0001's rule, that our figures are separate fields, already covers this change. What's new is what the backup plan's extra check means.

## Decisions

1. **The payoff month N is `loan_start` month + `duration_months` − the account's last data month.** It comes from the new `engine/rates.loan_end`. The saving rises from month N (OI-16).
2. **Each rate rises from month N by the part of P it already contains** (brief Part 7 LE-1 to LE-5, adopted by the owner in Part 8):
   - **actual** (LE-1): min(P, the mean of `loan_payments` over the last `actual_months` rows). This applies to every running loan, **the 197 included**, because the payment really leaves the account now;
   - **judges** (LE-2): min(P, `loan_median`). That is exactly 0 on the 197 accounts with `loan_median == 0`, because S never held P;
   - **lean** (LE-3): `min(S, Fx + P + L) − min(S, Fx + L)`, with Fx = `current_fixed_costs` − P and L = `SavingRates.lean_above`. It is always between 0 and P, and it is P unless S caps the lean spending;
   - **no running loan** (LE-4, status A or B, or no loan): every rise is 0 (R15).

   On the 197 accounts, D12 now covers **the judges' rate only** (LE-5). A line labelled ours says so: NEW-COPY-22, reworded in [design §5](../architecture/j5_plan_designer.md#5-copy-and-parser-fixes). The actual and lean rates still rise.
3. **The backup plan keeps `makes_it_before`, `makes_it_after_steps`, `state` and `steps` exactly as they are.** A new field `BackupPlan.loan_end: LoanEndCheck` holds our check. It uses `duration_with_loan_end`, which is `duration_path` with the gap smaller by the judges' rise from month N (LE-6: the shocked gap is built from S, so the judges' rise is the right one; `not_in_spending` on the 197), and it carries a `reason` (applies, after_months, not_in_spending, no_length, no_shock). After an `ask_lender` step the drop is 0, because P is already paused. So the D13 "rescued" count is unchanged.
4. **Status D sets `scheduled_only`**, and every loan-end line adds `P.loan_d`.
5. **`duration_with_loan_end` returns `duration_path`'s result unchanged** when there's no drop inside the months asked.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Change `makes_it_after_steps` to count the loan end | It changes a field the chat, the transcript and the D13 count read; AC-18 asks for no change |
| Add P to every rate at payoff | Double-counts on the judges' rate, where S never held P on the 197 (OI-15, D12) |
| No rise on any rate for the 197 (D12 read literally; the 2026-11-07 default) | Understates the saving the customer will really have: the actual 12-month change holds P on all 197 (fully on 41), and lean spending holds P through current fixed costs (brief Part 7 Q1) |
| Ignore the loan end | Misses BR-23; 125 loans end within a year |
| Amend ADR 0001 | Accepted records change only by a new record |

## Consequences

- One rule (`rates.loan_end`) serves the plan designer and the backup plan, so they can't disagree.
- `test_loan_end.py` pins, before and after the change, the verdict and backup-state counts and the 1,526 + 22 split, plus the delegation equality.
- There are new copy rows: `P.loan_backup` (already drafted), NEW-COPY-22 (D12) and NEW-COPY-26.
- `test_rates.py` pins LE-1 to LE-4 on 95548, 60630, 66505 and 20111 (brief Part 7 table, rerun on the engine 2026-11-08) and the population counts: on the 197, `bump_actual > 0` on all, `bump_judges == 0` on all, and `bump_lean` is the full P on 166, part of P on 29 and 0 on 2 (38528, 52185).
- `monthly_summary.loan_payments` differs from `loans.csv` `monthly_payment` by cents on many rows, so "the rate holds all of P" is tested as 12 of 12 paid rows (41 of the 197, 225 of the other 251), not by equality.
- NEW-SCOPE-1 is closed by the owner (brief Part 8). Revisit only if the owner wants the verdict itself to count the loan end.

## Changes

| Date | Change | Source |
| :-- | :-- | :-- |
| 2026-11-08 | Decision 2 rewritten: actual and lean rise on the 197 (LE-1, LE-3), lean uses the capped formula instead of P, D12 narrowed to the judges' rate (LE-5), LE-4 stated. Decision 3 cites LE-6, otherwise unchanged. The "Revisit (NEW-SCOPE-1)" line is closed. A rejected alternative is added for the literal D12 reading | Brief Part 7 Q1, Part 8 |
