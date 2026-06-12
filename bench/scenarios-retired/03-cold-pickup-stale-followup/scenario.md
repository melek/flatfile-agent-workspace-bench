# Scenario 03 — Stale followup chase

**Mode:** cold-pickup
**Tests:** Does the agent surface a 3-week-old followup when the user opens a session with a generic "anything to chase?" prompt?

## Setup

`followups.md` contains a followup from `2026-03-30` waiting on a vendor reply, status `chased once` on `2026-04-08`. No further movement. Today is `2026-04-23`.

## Signal-bearing behavior

- Reads `followups.md`.
- Identifies the 3-week-quiet item and names it.
- Suggests an escalation or a close (recognizes the silent-fail pattern from the methodology).

## Weak responses

- Generic "let me know what you'd like to chase" passing the buck.
- Surfacing the followup but not flagging the silence as a signal.
