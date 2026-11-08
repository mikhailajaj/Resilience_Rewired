## Biggest finding

Spending doesn't stay flat after a shock, though the runway formula assumes it does. We found 735 real income drops. Customers kept a median of 50% of their usual spending. The formula predicted 493 of those events would be below \$0 after 3 months; 31 were. Details are under the challenges below.

## Inspiration

Most people can tell you their balance. Very few can tell you how long it would last if their pay stopped next month. The Resilience Rewired challenge asked us to answer that for real bank customers. We wanted one screen to answer the question for any customer, live: *how long can this customer last if money gets tight, and what should they do about it?*

We set ourselves two rules. Every number must come from the customer's own account, not a generic budgeting rule. And the judges' numbers must never change: anything we add sits beside them, labelled as ours.

## What it does

Type any of the 4,500 account IDs and the app does three things.

1. **Know the customer.** It shows income, bills, fixed costs, savings buffer and months of runway.
2. **Take a shock.** Pick a job loss on EI, higher rent or bills, a surprise repair, or a mix, at any size. The runway updates instantly.
3. **Make a plan.** A goal plan builds an emergency fund. A backup plan lists the cuts, in order, that would get the customer through the shock.

The app has four pages: Shock and plan, Customer profiling, Chat and Findings. *Customer profiling* shows everything on file for the customer, including charts of where their money went. It also writes a list of questions to ask the stakeholder, generated from the customer's own numbers, with room to type answers and download them. *Chat* runs a twist on the loaded customer in a guided conversation, and *Findings* shows what we found across all accounts. On the first page, a plan designer lets the customer adjust the plan ("If you adjust") and see the effect of each change on the date they reach their goal.

## How we built it

**1. Data model first.** We documented every table and column before writing any analysis, and cross-checked it against the challenge's definitions. One check paid off for the rest of the project: on every row, money in minus money out equals the change in balance, to within 14 cents. That meant we could trust the totals.

**2. Discovery.** A notebook tested the runway formula against what customers actually did (see the challenges below).

**3. The engine.** A pure Python package (`app/engine/`) with no UI code in it. It uses the challenge's definitions:

$$
I = \operatorname{median}(\text{money in}), \qquad
S = \operatorname{median}(\text{money out}), \qquad
B = \operatorname{mean}_{\text{last 6 months}}(\text{average daily balance})
$$

$$
\text{runway} = \min\!\left(\frac{B - \text{one-off costs}}{S_{\text{after}} - I_{\text{after}}},\; 120\right)
$$

A job loss on EI keeps 55% of income. We also show a second figure using the 2026 EI weekly maximum of \$729, beside the judges' number and never instead of it:

$$
I_{\text{after}} = 0.55\,I
\qquad\text{or, capped,}\qquad
I_{\text{after}} = \min\!\left(0.55\,I,\; 729 \times \tfrac{52}{12}\right)
$$

The **goal plan** sets a target of $k$ months of spending ($k = 3$ by default) and saves a share $\alpha$ of the monthly surplus:

$$
\text{months to goal} = \left\lceil \frac{k\,S - B}{\alpha\,(I - S)} \right\rceil
$$

The **backup plan** finds the smallest monthly cut $c$ that keeps the balance at or above \$0 for the whole shock. For a constant monthly gap $G$ over $n$ months, with $B_{\text{left}}$ left after one-off costs:

$$
c = \max\!\left(0,\; G - \frac{B_{\text{left}}}{n}\right)
$$

It then builds that cut from the customer's own options, in order:

1. Cover a negative balance.
2. Cancel unlabelled standing orders.
3. Bring spending down to the customer's own leanest quarter of months.
4. Cut all flexible spending.
5. Ask the lender to pause the loan payment.

The leanest-quarter target is the 25th percentile of the customer's spending above bills, insurance and loan payments. Every cut we suggest is a level the customer has already lived at.

**4. The app.** Streamlit, with four pages, Altair charts and a design system with self-hosted fonts and checked colour contrast. Results are cached, so a shock and plan take about 3 ms after startup.

**5. Tests.** 1,214 tests, including sweeps that build a profile, a shock, a plan and the charts for **all 4,500 accounts**. A judge can type any ID, and we've already run it.

We used AI coding assistants throughout, as the challenge allows, for drafting code, documents and checks. Every number in this write-up was recomputed from the data.

## Challenges we ran into

**Medians don't add up.** Account 20111 has typical money in of \$6,339 and typical spending of \$8,600, a gap of \$2,260 a month. Yet it holds a \$17,612 buffer. Over 38 months it took in \$462,327 and paid out \$451,464, ending \$10,863 up. The medians are each correct, but they come from different months, so their difference isn't the real monthly change. We kept the judges' numbers and added the actual change beside them. Over the last 12 months, 20111's balance fell \$748 a month. The fix mattered across the whole dataset: on 40% of accounts that look like savers on paper (1,038 of 3,309 accounts with a surplus), the balance hasn't grown in a year.

**The formula assumes spending stays flat after a shock. Real customers don't.** We found 735 real income drops across 480 accounts, where money in stayed below 55% of normal for at least 3 months. Customers kept a median of 50% of their usual spending. The formula predicted 493 of those events would be below \$0 after 3 months. Only 31 were. That shaped the backup plan: cutting to your own leanest months is something these customers have already done.

**Most money is cash.** Cash is 75% of all money in, so on cash-only accounts nothing shows whether a deposit is pay. We label income types as *ours* and say plainly that flexible spending may include rent paid in cash.

**Hidden costs.** Lifetime medians show \$0 of loan payment on 197 of 448 running loans, because most started in 2024 or 2025. On 293 accounts, household bills on standing orders exceed the bills the data labels, by a median of \$1,145 a month. We show both figures rather than silently swapping one in.

**A live demo with any account and any twist.** Edge cases had to work first time: 77 accounts with no regular spending, 23 with no buffer, 39 that paid out more than they took in, and IDs that don't exist. The sweep tests over every account are what let us say "pick any one".

**Small things that bit us.** In Streamlit, a dollar sign in Markdown starts LaTeX, so every amount had to be escaped. A chart legend fitted on most accounts but ran off the edge on the one account with nine money types. We only caught it by opening the app and looking.

## Accomplishments that we're proud of

- **It works for any customer, live.** All 4,500 accounts build a profile, a shock, a plan and charts, and the tests check every one. A shock and plan take about 3 ms.
- **We found the medians problem and handled it honestly.** The judges' numbers are untouched, and the actual balance change sits beside them so nobody is misled.
- **Discovery changed the product.** The 735 real income drops showed customers cut their spending, so our backup plan asks for cuts the customer has already made in their own leanest months.
- **The plans give an answer, not just a number.** On the judges' rules, all but 70 of 4,500 customers can get through 6 months on EI, 1,526 by cuts, plus 22 more if the lender agrees to pause the loan payment (1,548 in all). Under the real EI maximum, 600 would need to cut more than half of what they spend. Those are the customers a bank should call first.
- **Every number is checked.** The notebooks recompute the engine's figures from their definitions and found 0 mismatches across all accounts.
- **It's built for the people using it.** Plain-language copy, large text, checked colour contrast, alt text on every chart and table, and a stakeholder questionnaire generated from each customer's own numbers.

## What we learned

- **Check the data before trusting a definition.** One check, that money in minus money out equals the balance change, told us the medians were the problem, not the data.
- **The lowest balance predicts trouble better than income does.** Before each loan, the lowest balance in loan payments separated defaults with an AUC of 0.85, against 0.57 for income. Loans whose lowest balance was under one payment defaulted 34% of the time, against 3.3% for the rest. We found this on the same data with no holdout, so it's a lead, not a model.
- **Higher earners look more fragile under a flat EI rate.** A 45% cut scales with how much money flows through an account, so runway tracks income (rank correlation −0.68) and barely tracks the buffer (−0.04).
- **District data didn't help.** Salary, unemployment and crime all had a correlation of about 0 with runway. A finding that something *doesn't* work is still a finding.
- **Timing matters.** Money out peaks in January and June, so a shock starting in November costs 1.34× a typical month over the next 3 months.
- **Show your numbers next to the official ones, never instead of them.** Judges, and in real life a bank's advisers, need to see both and why they differ.

## What's next for Resilience Rewired

- **Find rent hidden in cash.** Split cash withdrawals into probable rent or bills and discretionary spending, using amounts that repeat each month. That would make the "flexible spending" in every plan more realistic.
- **Rank customers by how hard their plan is.** Score each plan by the cut it needs as a share of spending, so a bank knows whom to call first.
- **Turn the lowest-balance signal into a tested early warning.** Validate it on held-out data before relying on it.
- **Model what customers really do after a shock.** Use the spending response from the 735 income drops as an optional second runway, beside the judges' flat-spending figure.
- **Model tax and EI eligibility**, which the plans don't cover yet.
- **Track the plan over time.** Re-run it each month on new data and show whether the customer is on track for their goal.

## Sources

- CTU Relational Dataset Repository, Financial dataset: https://relational.fel.cvut.cz/dataset/Financial
- Government of Canada, EI regular benefit amount: https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/benefit-amount.html

## Credits

- The data is the PKDD'99 Discovery Challenge Financial dataset, from the CTU Relational Dataset Repository (https://relational.fel.cvut.cz/dataset/Financial).
- The EI weekly maximum is from the Government of Canada.
