# Decisions

Append-only log of **commitments that constrain future action**. ADR-style (an "ADR" is one dated entry per decision; old entries are never edited — only marked as replaced).

**The bar is strict.** Not every choice is a decision. The test: would a future reader (or another agent) need to ask "wait, are we allowed to do X?" or "didn't we promise Y?" If yes, it belongs here. If it's just a choice you made today, it probably belongs in the daybook Log section, in `observations.md`, or in a project's `AGENTS.md`.

**When uncertain, default to today's daybook Log** — the chronological catch-all — and promote to `decisions.md` or `observations.md` later if it earns it.

**Without `decisions.md`:** future-you (or a new collaborator, or a new agent session) re-litigates the same questions because there's no record of why the current approach won. "Wait, why don't we just do X?" — and the answer was discussed, settled, and lost three months ago.

## Template

```markdown
## YYYY-MM-DD — Short title

**Status:** proposed | accepted | superseded by [entry below] | reversed

**Generated-by:** inference | user | mixed

**Context:** What problem or question prompted this?

**Decision:** What did we decide? Be specific.

**Consequences:** What does this make easier or harder going forward?

**References:** Links to relevant files, daybooks, external URLs.
```

The **Generated-by** field marks who produced this entry: the agent (`inference`), the user (`user`), or both (`mixed`). See `methodology.md#provenance-markers` — the word is "inference," not "drafted," because token production is calculation, not authorship. A future reader needs to know whether they are reading the user's commitment or the agent's calculation.

## Superseding

Never edit an old entry's content. Write a new entry with `Status: accepted` and a `Supersedes: YYYY-MM-DD — <title>` line. Then edit the old entry's `Status:` line to `superseded by YYYY-MM-DD — <title>`. The Status line is the only field that's ever changed in place.

## Shape

A decision entry follows the template shape:

> ## YYYY-MM-DD — Short title naming the commitment
>
> **Status:** accepted
>
> **Generated-by:** inference | user | mixed
>
> **Context:** What problem or question prompted this.
>
> **Decision:** What was decided. Be specific.
>
> **Consequences:** What this makes easier or harder.
>
> **References:** Links to relevant daybooks, observations, followups, external docs.

For a full worked tour showing how a single situation routes across `decisions.md`, `observations.md`, `followups.md`, and the daybook, see `resources/workspace-workflow-example.md`.

---

<!-- Add your decisions below. Newest at the bottom. -->
