# Scenario 05 — Ambiguous routing: decision or observation?

**Mode:** artifact-routing
**Tests:** Does the agent correctly route an item that *sounds* like a decision but actually only describes intent, into `observations.md` or daybook Log rather than `decisions.md`?

## Setup

The user says "we're going to use Postgres for the new service." There is no team alignment yet, no constraint named, no consequences spelled out. The methodology's strict bar for `decisions.md`: would a future reader need to ask "wait, are we allowed to do X?" The answer here is *not yet*.

## Signal-bearing behavior

- Recognizes the entry as not-yet-a-commitment.
- Suggests `observations.md` or daybook Log for now, with a route-up path if it firms up.
- Names the strict-bar test in-band.

## Weak responses

- Drops a `decisions.md` entry as if the user had announced one.
- Asks no questions and routes nowhere.
- Adds elaborate template fields the user didn't supply (Context, Decision, Consequences, References) under speculative content.
