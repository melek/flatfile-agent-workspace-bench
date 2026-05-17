# Scenario 02 — Cold pickup with cross-day decision reference

**Mode:** cold-pickup
**Tests:** Does the agent locate and respect a decision from an earlier day when the user gestures at it vaguely ("what we decided last week about the hiring scope")?

## Setup

`decisions.md` contains an entry dated `2026-04-15` titled "Restrict initial hiring to mid-level engineers only" with `Status: accepted`. The user's prompt today refers to it indirectly. The most recent daybook (`2026-04-22.md`) does not mention hiring.

## Signal-bearing behavior

- The agent searches `decisions.md` for the relevant entry.
- The agent quotes or paraphrases the decision in its response.
- The agent does not invent or re-derive a hiring policy.

## Weak responses

- Inferring a hiring policy without locating the decision.
- Asking the user to remind it (high orientation cost).
- Locating the decision but burying the citation.
