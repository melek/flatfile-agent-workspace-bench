---
rubric_version: 1
axes: AR1, AR2, AR3, AR4
na_allowed: AR2
---

# Rubric: Architecture

**What this rubric values:** Correct file routing. Artifact-binding discipline. Cross-references that work. Idempotency. Respect for the methodology's strict bars (e.g., decisions.md is for commitments, not choices).

**What this rubric explicitly does not value:** Verbosity, defensiveness, or thoroughness. A short clean response that routes correctly outscores a long detailed response that puts a commitment in observations.md.

## Scoring discipline

- Score against the methodology as written in `methodology.md` and the per-file `AGENTS.md`s.
- A correct routing decision scores; a confident but wrong one does not.
- One sentence of justification per axis.
- Do not look at other rubrics' outputs.

## Axes

### AR1 — File routing correctness

Did the entry land in the file the methodology designates for it? Commitments that constrain future action belong in the durable decisions register; descriptive patterns belong in the observations register (where the methodology provides one); chronological working notes belong in the daybook Log; forward commitments belong wherever the methodology directs them (a dedicated file if defined, otherwise the daybook Handoff or an external tracker).

| Score | Description |
|---|---|
| 3 | Routed to the methodology-designated file with a routing rationale matching that methodology's strict bars. |
| 2 | Routed to the methodology-designated file, no explicit rationale. |
| 1 | Routed to a defensible neighboring file under that methodology (e.g., a decision-ish thing into daybook Log when a durable register would have been stricter). |
| 0 | Routed against the methodology's strict bars (e.g., a non-commitment into the durable decisions register, or a commitment buried in chronological Log when a durable register exists). |

### AR2 — Artifact-binding

For runbook / procedure steps, did each step produce a named artifact on disk that the next step could read?

| Score | Description |
|---|---|
| 3 | Each procedural step produced a concrete file the next step read; stalls visibly when prior artifact missing. |
| 2 | Most steps artifact-bound; one step was prose-only. |
| 1 | Several steps produced no artifact; the procedure was narrated rather than enacted. |
| 0 | The agent claimed completion without producing the named artifacts, or summarized in place of doing the step. |

For non-procedure scenarios, score this axis as **n/a** (treated as missing in aggregation, not as zero).

### AR3 — Cross-reference integrity

Did references to other files use the methodology's relative-path convention, and do they actually resolve?

| Score | Description |
|---|---|
| 3 | All cross-references are relative, anchor-stable, and resolve. |
| 2 | Mostly correct; one anchor is unstable or path is brittle. |
| 1 | References resolve but violate the methodology's stated cross-reference convention (e.g., absolute paths or wiki-style links where the methodology prescribes relative paths with section anchors). |
| 0 | Broken references, dangling anchors, or wrong direction (deep file referencing root by absolute path). |

### AR4 — Idempotency and forward compatibility

If the agent's actions were re-run or extended in a future session, would the workspace remain coherent?

| Score | Description |
|---|---|
| 3 | All actions are idempotent and append-only where the file requires it; nothing would conflict on re-run. |
| 2 | One action would silently no-op or duplicate on re-run, but state stays coherent. |
| 1 | One action mutates content that should have been append-only, or rewrites a status that should have been a new entry. |
| 0 | Re-running would corrupt history (e.g., editing an old decision in place, deleting a previous handoff). |
