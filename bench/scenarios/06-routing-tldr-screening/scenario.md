# Scenario 06 — TLDR-only record handling

**Mode:** artifact-routing
**Tests:** When the user surfaces a summary-only artifact (a TLDR-style abstract of an outside resource, no full source), does the agent route it provisionally to `tmp/` for triage rather than treating it as durable reference?

## Setup

The user pastes a one-paragraph AI-generated summary of an external research article they haven't actually read yet. They ask where to keep it.

## Signal-bearing behavior

- Recognizes that an AI-summary-without-source is not the same as the source.
- Routes to `tmp/<topic>/` for triage with a note to verify against the original.
- Names the provenance gap in-band (the summary is automated, not authored).

## Weak responses

- Drops the summary in `resources/` as if it were durable reference material.
- Routes silently to daybook Log.
- Treats the AI-generated summary as authoritative content.
