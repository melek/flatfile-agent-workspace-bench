# Start Session

**When to run:** At the beginning of a work session, when the user invokes it. The runbook is **user-invoked** — the agent does not detect session boundaries. Invoke explicitly on request, or when the user opens with intent-shaped language ("I want to work on...", "today I'm trying to...", "let's start").

**Inputs:**
- The workspace as it is on disk.
- The user's stated intent for the day, if any.

**Outputs:**
- Oriented agent.
- `daybook/YYYY-MM-DD.md` with an Intent line for today (created if it doesn't exist yet; updated if it does).

## Steps

1. **Read the most recent daybook handoff.** `ls -1 daybook/ | grep -v AGENTS | tail -1` to find the most recent dated entry. Open it and read the Handoff section first. → produces no on-disk artifact; if no handoff exists, this step fails visibly (you know the workspace has no prior state to pick up from).

2. **Open today's daybook and record Intent.** Create `daybook/YYYY-MM-DD.md` (today's date) if it doesn't exist; if it does, open the existing file and pick up where the prior session left off. Write a one-line Intent under the **Intent** section reflecting the user's stated goal for the session. If the user has not stated an intent, leave the line as `(no specific intent stated)` and move on. → produces `daybook/YYYY-MM-DD.md` with an Intent section.

## Notes

The two load-bearing steps are the daybook-handoff read (where the prior session left its cold-pickup artifact) and the today's-daybook Intent write (the starting anchor for what gets logged through the day). Anything else is performative unless it produces a downstream artifact or fails visibly.

Common user extensions to add as separate numbered steps when the need arises:

- Scan `projects/*/AGENTS.md` Status sections for in-flight project state.
- Read recent `decisions.md` entries if a topic is unfamiliar.
- Read `observations.md` if the work touches a domain with known gotchas.
- Pull state from external systems (calendar, issue tracker, message queue).

Extend the runbook as patterns settle for your workspace. Keep additions artifact-bound where possible (each step should produce a file or fail visibly, per `runbooks/AGENTS.md#performative-confirmation`).
