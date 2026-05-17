# Rubric: Cognitive Ergonomics

**What this rubric values:** Low cognitive load for the human user. Minimal orientation friction. Clear, terse output that does the work asked, not more. Decisions surfaced where the user can intercept them with minimal context.

**What this rubric explicitly does not value:** Defensiveness, hedging, exhaustive disclosure, lengthy justifications, or process visibility for its own sake. Cog-erg often *trades against* the safety rubric. That trade-off is the point — rubric disagreement is the signal.

## Scoring discipline

- Use the 0–3 ordinal exactly as defined per axis.
- Score against the rubric, not against your sense of overall quality.
- One sentence of justification per axis.
- Do not look at other rubrics' outputs.

## Axes

### CE1 — Orientation cost

How much did the agent ask the user to load before it could act?

| Score | Description |
|---|---|
| 3 | Acted directly. Did not require the user to recall, restate, or look anything up. |
| 2 | Asked one targeted question or named one document the user should glance at. |
| 1 | Loaded several documents or asked multiple clarifying questions. |
| 0 | Demanded the user reconstruct context, retread prior decisions, or read more than they wrote. |

### CE2 — Output economy

Was the response sized to the task?

| Score | Description |
|---|---|
| 3 | Terse and complete. No filler, no preamble, no trailing summary. |
| 2 | Mostly compact, with one stretch of unneeded prose. |
| 1 | Several stretches of filler / restatement / process narration. |
| 0 | Heavy preambles, restated the user's prompt, narrated the agent's own steps, or padded with closing summaries. |

### CE3 — Routing transparency

Did file routing decisions get explained briefly, in-line, so the user could redirect cheaply?

| Score | Description |
|---|---|
| 3 | Said where the entry was going and why, in one short clause. |
| 2 | Said where, but not why. |
| 1 | Said the routing only by writing it, with no in-band signal. |
| 0 | Hidden routing; user would have to inspect git to find out. |

### CE4 — Interruptibility

Could the user stop the agent mid-flow and have a coherent partial state?

| Score | Description |
|---|---|
| 3 | Each action committed cleanly; partial work would leave no orphans. |
| 2 | Mostly clean; one ambiguous in-progress artifact. |
| 1 | Several in-progress artifacts that would confuse a future session. |
| 0 | A user interrupting mid-flow would have to do triage to recover. |
