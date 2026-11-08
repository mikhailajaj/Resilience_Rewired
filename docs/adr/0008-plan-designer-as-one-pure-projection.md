# ADR 0008: The plan designer as one pure month-by-month projection

Status: proposed, 2026-11-07; revised 2026-11-08 (decisions 2, 3, 5 and 7, alternatives, consequences). Sources: brief Part 1, Part 6 (NEW-SCOPE-2, NEW-SCOPE-3), Part 7 Q2 (WL-1 to WL-9), Part 8, BR-19 to BR-22, RU-24 to RU-26, RU-29, RU-30, OI-17 to OI-20, AC-11 to AC-16, AC-19, [design §3.2 and §4.3](../architecture/j5_plan_designer.md#43-design_plan-projection-adr-0008).

## Context

Three plans (a savings goal, time off and an emergency) share one timeline, with these rules:

- the emergency fund comes first, then the items in tick order;
- a goal is never paid for out of the fund;
- a rate can rise at a payoff month;
- interest is optional;
- there is a 120-month cap.

Closed-form "need ÷ rate" can't express these. The UI may not compute numbers, and the chat should be able to call the same function later.

The owner then framed a goal as a **savings wallet** that fills up, the plan being accomplished when it reaches the target (brief Part 6, NEW-SCOPE-2), and chose to show the deadline cut counting the loan end beside the cautious one (Part 8).

## Decisions

1. **There is one engine function, `goals.design_plan(account_id, PlanRequest) -> PlanDesign`.** It is pure, takes no shock (RU-11), and raises `InvalidPlanError(field)`.
2. **It simulates month by month, 0 to 120, for each rate, with and without the loan end.**
   - The timeline draws the run with the loan end. The no-loan month feeds the "31 months; 22 counting the loan" lines.
   - Interest is monthly at `interest_pct` ÷ 12 on a positive balance (OI-19). `interest_pct` defaults to **0%** and is accepted from 0 to `goals.MAX_INTEREST_PCT = 25.0`, a named constant the owner may change in one place; the page's box reads its upper bound from it (NEW-SCOPE-3).
3. **The order is fixed.** The fund comes first. Then each item in tick order waits until the balance reaches the fund plus its amount. **A goal is accomplished and bought in the same month** (WL-4, confirmed 2026-11-08): its wallet empties, the balance drops by the amount, and saving moves to the next wallet from the next month. The time off runs at no income and spending S (less `bump_judges` after N), and the next item waits for it to end (WL-5). The emergency cost is taken at month 0 (OI-18).
4. **The time-off check reuses the engine's shock path.** It is `duration_with_loan_end` on the projected balance at the start of the time off, or on B at month 0 if the time off isn't saved by month 120 (OI-17, OI-20). The emergency reuses `apply_shock` and `make_plan` with `Shock(one_off_dollars=cost)`.
5. **The deadline answer shows two cuts when the payoff month N ≤ the deadline D** (WL-8, reversing the 2026-11-07 decision "deadline figures ignore the loan end"):
   - `cut_needed`, the cautious cut without the loan end: `max(need ÷ D − rate, 0)`, unchanged, shown first;
   - `cut_with_loan`, counting the loan end on the headline rate: `max((need − Σ_{t=1..D} rate.at(t, N)) ÷ D, 0)`. With interest it is the smallest level cut that reaches `need` by D on the with-loan run, to the cent.

   When there's no running loan or N > D, only the cautious cut is shown and `cut_with_loan` is `None`. `monthly_needed` is unchanged and doesn't depend on the loan (WL-7). Status D adds `P.loan_d`, because its end is only scheduled.
6. **`never` versus more than 120 months:** "never" means no progress by month 120; any other miss is "more than 120 months", never an estimate (RU-26).
7. **Wallets are a presentation of the one balance** (WL-1 to WL-3, WL-9). There is one wallet per item, in the fixed order: the fund (target `target_months` × S), then the items in tick order (a time off's target is `months_off` × S). At any month on a line:
   - the **fund wallet** = min(balance, fund target), which may be negative;
   - the **wallet in progress** (the first item not yet accomplished) = max(balance − fund target, 0);
   - later wallets show $0, and wallets already accomplished show $0 and "accomplished".

   Saving fills the fund, then the items in tick order. An emergency at month 0 therefore comes out of the wallet in progress first, then the fund. `goals.wallets_at(design, rate, month)` returns the split, so the page computes nothing. **The wallet changes no month**: every reached month, timeline value and deadline figure is the projection's.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Closed form per plan | Can't handle the payoff rise, the sequential order, the time off in the middle or interest |
| Compute in the page | Breaks "every number from the engine", can't be swept, and the chat can't reuse it |
| One engine function per plan | Each would rebuild the shared timeline and order; there's one projection, so one function |
| Only the cautious deadline cut (the 2026-11-07 decision 5) | The owner chose both (Part 8). The cautious figure stays first, so nothing is lost when a status D loan slips |
| Only the cut counting the loan end | Overstates when a status D loan slips; hides the cautious reading |
| Wallets as separate balances in the simulation | Gives the same months (the fund must be whole before any goal wallet fills, WL-9) for more state and more tests |
| Interest bound hard-coded in the page | Two places to change; the owner asked for one modifiable constant |

## Consequences

- AC-16's 4,500-account sweep runs without Streamlit.
- Adding a plan kind means adding an `Item` type and a settle rule.
- The page only maps inputs to a `PlanRequest` and words to fields. AC-19 is tested with sentinel values.
- `DeadlineAnswer` gains `payoff_month`, `cut_with_loan` and `on_pace_with_loan`, and `counts_loan_end` now means "the second cut is shown". NEW-COPY-27 is replaced by the with-loan cut line.
- `test_goals.py` pins the brief Part 7 worked examples (66505 and 20111), the wallet split invariant (on every line and month with a fund target, the wallets add up to the balance) and the emergency's split.
- Revisit for a chosen time-off start (OI-17, stretch) or a chat entry point (stretch).

## Changes

| Date | Change | Source |
| :-- | :-- | :-- |
| 2026-11-08 | Decision 5 reversed: the deadline answer shows the cautious cut and, when N ≤ D, the cut counting the loan end | WL-8, brief Part 8 |
| 2026-11-08 | Decision 3 confirms "accomplished = bought" in the same month | WL-4 |
| 2026-11-08 | Decision 7 added: the wallet split and fill order, and the emergency coming out of the wallet in progress first | WL-1 to WL-3, WL-9 |
| 2026-11-08 | Decision 2 states the interest default 0% and the modifiable 25% cap constant | NEW-SCOPE-3 (Part 6) |
| 2026-11-08 | Alternative "Count the loan end in deadlines" removed; three alternatives added | Brief Part 7 records table |
