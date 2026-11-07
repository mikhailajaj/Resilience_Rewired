# Contrast: every text and control pair

WCAG 2.x relative-luminance ratios, computed with a script (scratchpad, formula from the spec). AA needs 4.5:1 for text under 24px (or 18.66px bold), 3:1 for large text, graphics and control boundaries. Our smallest text is 18px/400, so **4.5:1 is the bar for all text**.

## Text

| # | Foreground | Background | Ratio | Result | Where |
| :-- | :-- | :-- | --: | :-- | :-- |
| 1 | ink `#3A3835` | white `#FFFFFF` | 11.69 | AAA | Body, numbers, headings |
| 2 | ink | `#F7F6F6` | 10.83 | AAA | "Our numbers" panel, inputs |
| 3 | ink | `#F2F0E4` | 10.22 | AAA | Title band |
| 4 | ink | `#F0F0EF` | 10.25 | AAA | Table header |
| 5 | muted `#716B60` | white | 5.28 | AA | Help, captions |
| 6 | muted | `#F7F6F6` | 4.90 | AA | Help inside "Our numbers" |
| 7 | muted | `#F2F0E4` | 4.62 | AA (thin) | Subtitle in title band; keep at 22px+ |
| 8 | muted | `#F0F0EF` | 4.63 | AA (thin) | Disabled-control text; keep 18px+ |
| 9 | link `#006BCE` | white | 5.26 | AA | Links |
| 10 | link | `#F7F6F6` | 4.87 | AA | Links inside panel |
| 11 | success `#1B6B3A` | white | 6.54 | AA | Verdict "makes it" text and check |
| 12 | success | `#F7F6F6` | 6.06 | AA | |
| 13 | error `#B3261E` | white | 6.54 | AA | Invalid ID line, "runs out" |
| 14 | error | `#F7F6F6` | 6.06 | AA | |
| 15 | warning `#8A5A00` | white | 5.93 | AA | Reserved |
| 16 | warning | `#F7F6F6` | 5.49 | AA | Reserved |

## Buttons and controls

| # | Pair | Ratio | Result | Note |
| :-- | :-- | --: | :-- | :-- |
| 17 | white on primary fill `#C84B0C` | 4.70 | AA | **Fix for brand 3.08:1** |
| 18 | white on primary hover `#A63D08` | 6.38 | AA | |
| 19 | white on brand orange `#F2691D` (rejected) | 3.08 | fails 4.5 | Why the fill is darkened |
| 20 | white on brand hover `#E34F13` (rejected) | 3.89 | fails 4.5 | |
| 21 | ink on brand orange (alternative, rejected) | 3.79 | fails 4.5 | Dark label on bright orange also fails |
| 22 | ink on outline-button hover `#F2F0E4` | 10.22 | AAA | |
| 23 | secondary-button / input border `#8B857B` on white | 3.66 | AA non-text | Brand `#BFB7B3` is 1.97:1 and fails, so replaced |
| 24 | same border on `#F7F6F6` | 3.39 | AA non-text | Inputs sit on surface-2 |
| 25 | primary `#C84B0C` (slider fill, thumb, switch on, tab underline) on white | 4.70 | AA non-text | |
| 26 | focus ring `#006BCE` on white | 5.26 | AA non-text | Ring sits on the 2px white gap |
| 27 | focus ring on `#F7F6F6` | 4.87 | AA non-text | |
| 28 | slider unfilled track `#E9E8E5` on white | 1.23 | **below 3:1, accepted** | Decorative: the thumb (row 25) and the number box carry the value as text |

## Charts and decoration

| # | Pair | Ratio | Result |
| :-- | :-- | --: | :-- |
| 29 | chart "money in" line `#006BCE` on white | 5.26 | AA non-text |
| 30 | chart "money out" line `#F2691D` on white | 3.08 | AA non-text (3:1) |
| 31 | chart text, ink on white | 11.69 | AAA |
| 32 | chart zero line `#716B60` on white | 5.28 | AA |
| 33 | gridline `#E9E8E5` on white | 1.23 | decorative; marks are never read from gridlines alone |

Rows 19-21 are the rejected options, kept to show the numbers behind decision D1. Only row 30 and row 28 sit under 4.5:1, each for the stated reason.
