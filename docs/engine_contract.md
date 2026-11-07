# Engine contract

The public API of `app/engine/`, a package with no UI code. Import it only through the package root. Field names here are the contract; modules behind it can change.

```python
from app.engine import get_profile, apply_shock, make_plan, Shock, IncomeCut, get_preset
```

If the UI runs from `app/`, `from engine import ...` also works, because the package uses relative imports.

Startup takes about 5 seconds, measured once on this machine: 1.1s to import, 1.1s to load the CSVs (`transactions.csv` isn't read) and 2.7s to recompute the spending response. Call `warm_up()` when the app starts so this happens before the demo, and cache it in Streamlit with `st.cache_resource`. After that, a shock and plan together take about 3 ms, and an account's first profile about 10 ms. Profiles are then cached. Results are frozen dataclasses, with native Python types and no `NaN`. Call `to_dict(result)` to get plain dicts that `json.dumps` accepts.

## Functions

| Function | Returns | Raises |
| :-- | :-- | :-- |
| `warm_up()` | `None`. Loads the data and the spending response | |
| `get_profile(account_id)` | `CustomerProfile` | `InvalidAccountIdError` |
| `flags(profile)` | The profile's `AccountWarning` tuple (same as `profile.warnings`) | |
| `account_id_range()` | `AccountIdRange(min, max, count)` | |
| `account_overview(account_id)` | `AccountOverview(account_id, income_type, first_month, last_month, n_months, notes)` | `InvalidAccountIdError` |
| `account_flows(account_id)` | `AccountFlows`: actual totals, averages and recent changes | `InvalidAccountIdError` |
| `customer_record(account_id)` | `CustomerRecord`: people, cards, full district details and standing orders | `InvalidAccountIdError` |
| `note_catalogue()` | All 17 `NoteDefinition(code, title, condition, copy_key)`, in document order | |
| `monthly_history(account_id)` | A copy of the account's `monthly_summary` rows as a DataFrame, for charts | `InvalidAccountIdError` |
| `apply_shock(account_id, shock=None, *, through_months=None)` | `ShockResult` | `InvalidAccountIdError`, `InvalidShockError` |
| `list_presets()` | Tuple of `Preset(key, name, twist, shock)` | |
| `get_preset(key, **overrides)` | `Shock` | `InvalidShockError` for an unknown key or bad value |
| `make_plan(account_id, shock=None, *, target_months=3.0, surplus_share=1.0, horizon_months=12, through_months=None)` | `Plan` | `InvalidAccountIdError`, `InvalidPlanError`, `InvalidShockError` |
| `spending_response()` | `SpendingResponse`: the tier values recomputed from the data | |
| `to_dict(result)` | Nested plain dicts | |

`make_plan` with `shock=None` uses the `job_loss_ei` preset. An empty `Shock()` gives the backup state `no_shock`, which is what the UI's Reset passes.

## Errors

All inherit from `EngineError`, and from `ValueError`.

| Error | Fields | When |
| :-- | :-- | :-- |
| `InvalidAccountIdError` | `value`, `reason` (`not_digits` or `not_found`), plus a plain message | Anything but digits (`abc`, `20111.0`, `None`, `True`, `20_111`), or an ID not in the data. Spaces around digits are trimmed |
| `InvalidShockError` | `field`, plus a message | A shock value out of range, `NaN` or infinite |
| `InvalidPlanError` | `field`, plus a message | A plan input out of range |

## Inputs

### `Shock`

Every field is optional, and they mix freely. `Shock()` means no shock.

| Field | Type | Default | Meaning | Allowed |
| :-- | :-- | :-- | :-- | :-- |
| `income_cut` | `IncomeCut` or `None` | `None` | Lower income | |
| `bills_increase_pct` | number | `0` | Percent on H. **15 means 15%** | 0 or more |
| `other_spending_change` | number | `0` | Dollars a month added to spending. Negative lowers it | Any |
| `one_off_dollars` | number | `0` | Dollars paid once | 0 or more |
| `one_off_spending_multiple` | number | `0` | Months of S paid once. Adds to `one_off_dollars` | 0 or more |
| `start_month` | int or `None` | `None` | Calendar month the shock starts. Only adds a January fact; never changes runway | 1 to 12 |

### `IncomeCut`

| Field | Type | Default | Meaning | Allowed |
| :-- | :-- | :-- | :-- | :-- |
| `keep_fraction` | number | `0.55` | Fraction of I kept. **0.55 means 55%**. Any value works, such as 0.57 | 0 to 1 |
| `months` | int or `None` | `None` | How long the lower income lasts. `None` means open-ended | 1 to 120 |
| `after_ends` | str | `"no_income"` | Income after those months: `"no_income"` or `"income_returns"` | |
| `ei_weekly_max` | number or `None` | `None` | EI weekly maximum in dollars a week. `None` is off. Any value typed in works; pass the 2026 value as `EI_WEEKLY_MAX_2026` | 0 or more |

`keep_fraction=1` means no income change: the result has no duration answer unless `through_months` is passed, and the EI maximum has nothing to limit, even if one is supplied.

Inputs are numbers, so the UI converts typed text before calling. Text raises `InvalidShockError`, whose `field` says which input it was. `start_month` works the same way: leave it `None`, or pass a whole number from 1 to 12.

### Presets

| Key | Button (copy deck) | Shock |
| :-- | :-- | :-- |
| `job_loss_ei` | Laid off, EI 55% | keep 0.55, 6 months |
| `furnace_repair` | Furnace dies | one-off of 1 × S |
| `job_loss_bills` | Laid off + bills up 15% | keep 0.55, 6 months, bills +15% |
| `bills_up` | Rent or bills up | bills +15% |
| `no_shock` | Reset (no shock) | nothing |

The README's third twist gives no length, so the 6 months on `job_loss_bills` comes from the copy deck. It only sets the "do they make it" question, not runway.

`get_preset` overrides are `keep_fraction`, `months`, `after_ends`, `ei_weekly_max`, `bills_increase_pct`, `other_spending_change`, `one_off_dollars`, `one_off_spending_multiple` and `start_month`.

## `Runway`

Used everywhere a runway appears.

| Field | Type | Meaning |
| :-- | :-- | :-- |
| `state` | str | `no_buffer`, `no_shortfall` or `months` |
| `months` | float or `None` | `0.0` for `no_buffer`, `None` for `no_shortfall`, otherwise rounded to 1 decimal and at most 120 |
| `label` | str | `0 months`, `No shortfall (120+)` or `7.8 months` |

`state` is `months` with `months` of `0.0` when a tiny buffer rounds down. One account does this with no shock.

`No shortfall (120+)` means gap ≤ 0. It isn't the cap: a runway at the cap reads `120.0 months` with `state` `months`, as on 20134 with no shock.

## `CustomerProfile`

| Group | Fields |
| :-- | :-- |
| Judges' numbers | `I`, `S`, `H`, `F`, `P`, `B`, `gap` (S − I), `runway` |
| Our additions | `bills_on_standing_orders`, `current_fixed_costs`, `buffer_months` (`None` if B ≤ 0 or S = 0), `lowest_balance`, `last_6` (`.I`, `.S`, `.H`, `.F`), `income_type` (`Pension`, `Transfers`, `Cash only`) |
| Below zero | `months_below_zero_last_6`, `months_below_zero_last_12`, `months_below_zero_all`: months with at least one day ending below zero |
| Data range | `first_month`, `last_month`, `n_months`, `opened` |
| Detail | `insurance`, `loan_median`, `bills_hidden`, `leasing`, `latest_balance`, `income_low`, `income_high` (10th and 90th percentile), `income_sources` and `spending_items` (each `LineItem(key, label, typical, share)`, largest first) |
| Loan and orders | `running_loan`, `loan` (`LoanInfo(start, amount, duration_months, monthly_payment, status, status_meaning)` or `None`), `standing_orders` (`OrderInfo(purpose, amount)`, largest first; a blank purpose is `other`) |
| Customer | `age`, `home_district` and `branch_district` (`DistrictInfo(name, average_salary)`), `n_authorized`, `cards` |
| Warnings | `warnings`: `AccountWarning(code, title, message, condition, copy_key)` |

### The 17 warnings

Conditions and counts match `docs/know_the_customer.md`.

| `code` | Title | `copy_key` |
| :-- | :-- | :-- |
| `little_activity` | Little activity | `N.zero` |
| `irregular_income` | Irregular income | `N.no_income` |
| `irregular_spending` | Irregular spending | `N.no_spend` |
| `out_of_date` | Out of date | `N.stale` |
| `no_buffer` | No buffer | `N.neg_buf` |
| `pension_income` | Pension income | `N.pension` |
| `cash_income` | Cash income | `N.cash` |
| `high_flow` | High flow | `None`: the copy deck has no line, so use `title` and `message` |
| `bills_missing_from_h` | Bills missing from H | `N.bills_gap` |
| `no_regular_bills` | No regular bills visible | `N.no_bills` |
| `recent_loan_missed` | Recent loan missed by F | `N.loan_recent` |
| `finished_loan_counted` | Finished loan still counted | `N.loan_done` |
| `loan_in_trouble` | Loan in trouble | `N.loan_trouble` |
| `missed_payment` | Missed payment | `N.missed` |
| `went_negative` | Went negative | `N.low` |
| `thin_low_point` | Thin low point | `N.thin` |
| `leasing_not_counted` | Leasing not counted | `N.leasing` |

## `AccountFlows`

The judges' I and S are separate medians, so S − I isn't how much the balance changes. These fields show what actually moved. Money in minus money out equals the change in month-end balance on every row of every account, within 14 cents, and every account has at least 12 rows.

| Field | Meaning |
| :-- | :-- |
| `n_months` | Rows on the account |
| `total_in`, `total_out`, `total_change` | Sums over all rows |
| `average_in`, `average_out`, `average_change`, `median_change` | Per month, over all rows |
| `change_last_12`, `change_last_6` | Mean of money in − money out over the last 12 and last 6 rows |
| `months_in_above_out`, `months_out_above_in` | Rows in each direction |
| `highest_in`, `highest_in_month`, `lowest_in`, `lowest_in_month` | Largest and smallest money in |
| `top_5_months_share_of_in` | Share of all money in from the 5 largest months. `None` if there's no money in |
| `lumpy_income` | The top 5 months hold at least twice their even share of money in |

## `CustomerRecord`

| Field | Meaning |
| :-- | :-- |
| `statement_frequency` | From `accounts.csv` |
| `people` | `PersonDetail(client_id, role, gender, birth_date, age, home_district, card_type, card_issued)`, owner first |
| `home_district`, `branch_district` | `DistrictDetail(name, region, inhabitants, urban_ratio_pct, average_salary, unemployment_rate_2022, unemployment_rate_2023, entrepreneurs_per_1000, crimes_2022, crimes_2023)` |
| `orders` | `OrderDetail(purpose, amount, to_bank, to_account)`, largest first |

## `ShockResult`

| Field | Meaning |
| :-- | :-- |
| `account_id`, `shock` | The request |
| `no_shock` | True when the shock requests no change. `keep_fraction=1` counts as no change, and `start_month` alone doesn't count as a change |
| `before` | `Figures` with no shock |
| `after` | `Figures` after the shock |
| `one_off` | One-off cost in dollars |
| `bills_added` | Dollars a month added by the bills increase (judges' H basis) |
| `runway`, `buffer_left`, `gap`, `income_after`, `spending_after` | **The judges' numbers**, repeated from `after` for short access |
| `verdict_case` | Picks the copy deck's sentence. See below |
| `duration` | `DurationResult`, or `None` when no length is known |
| `bills_on_standing_orders` | `ExtraFigure`, our addition |
| `if_you_adjust` | `ExtraFigure`, our illustration |
| `ei_capped` | `CappedFigure`, our addition. Always present |
| `facts` | Tuple of `Fact(code, message)` |

`Figures` has `income`, `spending`, `buffer`, `gap` and `runway`.

`runway`, `income_after`, `gap`, `verdict_case`, `duration` and the two `ExtraFigure`s always use the judges' flat rate, even with `ei_weekly_max` set. Only `ei_capped` and `Plan.backup_capped` use the maximum.

### `verdict_case`

Checked in this order.

| Value | When |
| :-- | :-- |
| `no_shock` | `no_shock` is true |
| `runway_zero` | Buffer left ≤ 0. If B was already ≤ 0, `facts` also has `no_buffer_before_shock`, so don't blame the cost |
| `no_shortfall` | Gap ≤ 0 |
| `income_cut_makes_it` | Income cut with a length, and `duration.verdict` is `makes_it` |
| `income_cut_runs_out` | Income cut with a length, and `duration.verdict` is `runs_out` |
| `income_cut_open_ended` | Income cut with no length |
| `cost_or_bills_only` | Anything else |

`no_shortfall` describes the shocked level, so it's a separate verdict and never reads "runs out in month N". If `through_months` runs past the lower income, `duration.verdict` can still be `runs_out` on the same result; `duration.assumption_applied` is then true.

### `DurationResult`

Answers "do they make it through N months?". N is `through_months` if passed, otherwise `income_cut.months`.

| Field | Meaning |
| :-- | :-- |
| `months_asked` | N |
| `verdict` | `makes_it` or `runs_out` |
| `runs_out_in_month` | First month that can't be covered, or `None` on `makes_it`. `0` means no buffer before month 1 |
| `months_short` | N minus the months the money lasts, to 1 decimal, or `None` on `makes_it` |
| `money_lasts_months` | Months until the balance goes below zero on this path, to 1 decimal, or `None` if it doesn't within 120 |
| `balance_end`, `lowest_balance` | On this path. Can be negative |
| `shortfall_at_end` | Dollars missing at month N, or 0 |
| `balance_by_month` | Balances for month 0 to N, for a chart |
| `benefit_months` | Length of the lower income, or `None` |
| `after_ends`, `assumption_applied`, `assumption` | What's assumed after the lower income ends, whether it affects this answer, and that assumption in words |

**The UI must use `verdict` and `runs_out_in_month`.** Don't work them out from the rounded runway: 5.96 months shows as `6.0`, but that doesn't last 6 months, and the copy deck's `ceil(R)` can be a month early. An exact 4.0 months makes it through month 4 and runs out in month 5.

Assumptions on this path, separate from the README runway, which is never affected:

- A surplus month adds to the balance.
- Bills and other spending changes last the whole period.
- The one-off is paid before month 1.
- After the lower income ends, income is 0 by default. EI ending doesn't mean a new job has started, so this is the cautious reading. Pass `after_ends="income_returns"` for the other one.

### `ExtraFigure`

| Field | Meaning |
| :-- | :-- |
| `label` | Plain label |
| `applies` | False means show `n/a` |
| `reason` | Why, as a code (below) |
| `runway` | `Runway`, or `None` when it doesn't apply. Never a guess |
| `spending_after` | Spending used for this figure, or `None` |
| `is_illustration` | True on `if_you_adjust` |
| `note` | One plain sentence |
| `metadata` | Basis of the figure. See below |

| Figure | `reason` when it applies | `reason` when it doesn't |
| :-- | :-- | :-- |
| `bills_on_standing_orders` | `bills_missing_from_h` | `no_bills_shock`, `bills_not_missing` |
| `if_you_adjust` | `cash_only_response` | `pension_income`, `transfers_income`, `no_income_lost`, `no_typical_spending` |

`bills_on_standing_orders` uses spending = S + pct × max(H, orders) + other. `metadata` has `bills_basis`.

`if_you_adjust` uses spending = max(spending after − response × income lost, 0), on the same buffer left. The tier comes from B ÷ S before the shock, as in `discovery.ipynb`. The 6+ months tier has a response of 0, so it applies and equals the judges' number. `metadata` has `illustration` (True), `tier`, `response_per_dollar`, `events_in_tier`, `evidence` and `statement`, which says it's an illustration and not a forecast.

### `CappedFigure`

Income = min(`keep_fraction` × I, `weekly_max` × 52 ÷ 12). Everything else follows the README formula.

| Field | Meaning |
| :-- | :-- |
| `label` | `Runway with the EI weekly maximum` |
| `available` | False when there's no income cut. Show `n/a` |
| `reason` | `max_applied`, `max_not_reached` or `no_income_cut` |
| `switched_on` | True if the shock supplied `ei_weekly_max` |
| `weekly_max`, `weekly_max_source` | The value used, and `supplied` or `default` |
| `monthly_max` | `weekly_max` × 52 ÷ 12 |
| `max_applied` | True if `keep_fraction` × I is above the monthly maximum. Exactly at it isn't limited |
| `income_after`, `gap`, `runway` | On capped income, or `None` when not available |
| `effective_share_of_income` | `income_after` ÷ I. `None` if I = 0 or not available |
| `duration` | `DurationResult` on capped income, or `None` when no length is known |
| `note` | One plain sentence |

**Decision: the figure is worked out even with the switch off**, using `EI_WEEKLY_MAX_2026`, so the UI can show it beside the judges' number without a second call. `switched_on` and `weekly_max_source` show which case it is. The switch doesn't change the headline. It adds the `ei_weekly_max_applied` fact and `Plan.backup_capped`.

`EI_WEEKLY_MAX_2026` is 729, `EI_WEEKLY_MAX_2026_SOURCE` holds its source, and `WEEKS_PER_MONTH` is 52 ÷ 12.

With 729 across all 4,500 accounts, as in `docs/shock_sizing.md`: 2,574 limited (57.2%), median runway 5.7 months, 51.2% under 6 months, 27.9% under 3 months, no pension account limited, and a median of 25% of I kept on limited accounts.

### Fact codes

`ei_weekly_max_applied`, `layoff_doesnt_fit_pension`, `income_cut_no_income`, `bills_shock_no_bills`, `bills_shock_too_small`, `one_off_zero_spending`, `no_buffer_before_shock`, `one_off_exceeds_buffer`, `data_stops_early`, `little_activity`, `spending_floored_at_zero`, `runs_into_january`.

## `Plan`

`Plan` has `account_id`, `goal`, `backup`, `low_balance`, `facts` and `backup_capped`.

`backup` always uses the judges' flat rate. `backup_capped` is a second `BackupPlan` on capped income, or `None` unless the shock has an income cut and supplies `ei_weekly_max`. The `make_plan` signature didn't change: the maximum travels on the shock.

### `GoalPlan` (always before any shock)

| Field | Meaning |
| :-- | :-- |
| `state` | `already_there`, `on_track`, `no_surplus`, `no_regular_spending` |
| `target_months`, `target_amount` | Target; amount is target × S, `None` if S = 0 |
| `current_buffer`, `still_needed`, `months_covered` | B, what's left to save, B ÷ S |
| `surplus`, `surplus_share` | I − S, and the share set aside |
| `monthly_amount`, `months_to_goal` | Savings per month and whole months to reach the target. `0` and `0` on `already_there`, `0` and `None` when no saving is possible |
| `reaches_within_horizon` | Whether `months_to_goal` ≤ `horizon_months` |
| `below_zero_by` | Dollars needed to get B back above 0 first, otherwise 0 |
| `cut_to_break_even` | On `no_surplus`, spending cut that makes I = S |
| `cut_to_reach_in_horizon` | On `no_surplus`, spending cut that reaches the target in `horizon_months` |
| `flexible_spending`, `cut_is_possible` | Spending above current fixed costs, and whether the break-even cut fits within it |
| `savings_path` | Up to 6 `PathPoint(month, balance)` rows for the table |
| `actual_change_last_12` | Mean of money in − money out over the last 12 rows |

Medians don't add up, so a positive `surplus` isn't always money that actually stays. When `actual_change_last_12` ≤ 0 and `surplus` > 0, `facts` has `surplus_not_seen_in_balance`. The reverse also happens: when `actual_change_last_12` > 0 and `surplus` < 0, `facts` has `balance_rose_despite_gap`.

### `BackupPlan`

| Field | Meaning |
| :-- | :-- |
| `state` | `no_shock`, `no_cuts_needed`, `cuts_needed`, `cuts_not_enough`, `no_buffer` |
| `income_basis` | `flat` on `backup`, `ei_weekly_max` on `backup_capped` |
| `shock`, `through_months` | The request, and the length tested (or `None`) |
| `runway_before`, `runway_after_steps` | Shock runway on this plan's `income_basis` (the judges' number when `flat`), and runway after every step |
| `makes_it_before`, `makes_it_after_steps` | Against `through_months`, otherwise `None` |
| `fixed_costs` | Current fixed costs + bills added by the shock |
| `flexible_spending` | Biggest cuttable amount: S (lowered by any negative `other_spending_change`) − current fixed costs, at least 0 |
| `fixed_share_of_spending` | Current fixed costs ÷ S, capped at 1. `None` if S = 0 |
| `fixed_exceeds_spending` | True if the cap applied, which is normal for a recent loan |
| `cut_to_last` | Spending cut a month needed to last `through_months`. `None` with no length or no buffer |
| `cut_to_last_share_of_spending`, `cut_to_last_share_of_flexible` | That cut as shares of S and of flexible spending, or `None` |
| `cut_to_close_gap` | Spending cut a month that stops the buffer falling |
| `cut_is_possible` | The needed cut fits within flexible spending |
| `runway_if_all_flexible_cut` | For "Even with all other spending cut" |
| `cover_needed`, `months_to_cover` | Dollars to get the buffer back to 0, and months at the current surplus (`None` if there's no surplus) |
| `months_to_low_balance_line` | Months until the balance reaches one loan payment under the shock. `0.0` if already there, `None` with no loan or no shortfall |
| `steps` | Ordered tuple of `BackupStep` |

`BackupStep` has `order`, `code`, `action` (plain sentence), `monthly_saving`, `one_time_amount`, `needs_agreement`, `runway_before`, `runway_after` and `adds_months` (`None` if either end isn't a number of months).

Step codes, in order. Steps stop once the cut needed is reached.

| Code | Amount |
| :-- | :-- |
| `cover_buffer` | Only when buffer left ≤ 0: the one-time amount to get back to 0 |
| `cancel_other_orders` | Unlabelled standing orders, capped at flexible spending. 99.9% of these have matching transfers, so they are in S |
| `lean_months` | Down to the account's own lowest quarter of months for spending above fixed costs |
| `all_flexible` | Whatever flexible spending remains |
| `ask_lender` | Only with a running loan. `needs_agreement` is True, because it isn't the customer's decision |

When runway is 0, steps stay computed: `cover_buffer` gives the amount, and the later steps show the cut that closes the gap. Their `runway_after` stays 0, because cuts don't create a buffer.

### `LowBalanceGoal`

`None` unless a loan is running. Fields: `payment`, `lowest_balance`, `met` (lowest ≥ payment), `top_up_needed`, `months_to_line` at the goal's monthly amount (`None` if there's no saving).

## Defaults the owner can change

| Decision | Default | Change it with |
| :-- | :-- | :-- |
| Emergency fund target | 3 months of spending | `target_months`, so 6 also works |
| Share of surplus saved | All of it (`1.0`), so no invented percentage | `surplus_share` |
| Income kept | Any value from 0 to 1, not only 5% steps | `keep_fraction` |
| Start month | Optional, off by default; never changes the judges' runway | `start_month` |
| EI weekly maximum | Off; the headline stays at the judges' flat rate. The capped figure still shows, using 729 | `ei_weekly_max` |
| Capped figure with the switch off | Worked out using 729 | Code: `shock.py` |
| "If you adjust" on pension and transfer accounts | `n/a` with a reason, because the evidence comes from cash-only accounts | Code: `shock.py` |
| Income after the lower income ends | $0 | `after_ends` |
| Goal plan when S = 0 | `no_regular_spending`, no target | Code: `plan.py` |

## Limits

- This isn't financial advice.
- The EI weekly maximum treats typical money in as insurable earnings. Much of that flow may not be pay, so the true benefit could be lower still. Tax and EI eligibility aren't modelled. `if_you_adjust` and `bills_on_standing_orders` stay on the flat rate.
- The "if you adjust" runway comes from falls in deposits on cash-only accounts, not confirmed job losses, and those falls are deeper than a 45% cut. Don't quote it as a result.
- The one-payment line was found on balances before a loan was granted, with thresholds chosen on the same data. Here it's a goal and warning sign, not a prediction.
- Standing orders are an undated snapshot.
- Not moved from the notebook: `rank_text` ("compared with other accounts"), `customer_report` and `plot_account`, which are display code.

## Conflicts in `docs/inception/scope.md`

How the engine settles the items that touch it. The UX designer owns the wording in the design docs.

| ID | The engine's answer | Behaviour change |
| :-- | :-- | :-- |
| CON-1 | Use `duration.verdict` and `runs_out_in_month`. Never compare the rounded runway with the length, or use `ceil(R)` | None |
| CON-2 | Income is $0 after the lower income ends unless `after_ends` says otherwise, so "before income recovers" isn't what the engine assumes. `duration.assumption` has the wording | None |
| CON-3 | `if_you_adjust` can be `n/a` for four reasons: `pension_income`, `transfers_income`, `no_income_lost` and `no_typical_spending`. The furnace twist is always `n/a`, because income isn't lost. Income type is checked first, so 20134 gives `transfers_income` on both twists | None |
| CON-4 | `backup.fixed_costs` is current fixed costs plus bills added, which isn't F. `fixed_share_of_spending` uses current fixed costs alone, without bills added | None |
| CON-5 | `runway_zero` always comes with exactly one fact: `no_buffer_before_shock` (don't blame the cost) or `one_off_exceeds_buffer` | None |
| CON-7 | `no_shortfall` is its own verdict. See [`verdict_case`](#verdict_case) | None |
| CON-8 | `No shortfall (120+)` means gap ≤ 0, and the cap reads `120.0 months`. See [`Runway`](#runway) | None |
| CON-9 | `income_type` is one of our additions. Where it's shown and how it's labelled is for the owner | None |
| CON-10 | For 20111, the engine gives data from 2022-11, layoff runway 3.4 and standing-order bills of $0. 3.2 is only the figure with the EI maximum (`ei_capped.runway`), which runs out in month 4 | None |
| CON-11 | Warnings follow `docs/know_the_customer.md`: `no_regular_bills` fires on 1,063 accounts, when H is 0 and bills aren't missing from H. `N.no_bills` as written (H = 0, 1,225 accounts) would also fire alongside `bills_missing_from_h` | None |

CON-6 is wording only. The engine's `if_you_adjust` text calls it an illustration and doesn't say people cut back.

| Open item | The engine's answer |
| :-- | :-- |
| OI-1 | `keep_fraction` takes any value. The slider step is a UI choice |
| OI-4 | Now modelled, off by default. This replaces the "not modelled" default in `scope.md` and `shock_sizing.md` |
| OI-5 | `target_months` defaults to 3 and takes any value above 0 |
| OI-6 | `one_off_dollars` and `other_spending_change` take dollars, and a rent rise in dollars can use `other_spending_change`. `one_off_dollars` adds to `one_off_spending_multiple` |
| OI-7 | `start_month` is optional and off by default. It only adds the `runs_into_january` fact |
