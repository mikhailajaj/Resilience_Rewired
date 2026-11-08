# ADR 0005: Transcript built from stored records only

Status: accepted, 2026-11-07. Sources: BR-17, RU-18, RU-20, J4.4, [design §4.5](../architecture/j4_chat.md#45-transcriptpy).

## Context

The team wants a record of each twist (BR-17). If the download recalculated results, a later code or data change could make the file disagree with what the judges saw. The chat already stores each card answer and engine run (RU-18).

## Decisions

1. **`app/assistant/transcript.py` builds Markdown only from `ChatState`**: the messages as shown, the card answers and the engine outputs. It imports no engine function.
2. **An `EngineOutput` is copied from the result when the engine runs**: function, call text, shock, `through_months`, `target_months`, verdict case, runway labels, gaps, fact codes and plan states.
3. **One section per customer**, earlier customers first, from `ChatState.archive` (RU-20). File name `chat_transcript_{id}.md`; the download doesn't rerun the page (`on_click="ignore"`).

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Recalculate from the card answers at download | Can disagree with what was shown; slower |
| Store the full `ShockResult` and `Plan` with `to_dict` | Larger session state; kept as a stretch item in scope |
| No transcript; the presenter takes screenshots | Misses BR-17 |

## Consequences

- `test_chat_transcript.py` builds a transcript with every engine function patched to raise, which proves nothing is recalculated.
- Adding a field to the transcript means adding it to `EngineOutput` first (a contract change, ADR 0003).
- The transcript is lost when the tab closes unless downloaded; `T.download_help` says so.
