# Engineering note: J4 Ask the assistant

Status: 2026-11-07, software-engineer lead. Design: [`j4_chat.md`](j4_chat.md). Build plan: [`j4_chat_build.md`](j4_chat_build.md). This note adds only how the build is split and run; it decides no behaviour.

## Diagrams

The design already carries every required diagram, and this build follows them unchanged:

- part of the system: [design §2 flowchart](j4_chat.md#2-design-model-software-system-architecture) (UI / application / chat domain / shared wording / engine);
- component diagram: [design §2 classDiagram](j4_chat.md#2-design-model-software-system-architecture) (`flow`, `parse`, `replies`, `controls`, `transcript`);
- interaction model: [design §7](j4_chat.md#7-interaction-model), collaborations "J4.1 Ask a twist with buttons", "J4.2 Ask in free text", "J4.3 Follow up a result", "J4.4 Download the transcript", with sequences 7.1 to 7.4.

## Code map

| Path | One responsibility | Layer |
| :-- | :-- | :-- |
| `app/assistant/state.py` | Frozen contract: records, events, `RULES`, `check_size`, `shock_from` | chat domain |
| `app/assistant/chat_text.py` | `T.*` copy, copy §10 verbatim plus drafted NEW-COPY strings | chat domain |
| `app/assistant/parse.py` | Text to `ParseResult` | chat domain |
| `app/assistant/replies.py` | Engine results to lines and `EngineOutput` | chat domain |
| `app/assistant/flow.py` | `step(state, event, ctx)` state machine | application |
| `app/assistant/controls.py` | `cant_send`, `to_inputs` for `ss.inp` | application |
| `app/assistant/transcript.py` | Markdown from `ChatState` only | application |
| `app/app_pages/assistant.py` | Draw state, widgets to events, hand-off | UI |

Dependency direction: page → `app.assistant` → `app.engine` and `app.ui.text`; nothing in `app/assistant/` imports Streamlit or the network (rules D1 to D6, checked by `test_chat_imports.py`).

## Decisions taken here (structure only)

- **`T0` scaffold by the lead:** `__init__.py`, `state.py` (fully implemented, it is the contract), `chat_text.py` (all keys, so WP2 and WP4 code against names), and signature-exact stubs of `parse`, `flow`, `replies`, `controls`, `transcript`.
- **`state.py` adds `SIZE_WORDS`, `RANGE_WORDS`, `ZERO_OR_MORE`:** `check_size` must fill `RangeProblem.size` and `.range` (NEW-COPY-4) and `state` may not import `chat_text` (design graph: `state → engine` only). Additive; no §3 name changed.
- **`shock_from` turns an integer-valued float month (6.0) into `int`**, since the engine's `_whole` refuses floats; 2.5 passes through and the engine refuses it.
- **D5 allow-list adds `app/streamlit_app.py` importing `app.assistant.chat_text`** so the nav title is `T.page` (build plan WP4) without a second copy of the word.
- Patterns: functional core / imperative shell (ADR 0003; force: the 4,500-account sweep must run without Streamlit). No other pattern.

## Test strategy

As [build §2](j4_chat_build.md#2-test-strategy). Determinism: the engine is in memory and deterministic; `test_chat_flow.py` blocks `socket.socket`. Fixtures: accounts 20111 (AC-1, AC-2), 32078 (B ≤ 0, AC-5), 20134 (cap, AC-6).

## Conventions

Money via `text.money` (`app/ui/text.py`); keep stored as a percent and divided once (design §3); errors are `InvalidShockError.field`; `$` unescaped in stored lines, escaped by the page with `shared.md`.

## Tasks

| Task | Owns | Depends on | Status |
| :-- | :-- | :-- | :-- |
| J4.WP-1.T0 Scaffold | `app/assistant/__init__.py`, `state.py`, `chat_text.py`, stubs | none | done (lead) |
| J4.WP-1.T1 Parser | `parse.py`, `app/tests/test_chat_parse.py` | T0 | passed review, round 1 |
| J4.WP-2.T1 Flow and replies | `flow.py`, `replies.py`, `app/ui/text.py` (`orders_row` only), `test_chat_flow.py`, `test_chat_replies.py` | T0 | passed review, round 1 |
| J4.WP-3.T1 Transcript, controls, guard | `transcript.py`, `controls.py`, `test_chat_transcript.py`, `test_chat_controls.py`, `test_chat_imports.py`, `test_chat_text.py` | T0 | passed after lead fixes at integration (below) |
| J4.WP-4.T1 Page | `app/app_pages/assistant.py`, `app/streamlit_app.py` (one `st.Page`), `test_chat_ui.py`, `app/README.md` | T0; real modules at integration | passed after one lead fix (below) |

All four run in the shared working tree with disjoint files (no worktrees: the branch is uncommitted, so a worktree would not see T0).

## Gaps found while splitting (for the architect / copy owner)

- AC-6 says the 20134 greeting reads `120.0 months` "via `summary_line`", but `summary_line` gives "lasts 120 months or more" for that account. The build tests the words `summary_line` returns and that "No shortfall" never appears; no new line is invented.
- NEW-COPY-9: singular forms "for 1 month", "a one-off cost of 1 month of spending" (drafted in `chat_text.py`).
- NEW-COPY-10: `T.stack_replace {kind}` words and the PickSize button label `"{size}: {shown}"` (drafted).

## Review and integration fixes (lead, 2026-11-07)

- `controls.cant_send` returned the whole `T.send_cant` sentence; design §4.4 says only `{what}`, and `flow` formats it. Fixed in `controls.py` and `test_chat_controls.py`; `test_chat_ui.py` now asserts the full sentence.
- `test_chat_transcript.py` used fake account 5, which only the stub flow accepted; it now drives the real AC-1 path on 20111 with the engine patched to raise.
- D2 in `test_chat_imports.py` allows `socket` in `app/tests/` only (the flow test imports it to block it), with a planted `requests` case in tests still flagged.
- Page buttons: `st.columns` + deprecated `use_container_width` replaced by `st.container(horizontal=True)` so they wrap (wireframe T).
- Parser reads "N years" as N x 12 months, beyond the grammar (kept; harmless, reported).
