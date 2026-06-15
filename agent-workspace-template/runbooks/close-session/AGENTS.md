# Close Session

**When to run:** At the end of a work session, when the user invokes it. The agent doesn't know a session is ending — only the user does. This runbook is **user-invoked**, not auto-triggered.

**Inputs:**
- Today's work — what got done, what's in progress, blockers, anything worth carrying forward.
- Any decisions made today that earned a place in the durable log.

**Outputs:**
- Today's `daybook/YYYY-MM-DD.md` with a filled Handoff section.
- Any new entries in `decisions.md`.
- Any new entries in `observations.md`.
- A git commit.

## Steps

1. **Surface open threads to the user.** List what's still in flight from today's session — incomplete tasks, unresolved questions, blockers, holds awaiting external input, half-decisions that didn't fully land. Ask the user, item by item, which become Handoff lines, which earn a decision or observation, and which get dropped. → produces no artifact directly; informs steps 2–4.

2. **Write today's daybook Handoff.** Open or create `daybook/YYYY-MM-DD.md` (today's date). Add or update the Handoff section using the user's triage from step 1: what got done, what's in progress, blockers, and the very first thing the next session should do. Include any boundary conditions (`do NOT` instructions, holds awaiting external input) in a `Guardrails for next session` sub-section if relevant. → produces `daybook/YYYY-MM-DD.md` with a filled Handoff.

3. **Append decisions earned today.** If any commitments were made today that constrain future action — including any surfaced in step 1 — append entries to `decisions.md` using the template at the top of that file. If no decision earned its place, skip this step explicitly. → produces zero or more new entries in `decisions.md`.

4. **Append observations earned today.** If today's work surfaced any findings that cost significant inference to arrive at and would help a future session avoid re-deriving them — including any surfaced in step 1 — append entries to `observations.md` using the template at the top of that file. If no observation earned its place, skip this step explicitly. → produces zero or more new entries in `observations.md`.

5. **Commit.** `git add . && git commit -m "<short summary of the day's work>"`. → produces a git commit.

## Notes

This runbook is intentionally minimal. The five steps are the load-bearing moves: triage open threads with the user, write the cold-pickup artifact, durably record any commitments, durably record any inference-expensive findings, snapshot the day. Step 1 is the only non-artifact-bound step; it earns its place because the user is the only source of truth for which open threads belong in the Handoff versus the logs versus the floor.

Common user extensions to add as separate numbered steps when the need arises:

- Close out any open commitments in an external tracker (issue tracker, todo system, etc.).
- Update `projects/<name>/AGENTS.md` Status sections for projects that moved meaningfully.
- Run any project- or repo-specific procedures (CI checks, deploy commands, etc.).

Extend the runbook as patterns settle for your workspace. Keep additions artifact-bound where possible (each step should produce a file or have a visible failure mode, per `runbooks/AGENTS.md#performative-confirmation`).
