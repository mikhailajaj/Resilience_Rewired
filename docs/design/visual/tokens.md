# Tokens: Resilience Rewired

Status: proposed, 2026-11-07. Brand values are measured on tangerine.ca ([research](../research/tangerine_brand.md)); everything marked **own** is our design decision. Implemented in [config.toml](config.toml) first; the few values Streamlit can't take are the injected CSS in [components.md](components.md#injected-css-the-whole-list).

## Decisions and reasons

| # | Decision | Choice | Reason |
| :-- | :-- | :-- | :-- |
| D1 | White text on brand orange `#F2691D` is 3.08:1 | **Darken the fill** to `#C84B0C` (white on it 4.70:1, AA for any size). Hover `#A63D08` (6.38:1). Brand orange stays for chart lines, bars and decoration only (3.08:1 clears the 3:1 graphics rule). | Keeping orange for "large bold labels only" would mean every button label (20px bold, 3.08:1) passes only under the large-text exception and a projector washes out mid-contrast. A darker fill is still recognisably Tangerine; the hue (`h` about 20) is the same. |
| D2 | Orange as text | Never. Small or large text is ink `#3A3835`. Orange is allowed as text only as `#C84B0C` at 4.70:1 and we don't use it. | Brand research: orange text 3.08:1 on white, 2.69:1 on beige. |
| D3 | Page background | **White** `#FFFFFF`. Beige `#F2F0E4` appears once, as the title band. | White gives the highest ink contrast (11.69) and the best margin on a washed-out projector. Beige muted text is only 4.62:1. |
| D4 | Success, error, warning, focus (not observable on tangerine.ca) | See Status below. All own. All text uses are 4.5:1 or more on white and on `#F7F6F6`. | Brief asked us to choose. |
| D5 | Dark mode | **Out of scope.** `base = "light"` is fixed. | Presented on a projector in a lit room; one mode is one thing to test. |
| D6 | Injected CSS | Small, listed in full in components.md (about 30 lines), every rule tied to a `st-key-*` class we create or to a documented `data-testid`. | Theme config can't set per-region type sizes. |

## Colour

### Neutrals and brand

| Token | Value | Source | Role |
| :-- | :-- | :-- | :-- |
| `--ink` | `#3A3835` | brand | Body, headings, numbers, chart text |
| `--ink-muted` | `#716B60` | brand | Help text, captions, "Our numbers" labels. Never below 18px |
| `--surface` | `#FFFFFF` | brand | Page, cards, Before and After |
| `--surface-2` | `#F7F6F6` | brand | Inputs, "Our numbers" panel, expander header, `secondaryBackgroundColor` |
| `--surface-hero` | `#F2F0E4` | brand | Title band only |
| `--surface-head` | `#F0F0EF` | brand | Table header row |
| `--hairline` | `#E9E8E5` | brand | Card and chart gridlines, decorative (1.23:1 by design) |
| `--border-control` | `#8B857B` | own | Input, slider and secondary-button border (3.66:1 on white) |
| `--brand-orange` | `#F2691D` | brand | Chart "money out" line, selected-twist accent bar. Never text |
| `--primary` | `#C84B0C` | own, from brand | Filled buttons, slider fill and thumb, active tab underline, switch on |
| `--primary-hover` | `#A63D08` | own | Button hover and pressed |
| `--link` | `#006BCE` | brand | Links, chart "money in" line, focus ring |

### Status and focus (all own)

| Token | Value | Used for | Always paired with |
| :-- | :-- | :-- | :-- |
| `--success` | `#1B6B3A` | Verdict "they make it" bar, "Selected" check | The words and a check mark |
| `--error` | `#B3261E` | Invalid ID line, verdict "runs out", negative buffer | The words and a cross mark |
| `--warning` | `#8A5A00` | Reserved, **unused in v1** (no banners, no warnings in UI) | Defined so a later "tight" state doesn't invent a colour |
| `--focus` | `#006BCE` | 3px ring, 2px white gap, on every focusable control | Shape (ring) |

Rule: status is words plus a glyph (check, cross) plus colour. Colour is never the only signal. Brand orange carries no status meaning; the primary fill is a brand and action colour, never "bad".
Delta arrows in `st.metric` use `delta_color="off"` and the delta text spells the direction ("down 4.6"), so green and red are not needed there.

## Type

Family: Figtree (OFL), weights 400, 500, 700, self-hosted. Fallback Arial. Minimum size anywhere is **18px**. Body is 20px (brand 16px, raised for projection).

| Role | Size / line | Weight | Colour | Where |
| :-- | :-- | :-- | :-- | :-- |
| `runway-hero` | 72 / 76 | 700 | ink | Before and After runway value (D) |
| `verdict` | 40 / 48 | 700 | ink | Verdict sentence (D) |
| `metric` | 48 / 52 | 700 | ink | Judges' tiles in B (`metricValueFontSize`) |
| `metric-d` | 36 / 40 | 700 | ink | Before and After rows other than runway |
| `h1` | 36 / 44 | 700 | ink | Wordmark "Resilience Rewired" |
| `h2` | 32 / 40 | 700 | ink | Section titles (Pick a twist, Goal plan, Backup plan, Our numbers) |
| `h3` | 28 / 36 | 700 | ink | Sub-headings, Before / After column titles |
| `ours-value` | 28 / 32 | 500 | ink | "Our numbers" values (quieter than judges': smaller and lighter) |
| `body` | 20 / 30 | 400 | ink | Sentences, notes, table cells |
| `label` | 20 / 28 | 500 | ink | Widget labels, metric labels |
| `button` | 20 / 24 | 700 | white on primary, ink on outline | Buttons |
| `help` | 18 / 26 | 400 | ink-muted | Help, captions, "(judges': $2,330)" |
| `eyebrow` | 18 / 24, tracking 0.8px, uppercase | 700 | ink | BEFORE / AFTER, "OUR NUMBERS" tags |

Brand H1 56px is not used: the verdict, not the title, is the top of the page.
Numbers use tabular figures: `font-variant-numeric: tabular-nums` on `.rr-num` so before and after digits line up.

## Spacing (px, 4/8 base from brand)

`--s1` 4, `--s2` 8, `--s3` 12, `--s4` 16, `--s5` 24, `--s6` 32, `--s7` 48, `--s8` 64.
Card padding 24. Gap between columns 32. Gap between page sections 48. Twist button row gap 12. Control height is native at the 20px base (about 50px, no CSS). Content width: `layout="wide"`, side padding 48.

## Radius and shadow

| Token | Value | Use |
| :-- | :-- | :-- |
| `--r-pill` | 999px (`buttonRadius = "full"`) | Buttons (brand 24px on a 48px button is a pill) |
| `--r-card` | 16px (`baseRadius`) | Cards, inputs, expander, "Our numbers" panel |
| `--shadow-judge` | `0 0 15px 0 rgba(0,0,0,.15)` (brand "elevated") | Before and After cards only |
| `--shadow-ours` | none; 1px `--hairline` border instead | "Our numbers" panel: visibly quieter than the judges' cards |

The brand's default card shadow (`0 0 5px 2px rgba(0,0,0,.05)`) disappears on a projector, so it isn't used.

## Dark mode

Out of scope. If ever needed: invert `--surface`/`--ink`, keep `--primary` as fill, and re-run [contrast.md](contrast.md).

## Font files the build needs (not downloaded here)

`app/static/Figtree-Regular.woff2`, `Figtree-Medium.woff2`, `Figtree-Bold.woff2`, from Google Fonts' OFL release; keep the OFL text in the repo next to them (credit in README). Without them the page falls back to Arial and the sizes above still hold.
