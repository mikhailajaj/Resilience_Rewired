# Requirements

"Serves" names a [judging criterion](../../README.md#how-judging-works). That mapping is our judgement. A requirement is settled unless it says Gated, and gates are in [scope](scope.md#open-items-for-the-owner).

## Business requirements

### Judge

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-1 | As a judge, I want any `account_id` to show income, bills and fixed costs, buffer and runway, so that I can test a customer I choose | [README](../../README.md#the-challenge) | J1 | Data Use |
| BR-2 | As a judge, I want to apply and resize a shock or a mix, so that I can run my twist live. **Gated on OI-1, OI-6** for values the controls can't set | [README](../../README.md#the-challenge) | J2, J4.1, J4.3 | Data Use |
| BR-3 | As a judge, I want a goal plan and a backup plan from the customer's own numbers, so that I can judge the fit. **Default target gated on OI-5** | [README](../../README.md#the-challenge) | J3, J4.3 | Impact |
| BR-4 | As a judge, I want numbers from the published definitions, so that I can check my worked answers | [README](../../README.md#how-judges-calculate-the-numbers) | J1, J2 | Data Use |
| BR-5 | As a judge, I want a direct answer to "do they make it?", so that I don't have to infer it | [ADR 0001](../adr/0001-engine-shock-semantics.md) | J2, J4.1 | Communication |
| BR-6 | As a judge, I want to see where flat spending breaks, beside my number, so that I can judge the discovery | [Biggest finding](../discovery.md#biggest-finding) | J2 | Discovery |

### Presenter and team

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-7 | As a presenter, I want a designed state for every hard account and invalid ID, so that no judge's pick looks like a bug | [Live demo traps](../discovery.md#live-demo-traps) | J1, J2, J3 | Communication |
| BR-8 | As a presenter, I want ready sentences, instant recalculation and numbers readable across a room, so that a twist fits in 3 minutes | [Flows](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) | J1, J2, J3 | Communication |
| BR-9 | As the team, I want a demo video, repo, write-up and sources submitted, so that the entry is complete. Hosting settled (OI-8); repo visibility open (OI-13) | [README](../../README.md#what-to-submit-on-devpost) | None: see [checklist](scope.md#submission-checklist) | All |

### Bank customer (offstage)

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-10 | As a customer, I want the team to be clear about what my data can't show, so that nobody reads too much into it | [Known limits](../know_the_customer.md#known-limits) | J1, J2, J3 | Impact |
| BR-11 | As a customer, I want a layoff that doesn't fit my pension marked, and missed loans or bills shown beside the typical figure, so that my numbers aren't misread | [Engine requirements](../discovery.md#engine-requirements) | J1, J2, J3 | Discovery |
| BR-12 | As a customer with a running loan, I want a goal to keep my lowest balance above one payment, so that I have a line to act on | [Lowest balance](../discovery.md#the-lowest-balance-predicts-default) | J3, J4.3 | Discovery |
| BR-13 | As a customer, I want a shock's start month considered, so that one running into January isn't undersized. **Gated on OI-7** | [Timing](../discovery.md#timing-changes-the-cost-of-a-shock) | J2 | Discovery |

### Chat assistant (J4)

Source for all five: the owner's brief for the chat, dated 2026-11-07, which chose a guided chat with no language model.

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-14 | As a judge, I want to give my twist card as buttons or in my own words, and see the sizes used, so that I know the run matches my card | Owner's brief | J4, J4.1, J4.2 | Data Use |
| BR-15 | As a presenter, I want the chat to ask for one size at a time, with common values as buttons, so that I can run any card without hunting for sliders | Owner's brief | J4, J4.1, J4.3 | Communication |
| BR-16 | As a judge, I want each answer to show the engine call behind it, so that I can see the chat didn't make the numbers up | Owner's brief, RU-1 | J4, J4.1, J4.2, J4.3 | Data Use |
| BR-17 | As the team, I want a transcript of the card answers and engine outputs, so that we keep a record of each twist | Owner's brief | J4, J4.4 | Communication |
| BR-18 | As a customer, I want my data to stay inside the app when it's hosted online, so that no outside service reads it | Owner's brief, OI-8 | J4, J4.2, J4.4 | Impact |

### Plan designer and loan end (J5)

Source for all five: the [owner's brief](../briefs/plan_designer_brief.md) of 2026-11-07, Parts 1 and 2. Feasibility is in [scope](scope.md#plan-designer-j5-feasibility).

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-19 | As a judge, I want to give a customer a savings goal with an amount and an optional deadline, and see the months to reach it at three labelled rates, so that I can judge a plan built on their own numbers | Brief Part 1 | J5, J5.1, J5.4 | Impact |
| BR-20 | As a customer, I want to know what time off work would cost and whether my money lasts through it, so that I can plan a break | Brief Part 1 | J5, J5.2, J5.4 | Impact |
| BR-21 | As a customer, I want to know whether my buffer covers an emergency cost, with a budget for straight away if it doesn't, so that I know what to do first | Brief Part 1 | J5, J5.3, J5.4 | Impact |
| BR-22 | As a presenter, I want every plan on one timeline, with a table view, so that the room and a screen reader can both follow it | Brief Part 1 | J5, J5.4 | Communication |
| BR-23 | As a customer with a running loan, I want plans to count the loan ending, so that the plan doesn't assume I pay it for ever | Brief Part 2 | J3, J5, J5.1, J5.2, J5.4 | Discovery |

## Business rules

"Owner's brief" means the instructions for this release, dated 2026-11-07.

| ID | Rule | Source | Applies to |
| :-- | :-- | :-- | :-- |
| RU-1 | Judges' numbers come first, use only the README formula, and are never replaced | [ADR](../adr/0001-engine-shock-semantics.md#decisions), [our additions](../know_the_customer.md#our-additions) | J1, J2, J3, J4.1, J5, J5.1 |
| RU-2 | Our additions are labelled and sit beside the judges' numbers | [Our additions](../know_the_customer.md#our-additions), [copy](../design/ux/copy.md#5-our-numbers-e) | J1, J2, J4.1, J5, J5.1 |
| RU-3 | No warning banners in the UI. Every message is plain inline text | [Copy](../design/ux/copy.md), owner's brief | J1, J2, J3 |
| RU-4 | Method caveats live in the docs. Customer facts are plain inline data | [Copy](../design/ux/copy.md#2-know-the-customer-b), [contract](../engine_contract.md#limits), owner's brief | J1, J2, J3 |
| RU-5 | No Tangerine logo or proprietary font unless the organisers confirm | [Logo](../design/research/tangerine_brand.md#5-logo-v-for-observation-u-for-rules), [font](../design/research/tangerine_brand.md#8-font-recommendation), owner's brief | J1, J2, J3 |
| RU-6 | Runway follows the README formula, including its 0, no-shortfall and capped cases | [README](../../README.md#how-judges-calculate-the-numbers) | J1, J2, J3, J4.1 |
| RU-7 | "Do they make it?" comes from the engine's month-by-month verdict, never the rounded runway | [ADR decision 2](../adr/0001-engine-shock-semantics.md#decisions) | J2, J3, J4.1 |
| RU-8 | After the lower income ends, income is $0 by default, and results state this | [ADR decision 3](../adr/0001-engine-shock-semantics.md#decisions) | J2, J3, J4.1 |
| RU-9 | A figure that doesn't apply shows `n/a` with a reason, never a guess | [ADR decision 4](../adr/0001-engine-shock-semantics.md#decisions) | J1, J2, J4.1, J5, J5.1 |
| RU-10 | "If you adjust" is an illustration. Don't quote it as a result | [Limits](../discovery.md#limits) | J2 |
| RU-11 | The goal plan uses no-shock numbers. The backup plan uses the current shock. The plan designer uses no-shock numbers, plus its own time-off and emergency shocks | [Walkthrough P7](../design/ux/walkthrough.md#problems-found-and-fixed), brief Part 1 | J3, J4.3, J5, J5.1 |
| RU-12 | No section disappears for a valid account, and an old customer never stays on screen with a new ID | [Walkthrough P9](../design/ux/walkthrough.md#problems-found-and-fixed), [wireframes A2](../design/ux/wireframes.md#a2-loading) | J1, J2, J3, J4.3 |
| RU-13 | Shock changes recalculate at once. Changing the ID resets the shock | [Flow rules](../design/ux/flows.md#1-main-flow-any-user-any-account) | J2, J4.3 |
| RU-14 | Every outside source used is linked, and the data is credited | [README](../../README.md#credits) | Submission (no use case) |
| RU-15 | The chat makes no network call and uses no language model. Every number comes from `get_profile`, `apply_shock`, `make_plan`, `get_preset` or `list_presets` | Owner's brief | J4, J4.1, J4.2, J4.3, J4.4 |
| RU-16 | Result sentences come from `app/ui/text.py`. A chat line that shows one of our figures ends "(ours)" | RU-1, RU-2 | J4.1, J4.2, J4.3 |
| RU-17 | Free text is never run before the presenter confirms the reading. If the parser is unsure, the chat offers the buttons and doesn't guess | Owner's brief | J4, J4.2 |
| RU-18 | Every choice is stored as a card answer, and every engine run as an engine output. The transcript is built only from these and the shown messages | Owner's brief | J4.1, J4.2, J4.3, J4.4 |
| RU-19 | Only the latest message has live buttons. Earlier ones show the choice as text | Owner's brief | J4.1, J4.2, J4.3 |
| RU-20 | A new customer restarts the chat. Only the current customer is on screen, and the transcript keeps earlier ones in labelled sections | RU-12, RU-13 | J4, J4.1, J4.3, J4.4 |
| RU-21 | A stacked card of another kind adds to the shock. One of the same kind replaces the earlier size, and the chat says so | Owner's brief: "Add another shock (stack)" | J4.3 |
| RU-22 | Sizes are limited only by the engine: keep 0 to 100%, months a whole number from 1 to 120, bills and one-offs 0 or more. Sending to the controls needs values they hold: a set length, income not returning, bills box up to 500%, rent up to $20,000, one-off months 0 to 3 in steps of 0.25 or dollars up to $100,000, and one one-off kind | [`shock.py`](../../app/engine/shock.py), [`shock_and_plan.py`](../../app/app_pages/shock_and_plan.py) | J4.1, J4.2, J4.3 |
| RU-23 | The plan designer shows three monthly saving rates side by side, labelled: the judges' I − S, the actual change over the last 12 months (`actual_change_last_12`, the **headline**), and the lean rate (ours). Lean rate model **gated on OI-14** | Brief Part 1, RU-1, RU-2 | J5, J5.1, J5.2, J5.3, J5.4 |
| RU-24 | The emergency fund (J3's target, so OI-5) is saved first, then goals in the order ticked. A goal is bought only when the balance stays at or above the fund target after it | Brief Part 1, owner default | J5, J5.1, J5.2, J5.4 |
| RU-25 | Interest is 0% unless `{interest_pct}` a year is given. How it compounds is **gated on OI-19** | Brief Part 1, owner default | J5.1, J5.4 |
| RU-26 | The timeline runs from B for the longest plan horizon, at most 120 months. A plan not reached by month 120 reads "more than 120 months", never an estimate | Brief Part 1, RU-9, `MAX_MONTHS` | J5, J5.1, J5.2, J5.3, J5.4 |
| RU-27 | A running loan's payoff month N is `loan_start` month + `duration_months`, counted from the account's last data month. From month N, each rate rises by the loan payment it contains. Status D adds a note that N is scheduled, not certain. Ours. Bump size **gated on OI-15**, N's first month on OI-16 | Brief Part 2 | J3, J5, J5.1, J5.2, J5.4 |
| RU-28 | The backup plan's month-by-month check counts the loan ending (RU-27). The judges' runway and the J2 verdict don't change. **Gated on NEW-ADR-1** | Brief Part 2, ADR 0001 | J3 |
| RU-29 | Time off is checked with the engine's `IncomeCut(0, months_off)` on the projected balance at its start. `months_off` is a whole number from 1 to 120. Start month **gated on OI-17**, spending during it on OI-20 | Brief Part 1, RU-22 | J5.2 |
| RU-30 | An emergency cost is the one-off shock `Shock(one_off_dollars=cost)`, with cost 0 or more. If the buffer left is 0 or less, the instant budget is the backup plan's steps and the lean monthly budget. Timing **gated on OI-18** | Brief Part 1, RU-7 | J5.3 |
| RU-31 | "Rescued" means the backup plan makes it after its steps with no step needing the lender's agreement. Use the same definition in the app and on Devpost. **Gated on OI-21** | Brief Part 3, [`make_a_plan.ipynb`](../../make_a_plan.ipynb) | J3 |
