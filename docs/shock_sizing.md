# Shock sizing

How to size each shock for challenge requirement 2, using official Canadian figures, and what each size does to the 4,500 accounts. Figures were retrieved on 2026-11-07. The engine's shock fields are in [`engine_contract.md`](engine_contract.md).

## Summary

- **The EI weekly maximum is the biggest gap.** The 2026 maximum of $729 a week is about $3,159 a month. It limits 57% of accounts, and accounts under 6 months of runway go from 35% to 51%. The engine models it as a labelled second runway, off by default, so the judges' number doesn't change.
- **Bills sizes barely change the picture.** Official price changes are mostly well under the judges' 15% example, and even 25% moves few accounts.
- **Repair cost is better in dollars for many accounts.** One month of spending is the judges' definition, but it can be far from the cost of a real repair.

Judges' numbers still come first. These figures sit beside them, as labelled additions.

## Requirement coverage

| Requirement 2 asks for | Status |
| :-- | :-- |
| Job loss with EI | In the engine, with any income kept and any length |
| Higher rent or household bills | In the engine as a percentage of H, with a standing-order figure beside it |
| Surprise repair | In the engine, in dollars or as a multiple of S |
| A mix | In the engine |
| User can change the size | Engine accepts any size; sliders are designed but not built |
| Sizes grounded in sources | This page |
| **EI weekly maximum** | **In the engine, off by default, with a typed value** |

## Recommended controls

| Control | Default | Range | Reference points to show |
| :-- | :-- | :-- | :-- |
| Income kept | 55% | 0 to 100%, step 1 | 55% basic rate; up to 80% with the family supplement |
| EI weekly maximum | Off, to match the judges | On or off | $729 a week in 2026 |
| Length of lower income | 6 months | 3 to 15 months | 14 weeks minimum; 22.8 weeks average time unemployed; 45 weeks standard maximum; 65 weeks for long-tenured workers |
| Bills increase | 15% | 0 to 25%, step 1 | 2.8% rent CPI; 5.7% water, fuel and electricity CPI; 10.2% Montréal two-bedroom rent |
| Repair | 1 month of spending | $0 to $15,000, or a multiple of S | $1,500 repair; $3,500 and $10,000 furnace replacement |

Months use 52 ÷ 12 weeks a month, so 14 weeks is 3.2 months, 45 weeks is 10.4 and 65 weeks is 15.

## Job loss with EI

### Official rules

| Rule | Value | Source |
| :-- | :-- | :-- |
| Basic rate | 55% of average insurable weekly earnings | [Benefit amount][ei-amount] |
| Weekly maximum, 2026 | $729 | [Benefit amount][ei-amount] |
| Maximum insurable earnings, 2026 | $68,900 a year, about $5,742 a month | [Benefit amount][ei-amount] |
| Family supplement | Up to 80%, if net family income is $25,921 or less | [Benefit amount][ei-amount] |
| Length | 14 to 45 weeks, depending on insurable hours and regional unemployment | [Benefit amount][ei-amount] |
| Extra weeks | 20 more, up to 65, for long-tenured workers on claims starting June 15, 2025 to June 12, 2027 | [Temporary measures][ei-temp] |
| Waiting period | Normally 1 week, but waived for new claims starting March 30, 2025 to October 9, 2027 | [Temporary measures][ei-temp] |
| Separation earnings | Severance and similar pay aren't deducted, for claims or allocations starting March 30, 2025 to October 9, 2027 | [Temporary measures][ei-temp] |
| Tax | Benefits are taxable | [Benefit amount][ei-amount] |

### Effect of the weekly maximum

The maximum applies once typical money in is above about $5,744 a month. Limited accounts keep a median of 25% of typical money in, not 55%.

| Measure | Flat 55% (judges) | With the maximum |
| :-- | --: | --: |
| Accounts limited by the maximum | n/a | 2,574 (57.2%) |
| Median runway, all accounts | 8.6 months | 5.7 months |
| Median runway, limited accounts | 5.4 months | 3.1 months |
| Under 3 months | 9.7% | 27.9% |
| Under 6 months | 35.1% | 51.2% |
| Under 6 months, excluding pensions | 41.7% | 61.0% |

Limited accounts by income type: 74.1% of cash-only, 49.5% of transfer and none of the pension accounts.

**Caution:** this treats typical money in as insurable earnings. [`discovery.md`](discovery.md) shows that much of the flow may not be pay. In that case the true benefit would be lower still, because EI is based on earnings, not deposits.

### Can they last the benefit period?

The share of accounts with enough runway to last each length:

| Benefit length | Months | Flat 55% | With the maximum |
| :-- | --: | --: | --: |
| 14 weeks | 3.2 | 88.0% | 68.9% |
| 26 weeks | 6.0 | 64.9% | 48.8% |
| 36 weeks | 8.3 | 51.2% | 41.6% |
| 45 weeks | 10.4 | 43.7% | 37.8% |

### How long unemployment lasts

From the Labour Force Survey, October 2026, seasonally adjusted:

- Average time unemployed is 22.8 weeks, about 5.3 months. This covers people still unemployed, so it isn't how long a completed spell lasts.
- 23.7% of unemployed people have been out of work for 27 weeks or more.
- 189,600 of about 1.5 million unemployed have been out of work for 52 weeks or more.

So the 6-month default is close to the average, and a 12-month stress case isn't unrealistic.

### Unemployment rate

October 2026, seasonally adjusted: 6.7% for Canada, against 6.9% a year earlier. Provinces range from 5.0% in Manitoba to 8.7% in Newfoundland and Labrador. Use this as context only, because accounts can't be matched to Canadian regions.

### Earnings benchmark

Average weekly earnings were $1,354.55 in August 2026, up 3.7% from a year earlier. That's about $5,870 a month, seasonally adjusted, including overtime. It's just above the level where the EI maximum applies, about $5,744, so an average earner is already limited.

Median typical money in is $7,568, and 56.8% of accounts exceed average earnings.

## Rent and household bills

### Official price changes

Consumer Price Index for Canada, September 2026 against September 2025:

| Item | Change |
| :-- | --: |
| All items | +3.1% |
| Shelter | +1.8% |
| Rent | +2.8% |
| Water, fuel and electricity | +5.7% |
| Electricity | +3.6% |
| Water | +5.1% |
| Natural gas | −6.8% |
| Fuel oil and other fuels | +57.8% |

### Average rents

CMHC two-bedroom rents in apartment structures of six or more units, 2024 to 2025:

| City | 2024 | 2025 | Change | Per month |
| :-- | --: | --: | --: | --: |
| Vancouver | $2,315 | $2,367 | +2.2% | +$52 |
| Toronto | $1,979 | $2,056 | +3.9% | +$77 |
| Calgary | $1,909 | $1,936 | +1.4% | +$27 |
| Halifax | $1,724 | $1,838 | +6.6% | +$114 |
| Ottawa-Gatineau | $1,732 | $1,793 | +3.5% | +$61 |
| Hamilton | $1,639 | $1,656 | +1.0% | +$17 |
| Edmonton | $1,536 | $1,603 | +4.4% | +$67 |
| Winnipeg | $1,513 | $1,577 | +4.2% | +$64 |
| Montréal | $1,238 | $1,364 | +10.2% | +$126 |

Across all 164 centres with both years, the median change is +6.7%, from +0.8% at the 10th percentile to +15.1% at the 90th. Small centres can move sharply, so the nine cities above are the better reference.

These are survey averages across all units, not increases on one tenancy. The latest year is 2025, so this table is about a year older than the CPI.

### Effect on accounts

| Bills increase | Reference | Extra a month, median where H > $0 | Under 6 months alone | Under 6 months with EI at 55% |
| :-- | :-- | --: | --: | --: |
| 2.8% | Rent CPI | $60 | 2.8% | 35.6% |
| 3.9% | Toronto rent | $84 | 2.8% | 35.8% |
| 5.7% | Water, fuel and electricity CPI | $122 | 2.8% | 36.4% |
| 10% | Near Montréal rent | $215 | 2.9% | 37.6% |
| 15% | Judges' example | $322 | 3.1% | 38.7% |
| 25% | Stress case | $537 | 3.6% | 40.7% |

A bills increase alone rarely threatens an account, but it uses up the surplus. Accounts showing no shortfall fall from about 77% at 2.8% to about 64% at 25%.

H is $0 on 1,225 accounts, so a bills shock based on H does nothing there. The engine's standing-order figure helps on the 293 accounts where H misses bills.

The data has one household bills figure, so it can't separate rent from utilities. District names are the bank's original regions, so an account can't be matched to a Canadian city. City rents are "what if" sizes, not that customer's actual rent.

## Surprise repair

### Costs

No official source for furnace costs turned up. These come from contractor and industry guides, which vary, so treat them as rough and label them that way.

| Repair | Rough cost | Source |
| :-- | --: | :-- |
| Furnace repair | $150 to $1,500 | [Experts CA guide][repair-guide] |
| Furnace replacement, installed | $3,500 to $10,000 | [RenoQuotes guide][furnace-guide] |

For context, the CPI for homeowners' maintenance and repairs rose 1.2% in the year to September 2026.

### Effect on accounts

Median typical spending is $7,389, but the quartiles are $2,495 and $13,028. So "one month of spending" is below the cheapest furnace replacement for many customers and above the dearest for others.

| Repair | Accounts where it uses up the buffer | Under 3 months afterwards |
| :-- | --: | --: |
| $1,500 | 0.8% | 1.6% |
| $3,500 | 1.0% | 1.9% |
| $5,000 | 1.3% | 2.4% |
| $10,000 | 7.2% | 9.5% |
| 1 month of spending (judges) | 4.0% | 6.3% |

## Mixes to offer

| Mix | Income kept | Length | Bills | Repair | Source of the sizes |
| :-- | --: | --: | --: | --: | :-- |
| Judges' combined twist | 55% | 6 months | +15% | None | README |
| Realistic layoff | 55% with the maximum | 5.3 months | +2.8% | None | EI, Labour Force Survey and CPI |
| Long layoff, winter | 55% with the maximum | 10.4 months | +5.7% | $3,500 | EI, CPI and repair guide |

## Sources

Link these in the submission.

| Source | Period used | Table or page date |
| :-- | :-- | :-- |
| [Consumer Price Index, Table 18-10-0004][cpi] | September 2026 | File dated 2026-10-19 |
| [CMHC average rents, Table 34-10-0133][rent] | 2024 and 2025 | File dated 2025-12-17 |
| [Labour Force Survey, Table 14-10-0287][lfs] | October 2025 and 2026 | File dated 2026-11-06 |
| [Duration of unemployment, Table 14-10-0342][duration] | October 2026 | Added to the README's list |
| [Average weekly earnings, Table 14-10-0223][awe] | August 2025 and 2026 | File dated 2026-10-29 |
| [EI regular benefits: amount and weeks][ei-amount] | 2026 | Page dated 2026-10-19 |
| [EI temporary measures][ei-temp] | Current | Page dated 2026-10-06 |
| [Furnace replacement guide][furnace-guide] and [furnace repair guide][repair-guide] | 2026 | Non-official, from search results only; pages not read in full |

[cpi]: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401
[rent]: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410013301
[lfs]: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410028701
[duration]: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410034201
[awe]: https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410022301
[ei-amount]: https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/benefit-amount.html
[ei-temp]: https://www.canada.ca/en/services/benefits/ei/temporary-measures-for-major-economic-conditions.html
[furnace-guide]: https://renoquotes.com/en/blog/furnace-replacement-cost-in-canada-what-should-you-budget-in-2026
[repair-guide]: https://expertsca.vercel.app/resources/home-improvement/furnace-repair-cost-canada

## Known limits

- **The data isn't Canadian in origin.** Accounts come from a converted European dataset, so Canadian figures size the shocks but don't describe these customers' real cities or incomes.
- **Tax isn't modelled.** EI is taxable, so these figures are before tax and overstate the money received.
- **EI eligibility isn't modelled.** The data doesn't show insurable hours, so every non-pension account is treated as eligible for the chosen length.
- **Prices are one-year changes.** A shock can be larger for one household than for the national average.
- **Fuel oil is an outlier.** Its +57.8% isn't used as a default, because it only applies to homes heated with it.
