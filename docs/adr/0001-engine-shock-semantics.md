# ADR 0001: Shock figures beside the judges' runway

Status: accepted, 2026-11-07. The owner can change the defaults listed in [`engine_contract.md`](../engine_contract.md).

## Context

Judges check runway against the README formula, which holds a shock's income and spending level forever. A twist can also ask "do they make it through 6 months?", and the discovery work adds figures the formula doesn't have. The UI needs to know which number is which.

## Decisions

1. **The judges' runway is calculated only by the README formula.** A shock's length, start month and all our additions can't change it. Our figures are separate fields.
2. **"Do they make it?" is a separate result, worked out from unrounded balances month by month.** A runway of 5.96 shows as 6.0 but doesn't last 6 months, so the UI uses `duration.verdict`, not the rounded runway.
3. **Income after the lower income ends is $0 by default.** A benefit ending doesn't mean a new job has started, so this is the cautious reading. `after_ends="income_returns"` gives the other one, and each result states its assumption. It only matters when the months asked exceed the length of the lower income.
4. **The EI weekly maximum sits beside the judges' number and never replaces it.** It's off by default. `ei_capped` is worked out on every income cut, using 729 if none is supplied, so the UI needs no second call. Supplying a maximum adds a fact and `Plan.backup_capped`, while `Plan.backup` stays on the flat rate. It rides on `IncomeCut`, so the `make_plan` signature doesn't change. Added on 2026-11-07, after the owner approved it.
5. **An extra figure that doesn't apply returns `applies=False`, a reason and no number.** "If you adjust" is n/a for pension and transfer accounts, because the evidence comes from cash-only accounts.

## Consequences

- A verdict and a runway can look different in the same result, as in decision 2 or when the months asked run past the benefit. The contract tells the UI which to use.
- The spending response is recomputed when first needed, which adds to startup. `warm_up()` moves that cost to app start.
