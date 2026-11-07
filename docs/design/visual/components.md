# Components: mapped to Streamlit

Wireframe regions A to H from [wireframes.md](../ux/wireframes.md). Copy comes from [copy.md](../ux/copy.md) word for word. Tokens: [tokens.md](tokens.md). Theme: [config.toml](config.toml). Where a spec says "native", no CSS is needed.

Hook rule: wrap each styled region in `st.container(key="...")`. Streamlit 1.64 puts the class `st-key-<key>` on it. Our CSS targets only those classes, plus a few documented `data-testid`s. Keys: `hero`, `verdict` / `verdict-ok` / `verdict-bad`, `runway-before`, `runway-after` (wrap the runway metric in each card), `before`, `after`, `ours`, `plan-f`, `plan-g`.

## Injected CSS: the whole list

One `st.html("<style>...</style>")` (or `st.markdown(..., unsafe_allow_html=True)`) near the top. This is the complete budget; anything more needs a reason.

```css
/* 1 title band */
.st-key-hero { background:#F2F0E4; border-radius:16px; padding:24px 32px; }
/* 2 verdict: top of the type scale */
[class*="st-key-verdict"] { border-left:8px solid #716B60; padding:8px 0 8px 24px; }
[class*="st-key-verdict"] p { font-size:40px; line-height:48px; font-weight:700; margin:0; }
.st-key-verdict-ok  { border-left-color:#1B6B3A; }
.st-key-verdict-bad { border-left-color:#B3261E; }
/* 3 Before / After cards: judges' numbers */
.st-key-before, .st-key-after { background:#fff; border-radius:16px; padding:24px; box-shadow:0 0 15px rgba(0,0,0,.15); }
.st-key-before [data-testid="stMetricValue"], .st-key-after [data-testid="stMetricValue"] { font-size:36px; font-variant-numeric:tabular-nums; }
.st-key-runway-before [data-testid="stMetricValue"], .st-key-runway-after [data-testid="stMetricValue"] { font-size:72px; line-height:76px; }
/* 4 Our numbers: quieter */
.st-key-ours { background:#F7F6F6; border:1px solid #E9E8E5; border-radius:16px; padding:24px; box-shadow:none; }
.st-key-ours [data-testid="stMetricValue"] { font-size:28px; font-weight:500; }
/* 5 focus ring on every control */
:is(button,input,textarea,[role="slider"],[role="switch"],summary,a):focus-visible { outline:3px solid #006BCE; outline-offset:2px; }
/* 6 tabular numbers */
[data-testid="stMetricValue"], .rr-num { font-variant-numeric:tabular-nums; }
```

Fragile (check after any Streamlit upgrade): `data-testid="stMetricValue"` (stable for years, but not a public API); the slider thumb has `role="slider"` and BaseWeb may draw its own focus style over rule 5; `st-key-*` needs Streamlit 1.39+ (we run 1.64). Verdict state is chosen by the key: `verdict` (neutral), `verdict-ok`, `verdict-bad`; the attribute selector `[class*="st-key-verdict"]` is the other fragile rule. Dropping all CSS leaves a working but plainer page: everything below degrades to theme defaults.

## A. Customer picker

| Part | Streamlit | Spec |
| :-- | :-- | :-- |
| Wordmark | `st.title("Resilience Rewired")` inside `container(key="hero")` | h1 36px bold ink, text only, no logo. Subtitle `st.markdown` 22px muted (7: 4.62:1 on beige, so never smaller). |
| ID box | `st.text_input("Account ID", ...)` | Label above, 20px/500. Native height (about 50px at the 20px base, no CSS), `--surface-2` fill, 1px `#8B857B`, 16px radius (native via theme). Help text is the widget `help`/caption below in 18px muted. |
| Show customer | `st.button(type="primary")` in `st.form` with the box so Enter works | Filled `#C84B0C`, white 20px bold, pill, native height (about 50px). |
| Loading | `st.spinner` plain text | 20px ink, no overlay. |
| Invalid ID (A3, A4) | `st.caption` or `st.markdown` under the box | `--error` 20px, leading text is the copy itself, prefixed with `✕ `. Box border becomes 2px `#B3261E` (CSS only if cheap; the text alone is enough). Never a banner. |
| Empty (A1) | `st.markdown` K.empty_page | 24px ink, centred below picker. |

States: default, hover (button `#A63D08`), focus-visible (3px blue ring), active (button `#A63D08`, no extra shadow), disabled (not used), error (above), loading (spinner text), empty.

## B. Know the customer

- Four tiles: `st.columns(4)` of `st.metric`, `border=True`. Value 48px/700 (theme), label 20px/500 above, caption 18px muted. Border radius 16px native. No fill, no shadow.
- Runway cap text ("No shortfall (120+)") is longer than a number. Streamlit truncates long metric values with an ellipsis, so if it truncates at projector width, show "120+ months" as the value and "No shortfall" in the caption. Check this one case on screen.
- H, F, P row: `st.columns(3)` metrics, `border=False`, same component at 28px (`.st-key-bfp [data-testid=stMetricValue]` is optional; skip if default 48px fits).
- Summary sentence: `st.markdown` 24px ink (the presenter reads it).
- Notes: `st.markdown` bullets, 20px ink, max 3. Facts only, no icons, no colour.
- Header facts line (income type, data range): `st.caption`-level 18px muted. This is the one place muted text carries a fact, so it never goes under 18px.

## C. Twist controls

| Part | Streamlit | Spec |
| :-- | :-- | :-- |
| Twist buttons | `st.columns` of `st.button(use_container_width=True)` | Unselected: `type="secondary"`, white fill, 1px `#8B857B`, ink label 20px/700, hover fill `#F2F0E4`. **Selected: `type="primary"`** (filled `#C84B0C`, white) and the label is prefixed `✓ ` plus the copy (`Selected: Laid off, EI 55%`, K.b_selected). Selection is never colour alone: fill, check and the word "Selected". |
| Reset | `st.button(type="tertiary")` | Text-only pill, link colour `#006BCE`, underline on hover. Secondary in hierarchy. |
| Selected / Custom line | `st.markdown` under the buttons | "Selected: Laid off, EI 55%" or "Custom" (K.b_selected, K.b_custom), 20px/700 ink, so state is readable without colour. |
| Slider plus number box (Income kept, Income stays lower for, Household bills up, One-off months, Emergency fund target) | `st.columns([3, 1])`: `st.slider` left, `st.number_input` right, both bound to one `session_state` value through `on_change` callbacks | Label once, above the slider, in the label text (unit included, e.g. "Income kept (%)", 20px/500). Slider: filled track and thumb `#C84B0C`. The value is shown in the number box, not only on the thumb. Number box native height (about 50px), about 120px wide, digits right-aligned, tabular figures. Box range can be wider than the slider (months: slider 1 to 24, box up to 120); the slider pins at its end. Help text (K.s_*_help) is a visible `st.caption` under the pair, 18px muted. |
| Number-only boxes (Bills or rent up ($ a month), One-off cost ($), Weekly maximum ($)) | `st.number_input` | Same box spec, width 160px, `$` in the label (never inside the box). No slider. Step per wireframe. |
| One-off pair | slider (months) and `$` box side by side | The last edited one wins and the other resets to 0 (wireframe C). Below them `st.markdown` "Total one-off: $5,000" (K.oneoff_total) at 24px/700 ink, so the room sees the sum, not two boxes. |
| EI maximum switch | `st.toggle("Apply the EI weekly maximum")` with the weekly box on the same row (`st.columns([3, 2])`) | Off: 1px `#8B857B` track, knob left. On: `#C84B0C` track, white knob right. State is also in words: caption "On" / "Off" at the right of the label, 18px ink. Weekly box `disabled=True` while the switch is off. Disabled while Income kept is 100 (caption K.s_disabled). |
| Help text | `st.caption`, never only the `help=` tooltip | 18px muted. The "(i)" help in E is also a caption line, not a hover. |
| Disabled controls (C3) | `disabled=True` | Track, thumb and box border `#BFB7B3`, text `#716B60`. Disabled controls are exempt from contrast; this stays legible anyway. The reason caption (K.s_disabled) stays in 18px ink. |
| More options | `st.expander("More options")` | Same as H expander. Contains the Shock starts in `st.selectbox` (native height, same border as inputs). |

States for every control: default, hover (border `#3A3835`), focus-visible (ring), active, disabled, error (number box out of range: clamp, no red), selected (buttons).

## D. Before and After (judges' numbers, top of page)

Order: verdict first, then two cards, then monthly gap line.

| Part | Streamlit | Spec |
| :-- | :-- | :-- |
| Verdict | `container(key=...)` with `st.markdown` | 40/48 bold ink, 8px left bar. By `verdict_case`: `verdict-ok` (`income_cut_makes_it`, `no_shortfall`): `#1B6B3A` bar and `✓ ` prefix. `verdict-bad` (`income_cut_runs_out`, `runway_zero`): `#B3261E` bar and `✕ ` prefix. `verdict` neutral (`no_shock`, `income_cut_open_ended`, `cost_or_bills_only`): muted bar, no glyph. The second line "The judges' runway is R." is 24px ink, regular. The sentence text itself says the outcome ("They make it through." / "Money runs out in month 4"). |
| Under-verdict facts | `st.markdown` 20px ink | Plain text, no box, no icon, one line per `facts` item. The duration assumption line ("After month 6 we assume no income...") sits under the gap line, 18px muted. |
| Before card | `container(key="before")` with `st.metric` rows | Eyebrow "BEFORE" (18px caps), runway at 72px, other rows 36px. White card, `--shadow-judge`. |
| After card | `container(key="after")` | Same, with `delta` text on each metric: `delta="down 4.6"`, `delta_color="off"` (grey arrow, words carry direction). Delta text 20px. |
| Equal Before and After | delta omitted | Card shows no delta text. |
| Monthly gap line | `st.markdown` 28px with `.rr-num` | "Monthly gap  $2,260 -> $5,114", ink. |
| Runway caps | value text "No shortfall (120+)" / "0 months" | Wrap OK; keep unit "months" beside the number. |

States: default, no shock (Before = After, deltas hidden), D1 no shortfall, D2 runway 0 (buffer left shown negative, real minus sign `-$3,200`, ink, plus the verdict), loading none.

## E. Our numbers

`container(key="ours")` directly below D, with rows in `st.columns(3)`. D takes the full width so the 72px runway fits, and its other rows sit in `st.columns(3)`. Heading `st.subheader("Our numbers, shown beside the judges'")` at 24px (h4), line "They never replace the judges' figures." 18px muted. Rows: `st.metric` or two-column markdown, value 28px/500, label 18px, counterpart `(judges': $2,330)` 18px muted. Panel is `--surface-2`, 1px hairline, no shadow. The first row ("Runway, if you adjust") has the same size as the others and no status colour (RU-10). The row "Runway with EI weekly max" appears only when the switch is on, same size and style, with its own plain line "With the maximum, they run out in month 4." (no coloured bar: the colour bar belongs to the judges' verdict only). `n/a` rows: value `n/a` in ink, reason in the caption beneath, never blank. Help text is a visible caption, not only a tooltip.

## F, G. Plan sections

- Each plan in `container(key="plan-f"|"plan-g", border=True)`: 16px radius, white, 1px `#E9E8E5` (native border), 24px padding.
- Title h2 32px (K.f_head, K.g_head). F caption "Before any shock" 18px muted.
- Sentence (K.f_sentence, K.g_sentence): 24px ink, the numbers are plain bold within the sentence (`**$51,600**`).
- Target slider plus number box: as C.
- Inline state lines (Already there, no surplus, floor): 20px ink plain text, no icon, no colour.
- Order to act (G): `st.markdown` numbered list, 20px.
- Placeholder (K.g_none): 20px muted (5.28:1).

## H. Details

| Part | Streamlit | Spec |
| :-- | :-- | :-- |
| Expander | `st.expander(K.h_expander, expanded=False)` | Header `--surface-2`, 16px radius, 20px/700 label, chevron native. Focus ring from rule 5 (`summary`). |
| Tabs | `st.tabs` | 20px/700. Active: ink label, 3px underline `#C84B0C` (primaryColor, native). Inactive: 20px/500 muted ink `#716B60`. Because two states differ by weight and underline, not colour alone. |
| Tables | `st.dataframe(hide_index=True, use_container_width=True)` | Header `#F0F0EF` bold, hairline row borders, 18px cells, numbers right-aligned (set `column_config` alignment/format), 1.5x row height. Do not rely on zebra. Savings path table: max 6 rows. |
| Charts | `st.altair_chart` | See [charts.md](charts.md). |
| Alt text | `st.caption` under each chart | K.h_chart_alt text, 18px muted. |
| Footer | `st.caption` | K.footer 18px muted. |

## Page-level

- `st.set_page_config(layout="wide", page_title="Resilience Rewired")`. Hide the Streamlit header/footer toolbar only if the build already hides it; do not add CSS for it.
- Section spacing 48px: use `st.write("")` sparingly or `st.container(height=...)`; avoid `<br>`.
- Narrow window: columns stack (native). The twist buttons wrap to two rows.
