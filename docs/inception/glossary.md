# Glossary

The links hold the definitions, and the notes only help you find the right one. Not yet reviewed by a domain expert (OI-9).

## Judges' numbers

Defined in the [README](../../README.md#how-judges-calculate-the-numbers). On-screen labels are in the [copy deck](../design/ux/copy.md#2-know-the-customer-b).

| Term | On screen | Note |
| :-- | :-- | :-- |
| I | Typical money in | |
| S | Typical spending | |
| H | Household bills | Rent and utility shocks change this |
| F | Fixed costs | Shown, but not used in runway |
| P | Loan payment | 0 unless the loan is running |
| B, buffer | Buffer | "Buffer left" is B after one-off costs |
| Runway | Runway | See its [states](../engine_contract.md#runway) |
| Gap | Monthly gap | The README's "shortfall". The copy deck says "gap" in sentences |

## Our additions

Defined in [Our additions](../know_the_customer.md#our-additions) unless linked otherwise.

| Term | Note |
| :-- | :-- |
| Income type | `Pension`, `Transfers` or `Cash only`. Also in the [data model](../data_model.md#fields-derived-for-analysis) |
| Bills on standing orders | From an undated snapshot |
| Current fixed costs | Ours, against the judges' F (CON-4) |
| Buffer in months of spending | Shows savings without the money-flow effect |
| Lowest balance | Taken from the last 6 rows |
| If you adjust | [Illustration](../engine_contract.md#extrafigure), not a result (RU-10) |
| One-payment line | [A goal, not a prediction](../engine_contract.md#limits) |

## Shocks, plans and data

| Term | Note | Definition |
| :-- | :-- | :-- |
| Twist | What a judge reads from a card | [README](../../README.md#how-judging-works) |
| Shock | What the engine applies for a twist | [`Shock`](../engine_contract.md#shock) |
| Preset | The shock behind a twist button | [Presets](../engine_contract.md#presets) |
| EI | Employment Insurance; weekly maximum is an optional second figure (OI-4) | [README](../../README.md#canadian-sources-for-sizing-shocks) |
| Verdict | The sentence answering the twist | [`verdict_case`](../engine_contract.md#verdict_case) |
| Makes it, runs out | The two duration answers | [`DurationResult`](../engine_contract.md#durationresult) |
| Goal plan | Emergency fund saving, before any shock | [`GoalPlan`](../engine_contract.md#goalplan-always-before-any-shock) |
| Backup plan | Ordered steps if the shock hits | [`BackupPlan`](../engine_contract.md#backupplan) |
| Income drop event | A fall in deposits, not a confirmed job loss | [Data model](../data_model.md#fields-derived-for-analysis) |
| Running loan | Status C or D | [Data model](../data_model.md#fields-derived-for-analysis) |
| Hard account | Team shorthand for an account in the trap list | [Traps](../discovery.md#live-demo-traps) |

## Words for on-screen messages

| Word | Used in | On screen |
| :-- | :-- | :-- |
| Warning | [`know_the_customer.md`](../know_the_customer.md#warnings), `AccountWarning` | Shown as a note, never a banner (RU-3) |
| Note | [Copy `N.*`](../design/ux/copy.md#2-know-the-customer-b) | Plain line about the customer |
| Fact | [Copy, inline facts](../design/ux/copy.md#4-before-and-after-d), `Fact` | Plain line about this shock |
| Flag | [`discovery.md`](../discovery.md#engine-requirements) | Means show a note or fact |

## Chat (J4)

Defined here; the fields are from the owner's brief for the chat. Not yet reviewed by a domain expert (OI-9).

| Term | Note | Definition |
| :-- | :-- | :-- |
| Card answer | One choice in the chat, stored as a typed field: kind, `Shock` field, value, unit, and source (`button`, `typed` or `parsed`) | [J4.1](use_cases_chat.md#j41-ask-a-twist-with-buttons) |
| Engine output | One engine run: the function, its inputs (account, `Shock`, `through_months`, `target_months`) and its outputs (`verdict_case`, runways, gaps, fact codes, plan states) | RU-18 |
| Engine call line | The `⚙ engine call` text that shows an engine output's inputs | `T.engine_call` |
| Parse result | What the parser returns: `ok`, `partial`, `out_of_range` or `unsure`. These four are the chat's only parse statuses | [Parser](../design/ux/chat_parser.md#results) |
| Kind | Job loss, bills or repair. Mix is job loss plus bills. Not the same as a preset | [Grammar](../design/ux/chat_parser.md#grammar) |
| Stack | A second card added to the current shock (RU-21) | J4.3 |
| Transcript | The Markdown file of the shown messages, card answers and engine outputs, one section per customer | [J4.4](use_cases_chat.md#j44-download-the-transcript) |

## Plan designer (J5)

From the [owner's brief](../briefs/plan_designer_brief.md). Not yet reviewed by a domain expert (OI-9). "Rate" alone always means a monthly saving rate, never interest.

| Term | Note | Definition |
| :-- | :-- | :-- |
| Plan designer | The section at the bottom of Shock and plan with one checkbox per plan | [J5](use_cases.md#j5-design-a-plan) |
| Saving rate | Dollars a month added to the balance. Three are shown: judges' rate, actual change, lean rate | RU-23 |
| Judges' rate | I − S. The engine's `surplus`; can be below 0 | [README](../../README.md#how-judges-calculate-the-numbers) |
| Actual change | Mean of money in minus money out over the last 12 months (`actual_change_last_12`). The headline rate. Called "Actual change, last 12 months" in region E | [`GoalPlan`](../engine_contract.md#goalplan-always-before-any-shock) |
| Lean rate | Ours: I minus lean spending (OI-14) | RU-23 |
| Lean spending | Current fixed costs plus other spending at the account's lowest quarter of months (`LEAN_QUANTILE`); the backup step `lean_months` uses the same level | [`plan.py`](../../app/engine/plan.py) |
| Lean-quarter cut | Flexible spending less the lean level: the most the `lean_months` step saves | RU-23 |
| Flexible spending | S less current fixed costs, at least $0. The same as "spending above fixed costs" in F and G | [`GoalPlan`](../engine_contract.md#goalplan-always-before-any-shock) |
| Savings goal | A named amount, with an optional deadline in months | J5.1 |
| Reached, bought | Reached: the balance is at the fund target plus the amount. Bought: the amount leaves the balance that month | RU-24 |
| Never | Not reached at this rate because it is 0 or below. Not the same as "more than 120 months" | RU-26 |
| Time off | Months with no income (`IncomeCut(0, months_off)`), spending at S | RU-29 |
| Emergency cost | A one-off cost in dollars (`one_off_dollars`) | RU-30 |
| Instant budget | The backup plan's steps and the lean monthly budget, when the buffer can't cover an emergency cost | RU-30 |
| Payoff month | Month N after the last data month when a running loan's last payment is scheduled | RU-27 |
| Timeline | The balance by month for each rate, with markers; also as a table | J5.4 |

```mermaid
classDiagram
    class Customer {
        <<concept>>
        account_id
    }
    class SavingRate {
        <<concept>>
        kind
        dollars_a_month
    }
    class EmergencyFund {
        <<concept>>
        target_months
    }
    class SavingsGoal {
        <<concept>>
        amount
    }
    class TimeOff {
        <<concept>>
        months_off
    }
    class EmergencyCost {
        <<concept>>
        cost
    }
    class RunningLoan {
        <<concept>>
        payoff_month
    }
    class Timeline {
        <<concept>>
        horizon_months
    }
    class Marker {
        <<concept>>
        month
        event
    }
    Customer "1" --> "3" SavingRate : earns
    Customer "1" --> "1" EmergencyFund : keeps first
    Customer "1" --> "0..*" SavingsGoal : saves for
    Customer "1" --> "0..1" TimeOff : plans
    Customer "1" --> "0..1" EmergencyCost : faces
    Customer "1" --> "0..1" RunningLoan : repays
    RunningLoan "1" --> "3" SavingRate : raises at payoff
    Timeline "1" --> "1..3" SavingRate : draws one line per
    Timeline "1" --> "0..*" Marker : shows
    SavingsGoal "1" --> "0..2" Marker : is reached and bought at
