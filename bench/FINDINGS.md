# Findings — single-session deterministic measurement (as of v0.5)

This is the bench's honest result to date, scoped exactly as narrowly as the
instrument supports. It is **not** a claim that "the methodology works."

## The one real finding

**The workspace methodology induces work-product attribution that bare-framework agents omit.**

On the scenarios that produce a durable work product (a deliverable under
`projects/`/`resources/`), an agent operating the full template ends the work
product with an authorship footer; agents operating no-framework or
bare-scaffold controls do not. Measured deterministically (`runner.py check`,
SA2) over a hash-verified workspace diff, with leakage-free rater inputs:

- Smoke, scenario 07 (incident-postmortem runbook), pinned `claude-sonnet-4-6`:
  full = **pass** (attributed the postmortem), all three controls = **fail**
  (no attribution). The signal-localization audit classifies SA2 on the
  work-product scenarios (07, 08) as **DISCRIMINATING**.

**Applicable-n = 2.** This is a *direction signal*, not a magnitude or a
significance claim, and it rests on two scenarios. It is exploratory.

## What the instrument cannot resolve (and why that is not a null)

The other two deterministic axes do **not** measure the framework:

- **AR3 (cross-references resolve), AR4 (append-only respected)** are
  RANGE-FAILURE or SEED-CARRIED on every scenario (`SIGNAL-LOCALIZATION.md`).
  A capable agent writes resolving relative links and respects append-only
  registers *whether or not* the framework is present, and where the behavior
  does occur it is induced by the **scenario seed** (the runbook, overlaid on
  all arms), not by the framework. AR4 additionally cannot fire on a blank
  control (no pre-existing register to mutate).

Reporting their near-zero full-vs-control deltas as "the framework has no
effect" would be a **measurement-range error, not a true null.** The instrument
is structurally unable to resolve a difference on these axes under
single-session conditions, because the behaviors are at the capable model's
ceiling.

## Why (root cause)

1. **The scenario seed carries the procedural signal.** It is overlaid on every
   arm, controls included; for procedure scenarios the seed *is* the runbook.
   So controls receive the task scaffolding the framework was meant to supply.
2. **A capable agent saturates the checkable single-session behaviors.** Cross-
   reference hygiene and append-only discipline are things a frontier model does
   correctly by default.
3. The one behavior that *does* differ — emitting an attribution footer — is a
   template-private convention controls are never told, which is why SA2 alone
   discriminates.

Evidence: `bench/SIGNAL-LOCALIZATION.md` (decidable audit, zero inference);
the `v0.4-smoke*` records; the ieops verdict panel that BLOCKED the v0.4 run.

## Scope of the claim (what may and may not be said)

- **May:** "On work-product tasks, the full template induces an authorship-
  attribution footer that no-/bare-framework agents omit (direction signal,
  n=2, single Claude-family agent)."
- **May not:** "the methodology improves agent behavior" / any magnitude /
  generalization beyond the pinned agent / any claim on AR3, AR4, the ordinal
  (same-family-judged) axes, or the safety rubric.

## What this implies for the bench

The framework's substantive value is **longitudinal** — cross-session
accumulation (history that builds, continuity carried across handoffs, register
state the agent must respect *because it wrote it last session*). A
single-session design is structurally blind to it: AR4's "pre-existing register"
can only become live when it is the agent's *own* prior output, not a seed.
The next horizon is a redesign of the instrument toward longitudinal
measurement (planned separately). Until then, the single-session result is the
narrow finding above, and nothing more.
