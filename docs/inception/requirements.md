# Requirements

"Serves" names a [judging criterion](../../README.md#how-judging-works). That mapping is our judgement. A requirement is settled unless it says Gated, and gates are in [scope](scope.md#open-items-for-the-owner).

## Business requirements

### Judge

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-1 | As a judge, I want any `account_id` to show income, bills and fixed costs, buffer and runway, so that I can test a customer I choose | [README](../../README.md#the-challenge) | J1 | Data Use |
| BR-2 | As a judge, I want to apply and resize a shock or a mix, so that I can run my twist live. **Gated on OI-1, OI-6** for values the controls can't set | [README](../../README.md#the-challenge) | J2 | Data Use |
| BR-3 | As a judge, I want a goal plan and a backup plan from the customer's own numbers, so that I can judge the fit. **Default target gated on OI-5** | [README](../../README.md#the-challenge) | J3 | Impact |
| BR-4 | As a judge, I want numbers from the published definitions, so that I can check my worked answers | [README](../../README.md#how-judges-calculate-the-numbers) | J1, J2 | Data Use |
| BR-5 | As a judge, I want a direct answer to "do they make it?", so that I don't have to infer it | [ADR 0001](../adr/0001-engine-shock-semantics.md) | J2 | Communication |
| BR-6 | As a judge, I want to see where flat spending breaks, beside my number, so that I can judge the discovery | [Biggest finding](../discovery.md#biggest-finding) | J2 | Discovery |

### Presenter and team

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-7 | As a presenter, I want a designed state for every hard account and invalid ID, so that no judge's pick looks like a bug | [Live demo traps](../discovery.md#live-demo-traps) | J1, J2, J3 | Communication |
| BR-8 | As a presenter, I want ready sentences, instant recalculation and numbers readable across a room, so that a twist fits in 3 minutes | [Flows](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) | J1, J2, J3 | Communication |
| BR-9 | As the team, I want a demo video, repo, write-up and sources submitted, so that the entry is complete. **Repo gated on OI-8** | [README](../../README.md#what-to-submit-on-devpost) | None: see [checklist](scope.md#submission-checklist) | All |

### Bank customer (offstage)

| ID | Requirement | Source | Use cases | Serves |
| :-- | :-- | :-- | :-- | :-- |
| BR-10 | As a customer, I want the team to be clear about what my data can't show, so that nobody reads too much into it | [Known limits](../know_the_customer.md#known-limits) | J1, J2, J3 | Impact |
| BR-11 | As a customer, I want a layoff that doesn't fit my pension marked, and missed loans or bills shown beside the typical figure, so that my numbers aren't misread | [Engine requirements](../discovery.md#engine-requirements) | J1, J2, J3 | Discovery |
| BR-12 | As a customer with a running loan, I want a goal to keep my lowest balance above one payment, so that I have a line to act on | [Lowest balance](../discovery.md#the-lowest-balance-predicts-default) | J3 | Discovery |
| BR-13 | As a customer, I want a shock's start month considered, so that one running into January isn't undersized. **Gated on OI-7** | [Timing](../discovery.md#timing-changes-the-cost-of-a-shock) | J2 | Discovery |

## Business rules

"Owner's brief" means the instructions for this release, dated 2026-11-07.

| ID | Rule | Source | Applies to |
| :-- | :-- | :-- | :-- |
| RU-1 | Judges' numbers come first, use only the README formula, and are never replaced | [ADR](../adr/0001-engine-shock-semantics.md#decisions), [our additions](../know_the_customer.md#our-additions) | J1, J2, J3 |
| RU-2 | Our additions are labelled and sit beside the judges' numbers | [Our additions](../know_the_customer.md#our-additions), [copy](../design/ux/copy.md#5-our-numbers-e) | J1, J2 |
| RU-3 | No warning banners in the UI. Every message is plain inline text | [Copy](../design/ux/copy.md), owner's brief | J1, J2, J3 |
| RU-4 | Method caveats live in the docs. Customer facts are plain inline data | [Copy](../design/ux/copy.md#2-know-the-customer-b), [contract](../engine_contract.md#limits), owner's brief | J1, J2, J3 |
| RU-5 | No Tangerine logo or proprietary font unless the organisers confirm | [Logo](../design/research/tangerine_brand.md#5-logo-v-for-observation-u-for-rules), [font](../design/research/tangerine_brand.md#8-font-recommendation), owner's brief | J1, J2, J3 |
| RU-6 | Runway follows the README formula, including its 0, no-shortfall and capped cases | [README](../../README.md#how-judges-calculate-the-numbers) | J1, J2, J3 |
| RU-7 | "Do they make it?" comes from the engine's month-by-month verdict, never the rounded runway | [ADR decision 2](../adr/0001-engine-shock-semantics.md#decisions) | J2, J3 |
| RU-8 | After the lower income ends, income is $0 by default, and results state this | [ADR decision 3](../adr/0001-engine-shock-semantics.md#decisions) | J2, J3 |
| RU-9 | A figure that doesn't apply shows `n/a` with a reason, never a guess | [ADR decision 4](../adr/0001-engine-shock-semantics.md#decisions) | J1, J2 |
| RU-10 | "If you adjust" is an illustration. Don't quote it as a result | [Limits](../discovery.md#limits) | J2 |
| RU-11 | The goal plan uses no-shock numbers. The backup plan uses the current shock | [Walkthrough P7](../design/ux/walkthrough.md#problems-found-and-fixed) | J3 |
| RU-12 | No section disappears for a valid account, and an old customer never stays on screen with a new ID | [Walkthrough P9](../design/ux/walkthrough.md#problems-found-and-fixed), [wireframes A2](../design/ux/wireframes.md#a2-loading) | J1, J2, J3 |
| RU-13 | Shock changes recalculate at once. Changing the ID resets the shock | [Flow rules](../design/ux/flows.md#1-main-flow-any-user-any-account) | J2 |
| RU-14 | Every outside source used is linked, and the data is credited | [README](../../README.md#credits) | Submission (no use case) |
