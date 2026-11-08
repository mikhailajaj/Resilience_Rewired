# Scope

Status on 2026-11-07: the engine, the Streamlit UI and the chat (J4) are built. `pytest app/tests` collects 1,214 tests, all passing. The app has four pages, Shock and plan, Customer profiling, Chat and Findings, under a shared customer picker. The plan designer (J5) is built.

## What ships for judging

The Shock and plan page, as [wireframed](../design/ux/wireframes.md#page-structure), the Customer profiling page, the Chat page once built ([J4](use_cases.md#j4-ask-the-assistant)), and the docs that hold the method caveats. The Customer profiling page has no use case yet.

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
| P. Plan designer | J5 1 to 5, J5.1 to J5.4 |
| T. Chat | J4, J4.1 to J4.4 |

## Explicitly out

- Tangerine logo and proprietary font, unless the organisers confirm (RU-5, OI-2)
- Warning banners (RU-3)
- Any figure that replaces a judges' number (RU-1)
- [Leasing](../know_the_customer.md#known-limits) in any figure
- Plans driven by [district data](../discovery.md#district-data-doesnt-help)
- Default prediction: the one-payment line is [only a goal](../engine_contract.md#limits)
- Login ([flows](../design/ux/flows.md))
- A language model or any outside API in the chat (RU-15)

## Submission checklist

From the [README](../../README.md#what-to-submit-on-devpost). None of these exists yet.

- [ ] Demo video, 2 to 3 minutes
- [ ] Code repo, public link or zip. Hosting is approved (OI-8); visibility is open (OI-13)
- [ ] Short write-up: what it does and the biggest finding
- [ ] Links to every outside source used
- [ ] [Credits](../../README.md#credits) for the data and any public sources

Also needed for judging: a 1-minute pitch, since [the flows](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) only script the 3-minute twist.

## Risks

| ID | Risk | Response |
| :-- | :-- | :-- |
| RSK-1 | The chat isn't started, with judging under way | Build the [chat MVP](#chat-assistant-j4-mvp-and-stretch) only; the sliders stay the main path |
| RSK-2 | The presenter reads a wrong verdict from the copy deck (CON-1, CON-2) | Fix the verdict copy before rehearsal |
| RSK-3 | A card uses a value the controls can't set (OI-1, OI-6) | Decide before rehearsal |
| RSK-4 | "People cut back" sounds proven (CON-6) | Keep the [limits](../discovery.md#limits) ready |
| RSK-5 | A judge asks about December 2025 or [high earners](../discovery.md#higher-earners-look-more-fragile) | State the limit first; don't defend a number we can't source |
| RSK-6 | Code is pushed to the wrong repo | Create a separate repo first; `Tangerine/` is still inside the unrelated `Projects` repo |
| RSK-7 | The hosted or live run fails, or the projector is unreadable | Run GO-1 and GO-9, and [test from 5 m](../design/ux/walkthrough.md#remaining-risks-need-a-real-session). Use the video as fallback (ASM-1, ASM-2) |

## Go/no-go before the demo

All must pass on the demo laptop.

| ID | Check | Pass |
| :-- | :-- | :-- |
| GO-1 | Start the local copy from a clean setup, network off. This is the fallback if the hosted app or venue network fails | Loads; `warm_up()` has run; [no font fetched at run time](../design/research/tangerine_brand.md#8-font-recommendation) |
| GO-2 | `.venv/bin/python -m pytest app/tests -q -p no:cacheprovider` | All pass: 1,214 on 2026-11-08, plan designer tests included |
| GO-3 | Load 20111 | Matches the [worked example](../know_the_customer.md#worked-example-account-20111) |
| GO-4 | Run the [walkthrough twists](../design/ux/walkthrough.md) on 20111 and 20134 | Matches the engine; the 20111 bills result explains itself |
| GO-5 | Enter `abc`, then `12345` | Plain inline messages, and no old customer on screen |
| GO-6 | One account per trap ([notebook section 10](../../discovery.ipynb)) | Page complete, no error trace |
| GO-7 | Timed run of the [flows script](../design/ux/flows.md#2-live-twist-flow-3-minutes--180-s) | Twist inside 3:00 |
| GO-8 | Scan the screen | No banner, logo or proprietary font; our numbers labelled |
| GO-9 | Open the hosted app on the venue network | Loads; 20111 matches GO-3 |
| GO-10 | Run AC-1 to AC-10 on the Chat page, network off | All pass |
| GO-11 | Run AC-11 to AC-20 on Shock and plan | All pass |

## Open items for the owner

| ID | Item | Why it matters | Default if undecided |
| :-- | :-- | :-- | :-- |
| OI-1 | Income slider step size | [Wireframes](../design/ux/wireframes.md#c-twist-buttons-and-sliders-j2) use 5, the [contract](../engine_contract.md#defaults-the-owner-can-change) takes any value, and the [walkthrough](../design/ux/walkthrough.md#remaining-risks-need-a-real-session) asks about 1. Built with step 1 and a typed box; the owner hasn't confirmed | 5 |
| OI-2 | Logo permission | [Needs the organisers](../design/research/tangerine_brand.md#5-logo-v-for-observation-u-for-rules). No source settles brand colours either | No logo |
| OI-3 | Unexplained December 2025 drop | [It's in most buffer windows](../know_the_customer.md#known-limits), and the [cause is unknown](../discovery.md#open-questions) | README definition; caveat in docs |
| OI-4 | EI weekly maximum | Decided by the owner on 2026-11-07. See [`shock_sizing.md`](../shock_sizing.md) | Modelled, off by default, $729 a week or a typed value. The judges' runway doesn't change |
| OI-5 | Fund target default, 3 or 6 months | [Wireframes](../design/ux/wireframes.md#f-goal-plan-emergency-fund-j3) draw 6, the [contract](../engine_contract.md#defaults-the-owner-can-change) uses 3, and the [cheat sheet](../design/ux/copy.md#9-sentences-the-presenter-reads-cheat-sheet) says 6. "3 to 6 is common" in `K.f_target_help` has no source | 3 |
| OI-6 | Dollar inputs for a cost or rent rise | The engine supports them. Built as dollar boxes on Shock and plan; the wireframes still have no control | None: such a card can't be entered directly |
| OI-7 | Start month: include it? | [Discovery](../discovery.md#engine-requirements) requires it, the wireframes mark it TBD, and copy has no strings for it. Built as an optional "Shock starts in" under More options | Leave out; mention seasonality aloud |
| OI-8 | Where the code lives | **Settled 2026-11-07:** the data owner approved hosting the app online, planned on Streamlit Community Cloud. The chat sends no data out (RU-15) | Settled |
| OI-9 | Named owners and reviewers | No source names the team or a domain expert | Owner reviews |
| OI-10 | Submission deadline | Not in the README | Ask the organisers |
| OI-11 | Wording of `K.g_zero` | [Copy deck](../design/ux/copy.md#7-backup-plan-g) marks it TBD-Owner | As drafted |
| OI-12 | Short-history note in the chat | No source sets how few months is "short". The shortest history is 12 months (2 accounts) | No note; show the data range |
| OI-13 | Repo visibility for hosting | Checked 2026-11-07: `github.com/mikhailajaj/Resilience_Rewired` is already **public** and includes every `data/*.csv`, `transactions.csv` (102.6 MB, ASM-3; the engine doesn't read it) among them. **Settled 2026-11-07:** the owner confirmed the public repo is fine | Settled |
| OI-14 | Lean rate model (RU-23) | The brief names the level, not the base. I − lean spending agrees with the backup step `lean_months`; the alternative, actual change + lean-quarter cut, gives 20111 $2,117 instead of $604 | I − lean spending |
| OI-15 | What a rate gains at payoff (RU-27) | The brief says P, but 197 running loans have $0 of P in typical spending, so adding P would overstate the judges' and lean rates | Each rate rises by the part of P it contains (LE-1 to LE-6). The judges' rate rises only by the part of P already in typical spending, so it doesn't rise on the 197 (D12 narrows to the judges' rate). The actual rate rises by the smaller of P and the mean loan payment over the last 12 months, and the lean rate by the capped formula; both rise on the 197. The backup plan uses the judges' rise, so 1,526 + 22 is unchanged |
| OI-16 | First month without the payment (RU-27) | `loan_start` + `duration_months` could be the last payment or the first month without one | The rise starts in month N, as the brief says |
| OI-17 | When time off starts (RU-29) | The brief gives only its length | When its amount is saved after the fund and earlier goals; if not by month 120, now (month 0), which is J2's shock |
| OI-18 | When the emergency cost hits, and what "rebuild" means (RU-30) | The brief doesn't say | Month 0; rebuild to the buffer before the cost (at least $0) and to the fund target |
| OI-19 | How interest compounds (RU-25) | `{interest_pct}` is a yearly figure | Monthly, at `interest_pct` ÷ 12, on a positive balance only |
| OI-20 | Spending during time off | The brief checks with the engine's shock (spending S) and shows lean spending only as an amount | Check at S; lean amount shown as ours |
| OI-21 | "Rescued" count (RU-31) | The draft says 1,526 and the engine gives 1,548 for "makes it after steps". The 22 extra are `cuts_not_enough` accounts that make it only through `ask_lender`; no `no_buffer` account is rescued (0 of 23) | 1,526 by their own cuts, and "22 more if the lender agrees" |

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
- **ASM-2:** the venue network may be unreliable. No source says either way. The hosted app needs it; the local copy (GO-1) doesn't.
- **ASM-3:** `transactions.csv` is near GitHub's per-file limit. This is general knowledge, not from the project docs, so check before pushing.

## Chat assistant (J4): MVP and stretch

| MVP | Stretch |
| :-- | :-- |
| Chat page with greeting, twist buttons, size steps and the engine call line (J4.1) | Typed-out replies with `st.write_stream` |
| Results and both plans, from `ui/text.py` (J4.1, J4.3) | Type an account ID in the chat |
| Free text with confirm, PT-01 to PT-25 passing (J4.2) | EI weekly maximum and start month in text and buttons (OI-4, OI-7) |
| Stack, change size, new customer, send to the controls (J4.3) | Full `to_dict` engine output in the transcript |
| Card answers, engine outputs and the Markdown transcript (J4.4) | |

### Acceptance criteria

| ID | Given, when, then |
| :-- | :-- |
| AC-1 | Given 20111, when Job loss on EI, 55% and 6 months are clicked, then the call line reads `IncomeCut(0.55, 6)` and the verdict equals `text.verdict` on Shock and plan for the same shock |
| AC-2 | Every number in a chat reply equals the Shock and plan page for the same account and shock |
| AC-3 | PT-01 to PT-25 give their expected result, and nothing runs before Run it |
| AC-4 | A typed 150%, 0 months or 121 months gives `T.out_of_range` and no engine output |
| AC-5 | An account with B ≤ 0 shows the no-buffer verdict and doesn't blame the cost |
| AC-6 | 20134 with no shock: the greeting reads `summary_line`, which says `120.0 months`, and every runway figure reads `120.0 months`; neither says "No shortfall" or "120 months or more". A no-shortfall shock never reads "runs out". Revised 2026-11-07 by owner decision D5 (brief Part 5), which overrides the earlier alignment to the built copy |
| AC-7 | After a reply, only the latest message's buttons can be clicked |
| AC-8 | Changing the picker ID clears the old customer from the chat, and the transcript keeps them in a labelled section |
| AC-9 | Send to the controls sets the Shock and plan page to the same result; "until it runs out" gives `T.send_cant` |
| AC-10 | With the network off, the chat works, and a scan of the code finds no HTTP client or model call |

## Plan designer (J5): feasibility

Read-only pandas checks over the CSVs and the engine, 2026-11-07, all 4,500 accounts. "Lean" is OI-14's default.

| Check | Result |
| :-- | :-- |
| Rate above 0: judges', actual, lean | 3,309 · 2,893 · 4,402 |
| Median rate among those above 0 | $838 · $612 · $2,061 a month |
| Months to $60,000 at that median | 72 · 98 · 30 |
| Reach $60,000 by month 120 | 2,466 · 1,643 · 4,249 |
| Rate signs disagree | Actual above 0 but judges' not: 622; judges' above 0 but actual not: 1,038 |
| Running loans; payoff within 6, 12, 24, 36 months of each account's last data month | 448 (C 403, D 45); 60, 125, 235, 335; all within 60. Median payment $2,438. 2 are on stale accounts |
| Running loans whose 3-month fund date moves with the payoff (judges', actual, lean) | 164, 225, 80; of these 107, 149, 32 go from never to reachable |
| EI 6 months, runs out, loan ends within 6 months (RU-28) | 44 accounts; 6 make it once the gap falls by the typical loan payment (10 if by P) |
| Short history, pension, B ≤ 0, stale | 840 under 24 months (shortest 12); 740; 23; 76 |

Most demo accounts can't save at their current rate (20111: −$748 a month), so the cut-to-deadline answer (J5.1 6) is in the MVP.

### MVP and stretch

| MVP | Stretch |
| :-- | :-- |
| One engine function for all three plans, free of Streamlit so the chat can call it later | Chat: "save $60k for a car in 2 years", with cheatsheet rows only then |
| Savings goal with deadline and cut (J5.1); time off (J5.2); emergency budget (J5.3) | Time off with a chosen start month (OI-17) |
| Timeline with markers and table view (J5.4) | More than one goal at once (J5.1 7a): MVP takes one |
| Loan end in the plan designer (RU-27) | Loan end in the backup plan (RU-28), after NEW-ADR-1 |
| Part 3 fixes and the copy in [copy §10 and §11](../design/ux/copy.md#11-plan-designer-p) | |

### Acceptance criteria

| ID | Given, when, then |
| :-- | :-- |
| AC-11 | 20111, a $60,000 car, no deadline: rates −$748 (headline), −$2,260 and +$604 (ours); actual and judges' read "never", lean reads 113 months; 52 counting the loan ending in month 36 |
| AC-12 | Same, deadline 24: save $2,841 a month; cut $3,589, 57% of $6,269, more than the $2,864 lean-quarter cut |
| AC-13 | 20111, 24 months off: $206,391, and $137,643 at lean spending (ours); the check equals `apply_shock(20111, Shock(IncomeCut(0, 24)), through_months=24)`, running out in month 3 |
| AC-14 | A $10,000 cost: 20111 keeps $7,612; 32078 shows −$12,513, step 1 `cover_buffer`, lean budget $1,346, and both equal `apply_shock` and `make_plan` with `Shock(one_off_dollars=10000)` |
| AC-15 | The timeline starts at B, stops by month 120, has one line per rate and a table with the same values and markers |
| AC-16 | Amount 0, a goal covered above the fund, 121 months off, B ≤ 0, S = 0 and a deadline shorter than possible each show their J5.1 or J5.2 line and no error, on a sweep of all 4,500 accounts |
| AC-17 | Every running loan's payoff month equals `loan_start` month + `duration_months` − last data month; counts 60, 125, 235, 335; status D shows `P.loan_d` |
| AC-18 | On all 4,500 accounts and the 5 presets, the judges' numbers, runway and J2 verdict are unchanged after the loan-end change |
| AC-19 | Every plan designer number comes from the engine function; `app/engine/` has no Streamlit import |
| AC-20 | No sentence on Shock and plan reads "1 months" or "$$", on a sweep with target 1 and length 1 |

## Fixes from the J4 build (Part 3), 2026-11-07

- **AC-6:** aligned to the built copy (above). "No shortfall" stays off capped runways.
- **ADR status word:** "Accepted", as the [index rule](../adr/README.md) and 0001 use. 0002 to 0005 and the index updated.
- **Counts:** 829 tests in the status line, GO-2 and [`project_dev-post.md`](../../project_dev-post.md). `app/README.md` gives no count, so it needs no change (and `app/` is outside this pass).
- **Rescued:** OI-21's default; the Devpost line keeps 1,526 and adds the 22.
- **`K.g_oneoff`:** added to copy §7.
- **Loan end and the ADRs (Part 2):** a new record, NEW-ADR-1 for the architect to number and the owner to accept: "The backup plan's make-it check counts a scheduled loan end (ours); the judges' runway and the J2 verdict don't." Not an amendment to 0001, because the index rule changes an accepted record only by a new one, and this changes what `makes_it_after_steps` means.

## Changes from the previous version

| File | Change |
| :-- | :-- |
| [`requirements.md`](requirements.md) | BR-14 to BR-18, RU-15 to RU-22; J4 use cases added to BR-2, BR-3, BR-5, BR-12; BR-9 repo gate |
| [`use_cases.md`](use_cases.md), [`use_cases_chat.md`](use_cases_chat.md) | J4 summary; J4.1 to J4.4 new |
| [`glossary.md`](glossary.md) | Chat terms |
| [`system_context.md`](system_context.md) | Host actor; UI built; four areas |
| This file | Status, pages, OI-8 settled, OI-12, OI-13, GO-1, GO-2, GO-9, GO-10, RSK-1, RSK-6, RSK-7, ASM-2, chat MVP and acceptance |
| Design: [flows](../design/ux/flows.md#4-chat-state-machine-j4), [wireframes](../design/ux/wireframes.md#t-chat-page-j4), [copy](../design/ux/copy.md#10-chat-t), [parser](../design/ux/chat_parser.md) | Chat sections; stale one-page lines in flows and wireframes |
| Plan designer pass | BR-19 to BR-23, RU-23 to RU-31; J5 and [`use_cases_plan.md`](use_cases_plan.md); glossary and concept diagram; OI-14 to OI-21; J5 feasibility, MVP and AC-11 to AC-20; GO-2, GO-11, AC-6; copy §7, §10 settled, §11; wireframes P |
