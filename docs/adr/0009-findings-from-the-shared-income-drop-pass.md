# ADR 0009: Findings figures computed live by the engine and cached

Status: proposed, 2026-11-07; revised 2026-11-08 (title, decisions 2 to 5, alternatives, consequences). Sources: R3, D10, D13, brief Part 6 (NEW-SCOPE-5, NEW-SCOPE-7), [discovery §Biggest finding](../discovery.md#biggest-finding), `discovery.ipynb`, `know_the_customer.ipynb`, `make_a_plan.ipynb` (markdown and stored outputs, read 2026-11-08, not executed), [ADR 0001](0001-engine-shock-semantics.md) consequences, [design §4.5 and §6.3](../architecture/j5_plan_designer.md#45-findings-r3-d10-adr-0009).

## Context

The 1-minute pitch needs D10's figures on screen: 735 income drops, a median of 50% of spending kept, and 31 below $0 where the formula predicted 493. The owner made Findings a fourth page built from the knowledge in the three notebooks (NEW-SCOPE-5), and chose to compute the D13 rescued count **live in the app, cached after the first run**, with no precomputed file, because the owner warms the app before judging (NEW-SCOPE-7). The brief says every number comes from the engine.

Two costs differ. The income-drop pass is already made by `warm_up()` (`spending_response()`), so D10 is nearly free. The other figures need every account's profile and, for D13, a `make_plan` run per account: measured 2026-11-08 on the build laptop, about 50 s for 4,500 cold profiles plus 4.5 s for the plans, which is too slow for startup (the `warm_up` budget is 15 s, ours).

## Decisions

1. **`response.income_drop_events()` returns one record per event** (balances, means, kept shares, predicted end). It is cached, and it is the only pass over the events. `find_events` and `spending_response` read it and return exactly what they did before.
2. **`findings.biggest_finding()` reduces those records** to the D10 figures, the three buffer tiers and the per-event spending kept for the chart. It is cached, and `warm_up()` calls it.
3. **`findings.account_findings()` computes the across-accounts figures live, cached at first use** (`functools.lru_cache`, once per process). `warm_up()` does **not** call it. It reads only `get_profile`, `account_flows` and `make_plan(id, get_preset("job_loss_ei").shock, through_months=6)`; the profiles it warms are the same cached profiles every page uses.
4. **The page shows these notebook findings, every figure from the engine:**

   | # | Finding | Figures (notebook value, to be equal) | Notebook | Engine source |
   | :-- | :-- | :-- | :-- | :-- |
   | F1 | Spending doesn't stay flat after a shock (D10, the head) | 735 drops on 480 accounts; income kept 13%, spending kept 50%; within 10% of usual in 5%; 493 predicted below $0 after 3 months, 31 were | discovery §5 | `biggest_finding()` |
   | F2 | The response depends on the starting buffer | under 2 months 410 events, 37% kept; 2 to 6 months 219, 71%; 6+ months 106, 247% | discovery §5 | `biggest_finding().tiers` |
   | F3 | Most cuts are doable: the rescued count (D13) | of 1,596 accounts that don't last 6 months on EI at 55%, 1,526 last with their own cuts, plus 22 more if the lender agrees, 1,548 in all | make_a_plan "Across all 4,500 accounts" | `account_findings()` |
   | F4 | A surplus on paper often doesn't reach the balance | 1,038 of the 3,309 accounts with I − S > 0 didn't grow over the last 12 months | make_a_plan "Across all 4,500 accounts" | `account_findings()` |
   | F5 | Lifetime medians miss recent loans | 197 of 448 running loans show $0 of the payment in typical spending, a median $2,545.40 a month | discovery §6, know_the_customer checks ("Recent loan missed by F 197") | `account_findings()` |
   | F6 | A layoff doesn't fit pensioners | 740 pension accounts | discovery §3, know_the_customer checks | `account_findings()` |

   Kept in the notebooks and on Devpost only, because the engine doesn't compute them and building them isn't in this increment: the income paradox (rank correlation −0.68 with income, −0.04 with the buffer; discovery §4), the lowest balance as a default warning (AUC 0.85 against 0.72; 173 loans under one payment, 34% default against 3.3%; discovery §7), seasonality (1.34× from November, 0.90× from February; §8) and district data (correlations about 0; §9). The page's limits line links the notebooks for them. The choice of F2 to F6 is ours (labelled a guess until the owner reviews the page).
5. **The page is a fourth page**, `app_pages/findings.py`, needing no customer. F1 and F2 show at once from the warm cache. F3 to F6 show under `st.spinner` on the first open in a process (about a minute cold, **verify** on Community Cloud), then instantly.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Hard-code the notebook's numbers | Breaks "every number from the engine"; can drift |
| Read a CSV or JSON exported by the notebook, or a precomputed rescued file | The owner chose live (NEW-SCOPE-7); a second source to keep in step; a stale file passes silently |
| Compute the across-accounts figures in `warm_up()` | Startup grows from about 4 s to about a minute, past the 15 s budget, on every cold start, including pages that never need them |
| Compute on each page open without caching | About a minute per view |
| A panel on Shock and plan | That page is the twist path; the brief says don't rework it, and the pitch wants a clean screen |
| Port the AUC, correlation and seasonality analyses into the engine | New statistics code for a pitch page; outside the increment. Kept in the notebooks |

## Consequences

- Startup does no extra pass. `test_warm_up.py` checks it within a 15 s budget (ours), with `biggest_finding()` cache hits under 50 ms, and that `account_findings` is **not** yet cached after `warm_up()`.
- `test_findings.py` pins F1 and F2 (735, 480, 13%, 50%, 5%, 493, 31; tiers 410, 219, 106 and 37%, 71%, 247%) before and after the refactor, and F3 to F6 (1,596; 1,526; 22; 1,548; 1,038 of 3,309; 197 of 448; $2,545.40; 740). The D13 figures are the same as the AC-18 snapshot in `test_loan_end.py`, so the two tests can't disagree silently. No `slow` marker (NEW-SCOPE-6).
- The owner must open Findings once before judging (the warm-up step). If the process restarts, the first open is slow again.
- D13 wording appears in the app (F3) and on Devpost. Devpost says "four pages".

## Changes

| Date | Change | Source |
| :-- | :-- | :-- |
| 2026-11-08 | Title widened from "from the engine's shared income-drop pass" | NEW-SCOPE-5, NEW-SCOPE-7 |
| 2026-11-08 | Decision 3 added: `account_findings()` live, cached at first use, not in `warm_up()` | NEW-SCOPE-7 |
| 2026-11-08 | Decision 4 added: findings F1 to F6 named with their notebook and figures; what stays notebook-only | NEW-SCOPE-5 |
| 2026-11-08 | "A rescued count stays off the app" removed: F3 shows it | NEW-SCOPE-7, D13 |
| 2026-11-08 | Alternatives: precomputed file and `warm_up()` placement rejected | NEW-SCOPE-7 |
