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
