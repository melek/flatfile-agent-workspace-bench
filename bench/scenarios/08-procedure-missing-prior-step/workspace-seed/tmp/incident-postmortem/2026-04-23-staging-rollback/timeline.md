# Timeline — 2026-04-23 Staging Rollback

## Detection

- 14:18 — Synthetic monitor flagged staging /healthz at 503.
- 14:21 — Slack alert escalated; on-call pulled the cord.

## Diagnosis

- 14:24 — Identified the deploy that landed at 14:12 as the candidate cause.
- 14:27 — Confirmed migration step 2 hung on a lock acquisition.

## Mitigation

- 14:30 — Rolled back the deploy via the standard runbook.
- 14:33 — Staging recovered; smoke tests pass.

## Resolution

- 14:40 — Posted resolution in #incidents.
- 14:45 — Filed this timeline as the starting artifact for the postmortem.
