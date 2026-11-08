# ADR 0004: Deterministic free-text parser with a mandatory confirm

Status: accepted, 2026-11-07. Sources: BR-14, RU-15, RU-17, RU-22, AC-3, AC-4, [parser](../design/ux/chat_parser.md), [design §4.1](../architecture/j4_chat.md#41-parsepy).

## Context

A judge may read the card aloud and the presenter may type it. A wrong reading that runs at once would put a wrong number on screen in front of the judge. With no language model (ADR 0002), reading must be rule-based, and it must say when it isn't sure.

## Decisions

1. **`app/assistant/parse.py` reads text with keywords and regular expressions only**, by the [grammar](../design/ux/chat_parser.md#grammar). It returns `ok`, `partial`, `out_of_range` or `unsure`, with `unsure` winning, then `out_of_range`, then `partial`. It never raises.
2. **Nothing runs until the presenter clicks Run it.** `ok` shows the reading in plain words (`T.confirm`). `partial` asks only for the missing size. `unsure` and `out_of_range` offer the buttons. A parsed size becomes a card answer with source `parsed` only on Run it.
3. **Ranges come from one table** (`state.RULES`, the engine's limits), shared with the Other box.
4. **PT-01 to PT-25 are the parser's acceptance tests.** Every example in `app/ui/cheatsheet.py` must also parse to its stated `Shock`.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Run `ok` readings at once | One misread puts a wrong number on screen (RU-17) |
| Fuzzy matching or a small classifier | Hard to explain or test row by row; still needs a confirm |
| No free text, buttons only | Misses BR-14 "in my own words" |

## Consequences

- One extra click on the text path. The buttons stay the fast path.
- The grammar grows only by adding PT rows first.
- Cards the grammar doesn't cover (a start month, OI-7) get a fixed "can't" line, never a guess.
