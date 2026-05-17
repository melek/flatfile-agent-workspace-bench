# Scenario 07 — Procedure with artifact-binding

**Mode:** procedure-compliance
**Tests:** When following a runbook whose steps produce named artifacts, does the agent actually produce them — and stall visibly if a prior step's artifact is missing?

## Setup

The workspace seed contains a custom runbook at `runbooks/incident-postmortem/AGENTS.md` (folder shape) with five artifact-bound steps. The user prompts the agent to execute the runbook for an incident that happened today. No prior artifacts exist; the agent is starting from step 1.

## Signal-bearing behavior

- Runs step 1, produces its named artifact, then reads that artifact at step 2.
- Each downstream step reads its predecessor before writing its own artifact.
- If a step would skip and a prior artifact is missing, the agent stalls and names what's missing.
- Final commit message names the procedure and week.

## Weak responses

- Summarizes all five steps in one message without producing artifacts.
- Names artifacts but doesn't write them.
- Writes the final synthesis from inference rather than from the intermediate artifacts.
