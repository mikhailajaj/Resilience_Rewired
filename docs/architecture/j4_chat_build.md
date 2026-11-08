# Build plan: J4 Ask the assistant

Status: proposed, 2026-11-07. The design is [`j4_chat.md`](j4_chat.md); decisions are [ADR 0002 to 0005](../adr/README.md). This file is the increment's scope, the test map and the work packages for parallel sr-dev agents. Branch: `feature/guided-chat`.

## 1. Increment scope

The increment is the [chat MVP](../inception/scope.md#chat-assistant-j4-mvp-and-stretch), cut as four stories, one per use case. J4.1 is the architecturally significant one: it crosses every layer (page → flow → engine → `ui/text.py` → page) and proves the RU-19 key scheme and the AC-2 parity on its own. Build and demo it first.

| Story | Use case | Wireframe | Collaboration | Acceptance |
| :-- | :-- | :-- | :-- | :-- |
| S1 Buttons to a verdict | [J4.1](../inception/use_cases_chat.md#j41-ask-a-twist-with-buttons) | T1, T2, T3, T4, T6 | [§7.1](j4_chat.md#71-buttons--engine--reply-j41-ac-1) | AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, AC-10 |
| S2 Free text with confirm | [J4.2](../inception/use_cases_chat.md#j42-ask-in-free-text) | T5, T6 | [§7.2](j4_chat.md#72-free-text--parse--confirm--run-j42-ac-3) | AC-3, PT-01 to PT-25 |
| S3 Follow-ups and send | [J4.3](../inception/use_cases_chat.md#j43-follow-up-a-result) | T3, T4, T6 | [§7.3](j4_chat.md#73-send-to-the-controls-j43-1e-ac-9) | AC-8, AC-9 |
| S4 Transcript | [J4.4](../inception/use_cases_chat.md#j44-download-the-transcript) | T2 download | [§4.5](j4_chat.md#45-transcriptpy) | AC-8 (sections), RU-18 |

**Deferred** (the scope's stretch column): `st.write_stream` replies, an account ID typed in the chat, the EI weekly maximum and start month in the chat (OI-4, OI-7; a month name gives `T.unsure_month`), the full `to_dict` output in the transcript, stacking by free text, and the short-history note (OI-12).

**Construction rules for all packages:** match the existing style (module docstring, no comments that restate code, `from app.engine import ...`), keep every function pure except the page, and run the tests in the project `.venv` (Streamlit 1.67.0; the system `python3` has 1.64.0).

## 2. Test strategy

Tests are written first in each package, against the frozen contract. "Sweep" means all 4,500 accounts.

| File | Owner | What it proves | Maps to |
| :-- | :-- | :-- | :-- |
| `app/tests/test_chat_parse.py` | WP1 | One parametrized row per PT: status, `shock` (for ok), `missing` (partial), `unsure` code, `month_named`, `problem.field`. `read_number` cases (commas, `$1.5k`, `six`, `55%`, `abc` → None). `check_size` at each RU-22 edge (0, 100, 100.01; 1, 120, 121, 2.5). `shock_from` gives `keep_fraction == 55/100`. Every `app.ui.cheatsheet.TEMPLATES` example parses `ok` to its `Shock`. 200 odd strings (empty, emoji, 10 kB, only digits) never raise and never give `ok` out of range | PT-01 to PT-25, AC-3 (parser half), AC-4 (parser half) |
| `app/tests/test_chat_flow.py` | WP2 | Drives `flow.step` with events, no Streamlit. AC-1 path on 20111 (one output, `IncomeCut(0.55, 6)` in the call, verdict equals `text.verdict`). AC-3: after `TextSent` of each PT `ok` row, `outputs == ()` and phase is confirm; after `ConfirmPicked(True)`, one output. AC-4: `ValueTyped` "150" for keep, "0" and "121" for months → `T.out_of_range`, no output, no card answer. AC-7: an event with an old turn returns the same state object. AC-8: `CustomerSeen` archives the section, the greeting names the new ID. RU-21: stacking bills on job adds; bills on bills replaces with `T.stack_replace`. Change size reruns with one field changed. J4.1 6b: monkeypatch `app.assistant.flow.apply_shock` to raise `InvalidShockError("months", ...)` → `T.engine_refused`, back to months. J4.2 2f: a bare "6" while asking months is that size. Blank text is a no-op. The whole file runs with `socket.socket` patched to raise | AC-1, AC-3, AC-4, AC-7, AC-8, AC-10 (runtime), RU-17 to RU-21 |
| `app/tests/test_chat_replies.py` | WP2 | `call_text` forms (no shock, each field, open-ended, `after_ends`, `make_plan` with target). AC-5 on 32078 (B ≤ 0): the no-buffer sentence, no "one-off cost". AC-6: 20134 with no shock, greeting reads `120.0 months` via `summary_line` and no "No shortfall"; across a no-shortfall sweep sample, no line contains "runs out". `plain` per field. "(ours)" line only when standing orders apply, ending `(ours)`. **Sweep:** every account × every preset driven through `flow.step` as button events (the preset's fields as `ValuePicked`), asserting no exception and that the reply's verdict, second line, change line and fact lines equal `text.*` on `apply_shock(id, preset.shock, through_months=months)`, and the `EngineOutput` matches that result. Budget: about 1 to 2 minutes (22,500 `apply_shock` calls took 54 s here) | AC-1, AC-2, AC-5, AC-6, RU-16 |
| `app/tests/test_chat_transcript.py` | WP3 | Builds a `ChatState` by hand (no engine). Every message line appears verbatim; card answers and outputs are in their tables; archived customers come first under `## Customer {id}`; `file_name`. Then monkeypatch every engine function in `app.engine` to raise and build a real transcript from a flow-made state: it still builds (nothing recomputed, ADR 0005). Greeting-only state gives the greeting only (J4.4 1a) | AC-8 (transcript half), RU-18, J4.4 |
| `app/tests/test_chat_controls.py` | WP3 | `cant_send` for each RU-22 limit and for a fitting card. `to_inputs` keeps `target` and `ei_max`, sets `ei_on=False`, `start="Not set"`, `income == 55.0` exactly. `set(INPUT_KEYS)` equals the `DEFAULTS` keys read from `shock_and_plan.py` by `ast` | AC-9 (logic half) |
| `app/tests/test_chat_imports.py` | WP3 | AST walk of `app/**/*.py` for rules D1 to D6 in [design §2](j4_chat.md#2-design-model-software-system-architecture): no `streamlit` in `assistant/`, `engine/`, `ui/text.py`; no `requests`, `httpx`, `urllib`, `http.client`, `aiohttp`, `socket`, `anthropic`, `openai` anywhere in `app/`; the assistant's allow-list; no `app_pages` import from `assistant/` | AC-10 (static) |
| `app/tests/test_chat_ui.py` | WP4 | AppTest from `streamlit_app.py`, reusing `show()` and `page()` from `test_ui.py`. The Chat page is in navigation; T1 with no customer (`chat_input` disabled). AC-1 by clicks on 20111: page text contains `IncomeCut(0.55, 6)` and the verdict sentence. AC-2: the same card on Shock and plan (preset) shows the same verdict and `Monthly gap  $2,260 -> $5,113`. AC-7: after each click, every live `chat_` button key carries the latest turn. AC-8: change the picker to 20134; no "20111" in the messages; the transcript has both sections. AC-9: send a fitting card → Shock and plan opens, `n_income == 55`, verdict as in the chat; "until it runs out" → `T.send_cant`, page unchanged. Text path: type PT-02, see `T.confirm`, no engine line until Run it. Download button present with `chat_transcript_20111.md` | AC-1, AC-2, AC-6, AC-7, AC-8, AC-9, GO-10 |

AC-10's network-off half is GO-10 on the demo laptop. The static half is `test_chat_imports.py`, and `test_chat_flow.py` runs with sockets blocked.

## 3. Work packages

### Freeze first

`app/assistant/state.py` is the shared contract. **WP1 commits it first, verbatim from [design §3](j4_chat.md#3-the-frozen-contract-appassistantstatepy), with `RULES`, `KIND_FIELDS`, `FIELD_KIND`, `check_size` and `shock_from` implemented, plus `app/assistant/__init__.py`.** Target: within the first 30 minutes. After that commit it is frozen: a change needs the integration owner's (the software-engineer lead's) agreement and a message to every package. In the same first slot, WP3 commits `chat_text.py` with every `T.*` key (copy §10 verbatim plus NEW-COPY-1 to 8 as drafted), because WP2 and WP4 read its names.

Until a dependency lands, each package codes against a stub with the exact signature from [design §4](j4_chat.md#4-module-interfaces) that returns the simplest valid value.

| WP | Owns (only these files) | Codes against (stubs) | Tests first | Done when |
| :-- | :-- | :-- | :-- | :-- |
| WP1 Contract and parser | `app/assistant/__init__.py`, `state.py`, `parse.py`, `app/tests/test_chat_parse.py` | Engine only | PT-01 to PT-25 table, `read_number`, `check_size`, `shock_from`, cheatsheet examples, fuzz | All of `test_chat_parse.py` passes; no regex backtracks over 50 ms on a 10 kB string; `state.py` matches §3 exactly |
| WP2 Flow and replies | `flow.py`, `replies.py`, `app/ui/text.py` (only the `orders_row` extraction), `app/tests/test_chat_flow.py`, `test_chat_replies.py` | `state.py` (frozen), `parse.parse` (stub: `unsure` U1), `controls.cant_send` (stub: `None`), `chat_text.T` | The flow invariants of design §4.2, the transition table, AC-5 and AC-6, then the sweep | Both files pass, the sweep included; `test_ui.py` and `test_sweep.py` still pass unchanged after the `text.py` extraction; no Streamlit import |
| WP3 Copy, transcript, controls, import guard | `chat_text.py`, `transcript.py`, `controls.py`, `app/tests/test_chat_transcript.py`, `test_chat_controls.py`, `test_chat_imports.py` | `state.py` (frozen) | Hand-built transcript state; RU-22 limits; AST key check; import rules | The three files pass; every `T.*` key in copy §10 exists in `T` with identical text (a test reads the copy table) |
| WP4 Page and integration | `app/app_pages/assistant.py` (may show `cheatsheet.markdown()` in an expander), `app/streamlit_app.py` (one `st.Page` line: `"app_pages/assistant.py"`, title `T.page`, icon `:material/chat:`), `app/tests/test_chat_ui.py`, `app/README.md` (one line for the page) | `flow.initial/step/live` (stub: greeting with the twist buttons), `transcript.to_markdown` (stub: `""`), `controls.to_inputs` (stub: `dict(current)`), `chat_text.T` | AppTest: page in navigation, T1, AC-7 key scheme, then AC-1, AC-2, AC-8, AC-9 as the real modules land | `test_chat_ui.py` passes with the real modules; the full suite passes (`pytest app/tests`, GO-2); a manual run of [design §5](j4_chat.md#5-streamlit-mechanics-the-page) on 20111, 20134 and 32078 with the network off (GO-10) |

**Files no package owns.** `app/app_pages/shock_and_plan.py` (now with the cheatsheet expander in region C, added by the main session on 2026-11-07), `app/ui/cheatsheet.py` and `app/tests/test_cheatsheet.py` stay with the main session; `app/engine/` stays unchanged. No package edits them. WP4 reads `shock_and_plan.py`'s `ss.inp` contract only, and WP3's AST test reads its `DEFAULTS`. If the parser and a cheatsheet example disagree, WP1 reports it to the main session rather than editing the cheatsheet, since both come from [`chat_parser.md`](../design/ux/chat_parser.md).

Order: WP1 contract → WP1 to WP4 in parallel → WP4 integrates last. WP2 is the critical path (largest, and the sweep is its gate).

## 4. Plan hand-off for `pm-planner`

Points use the planner's scale; hours are estimates. Actuals are blank until the work is done.

| Item | Points | Dev tasks | Estimate (h) | Actual (h) | Risk notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| WP1 Contract and parser | 3 | freeze `state.py`; grammar; U1 to U6; tests | 3.0 | | Grammar edge cases (PT-04, PT-23); keep the regexes simple |
| WP2 Flow and replies | 5 | handlers per event; run; follow-ups; replies; `orders_row`; sweep | 4.5 | | Critical path; sweep time |
| WP3 Copy, transcript, controls, guard | 2 | `T`; transcript; controls; AST tests | 2.0 | | NEW-COPY items may change wording, not structure |
| WP4 Page and integration | 3 | page; nav; send; AppTest | 3.0 | | AppTest flakiness on reruns; `switch_page` path coupling |
| Rehearsal on the Chat page (GO-10) | 1 | AC-1 to AC-10 by hand, network off | 0.5 | | Needs the demo laptop |

Split: the chat MVP (scope RSK-1) becomes S1 to S4 above. If time runs short, ship S1 and S4 first; S2 and S3 follow, and the sliders stay the main path (RSK-1).

## 5. Risks and open items

| ID | Risk | Response |
| :-- | :-- | :-- |
| R-J4-1 | Not finished before judging (scope RSK-1) | S1 first; each story is usable alone; the Shock and plan page is unchanged |
| R-J4-2 | Parser reads a card wrongly | Mandatory confirm (ADR 0004); `unsure` wins over every other status; the twist buttons are always one click away |
| R-J4-3 | Chat and Shock and plan numbers drift apart | One wording source (`ui/text.py`), the same call inputs, keep stored as a percent, the sweep and AC-2 |
| R-J4-4 | `ss.inp` keys change on the Shock and plan page | `test_chat_controls.py` compares keys by AST; the chat writes no widget keys |
| R-J4-5 | A stale click runs the wrong step | Per-turn keys plus the turn check in `step` (AC-7) |
| R-J4-6 | Focus doesn't return to the text box after a click (wireframe T note) | Streamlit has no focus API; accepted; the presenter clicks the box |
| R-J4-7 | Tests run on the wrong Streamlit | Run in `.venv` (1.67.0); system `python3` has 1.64.0 |
| R-J4-8 | Cloud deploy settings (branch, Python version) unknown | **verify** in the Community Cloud settings before GO-9 |

Open items carried from [scope](../inception/scope.md#open-items-for-the-owner), cited not copied:

- **OI-5** (fund target default): the chat uses the controls' `target` if set, else 3 (`Context.target_months`). No chat change if the owner picks 6; only `DEFAULT_TARGET` follows `make_plan`.
- **OI-11** (`K.g_zero` wording): the chat shows `text.backup_lines` as is, so any change lands in both pages at once.
- **OI-12** (short-history note): none; the greeting shows the data range and month count (`T.range`).
- **OI-13** (repo visibility): **settled 2026-11-07**, the owner confirmed the public repo with all CSVs. Nothing open for the chat.
- **OI-9** (owners): the collaboration owners in [design §7](j4_chat.md#7-interaction-model) are work packages, not people, until the team is named.
- Copy and wireframe gaps NEW-COPY-1 to 8 and NEW-WF-1 are in [design §9](j4_chat.md#9-gaps-and-questions-sent-back) for the UX author.

## 6. Exit review

Elaboration for J4 is done when: `state.py` is committed and frozen; S1 runs end to end on 20111 in the hosted and local app with AC-1, AC-2 and AC-7 passing; `test_chat_imports.py` passes; ADR 0002 to 0005 are accepted or revised by the owner; NEW-COPY items are numbered or answered.
