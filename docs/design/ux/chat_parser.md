# Chat free-text parser (J4.2)

The parser is deterministic: lower-case the text, match keywords and regular expressions, and return a parse result. It never calls a model or a network (RU-15), and nothing runs before the presenter confirms (RU-17). Fields are the engine's [`Shock` and `IncomeCut`](../../engine_contract.md#shock).

## Grammar

`N` is digits, with optional commas and decimals, or a word from one to twelve. A dollar amount is `$N`, `N dollars` or `$Nk` (thousands). A percent is `N%`, `N percent` or `N per cent`.

| Kind | Found by | Size phrases | `Shock` field |
| :-- | :-- | :-- | :-- |
| Job loss | `laid off`, `layoff`, `lose` or `lost` + `job`, `job loss`, `unemployed`, or any keep phrase | `EI N%`, `EI at`, `pays` or `keeps N%`; `N% of (their usual) income` | `income_cut.keep_fraction` = N / 100 |
| | | `income` or `pay` `drops`, `falls` or `cut` **to** N% | `keep_fraction` = N / 100 |
| | | the same verbs **by** N% | `keep_fraction` = (100 − N) / 100 |
| | | `no EI`, `no income` | `keep_fraction` = 0 |
| | | `for N months`, `N months`, `N-month`; `a year`, `one year` = 12 | `income_cut.months` = N |
| | | `until it runs out`, `no end`, `open-ended` | `months` = `None` |
| | | `then back to work`, `then income returns` | `after_ends` = `"income_returns"` |
| Bills | `bills`, `rent`, `utilities`, `hydro` + `up`, `go up`, `rise` or `+` | N% | `bills_increase_pct` = N |
| | | `$N` (`a month`, `per month` or `monthly` optional) | `other_spending_change` = N |
| Repair | `repair`, `furnace`, `roof`, `car`, `surprise cost`, `one-off` | `N` or `a (full) month(s) of (their) (typical) spending` | `one_off_spending_multiple` = N |
| | | `$N` | `one_off_dollars` = N |

## Results

| Result | When | Chat does |
| :-- | :-- | :-- |
| `ok` | At least one kind, every size found, all in range | `T.confirm` |
| `partial` | A kind found with a size missing | `T.partial`, then asks only the missing size |
| `out_of_range` | A size outside RU-22, such as keep over 100%, months 0, over 120 or not whole | `T.out_of_range` |
| `unsure` | Any of U1 to U6 | `T.unsure` and the twist buttons |

When several apply, `unsure` wins, then `out_of_range`, then `partial`.

- **U1:** no kind found.
- **U2:** a number is left that no rule used.
- **U3:** one kind sized twice.
- **U4:** a decrease word (`down`, `drop`, `less`) on bills, or `drops N%` with neither `to` nor `by`.
- **U5:** a bare fraction such as `0.55`, with no `%`.
- **U6:** a calendar month or a negation (`not`, `n't`) next to a kind word. A month name shows `T.unsure_month` (OI-7).

## Acceptance tests

Each row is a test on the parser alone; no engine call is needed. `IC` is `IncomeCut`.

| ID | Input | Expected |
| :-- | :-- | :-- |
| PT-01 | laid off, EI 55% for 6 months | `ok` `Shock(income_cut=IC(0.55, 6))` |
| PT-02 | laid off, EI 55% for 6 months and bills up 15% | `ok` `IC(0.55, 6)`, `bills_increase_pct=15` |
| PT-03 | The furnace dies, and the repair costs a full month of their typical spending. | `ok` `one_off_spending_multiple=1` |
| PT-04 (changed, D2 / ADR 0010) | They lose their job (EI at 55%) and their household bills go up 15% in the same month. | `ok`: `IC(0.55, 6)` with the months source `assumed` (shown "6 months (assumed)"), `bills_increase_pct=15`; the confirm shows "for 6 months (assumed)" and stays mandatory |
| PT-05 | Rent or household bills go up 15%. | `ok` `bills_increase_pct=15` |
| PT-06 | rent up $300 a month | `ok` `other_spending_change=300` |
| PT-07 | car repair $2,500 | `ok` `one_off_dollars=2500` |
| PT-08 | roof repair $1.5k | `ok` `one_off_dollars=1500` |
| PT-09 | EI 57% for 12 months | `ok` `IC(0.57, 12)` |
| PT-10 | laid off for a year, EI 55% | `ok` `IC(0.55, 12)` |
| PT-11 | laid off, EI 55% until it runs out | `ok` `IC(0.55, None)` |
| PT-12 | laid off | `partial`: asks keep, then months |
| PT-13 | income drops to 70% for three months | `ok` `IC(0.7, 3)` |
| PT-14 | income cut by 30% for 3 months | `ok` `IC(0.7, 3)` |
| PT-15 | income drops 30% | `unsure` (U4) |
| PT-16 | EI 150% for 6 months | `out_of_range`: keep is 0 to 100% |
| PT-17 | laid off, EI 55% for 200 months | `out_of_range`: months are 1 to 120 |
| PT-18 | laid off, EI 55% for 2.5 months | `out_of_range`: months are whole |
| PT-19 | laid off, no EI, for 3 months | `ok` `IC(0, 3)` |
| PT-20 | laid off, EI 55% for 6 months, then back to work | `ok` `IC(0.55, 6, after_ends="income_returns")` |
| PT-21 | bills down 10% | `unsure` (U4) |
| PT-22 | the furnace dies in January | `unsure` (U6), `T.unsure_month` |
| PT-23 | bills up 15% and rent up 10% | `unsure` (U3) |
| PT-24 | EI 0.55 for 6 months | `unsure` (U5) |
| PT-25 | what if they win the lottery | `unsure` (U1) |

## J5 additions (R5, D2; placeholders until the copy owner and QA sign off)

A job kind plus a bills or repair kind with no length found gives months 6, source `assumed`, status `ok`. A bare "laid off" still asks (PT-12). "Half a year", "half-year" and "half year" read as 6 months and are taken before years. Number words read: one to twenty, thirty to ninety, "hundred", and compounds such as "fifty five" and "fifty-five".

| ID | Input | Expected |
| :-- | :-- | :-- |
| NEW-PARSER-1 | laid off, EI 55% for half a year | `ok` `IC(0.55, 6)` |
| NEW-PARSER-2 | EI pays 55% for half a year | `ok` `IC(0.55, 6)` (was `IC(0.55, 12)`) |
| NEW-PARSER-3 | bills up fifteen percent | `ok` `bills_increase_pct=15` |
| NEW-PARSER-4 | laid off, EI fifty-five percent for twenty months | `ok` `IC(0.55, 20)` |
| NEW-PARSER-5 | laid off, EI 55% for a year and bills up twenty percent | `ok` `IC(0.55, 12)`, `bills_increase_pct=20` |
| NEW-PARSER-6 | laid off and the furnace dies, EI 55% | `partial`: `IC(0.55, 6)` with months `assumed`; asks the repair size; the length stays assumed |
