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

## 2026-03-05 — Draft: Nudge to Marcus on Data Extract Delay

**Status:** proposed

**Generated-by:** inference

**Context:** Data team slip (5+ days beyond original EOW estimate) affects week 1 kickoff planning. Need to confirm revised timeline with Marcus, acknowledge impact professionally, and assess any schedule mitigation.

**Decision (Draft for review):**

---

**Subject:** Verdant Foods data extract — revised timeline

Hi Marcus,

Ash just synced with your data team this morning. They're now indicating the raw extract will be ready in about 5 business days beyond our original week-of-May-24 target — so we're looking at approximately May 29 or slightly later.

I wanted to flag this directly since it does compress our week 1 ramp-up window. The good news: it doesn't break delivery (week 6 is still ours), and Ash and I can use the extra days to finalize ETL design and spike any ambiguous schema questions with Priya's input.

Can you confirm that May 29 (or thereabouts) is realistic? And if there's any flexibility there, we'd obviously take an earlier hand-off. Otherwise, we're planning around that and will be ready to move fast once the data lands.

Thanks,
[Your name]

---

**Consequences:** Confirms revised timeline with client, manages expectations, signals competence and adaptability (not panic). Opens door for Marcus to escalate or negotiate if he has options.

**References:** daybook/2026-03-05.md, followups.md (data extract entry)

---

## 2026-03-05 — Draft: Onboarding Confirmation to Priya

**Status:** proposed

**Generated-by:** inference

**Context:** Priya is listed as training lead in the Verdant Foods project AGENTS.md, but no formal communication was sent confirming the role, scope, or timeline. User noted it was "in my head from kickoff but not sure it left my head."

**Decision (Draft for review):**

---

**Subject:** Verdant Foods engagement — your role as training lead

Hi Priya,

Following up on the Verdant Foods engagement we kicked off this week. I want to confirm your role and make sure everything is clear.

**Your role:** Training lead. You'll be responsible for designing and delivering hands-on training for procurement analysts at Verdant Foods — 2 power users per manufacturing plant (3 plants total = 6 trainees).

**Timeline:** Week 1 kicks off next week. Training delivery runs weeks 1–6, with the final delivery in week 6.

**What I need from you:**
- Confirm you're good with this scope and timeline
- Once Ash's data extract lands (looking like late next week), we'll do a quick technical sync to make sure you have what you need to design the training curriculum
- We're targeting a kickoff call all together (you, Ash, me, Marcus) for early next week

**Questions?** Let me know anytime. Looking forward to working together on this.

[Your name]

---

**Consequences:** Closes a communication gap before it becomes a problem. Confirms Priya's availability and expectations before week 1 kickoff. Sets up the technical sync she'll need to design training effectively.

**References:** daybook/2026-03-05.md, followups.md (Priya entry), projects/verdant-foods/AGENTS.md
