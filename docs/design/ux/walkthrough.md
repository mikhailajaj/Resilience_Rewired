# Usability walkthrough: Resilience Rewired

Method: cognitive walkthrough of each twist against `wireframes.md` and `copy.md`. Three questions at every step: (1) can the user tell what to do, (2) can they see it worked, (3) can they recover from a mistake?

All figures are real engine output (`.venv/bin/python`, `get_profile`, `apply_shock`, `make_plan`, run 2026-11-07) for accounts 20111 and 20134, except where marked "worked by hand".

| Account | Type | I | S | H | B | Runway, no shock |
| :-- | :-- | --: | --: | --: | --: | :-- |
| 20111 | Cash only | $6,339 | $8,600 | $0 | $17,612 | 7.8 months |
| 20134 | Transfers | $7,958 | $8,061 | $5,166 | $16,599 | 120.0 months (a $103 gap, capped) |

## Twist 1: "Laid off, EI 55% for 6 months. Do they make it?" (20111)

| Step | Action | Q1 | Q2 | Q3 | Result |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | Type 20111, Enter | One box, example in help | B appears | Retype | Pass |
| 2 | Read B | Summary sentence | 7.8 months | n/a | Pass |
| 3 | Click "Laid off, EI 55%" | Wording equals the card | "Selected: Laid off, EI 55%"; inputs show 55 and 6 | Reset | Pass |
| 4 | Read D | Verdict on top | "The money runs out in month 4, about 2.6 months short. The judges' runway is 3.4 months." Income $3,487, gap $5,113 | Reset | Pass |
| 5 | Read E | Labelled row | If you adjust 4.1 months beside judges' 3.4, reading "illustration" | | Pass |
| 6 | Read F | no_surplus | "Spending about $2,260 a month less to start; $2,942 less reaches 3 months ($25,799) in 12 months; fits within $6,269" | | Pass |
| 7 | Read G | cuts_needed | "Spending needs to drop by $2,178 a month, about 25%." Step 1: bring other spending down to $3,405 | | Pass |

If the judge says "EI 57%": type 57 in the box (no step limit). If the judge says "12 months": type 12. Both are one entry each.

EI maximum on (owner switch): monthly cap $3,159 against $3,487, so the capped runway is 3.2 months, shown in E beside the judges' 3.4. D is unchanged.

## Twist 2: "The furnace dies: repair costs a full month of typical spending" (20111, then 20134)

| Step | Action | Q1 | Q2 | Q3 | Result |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | Click "Furnace dies" | Wording matches. Sets one-off to 1.0 month and clears the income cut | Total one-off: $8,600 | Reset | Pass |
| 2 | Read D (20111) | "After this, the buffer lasts 4.0 months, down from 7.8." Buffer left $9,012, gap $2,260 | | | Pass |
| 3 | Read E | "If you adjust: n/a. No income is lost in this twist." | Row stays on screen | | Pass (CON-3) |
| 4 | Read G | No length, so "To stop the buffer falling, spending needs to drop by $2,260 a month." | | | Pass |
| 5 | Repeat on 20134 | Buffer left $8,539, gap $103, "buffer lasts 83.3 months, down from 120.0 months". E reads n/a: transfers account | | | Pass |

If the judge says "$5,000 repair": type 5000 in the dollar box. The months slider drops to 0 and the total line reads "Total one-off: $5,000". On 20111 that leaves $12,612 and runway 5.6 months.

## Twist 3: "Laid off (EI 55%) and household bills up 15% in the same month"

20134 (bills visible):
1. Click "Laid off + bills up 15%". Income $4,377, spending $8,835, gap $4,459.
2. D: "The money runs out in month 4, about 2.3 months short. The judges' runway is 3.7 months." (Layoff alone: month 5, 4.5 months.)
3. E: "If you adjust" is n/a: transfers account (CON-3).
4. G: `cuts_not_enough`: needs $1,692 a month, $1,582 is flexible, and with all flexible spending cut the runway is 5.8 months, short of 6.

20111 (no bills visible):
1. Same button. Bills part changes nothing; verdict stays month 4, runway 3.4.
2. Fact line: "No regular bills visible, so the judges' formula changes nothing for this." E bills row reads n/a with the engine reason `bills_not_missing` ("Standing orders match the bills already counted"). The presenter says the bills part has nothing to act on. Pass.

## Hard accounts and states (designed, not failures)

| Case | Example | Verdict / display |
| :-- | :-- | :-- |
| Buffer already negative | 32078, furnace | `runway_zero` with `no_buffer_before_shock`: "The balance was already -$2,513 before this, so runway is 0 months whatever the shock." Backup `no_buffer`: $5,480 needed first |
| No shortfall | an account with I at least S | "Income still covers spending", runway label `No shortfall (120+)` |
| Capped runway | 20134, no shock | `120.0 months`, not "no shortfall" |
| Surplus not in balance | 20189 | F shows the extra "Treat the savings figure as the most this could be" line |
| High flow | 20133 | B shows N.high_flow with the district salary |

## Problems found and fixed (original review)

| # | Problem | Fix |
| :-- | :-- | :-- |
| P1 | A twist leaves the previous twist's inputs in place | Each preset sets every input; Reset sets defaults |
| P2 | Bills shock on H = $0 looks like a bug | Fact line says nothing changed and why |
| P3 | Backup "cut $X" has no size | Share of spending and flexible spending shown |
| P4 | Furnace has no length, so a "full N months" backup makes no sense | Gap-closing wording (`K.g_gap`) |
| P5 | "Do they make it" lacked an explicit answer | Superseded: the answer is `duration.verdict` and `runs_out_in_month`, never the rounded runway (CON-1) |
| P6 | Delta only by colour | Delta also in words |
| P7 | Goal plan moved with the shock | F fixed to no shock and captioned |
| P8 | Pension layoff unexplained | Fact line |
| P9 | Hard accounts could look broken | Sections always draw; only text changes |
| P10 | "If you adjust" hard to explain | One sentence, plus an n/a sentence |

## Problems found in this revision and fixed

| # | Problem | Fix |
| :-- | :-- | :-- |
| P11 | CON-1: verdict compared rounded runway and used a ceiling | Verdict from engine fields only |
| P12 | CON-2: "before income recovers" | Replaced by the assumption line |
| P13 | CON-3: n/a only expected on pensions | n/a path for four reasons, with a cheat-sheet line |
| P14 | CON-4: F shown in the backup plan | Backup uses the engine's fixed costs with bills added |
| P15 | CON-5: runway 0 blamed the cost | Two wordings, keyed on `no_buffer_before_shock` |
| P16 | CON-6: copy said customers cut spending | "some accounts in the data", "illustration" |
| P17 | CON-7/8: no-shortfall routed to runs-out; cap case mislabelled | Separate branch; `120.0 months` is the cap |
| P18 | CON-9: income type sat in the judges' block | Moved to header, labelled "(our label)" |
| P19 | CON-10: mock numbers | Real engine values throughout |
| P20 | CON-11: Reset count, labels, N.no_bills condition, K.no_shock | Fixed in flows, wireframes and copy |
| P21 | A typed dollar repair would add to a leftover months slider | Last edit wins; total line shown |
| P22 | A judge's 57% or $5,000 could not be entered | Number boxes beside the sliders |

## Remaining risks (need a real session)

- Timing is an estimate. A 181 s case (EI maximum on) is at the limit.
- Projected text size has not been tested; test from 5 m.
- Slider and number box staying in step is a build detail to verify; if it lags, drop the slider for income kept and keep the box.
- "Our numbers" rows can read as competing answers. The heading is the guard; watch for it in the test.

## Usability test script (20 minutes, 3 people)

Setup: app open, empty. Moderator reads each card and says nothing else. The participant plays the presenter and talks aloud.

| Task | Card | Success criterion |
| :-- | :-- | :-- |
| T0 | "Look at account 20111." | ID entered without help in 15 s |
| T1 | "Laid off, EI 55%, 6 months. Do they make it?" | Right button in 15 s; says "no, month 4" |
| T2 | "Make that EI 57% for 9 months." | Types both values in 20 s |
| T3 | "The furnace dies; the repair is $5,000." | Uses the dollar box; reads 5.6 months |
| T4 | "Layoff and bills up 15%", on 20134 then 20111 | Explains why 20111 does not change |
| T5 | "Turn on the EI weekly maximum." | Finds the switch in 10 s; says the judges' number did not move |
| T6 | Type 12345, then abc | Knows what to do from the message alone |
| T7 | Load 32078 and press the furnace button | Says the buffer was already negative; does not blame the repair |
| T8 | "Why is 'if you adjust' n/a?" (20134) | Says it comes from cash-only accounts |
| T9 | "How is your 4.1 different from their 3.4?" (20111, layoff) | Says it is an illustration and the judges' keeps spending flat |

Pass overall if 2 of 3 participants meet every criterion; log each hesitation over 5 s.
