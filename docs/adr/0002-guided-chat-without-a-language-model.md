# ADR 0002: Guided chat without a language model

Status: accepted, 2026-11-07. Sources: BR-14 to BR-18, RU-15, RU-16, OI-8, [scope](../inception/scope.md#chat-assistant-j4-mvp-and-stretch), the owner's brief for the chat (2026-11-07), [design](../architecture/j4_chat.md).

## Context

The judges want to give a twist card and see the numbers behind the answer (BR-14, BR-16). The app is hosted on Streamlit Community Cloud with real, anonymized bank data, and the customer's interest is that no outside service reads it (BR-18). The demo may run with the network off (GO-1). The owner's brief asks for a guided chat with no language model.

## Decisions

1. **The chat is guided: twist buttons, then one size per step, with common values as buttons.** Free text is a second path (ADR 0004).
2. **No language model, no network call.** Every number comes from `get_profile`, `apply_shock` or `make_plan`, and every sentence from `ui/text.py` or the fixed `T.*` copy (RU-15, RU-16).
3. **Each reply shows the engine call that produced it** (`T.engine_call`), printed from the arguments actually passed.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| A hosted language model reads the card and writes the reply | Sends customer data out (BR-18); fails offline (GO-1); can word a number differently from the Shock and plan page (RU-1, RU-16); needs a secret on a public repo |
| A local model | Too large for Community Cloud; slow to start; still unpredictable wording |
| No chat; the sliders only | Misses BR-14, BR-15 and BR-17 |

## Consequences

- The chat can only read what the [grammar](../design/ux/chat_parser.md) covers. Anything else gets "I'm not sure" and the buttons.
- Wording is testable on every account, like the Shock and plan page.
- An import guard (`test_chat_imports.py`) keeps HTTP and model clients out of `app/` (AC-10).
- Revisit if the owner later wants open questions answered, which would need a new data-handling decision first.
