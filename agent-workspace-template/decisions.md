# Decisions

Append-only log of **commitments that constrain future action**. ADR-style (an "ADR" is one dated entry per decision; old entries are never edited — only marked as replaced).

**The bar is strict.** Not every choice is a decision. The test: would a future reader (or another agent) need to ask "wait, are we allowed to do X?" or "didn't we promise Y?" If yes, it belongs here. If it's just a choice you made today, it probably belongs in the daybook Log section, in `observations.md`, or in a project's `AGENTS.md`.

**When uncertain, default to today's daybook Log** — the chronological catch-all — and promote to `decisions.md` or `observations.md` later if it earns it.

**Not a decision yet:** A user saying "we're going to use Postgres" without alignment, constraints, or consequences is not a decision — it's an announcement. That belongs in today's daybook Log, or — if it represents a recurring pattern worth preserving — in `observations.md`. A decision exists when something is *constrained*: an alternative ruled out, a commitment that binds future work, an option closed off. If the entry's Consequences section would be empty or hypothetical, the entry is not yet a decision.

**Without `decisions.md`:** future-you (or a new collaborator, or a new agent session) re-litigates the same questions because there's no record of why the current approach won. "Wait, why don't we just do X?" — and the answer was discussed, settled, and lost three months ago.

## Template

```markdown
## YYYY-MM-DD — Short title

**Status:** proposed | accepted | superseded by [entry below] | reversed

**Context:** What problem or question prompted this?

**Decision:** What did we decide? Be specific.

**Consequences:** What does this make easier or harder going forward?

**References:** Links to relevant files, daybooks, external URLs.
```

## Superseding

Never edit an old entry's content. Write a new entry with `Status: accepted` and a `Supersedes: YYYY-MM-DD — <title>` line. Then edit the old entry's `Status:` line to `superseded by YYYY-MM-DD — <title>`. The Status line is the only field that's ever changed in place.

## Shape

A decision entry follows the template shape:

> ## 2026-05-15 — Switch to brick for new construction
>
> **Status:** accepted
>
> **Context:** Three structural failures this year, most recently the May site (pending insurance review). The pattern is documented in `observations.md#2026-05-15-wolf-related-project-delays-follow-a-pattern`. Straw and stick builds cannot be brought up to the required wind-load spec without effectively rebuilding them.
>
> **Decision:** All new construction starting 2026-07-01 will be brick. Projects mid-build on 2026-07-01 are grandfathered through completion; quotes outstanding will be re-issued at brick pricing.
>
> **Consequences:** Build timelines extend (4 weeks → 9 weeks typical). Materials cost roughly triples. Quote book and marketing collateral need refresh by 2026-06-15. Existing straw/stick inventory still serviceable for outbuildings and temporary structures.
>
> **References:** `observations.md#2026-05-15-wolf-related-project-delays-follow-a-pattern`, `daybook/2026-05-15.md`.

---

<!-- Add your decisions below. Newest at the bottom. -->
