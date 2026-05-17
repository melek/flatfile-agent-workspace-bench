# Scenario 04 — Route a novel pattern correctly

**Mode:** artifact-routing
**Tests:** Does the agent route a descriptive cross-cutting pattern into `observations.md` rather than `decisions.md` or daybook Log only?

## Setup

The user reports a pattern they've noticed several times this quarter: every time credentials get provisioned by IT, it takes 3+ business days, and downstream work always slips. The user is not announcing a decision; they are noticing the pattern.

## Signal-bearing behavior

- Routes the entry to `observations.md` (descriptive pattern, cross-cutting, not a commitment).
- Names *why* observations.md and not decisions.md or daybook Log.
- Uses an ISO-dated header.

## Weak responses

- Drops the pattern in daybook Log only.
- Drafts a "decision" to do something about credential provisioning that the user did not ask for.
- Routes to `observations.md` but with no in-band rationale (user cannot intercept).
