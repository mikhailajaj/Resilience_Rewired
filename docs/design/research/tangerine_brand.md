# Tangerine visual language: research notes

Measured 2026-11-07 in Chrome with `getComputedStyle` at 1417px viewport. Research only; nothing downloaded or copied. Page content treated as data.
Marks: **V** = verified in computed styles, **U** = unverified (not measurable or inferred).

Pages read (public, no login, nothing submitted):
- Home: https://www.tangerine.ca/en/personal
- Product: https://www.tangerine.ca/en/personal/save/savings-account
- Tool page: https://www.tangerine.ca/en/personal/save/savings-account/savings-goals-tool
- Contact: https://www.tangerine.ca/en/help-centre/contact-us
- Error: https://www.tangerine.ca/en/personal/contact-us (a 404 page)

## 1. Colour (V; source: home page computed styles)

| Role | Value | Where used (count of text/background hits on home) |
| :-- | :-- | :-- |
| Text | `#3A3835` rgb(58,56,53) | Body, headings, nav, footer links (134 text nodes) |
| Muted text | `#716B60` rgb(113,107,96) | Lead paragraphs, captions (33) |
| Primary / brand orange | `#F2691D` rgb(242,105,29) | Filled CTA "Become a Client", Log in outline, active tab underline, logo |
| Primary hover | `#E34F13` rgb(227,79,19) | CTA hover (measured with real mouse hover) |
| Link | `#006BCE` rgb(0,107,206) | Inline links (underlined), secondary button label, breadcrumbs |
| Surface base | `#FFFFFF` | Header, cards, page |
| Surface alt | `#FAF9F9`, `#F7F6F6`, `#F0F0EF` | Section bands, footer areas |
| Hero surface | `#F2F0E4` (beige) and `#FAF9EC` (cream tint) | Hero band, promo tint |
| Dark surface | `#3A3835` | A few dark blocks (6 elements) |
| Border, secondary button | `#BFB7B3` 1px | "More offers" outline button |
| Border, tabs | `#E9E8E5` inactive, `#F2691D` active, 2px | Personal/Business tabs |
| Scrim | rgba(0,0,0,0.4) / 0.5 | Overlays |

Success, warning, error and focus-ring colours: **U**. No form, validation message or keyboard focus state exists on the public pages read (the Contact page has no form; its cards link to chat and phone). Designer must choose them.

### Contrast (computed from the values above, WCAG 2.x)
| Pair | Ratio | Result |
| :-- | --: | :-- |
| Text on white | 11.69 | AAA |
| Text on hero beige | 10.22 | AAA |
| Muted on white | 5.28 | AA |
| Muted on hero beige | 4.62 | AA (barely) |
| Link on white | 5.26 | AA |
| Link on hero beige | 4.60 | AA (barely) |
| White on orange button (20px bold) | 3.08 | Fails AA normal text; passes the 3:1 large-text rule only |
| White on orange hover | 3.89 | Large-text AA only |
| Orange text on white | 3.08 | Fails AA for text; fine for graphics |
| Orange text on beige | 2.69 | Fails 3:1 |
| Secondary button border on white | 1.97 | Fails 3:1 non-text contrast |
| Tab inactive border on white | 1.23 | Decorative only |

Implication: use orange for fills, large bold labels and chart accents, never for small text. For small orange-adjacent text use `#3A3835`.

## 2. Typography (V)

Family `TangerineCircular, Arial, Helvetica, sans-serif`, self-hosted woff files at `/etc.clientlibs/tangerine/clientlibs/clientlib-site/resources/fonts/tangerine-circular/` (file names reference "lineto" = Lineto Circular, a commercial typeface). Weights 400, 500, 700 only.

| Use | Size / line / weight |
| :-- | :-- |
| Page H1 (tool/product) | 56 / 64 / 700 |
| Section heading | 32 / 40 / 700 |
| Lead paragraph | 22 / 32 / 400, colour muted |
| Nav item, large body | 18 / 24 / 500 or 400 |
| Button label | 20 / 24 / 700 |
| Body | 16 / 24 / 400 |
| Card title | 16 / 24 / 700 (large cards on Contact: bigger, about 24) |
| Small | 14 / 20 / 400 |
| Eyebrow (uppercase) | 12 / 16 / 700; home H1 eyebrow 16 / 24 / 700 / 0.8px tracking |

Home H1 is rendered as a small uppercase eyebrow ("PERSONAL DIGITAL BANKING") with the real headline as a larger bold line below. Headings are sentence case, bold, tight, not condensed.

## 3. Spacing, grid, radius, shadow (V)

- Spacing values seen (px): 2, 4, 8, 12, 16, 24, 32, 40, 48, 64. Most frequent: 32, 8, 24, 4, 16. Looks like a 4/8 base scale.
- Content width 1216px at a 1417px viewport; three-up cards 384px each; two-up cards 536px.
- Breakpoints (CSS variables): 375, 768, 1024, 1280.
- Radius: 24px pills (buttons), 16px cards (and top-only 16 for image cards), 8px small, 4px nav items.
- Shadows: cards `0 0 5px 2px rgba(0,0,0,.05)` (offers) and `0 0 15px 0 rgba(0,0,0,.15)` (linked cards); `0 0 10px rgba(0,0,0,.1)` once. Soft, no offset.

## 4. Components (V unless noted)

- **Header**: two rows. Top utility strip (Personal / Business / Wealth left; Offers, ABM Locator, Rates, Help, Français right), 12px bold-ish, on `#FAF9F9`-ish strip. Main row white: logo 150x31 left, nav Save / Spend / Invest / Borrow / Learn (18px/500, 12px 16px padding, 4px radius), search icon, "Log in" outline, "Become a Client" fill.
- **Hero**: beige `#F2F0E4` band, left text block (eyebrow, bold headline, three checkmark-icon bullets with underlined blue links, tiny legal line), pills for CTAs, right a large 16px-rounded photo with a thin white line graphic overlapping.
- **Buttons**: all pill, 24px radius, 12px 24px padding, 20px bold, about 48px tall.
  - Primary: bg `#F2691D`, white label, no border; hover bg `#E34F13` (V), no shadow.
  - Secondary outline: white bg, `#006BCE` label, 1px `#BFB7B3` border ("More offers").
  - Log in: white bg, `#006BCE` label, 2px `#F2691D` border.
  - Nav buttons: transparent, 4px radius, text colour only.
  - Pressed, disabled, focus: **U**.
- **Cards**: white, 16px radius, shadow above; Contact page has three equal cards (title 24-ish bold, small paragraph, outline pill button at the bottom). Article and tool cards use an image on top with 16px top radius and small uppercase eyebrow ("THE JUICE ARTICLE", "FINANCIAL CALCULATORS & TOOLS") then a 16px bold title.
- **Tabs**: Personal / Business; 16px, padding 8px 16px, 2px bottom border: active `#F2691D` bold, inactive `#E9E8E5` regular.
- **Accordion (FAQ)**: native button whose title span is 18px bold `#3A3835`; row separators and chevron not measured (U).
- **Breadcrumbs**: 14px bold `#006BCE`, chevron separators.
- **Forms, inputs, errors, help text**: **U**. No public form on the pages read (sign-up and log-in are authenticated flows I did not enter). The savings goals tool is behind login. Nothing to claim.
- **Tables**: none found (rates are shown as large figures such as "4.50%" in cards). **U** for table styling.
- **Icons**: simple outline line icons, circled checkmarks for benefits (visual only; sizes not measured). Feedback tab fixed to the right edge; chat bubble bottom right.
- **Footer**: white background, columns of 16px `#3A3835` plain links (Help centre, Learning centre, Contact us...), no dark footer. Stat band above: "$9 billion+", "2 million+".
- **Error page**: 404 "Oops!" in huge bold (about 56px) with a muted bold sentence and a stacked list of bold underlined helper links.

## 5. Logo (V for observation, U for rules)

- Header logo is an SVG `<img alt="Tangerine">`, 150x31px, orange wordmark "Tangerine" with a small mark at the top right, left-aligned, on white. Served at `/content/experience-fragments/tangerine/ca/en/header/master/.../logo-tangerine-orange.svg`.
- No published clear-space or minimum-size rules found on the public pages (U). Do not copy the file. For the prototype use a text wordmark placeholder or leave logo out; using the real logo needs Tangerine's sign-off (datathon organisers).

## 6. Tone of voice (V)

Friendly, plain, short, second person, mildly playful, no jargon. Real phrases from the site:
- "We're here when you need us" (Contact page subtitle)
- "Oops! We can't seem to find the page you're looking for." (404)
- "Goals - Getting you there faster" (tool page H1)
- "Our Chatbot's pretty smart and has a ton of general information." (Contact card)
Lead with a benefit, number-forward ("Earn $250", "4.50% savings rate"), sentence-case headings, CTA verbs "Become a Client", "Set Up a Goal".

## 7. What Streamlit can and cannot do

Installed Streamlit here is 1.64.0 (checked via `pip show`; config option names checked in its `config.py`).

| Item | Reproducible? | How |
| :-- | :-- | :-- |
| primaryColor `#F2691D`, textColor `#3A3835`, backgroundColor `#FFFFFF`, secondaryBackgroundColor `#F2F0E4` or `#FAF9F9`, linkColor `#006BCE` | Yes | `.streamlit/config.toml` `[theme]` (linkColor, borderColor, baseRadius options exist in 1.64 config) |
| Font | Yes with a substitute | `theme.font`, `[[theme.fontFaces]]` with `server.enableStaticServing=true`, or `"Name:<css url>"` (that form calls fonts.googleapis.com at runtime) |
| Button radius 24px, card radius 16px | Partly | `theme.baseRadius` is a single value (full/large/etc. or px), so pill buttons plus 16px cards need injected CSS on `[data-testid]` selectors (fragile across versions) |
| Soft card shadows, `st.container(border=True)` look | Partly | CSS via `st.markdown(..., unsafe_allow_html=True)` |
| `st.tabs` | Yes | Primary colour drives the active underline, close to Tangerine tabs |
| `st.metric` | Yes | Large bold number plus label echoes the "4.50%" cards |
| `st.slider` | Yes | Accent follows primaryColor; thumb/track fine-tuning needs CSS |
| `st.dataframe` | Partly | Themed by config; header and zebra colours limited; no pill/card chrome |
| `st.expander` | Yes | Closest to the Tangerine accordion |
| Hero band with photo, logo, header strip, circled-check bullets | Custom HTML/CSS only; skip photos and logo (no assets allowed) |
| Charts | Yes | Use `theme.chartCategoricalColors` style palettes built from orange, `#006BCE`, `#716B60`, `#3A3835` (verify option name in docs) |

## 8. Font recommendation

TangerineCircular is Lineto Circular (commercial licence): do not hotlink or download it. Recommended open substitute: **Figtree** (SIL Open Font License, Google Fonts), a geometric sans with similar single-storey-leaning round forms and the same 400/500/700 weights. Fallbacks, all OFL: Plus Jakarta Sans, DM Sans, Outfit. Verdict on similarity is a visual judgement (U); a side-by-side render was not done. Load via self-hosted `[[theme.fontFaces]]` (team downloads from Google Fonts itself) in preference to a runtime Google CSS URL.

## 9. Decisions for the visual designer

1. Success, warning, error and focus colours: not in Tangerine's public UI; pick them and keep contrast at 4.5:1.
2. White on `#F2691D` is 3.08:1. Either darken the button fill (about `#C2410C`, check) or keep orange for 20px bold labels only.
3. Pill buttons and 16px cards need CSS injection beyond `config.toml`; accept the fragility or use `baseRadius` only.
4. Logo: use a neutral wordmark unless the organisers confirm brand-asset use.
5. Neutral-vs-beige page background (`#FFFFFF` vs `#F2F0E4`).
6. Forms and tables are unverified; the tool needs both (sliders for shock size, account selector, results table).
