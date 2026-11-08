# ADR 0010: A stated assumption for a missing twist-card length

Status: proposed, 2026-11-07; decisions confirmed unchanged 2026-11-08 (brief Part 8: a bare "laid off" with no EI → ask, reading (a)). Sources: D2, D4, brief Part 7 Q3, Part 8, R5, R6, R7, PT-04, [ADR 0004](0004-deterministic-parser-with-mandatory-confirm.md), [design §5](../architecture/j5_plan_designer.md#5-copy-and-parser-fixes).

## Context

Twist 3 ("lose their job and bills go up 15% in the same month") gives no length. The owner decided to assume 6 months, as on card 1, and to say so on screen and in the chat (D2). ADR 0004 makes the parser refuse to guess, and it is accepted, so this needs its own record. The decision doesn't change 0004: the confirm is still mandatory.

## Decisions

1. **When the text has a job loss plus another twist kind, and no length, the parser fills months = 6** (`state.ASSUMED_MONTHS`). The answer has source `"assumed"`, and the status is `ok`. A job loss alone ("laid off") still asks for the length (PT-12 unchanged).
2. **The confirm reads "for 6 months (assumed)".** After the run, the result adds `text.ASSUMED_LENGTH`: "The card gives no length, so this assumes 6 months, as on the first card." On Shock and plan, the same line shows under "Selected: Laid off + bills up 15%".
3. **A one-off in months of spending is stated in dollars, on S before the shock** (D4), through `text.oneoff_line`, on both pages.
4. **`state.Source` gains `"assumed"`.** This is the one contract change to `state.py` (ADR 0003's rule), and the lead approves it at T0.

## Alternatives considered

| Option | Why not |
| :-- | :-- |
| Keep asking the length (PT-04 `partial`) | D2 says assume and say so |
| Assume 6 for every job loss without a length | Wider than D2; "laid off" alone is better asked |
| Assume silently | D2 requires saying so; the confirm must show what will run |

## Consequences

- PT-04's expected result changes. NEW-PARSER-6 covers a job loss with a repair.
- The transcript keeps the `"assumed"` source on the card answer, so the record shows it.
- NEW-SCOPE-4 is closed: the owner's "Job loss = laid off, or possibly EI = 0; nothing needs to change" keeps this record as written. PT-12 "laid off" asks the keep % and then the months; PT-19 "laid off, no EI, for 3 months" gives `IC(0, 3)`; PT-04 (card 3) is `IC(0.55, 6)` assumed.
- Revisit only if the owner wants a bare job loss to default to EI = 0 (reading (b) in brief Part 7 Q3, declined 2026-11-08).

## Changes

| Date | Change | Source |
| :-- | :-- | :-- |
| 2026-11-08 | No decision changes. Status line and Consequences record the owner's confirmation and close NEW-SCOPE-4 | Brief Part 7 Q3, Part 8 |
