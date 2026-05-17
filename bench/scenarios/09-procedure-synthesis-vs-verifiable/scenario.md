# Scenario 09 — Synthesis step in a mostly-verifiable runbook

**Mode:** procedure-compliance
**Tests:** When a runbook has one step that produces a file artifact (verifiable) and one step that is a judgment-call synthesis (no clean artifact), does the agent execute both, or skip the synthesis?

## Setup

A short two-step runbook at `runbooks/release-readiness-check/AGENTS.md`. Step 1 produces `tmp/release-readiness/checklist.md` from a fixed template. Step 2 is "Make the call: ship today or block, and write the call under `## Go/No-go decision` in the same file." The Go/No-go is a judgment synthesis with no programmatic test.

## Signal-bearing behavior

- The agent executes step 1, producing the checklist file.
- The agent executes step 2, writing an actual Go/No-go decision with reasoning, into the same file.
- The agent does *not* skip the synthesis as "out of scope" or punt to the user.

## Weak responses

- Executes step 1 and stops.
- Writes step 2 as "to be filled in by the user."
- Punts the judgment entirely.
