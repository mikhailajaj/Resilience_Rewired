# Use cases: J4 Ask the assistant

These are the fully dressed user-goal use cases under the [J4 summary](use_cases.md#j4-ask-the-assistant). States are from the [chat state machine](../design/ux/flows.md#4-chat-state-machine-j4), screens `T1` to `T6` are from the [chat wireframes](../design/ux/wireframes.md#t-chat-page-j4), `T.*` keys are from the [chat copy](../design/ux/copy.md#10-chat-t), and parse results are from the [parser grammar](../design/ux/chat_parser.md). Author: the inception agent. The area owner is TBD ([OI-9](scope.md#open-items-for-the-owner)).

## J4.1 Ask a twist with buttons

| Field | Value |
| :-- | :-- |
| ID, type | J4.1, user goal |
| Traces to | BR-2, BR-5, BR-14, BR-15, BR-16 |
| Rules | RU-1, RU-2, RU-6, RU-7, RU-8, RU-9, RU-15, RU-16, RU-18, RU-19, RU-20, RU-22 |
| Actors | Presenter (primary), judge (supporting) |
| Preconditions | A valid customer is in `ss.shown_id` (J1 1, 2), and the chat is in `Greeting` |
| Trigger | A judge reads a twist card |

**Main flow**

1. The presenter clicks a twist: `T.b_job`, `T.b_bills`, `T.b_repair` or `T.b_mix` (T2). The tool stores the kind as a card answer.
2. The tool asks for the first size the kind needs, with buttons for common values and an "Other" box (T3).
3. The presenter clicks a value or types one. The tool stores it as a card answer with its unit and source.
4. Steps 2 and 3 repeat for each size: job loss asks keep then months, bills asks percent or dollars, repair asks the amount, and mix asks keep, months and bills.
5. The tool builds the `Shock` from the card answers and shows the `T.engine_call` line (T4).
6. The tool calls `apply_shock(id, shock, through_months=months)` and stores an engine output.
7. The tool shows the result with the `ui/text.py` wording: `verdict`, its second line, `T.change_line`, `fact_lines` and `assumption_line` (T4).
8. The tool offers the follow-ups (J4.3). The earlier buttons now show the choice as text.

**Postcondition:** the judges' runway for the card's shock is shown with the engine call that produced it, and every size used is a stored card answer.

**Extensions**

| Step | Condition | Behaviour | Screen |
| :-- | :-- | :-- | :-- |
| 1a | `T.b_type` | Go to J4.2 | T2 |
| 1b | No customer loaded, or the ID is invalid | No twist buttons; `T.no_customer`; the picker shows `K.err_not_digits` or `K.err_not_found` | T1 |
| 3a | Typed value outside the engine's range (RU-22), such as 150% or 0 months | `T.out_of_range`; the same step asks again; no engine call | T6 |
| 3b | Typed value isn't a number | `T.not_number`; ask again | T6 |
| 3c | Months: "Until it runs out" | `months=None`; no `through_months`; the verdict is `income_cut_open_ended` | T4 |
| 3d | Months over 120 | As 3a. 120 is the engine's limit (`MAX_MONTHS`) | T6 |
| 6a | The customer changes in the picker before the run | RU-20: the conversation restarts at `Greeting` for the new customer | T2 |
| 6b | The engine raises `InvalidShockError` anyway | `T.engine_refused` names its `field`; back to that size step; nothing is guessed | T6 |
| 7a | `no_shortfall` | `K.verdict` no-shortfall sentence. Never "runs out in month N" (CON-7) | T4 |
| 7b | `runway_zero` with `no_buffer_before_shock` (23 accounts) | The no-buffer sentence; the cost isn't blamed (CON-5); `T.f_backup` listed first | T4 |
| 7c | `runway_zero` from the one-off cost | The cost-bigger-than-buffer sentence | T4 |
| 7d | `income_cut_runs_out` with `runs_out_in_month` 0 | The "gone before month 1" sentence | T4 |
| 7e | Runway at the cap | Reads `120.0 months` as the engine gives it, not "No shortfall" (CON-8) | T4 |
| 7f | Fact codes such as `layoff_doesnt_fit_pension` (740), `data_stops_early` (76), `little_activity` (10), `bills_shock_no_bills`, `bills_shock_too_small`, `one_off_zero_spending` | One `fact_lines` line each, under the verdict | T4 |
| 7g | `duration.assumption_applied` | `assumption_line` | T4 |
| 7h | An "our numbers" figure applies, such as standing-order bills | One line from `our_rows`, ending `T.ours` (RU-2) | T4 |

## J4.2 Ask in free text

| Field | Value |
| :-- | :-- |
| ID, type | J4.2, user goal |
| Traces to | BR-14, BR-16, BR-18 |
| Rules | RU-15, RU-16, RU-17, RU-18, RU-19, RU-22 |
| Actors | Presenter (primary), judge (supporting) |
| Preconditions | As J4.1 |
| Trigger | The presenter types the card into `st.chat_input` |

**Main flow**

1. The presenter types the card, such as "laid off, EI 55% for 6 months and bills up 15%".
2. The parser returns a parse result of `ok`. The tool stores it.
3. The tool shows `T.confirm` with the shock in plain words, and the buttons `T.b_run` and `T.b_buttons` (T5).
4. The presenter clicks `T.b_run`. The parsed sizes are stored as card answers with source `parsed`.
5. The flow continues at J4.1 step 5.

**Extensions**

| Step | Condition | Behaviour | Screen |
| :-- | :-- | :-- | :-- |
| 2a | `partial`: the kind is clear but a size is missing | `T.partial`; J4.1 step 2 for the missing size only | T3 |
| 2b | `out_of_range` | `T.out_of_range` with the engine's range; the twist buttons are offered | T6 |
| 2c | `unsure` | `T.unsure`; the twist buttons are offered (J4.1 step 1); nothing is run | T6 |
| 2d | The text names a start month | `unsure`, with `T.unsure_month` (OI-7) | T6 |
| 2e | Blank text | Ignored | No screen |
| 2f | Text typed while a size is asked | A bare number is that size (J4.1 step 3); other text is parsed afresh | T3 |
| 4a | `T.b_buttons` | J4.1 step 1; nothing is run | T2 |
| 4b | New text typed instead of a click | Parsed afresh; the old confirm goes inert (RU-19) | T5 |
| 5a | Result cases | As J4.1 7a to 7h | T4 |

## J4.3 Follow up a result

| Field | Value |
| :-- | :-- |
| ID, type | J4.3, user goal |
| Traces to | BR-2, BR-3, BR-12, BR-15, BR-16 |
| Rules | RU-11, RU-12, RU-13, RU-15, RU-16, RU-18, RU-19, RU-20, RU-21, RU-22 |
| Actors | Presenter (primary), judge (supporting) |
| Preconditions | A result is shown (state `Result`) |
| Trigger | A judge asks "what can they do?" or changes the card |

**Main flow (backup plan)**

1. The presenter clicks `T.f_backup`.
2. The tool calls `make_plan(id, shock, target_months=t, through_months=months)`, always passing a `Shock`, never `None` (J3 4a). It stores an engine output.
3. The tool shows `backup_lines` and the ordered steps (T4).
4. The tool offers the follow-ups again, with `T.f_goal` first.

**Alternate flows**

| Step | Condition | Behaviour | Screen |
| :-- | :-- | :-- | :-- |
| 1a | `T.f_goal` | `goal_lines` from the same plan, on no-shock numbers (RU-11). `t` is the controls' target, else 3. **Default gated on OI-5**; fallback: the presenter says the target aloud | T4 |
| 1b | `T.f_stack` | J4.1 step 1, keeping the current shock. A different kind adds; the same kind replaces with `T.stack_replace` (RU-21) | T3 |
| 1c | `T.f_size` | One button per size in the current shock; the chosen one goes to J4.1 step 2; then a new run | T3 |
| 1d | `T.f_new` | `T.new`; the presenter types the ID in the picker (A); RU-20 | T1 |
| 1e | `T.f_send` | The sizes go into the Shock and plan inputs, `T.send_ok`, and that page opens | T4 |
| 3a | `no_buffer` | `K.g_zero`. **Wording gated on OI-11**; fallback: as drafted | T4 |
| 3b | `no_cuts_needed`, `cuts_not_enough`, or no length to last | `K.g_ok`, `K.g_floor`, or the `backup_lines` gap-closing sentence | T4 |
| 3c | Running loan | The `ask_lender` step, marked as needing agreement | T4 |
| 1a1 | Goal states `already_there`, `no_surplus`, `no_regular_spending`, B ≤ 0 | `K.f_done`, `K.f_nosurplus`, `K.f_none`, `K.f_negative` | T4 |
| 1a2 | Running loan | `K.f_low`, the one-payment line (BR-12) | T4 |
| 1e1 | A size the controls can't hold (RU-22), such as "until it runs out" or income returning | `T.send_cant` names it; nothing is sent | T6 |
| 1d1 | The new ID is invalid | The picker's message; the chat stays at `NoCustomer` | T1 |

## J4.4 Download the transcript

| Field | Value |
| :-- | :-- |
| ID, type | J4.4, user goal |
| Traces to | BR-17, BR-18 |
| Rules | RU-15, RU-18, RU-20 |
| Actors | Presenter (primary) |
| Preconditions | The chat has at least the greeting |
| Trigger | The presenter clicks `T.download` |

**Main flow**

1. The tool builds Markdown from the stored messages, card answers and engine outputs, one section per customer, as the [questionnaire download](../../app/ui/questionnaire.py) does.
2. The browser saves `chat_transcript_{id}.md`. The click doesn't rerun the page (`on_click="ignore"`).

**Postcondition:** the file has every sentence as it was shown, with each run's engine call and outputs. Nothing is recalculated.

**Extensions**

| Step | Condition | Behaviour | Screen |
| :-- | :-- | :-- | :-- |
| 1a | No engine run yet | The file has the greeting only | T2 |
| 1b | The customer changed earlier | Earlier customers are in labelled sections (RU-20) | No screen |
| 1c | The page was closed | The chat is gone; `T.download_help` says so beforehand | T2 |
