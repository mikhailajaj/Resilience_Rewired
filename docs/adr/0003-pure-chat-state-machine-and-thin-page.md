# ADR 0003: Pure chat state machine behind a thin Streamlit page

Status: accepted, 2026-11-07. Sources: RU-18, RU-19, RU-20, AC-2, AC-7, AC-8, [flows §4](../design/ux/flows.md#4-chat-state-machine-j4), [design §2 and §5](../architecture/j4_chat.md).

## Context

Streamlit reruns the whole script on every click, and widgets that aren't drawn lose their state. The chat has eight states, must keep only the latest buttons live (RU-19), must reset on a new customer (RU-20), and must give the same numbers as the Shock and plan page on all 4,500 accounts (AC-2). Code that mutates session state inside callbacks is hard to test outside AppTest and slow to sweep.

## Decisions

1. **`app/assistant/flow.py` holds the state machine as `step(state, event, ctx) -> state`.** States and events are frozen dataclasses in `app/assistant/state.py`. `step` never mutates its input; its only outside call is the in-memory engine.
2. **`app/assistant/` imports no Streamlit.** Only `app/app_pages/assistant.py` does. It reads `ss.chat`, sends one event per widget callback, and draws `state.messages`.
3. **Every event carries the turn it was drawn on.** Widget keys are `chat_{turn}_{slug}`; `step` ignores an event from an older turn.
4. **A changed `ss.shown_id` becomes a `CustomerSeen` event**, which archives the old customer for the transcript.
5. **`ui/text.py` stays the only source of result sentences.** One behaviour-neutral extraction (`orders_row`) lets the chat reuse the "(ours)" wording without a second engine call.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Callbacks that edit `st.session_state` keys directly | State spread over many keys; only testable through AppTest; no cheap sweep |
| A state-machine library (`transitions` and similar) | A new dependency for eight states; still needs our own records |
| Put chat logic in the page and test with AppTest only | AppTest per account is far too slow for 4,500 accounts |

## Consequences

- `test_chat_flow.py` and the sweep run without Streamlit, and AppTest covers only the page wiring.
- The shared contract (`state.py`) must be frozen before parallel work starts; changing it touches every package.
- Session state holds one value, `chat`. It lives only as long as the browser session (`T.download_help`).
