# Discovery findings

What the bank data says about financial resilience, and what the engine should do about it. The analysis, charts and robustness checks are in [`discovery.ipynb`](../discovery.ipynb). Column definitions are in [`data_model.md`](data_model.md), and the customer lookup built on these findings is in [`know_the_customer.md`](know_the_customer.md).

Account figures use the [README's judging definitions](../README.md#how-judges-calculate-the-numbers) unless a section says otherwise.

## Biggest finding

**The runway formula assumes spending stays flat after a shock, and real customers almost never do that.**

The test used 735 real income drops across 480 accounts, where money in stayed below 55% of normal for at least 3 months.

| Measure | Result |
| :-- | --: |
| Income kept (median) | 13% of usual |
| Spending kept (median) | 50% of usual |
| Events where spending stayed within 10% of usual | 5% |
| Formula's prediction: below zero after 3 months | 493 events |
| Actually below zero after 3 months | 31 events |
| Actual loss as a share of predicted loss (median) | 40% |

Spending stays close to its usual level in months with no income drop, at 101% of its trailing median, so the fall isn't normal variation.

### The response depends on the starting buffer

| Starting buffer, in months of usual spending | Events | Spending vs usual | Predicted loss | Actual loss |
| :-- | --: | --: | --: | --: |
| Under 2 | 410 | 37% | $63,865 | $16,310 |
| 2 to 6 | 219 | 71% | $38,060 | $26,384 |
| 6 or more | 106 | 247% | $2,553 | $10,123 |

- **Under 6 months:** the formula overstates the loss. Accounts under 2 months couldn't have kept spending at their usual rate anyway, so part of that cut may be forced.
- **6 months or more:** usual spending is small compared with savings, and it rises during the drop. The formula understates the loss, though these buffers can absorb it.

### Limits

- These are falls in deposits, not confirmed job losses. All but one are on cash-only accounts, so they may be a business slowing down or money moving elsewhere.
- If deposits and withdrawals are partly the same cash going round, they would fall together with no real belt-tightening. Spending still isn't flat, but "people cut back" is only one reading.
- Customers may also have income or savings outside this bank.
- Pension and transfer accounts have almost no events, and most events come from high-flow accounts. An income drop this deep is also larger than a 45% EI cut.

The notebook's adjusted runway applies this response to cash-only accounts and cuts those under 6 months from 43% to 10%. It's an illustration, so don't quote it as a result.

## Other findings

### A job loss is the shock that matters

| Scenario | Accounts under 6 months |
| :-- | --: |
| No shock | 3% |
| Repair costing one month of spending | 9% |
| Job loss with EI at 55% | 35% |
| Job loss with bills up 15% | 39% |

### There are three kinds of customer

| Income type | Accounts | Median money in | Median buffer | Median EI runway | Under 6 months | Loans | Default rate |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| Cash only | 2,894 | $9,751 | $26,697 | 6.8 months | 43% | 472 | 13.3% |
| Transfers | 866 | $3,008 | $18,295 | 10.4 months | 39% | 210 | 6.2% |
| Pension | 740 | $3,530 | $14,335 | 35.4 months | 1% | 0 | None |

- A layoff doesn't fit pensioners. All 638 customers aged 65 or over have a pension.
- Cash makes up 75% of all money in and 76% of all money out. On cash-only accounts, nothing shows whether a deposit is pay.

### Higher earners look more fragile

| Income band | Median money in | Median buffer | Under 6 months on EI |
| :-- | --: | --: | --: |
| Lowest fifth | $2,068 | $13,599 | 4% |
| Low | $3,818 | $15,496 | 8% |
| Middle | $7,568 | $22,773 | 42% |
| High | $12,258 | $29,294 | 51% |
| Highest fifth | $20,046 | $35,417 | 70% |

Runway tracks income, with a rank correlation of -0.68, and barely reflects the buffer, at -0.04. A 45% income cut scales with how much money flows through an account, and flow varies far more than buffers do.

The highest district average salary is $7,892, against $20,046 for the top band. That suggests much of this flow isn't pay, though some accounts may have two earners. This table uses the judges' flat 55%, so real high earners would lose more than it shows. The engine's optional EI weekly maximum shows that second figure.

### Lifetime medians miss recent loans

- Typical fixed costs show $0 of loan payment on 197 of 448 running loans, a median of $2,545 a month. Almost all of those loans started in 2024 or 2025.
- 79 finished loans are still counted, at a median of $2,599 a month.
- Don't add the payment on top of spending. On the 197 accounts, recent money out is only $724 above typical spending, so a loan seems to displace other spending.

### Household bills miss unlabelled transfers

Found while building [`know_the_customer.ipynb`](../know_the_customer.ipynb).

- On 293 accounts, `household bills` standing orders exceed typical household bills (H) by more than 10%, a median gap of $1,145 a month. For 162 accounts, H is $0 even though they have such an order.
- The main cause is 279 orders whose transfers carry no bills label. They still count in spending, so runway doesn't change, but H and F are too low.
- A bills shock based on H is therefore too small on these accounts.
- None of the 341 leasing orders has a matching transfer, so that cost may be missing from spending altogether.

### The lowest balance predicts default

These use only data from before each loan, across 682 loans and 76 defaults.

| Signal | AUC |
| :-- | --: |
| Lowest balance, in loan payments | 0.85 |
| Lowest balance, in dollars | 0.83 |
| Average balance | 0.72 |
| Payment as a share of income | 0.67 |
| Loan amount | 0.64 |
| Income | 0.57 |

| Lowest balance in the 6 months before the loan | Loans | Defaults | Default rate |
| :-- | --: | --: | --: |
| Below $0 | 21 | 21 | 100% |
| $0 to 1 payment | 152 | 38 | 25% |
| 1 to 3 payments | 122 | 8 | 7% |
| 3 or more payments | 387 | 9 | 2% |

A lowest balance under one payment flags 173 loans and catches 59 of the 76 defaults. The default rate is 34% for those loans and 3.3% for the rest.

**Limits:** the thresholds were chosen on this same data with no holdout. The "below $0" group is small. Status is as of the end of 2025, so recent loans have had less time to default, and the data only covers loans the bank approved.

### Timing changes the cost of a shock

- Money out peaks in January and June every year.
- Money in jumps in June and December, mostly on cash-only accounts, while pensions stay flat.
- The next 3 months cost 1.34x a typical month starting in November, and 0.90x starting in February.

### District data doesn't help

District salary, unemployment, urban ratio and crime rate all have a rank correlation of about 0 with runway and buffer. Use them for context, not to drive a plan.

## Engine requirements

| Finding | Requirement |
| :-- | :-- |
| Flat spending almost never happens | Show the judges' flat-spending runway first, then a second "if you adjust" runway labelled as a scenario |
| Runway tracks flow, not savings | Show buffer in months of spending next to runway, and name the income type |
| Pensions don't stop with a layoff | Flag the mismatch on a job-loss twist, then still give the requested number |
| Lifetime medians go stale | Use `monthly_payment` for running loans in fixed costs, and leave out finished loans |
| H misses unlabelled bills | Show bills on standing orders next to H, and flag when a bills shock on H will be too small |
| Lowest balance predicts trouble | Use "keep your lowest balance above one payment" as a plan goal and warning sign |
| Spending is seasonal | Let a shock have a start month, and warn when it runs into January |

## Live demo traps

A judge can pick any `account_id`, so the engine should handle each of these on purpose. Example accounts are in section 10 of the notebook.

| Trap | Accounts |
| :-- | --: |
| Typical money in is $0 | 14 |
| Typical spending is $0 | 77 |
| Both are $0 | 10 |
| Buffer is zero or negative | 23 |
| Data stops before December 2025 | 76 |
| Pension income | 740 |
| Household bills are $0, so a bills shock does nothing | 1,225 |
| Running loan with $0 in typical fixed costs | 197 |
| Running loan with no payment in the last month | 12 |

## Open questions

- Why is December 2025 spending so low? It affects the buffer calculation, because it's in the last 6 months.
- What are the income drop events in real life: job losses, business slowdowns or money moving elsewhere?
- Does the one-payment warning line hold on loans it wasn't chosen on?
