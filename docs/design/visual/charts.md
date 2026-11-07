# Charts

Charts in the UX docs ([wireframes H](../ux/wireframes.md#h-details-closed-stexpander)): (1) money in and money out by month, (2) balance by month with the lowest point marked. Both live inside the closed expander, so they are supporting detail, not the headline. Build with `st.altair_chart` (native `st.line_chart` can't draw the lowest-point marker or direct labels).

## Palette

Brand-matched pair, validated:

```
node .../dataviz/scripts/validate_palette.js "#006BCE,#F2691D" --mode light
  [PASS] Lightness band   [PASS] Chroma floor
  [PASS] CVD separation   worst adjacent ΔE 27.7 (protan), tritan 33.3
  [PASS] Normal-vision    ΔE 37.7
  [PASS] Contrast vs surface (#fcfcfb)  all 2 >= 3:1
  -> ALL CHECKS PASS
```

The default validated order `#2a78d6, #eb6834, #1baf7a, #6250d6` also passes but warns that green `#1baf7a` is 2.74:1 on the surface; we only need two series, so the brand pair is used and the extras are not. Don't add a third colour to these two line charts. `#C84B0C` (the darkened primary) is not a chart colour: it matches `#F2691D` too closely.

| Series | Colour | Mark | Meaning |
| :-- | :-- | :-- | :-- |
| Money in | `#006BCE` | 2px solid line | Chart 1 |
| Money out | `#F2691D` | 2px solid line | Chart 1 |
| Balance | `#006BCE` | 2px solid line | Chart 2 (one series: no legend needed, title says it) |
| Zero line | `#716B60` | 1px solid | Chart 2, labelled "$0" |
| Lowest point | ink `#3A3835` | 10px circle, white 2px stroke | Chart 2 plus a text label "Lowest: -$120 in Mar 2025" |

Orange is on charts, not text, so its 3.08:1 meets the 3:1 graphics rule (see [contrast.md](contrast.md) row 30).

## Rules

- One y-axis per chart. Two measures that need different scales get two charts. Chart 1 shares one dollar axis because both series are dollars per month.
- Thin marks: 2px lines, no area fills, no markers on every point (only the lowest point).
- Gridlines: horizontal only, 1px solid `#E9E8E5`. No dashes, no vertical grid.
- Axis lines: bottom axis 1px `#716B60`; no left axis line.
- Text: titles 20px/700 ink; axis labels and tick labels 18px `#3A3835`; legend labels 18px ink. Nothing under 18px, no muted grey on chart text.
- Legend: chart 1 has two series, so a legend at the top-left (symbol = short 24px line) **and** direct labels at the right end of each line ("Money in", "Money out" in series colour is not allowed for text: label text is ink, with a short line swatch in series colour beside it). Chart 2 has one series: no legend.
- Dollar axis format `$,.0f`; month axis `%b %Y`, ticks every 6 months.
- Chart background transparent over white; width fills the tab; height 320px.
- Alt text and summary go in the caption below (K.h_chart_alt); the lowest point is also stated in plain text in the caption.
- Range of dates and missing months: leave gaps as gaps (no interpolation).

## Vega-Lite config to pass (via `.configure_*` in Altair)

```
view: stroke none; background: transparent
axis: labelFont/titleFont "Figtree", labelFontSize 18, titleFontSize 18, labelColor "#3A3835", titleColor "#3A3835",
      gridColor "#E9E8E5", gridWidth 1, gridDash [], domainColor "#716B60", tickColor "#716B60"
axisY: domain false, ticks false, labelPadding 8
legend: labelFontSize 18, labelColor "#3A3835", symbolType "stroke", symbolStrokeWidth 3, orient "top-left"
line: strokeWidth 2, interpolate "linear"
scale range (category): ["#006BCE", "#F2691D"]
```

## Money in and out tab

Both charts were asked for by the owner and sit on the Customer profiling page.

- **Pie:** the whole is money in, and the slices are money out by payee type, plus what's left in the account. If money out is larger, the whole is money out and the title says by how much. Each legend label carries its share, so the value is never colour alone.
- **Monthly columns:** two stacked columns a month. The left is money in by type, and the right is money out with loan payments at the bottom. Each side has its own titled legend, and the Month by month table holds every value.

| Stack position | Money in | Colour | Money out | Colour |
| --: | :-- | :-- | :-- | :-- |
| 1, bottom | Cash deposits | `#006BCE` | Loan payments | `#e34948` |
| 2 | Transfers in | `#1baf7a` | Household bills | `#eda100` |
| 3 | Interest | `#5598e7` | Cash withdrawals | `#6250d6` |
| 4 | Pension | `#008300` | Other transfers out | `#F2691D` |
| 5 | | | Insurance and bank fees | `#8F5A12` |
| 6 | | | Card withdrawals | `#e87ba4` |

Each colour order goes through `validate_palette.js`, because stack neighbours are the pairs that touch. Insurance and bank fees share a colour to stay within six series; the Where money goes table keeps them apart. "Left in the account" is neutral `#8B857B`, because it isn't a payee.

## Not used

Dual axis, area, gradient, 3D, a chart title in series colour.
