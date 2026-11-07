# Scope

Status on 2026-11-07: `app/engine/` exists, and its 146 tests passed on this date while the engine was still being built. The UI isn't started.

## What ships for judging

One Streamlit page, as [wireframed](../design/ux/wireframes.md#page-structure-single-page), plus the docs that hold the method caveats.

| Section | Use-case steps |
| :-- | :-- |
| A. Customer picker | J1 1, 2 |
| B. Know the customer | J1 3, 4 |
| C. Twist buttons and sliders | J2 1, 2 |
| D. Before and after | J2 3, 4, 5 |
| E. Our numbers | J1 5, J2 6 |
| F. Goal plan | J3 1, 2, 3 |
| G. Backup plan | J3 4, 5 |
| H. Details (closed) | J1 4 |

## Explicitly out

- Tangerine logo and proprietary font, unless the organisers confirm (RU-5, OI-2)
- Warning banners (RU-3)
- Any figure that replaces a judges' number (RU-1)
- [Leasing](../know_the_customer.md#known-limits) in any figure
- Plans driven by [district data](../discovery.md#district-data-doesnt-help)
- Default prediction: the one-payment line is [only a goal](../engine_contract.md#limits)
- Login and multiple pages ([flows](../design/ux/flows.md))

## Submission checklist

From the [README](../../README.md#what-to-submit-on-devpost). None of these exists yet.

- [ ] Demo video, 2 to 3 minutes
- [ ] Code repo, public link or zip (OI-8)
- [ ] Short write-up: what it does and the biggest finding
- [ ] Links to every outside source used
- [ ] [Credits](../../README.md#credits) for the data and any public sources

Also needed for judging: a 1-minute pitch, since [the flows](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) only script the 3-minute twist.

## Risks

| ID | Risk | Response |
| :-- | :-- | :-- |
| RSK-1 | The UI isn't started, with judging under way | Build A to D first, then E to H |
| RSK-2 | The presenter reads a wrong verdict from the copy deck (CON-1, CON-2) | Fix the verdict copy before rehearsal |
| RSK-3 | A card uses a value the controls can't set (OI-1, OI-6) | Decide before rehearsal |
| RSK-4 | "People cut back" sounds proven (CON-6) | Keep the [limits](../discovery.md#limits) ready |
| RSK-5 | A judge asks about December 2025 or [high earners](../discovery.md#higher-earners-look-more-fragile) | State the limit first; don't defend a number we can't source |
| RSK-6 | Code is pushed to the wrong repo (OI-8) | Create a separate repo first |
| RSK-7 | The live run fails, or the projector is unreadable | Run GO-1 and [test from 5 m](../design/ux/walkthrough.md#remaining-risks-need-a-real-session). Use the video as fallback (ASM-1, ASM-2) |

## Go/no-go before the demo

All must pass on the demo laptop.

| ID | Check | Pass |
| :-- | :-- | :-- |
| GO-1 | Start from a clean setup, network off | Loads; `warm_up()` has run; [no font fetched at run time](../design/research/tangerine_brand.md#8-font-recommendation) |
| GO-2 | `pytest app/tests` | All pass |
| GO-3 | Load 20111 | Matches the [worked example](../know_the_customer.md#worked-example-account-20111) |
| GO-4 | Run the [walkthrough twists](../design/ux/walkthrough.md) on 20111 and 20134 | Matches the engine; the 20111 bills result explains itself |
| GO-5 | Enter `abc`, then `12345` | Plain inline messages, and no old customer on screen |
| GO-6 | One account per trap ([notebook section 10](../../discovery.ipynb)) | Page complete, no error trace |
| GO-7 | Timed run of the [flows script](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) | Twist inside 3:00 |
| GO-8 | Scan the screen | No banner, logo or proprietary font; our numbers labelled |

## Open items for the owner

| ID | Item | Why it matters | Default if undecided |
| :-- | :-- | :-- | :-- |
| OI-1 | Income slider step size | [Wireframes](../design/ux/wireframes.md#c-twist-buttons-and-sliders-j2) use 5, the [contract](../engine_contract.md#defaults-the-owner-can-change) takes any value, and the [walkthrough](../design/ux/walkthrough.md#remaining-risks-need-a-real-session) asks about 1 | 5 |
| OI-2 | Logo permission | [Needs the organisers](../design/research/tangerine_brand.md#5-logo-v-for-observation-u-for-rules). No source settles brand colours either | No logo |
| OI-3 | Unexplained December 2025 drop | [It's in most buffer windows](../know_the_customer.md#known-limits), and the [cause is unknown](../discovery.md#open-questions) | README definition; caveat in docs |
| OI-4 | EI weekly maximum | Decided by the owner on 2026-11-07. See [`shock_sizing.md`](../shock_sizing.md) | Modelled, off by default, $729 a week or a typed value. The judges' runway doesn't change |
| OI-5 | Fund target default, 3 or 6 months | [Wireframes](../design/ux/wireframes.md#f-goal-plan-emergency-fund-j3) draw 6, the [contract](../engine_contract.md#defaults-the-owner-can-change) uses 3, and the [cheat sheet](../design/ux/copy.md#9-sentences-the-presenter-reads-cheat-sheet) says 6. "3 to 6 is common" in `K.f_target_help` has no source | 3 |
| OI-6 | Dollar inputs for a cost or rent rise | The engine supports them, but the wireframes have no control | None: such a card can't be entered directly |
| OI-7 | Start month: include it? | [Discovery](../discovery.md#engine-requirements) requires it, the wireframes mark it TBD, and copy has no strings for it | Leave out; mention seasonality aloud |
| OI-8 | Where the code lives | `Tangerine/` is untracked inside the unrelated `Projects` repo (remote `Tempho-ui`). Is bank data allowed in a public repo? `transactions.csv` is 102.6 MB (ASM-3) | No push until decided |
| OI-9 | Named owners and reviewers | No source names the team or a domain expert | Owner reviews |
| OI-10 | Submission deadline | Not in the README | Ask the organisers |
| OI-11 | Wording of `K.g_zero` | [Copy deck](../design/ux/copy.md#7-backup-plan-g) marks it TBD-Owner | As drafted |

## Conflicts between existing docs

Not resolved here. "Follow" says what to use until the docs are fixed.

| ID | Conflict | Follow |
| :-- | :-- | :-- |
| CON-1 | [Flows section 3](../design/ux/flows.md#3-shock-flow-detail), [copy verdicts](../design/ux/copy.md#4-before-and-after-d) and walkthrough P5 compare rounded runway with the length, and copy uses `ceil(R)`. [ADR decision 2](../adr/0001-engine-shock-semantics.md#decisions) forbids this | ADR |
| CON-2 | The copy verdict says "before income recovers". [ADR decision 3](../adr/0001-engine-shock-semantics.md#decisions) assumes $0 income after the benefit ends | ADR; new copy |
| CON-3 | Wireframes E only expect `n/a` on pensions. The [contract](../engine_contract.md#extrafigure) also gives it for transfers, no income lost and no spending, including the furnace twist and 20134. [Cheat sheet line 3](../design/ux/copy.md#9-sentences-the-presenter-reads-cheat-sheet) has no `n/a` path | Contract; new copy |
| CON-4 | `K.g_fixed` shows `${F}`, but the [backup plan's](../engine_contract.md#backupplan) `fixed_costs` is current fixed costs plus bills added. They can differ, as on the 197 recent-loan accounts | Contract |
| CON-5 | The Runway 0 verdict blames the cost. On the 23 accounts with B ≤ 0, the [contract](../engine_contract.md#verdict_case) says not to, and copy has no line for this | Contract; new copy |
| CON-6 | [`K.e_adjust`](../design/ux/copy.md#5-our-numbers-e) says most customers spend less, and `K.e_sentence` says they usually cut. [Discovery limits](../discovery.md#limits) call "people cut back" only one reading | Discovery; soften copy |
| CON-7 | [Flows section 3](../design/ux/flows.md#3-shock-flow-detail) sends "no shortfall" to "runs out in month N". The contract has a separate `no_shortfall` verdict | Contract |
| CON-8 | [Wireframes D](../design/ux/wireframes.md#d-before-and-after-the-judges-numbers-headline) call "No shortfall (120+)" the cap case. It means gap ≤ 0; a capped runway reads `120.0 months`, as on 20134 | README |
| CON-9 | Income type is [our addition](../know_the_customer.md#our-additions), but wireframes B show it unlabelled in a block described as purely the judges' (RU-2) | Owner |
| CON-10 | Wireframe mocks for 20111 differ from the engine: data from 2021-03 (2022-11), layoff runway 3.2 (3.4), standing-order bills $1,180 ($0) | Engine |
| CON-11 | Smaller mismatches: flows call Reset the fourth button, but there are five; wireframe slider labels differ from copy; `N.no_bills` has a wider condition than [the warning](../know_the_customer.md#warnings) (1,225 against 1,063 accounts); wireframes use `K.no_shock`, which isn't in copy; `tokens.json` lists the proprietary font (RU-5) | Copy, contract and RU-5 |

## Assumptions

- **ASM-1:** the demo video can stand in if the live run fails. No source confirms that judges accept this.
- **ASM-2:** the venue network may be unreliable. No source says either way.
- **ASM-3:** `transactions.csv` is near GitHub's per-file limit. This is general knowledge, not from the project docs, so check before pushing.
