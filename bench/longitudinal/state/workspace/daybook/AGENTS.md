# daybook/ — AGENTS.md

This folder holds **one file per workday**, named `YYYY-MM-DD.md`. Each file is a single-stream daybook with three sections: **Intent**, **Log**, **Handoff**. Open in the morning (or whenever you start), add to throughout the day, close with the handoff before committing.

**Without the daybook:** each new session starts cold. The agent can't pick up where you left off because there's no record of what "off" was. Yesterday's half-finished thought is gone unless you remember it. The handoff section in particular is the cold-pickup artifact — without it, every Monday becomes a partial reconstruction of last Friday.

See `0000-00-00-example.md` for a seeded example.

## Naming

`YYYY-MM-DD.md` — ISO date. One file per workday. If you work across midnight, keep the original date until you sleep.

## The three sections

```markdown
# YYYY-MM-DD

## Intent
(written when the day's purpose becomes clear — sometimes 9am, sometimes after the first hour of triage. One paragraph or a few bullets. What does today need to produce?)

## Log
(incremental, bidirectional — drop in and out throughout the day. Interim notes, partial findings, anything worth a second look. Timestamps optional but useful if the day is busy.)

## Handoff
(written before end-of-day commit. What got done. What's in progress. Blockers. The very first thing the next session should do.)

### Guardrails for next session
(optional sub-section — list any `do NOT` instructions, holds, or boundary conditions the next session needs to honor before acting. These are not the same as in-progress notes: they are constraints on action. If yesterday said "do NOT email the vendor until legal review is complete," that lives here. The next session should read this sub-section before acting on requests that might violate the constraint.)

**Generated-by:** inference | user | mixed
```

The `Generated-by` marker captures who produced today's entry: the agent (inference), the user, or both. Keep it on the last line, after Handoff, so a skim of the file always finds it. If the user typed the whole entry, mark `user`; if the agent drafted from a session and the user reviewed without rewriting, mark `mixed`; if the agent wrote it end-to-end without explicit user review, mark `inference`. The methodology calls this out specifically — see `methodology.md#provenance-markers`.

## Why a single file, not two

Earlier versions of this workspace had separate `sessions/` (AM) and `handoffs/` (PM) folders. Real-world practice — bullet-journal daily logs, captain's logs, executive daybooks, on-call shift notes — converges on **one chronological page per day**. Splitting forces a context switch and a "does this go in session or handoff?" decision that doesn't survive a busy week. One file, three sections, zero ambiguity.

## When to write the Intent section

Not necessarily at 9am. Sometimes the day's intent only crystallizes after triaging the inbox or sitting in the first meeting. Write Intent when you can state it in a sentence. If the day is purely reactive and never has a clear intent, leave the section as `(reactive day — no specific intent)` and move on.

## When to write the Handoff section

At the **end** of every working session, before committing. If you (the agent) are working at end-of-day, proactively offer to draft the handoff section. Don't wait to be asked.

The Handoff section is the canonical home for **boundary instructions** that must survive into the next session: `do NOT` rules, holds awaiting external input, anything that constrains tomorrow's first action. Put them in the `Guardrails for next session` sub-section. Cold-pickup sessions are expected to read the Handoff (including this sub-section) before acting on user requests that could collide with the constraint. This is how the workspace prevents a fresh session from cheerfully violating yesterday's promise to legal.

## When to skip the file entirely

If you didn't work in the workspace that day, don't create an empty file. A missing date in `daybook/` is fine — it just means "no work that day." The previous file is still the last known state.

## If you need to resume cold

If you (or the agent) come back unsure where things left off — that's when to read the previous daybook. Not as a morning ritual; on-demand, when something feels unfamiliar.

```bash
ls -1 daybook/ | grep -v AGENTS | tail -1
```

That's the most recent daybook. Read the Handoff section first — that's where the last session ended. Read Log and Intent only if you need fuller context.

## Why dated files instead of one rolling log?

- Each day's state is a discrete artifact you can diff, blame, and grep.
- "Where did we leave off on Monday?" → open Monday's file.
- The most recent file is always the right starting point.
- Old daybooks are append-only history; they don't need pruning. The monthly roll-up (see `methodology.md#review-cadence`) summarizes them into `decisions.md` if a milestone happened.
