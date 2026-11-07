"""Injected CSS, from docs/design/visual/components.md. Rules marked "build" are additions the theme options couldn't cover."""

CSS = """
<style>
.st-key-hero { background:#F2F0E4; border-radius:16px; padding:24px 32px; }
.st-key-hero h1 { font-size:36px; line-height:44px; padding:0; }
.st-key-hero p { font-size:22px; color:#716B60; }

[class*="st-key-verdict"] { border-left:8px solid #716B60; padding:8px 0 8px 24px; }
[class*="st-key-verdict"] p { font-size:40px; line-height:48px; font-weight:700; margin:0; }
.st-key-verdict-ok { border-left-color:#1B6B3A; }
.st-key-verdict-bad { border-left-color:#B3261E; }

.st-key-before, .st-key-after { background:#fff; border-radius:16px; padding:24px; box-shadow:0 0 15px rgba(0,0,0,.15); }
.st-key-before [data-testid="stMetricValue"], .st-key-after [data-testid="stMetricValue"] { font-size:36px; line-height:40px; }
.st-key-runway-before [data-testid="stMetricValue"], .st-key-runway-after [data-testid="stMetricValue"] { font-size:72px; line-height:76px; }

.st-key-ours { background:#F7F6F6; border:1px solid #E9E8E5; border-radius:16px; padding:24px; box-shadow:none; }

:is(button,input,textarea,[role="slider"],[role="switch"],summary,a):focus-visible { outline:3px solid #006BCE; outline-offset:2px; }
[data-testid="stMetricValue"], .rr-num { font-variant-numeric:tabular-nums; }

/* build: long values such as "No shortfall (120+)" wrap instead of being cut off */
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { white-space:normal !important; overflow:visible !important; text-overflow:clip !important; height:auto; }
/* build: the 18px minimum and muted colour for captions */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { font-size:18px; line-height:26px; color:#716B60; opacity:1; }
/* build: metric labels and deltas at the design sizes */
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { font-size:20px; font-weight:500; }
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * { font-size:20px; }
/* build: the invalid-ID line */
.st-key-id-error, .st-key-id-error * { color:#B3261E; font-size:20px; font-family:Figtree, Arial, sans-serif; }
/* build: the sentences the presenter reads, and the small tag above each card */
.st-key-summary p, .st-key-summary-verdict p, .st-key-plan-sentence p, .st-key-plan-sentence-g p { font-size:24px; line-height:32px; }
.rr-eyebrow { font-size:18px; line-height:24px; letter-spacing:.8px; text-transform:uppercase; font-weight:700; }
.rr-gap { font-size:28px; line-height:36px; }
.rr-our-value { font-size:28px; line-height:32px; font-weight:500; }
.rr-counterpart { font-size:18px; color:#716B60; }
.rr-label { font-size:20px; font-weight:500; }
</style>
"""
