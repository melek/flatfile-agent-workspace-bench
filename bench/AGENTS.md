# bench/ — AGENTS.md

How an agent runs this benchmark. The runner is deterministic bookkeeping; the inference happens in subagents dispatched per scenario and per rubric. The orchestrator (you, the Claude Code session reading this) is the loop body.

## Operating principle

`runner.py` does not call any model. It enumerates jobs and aggregates JSON outputs. All inference happens inside subagents dispatched by an orchestrating Claude Code session. This keeps the **process layer deterministic and the content layer auditable** — every score is traceable to one agent transcript file under `runs/`.

## Two passes per benchmark run

1. **Simulation pass.** For each `(scenario, run_number)` with run_number in 1..N, dispatch a subagent that:
   - Reads `workspace-seed/` files and `user-prompt.md` **only**. It must NOT read `scenario.md` or `expected-signals.md` — those are rater-side design notes (the answer key); the simulator is blinded to them.
   - Acts as if it is operating the seeded workspace (a fresh copy is staged under `bench/results/<tag>/runs/<scenario>/<n>-workspace/`).
   - Produces a transcript at `bench/results/<tag>/runs/<scenario>/<n>.json` whose schema and action semantics are pinned in the Simulator subagent template below (`model` and `variant` required; actions carry full `content` + `sha256`).

2. **Scoring pass.** For each `(scenario, run_number, rubric)` triple, dispatch a separate subagent that:
   - Reads the run transcript and the rubric.
   - Returns scores per rubric axis (0–3 ordinal), with a one-sentence justification per axis.
   - Writes `bench/results/<tag>/scores/<rubric>/<scenario>/<n>.json`.

Three rubrics × 60 runs = 180 scoring calls per benchmark version. Keep batches small (≤6 in parallel) to avoid rate limits.

## Orchestrator runbook

### Step 1 — Build the job plan

```bash
python bench/runner.py plan --version <workspace-tag>
```

Writes `bench/results/<tag>/jobs.jsonl` with one line per simulation job. Idempotent — re-running skips lines whose output already exists on disk.

→ produces `bench/results/<tag>/jobs.jsonl` and a count summary to stdout.

### Step 2 — Run simulation pass

Read `jobs.jsonl`. For each pending job, dispatch a subagent with the **user prompt** at `bench/scenarios/<id>/user-prompt.md` and the staged workspace path. The subagent operates the workspace from that path. The subagent must **not** see `scenario.md` or `expected-signals.md` — those are the rater's design notes and would contaminate the simulation.

→ produces `bench/results/<tag>/runs/<scenario>/<n>.json` per run.

**Anti-pattern (refuse if reached for):** Do *not* dispatch the simulator agents with elaborate roleplay framing (no "act as an expert in...", no panels, no personas). The point is to test what the workspace produces in a generic agent, not to fish for the highest possible result through prompt engineering. The simulator prompt is essentially: "Operate the workspace at this path as you would for a user. Here is the user's prompt. Produce the response and write any file changes."

### Step 3 — Build the scoring plan

```bash
python bench/runner.py plan-scoring --version <workspace-tag>
```

Writes `bench/results/<tag>/scoring-jobs.jsonl` with one line per (scenario, run, rubric) triple. Idempotent.

### Step 4 — Run scoring pass

For each pending scoring job, dispatch a separate subagent (one per rubric per run — three independent sessions per run). Each rater agent reads only the rubric, the scenario brief, and the run transcript. It does **not** see the other rubrics' scores.

→ produces `bench/results/<tag>/scores/<rubric>/<scenario>/<n>.json` per scoring call.

### Step 5 — Aggregate

```bash
python bench/runner.py aggregate --version <workspace-tag>
```

Reads all per-run score files, writes:
- `scores/<rubric>.csv` (one row per `(scenario, run, axis, score, justification)`)
- `disagreement-matrix.md` — flags scenarios where rubrics diverge by ≥2 points on the same axis (computed as the difference between rubric means per axis, after normalizing axis names to canonical labels).

### Step 6 — Compare versions

When two versions have completed aggregation, write `bench/results/<later-tag>/summary.md` comparing to the earlier tag. The framing rule is hard:

> Do not pitch v0.1 → v0.2 as improvement. Frame it as "where the three rubrics agree and where they disagree, comparing seed to revised."

If a rubric thinks the change helped and another thinks it hurt, that is the result; both views are reported with equal weight.

## Subagent prompt templates

### Simulator subagent

```
You are operating a flat-file workspace on behalf of a user. The workspace
is staged at:
  {WORKSPACE_PATH}

Step 1. Read the workspace's AGENTS.md (root) and any AGENTS.md files in
subdirectories you actually need (do not pre-load every one — let
the user prompt drive what you read).

Step 2. Respond to the user's prompt below. Take whatever actions the
methodology asks for: writing daybook entries, decisions,
observations, followups, runbook artifacts, etc. Write real
files in {WORKSPACE_PATH}. Do not write outside it.

  USER PROMPT:
  {USER_PROMPT}

Step 3. When you are done, write a JSON transcript to:
  {RUN_OUTPUT}

The transcript must be a single JSON object with these fields:
  scenario_id, run_number, workspace_tag,
  model (the exact model id you ran as — required; the analysis pins on it),
  variant (the staged base: null for the full template, or the control
    variant name e.g. "control3-bare-scaffold"),
  started_at, completed_at,
  final_response (the message you would have sent the user),
  actions (list of write operations — see schema and semantics below),
  notes (any flags the orchestrator should see; empty list if none).

Each action is an object:
  {path, action, content, sha256, content_summary}
  - path: workspace-relative (no leading "/", no ".." traversal).
  - action: one of "create", "append", "rewrite", "delete".
  - content: for "create"/"rewrite", the FULL post-write file text; for
    "append", ONLY the appended fragment; omit for "delete".
  - sha256: hex sha256 of the file as it stands on disk AFTER this action
    (omit for "delete"). This is what lets the runner verify a reconstructed
    diff against what was actually written, rather than trusting the prose.
  - content_summary: a short paraphrase (intent context only — NOT
    authoritative for what was written; scoring reads the artifact diff).

Action semantics are a hard contract (the runner replays them to reconstruct
the post-run workspace, and scores against that):
  - List order is apply order. Do not reorder.
  - "create" makes parent directories as needed; "append"/"delete" target a
    path that already exists (in the seed or from an earlier action).
  - "delete" unlinks an existing path; deleting a non-existent path is an error.
  - Paths must be relative and must not escape the workspace.

Important constraints:
- Operate as a generic agent reading AGENTS.md. Do NOT roleplay as a
  domain expert, persona, or panel.
- Do not read scenario.md or expected-signals.md — those are not part
  of what the user sees. You only have the workspace and the user
  prompt above.
- Do not minimize work to avoid file writes. The benchmark is testing
  whether you write the right files in the right places.
```

### Rater subagent

```
You are scoring a workspace simulation against one rubric.

Rubric: {RUBRIC_PATH}
Scenario brief: {SCENARIO_BRIEF}
Run transcript: {RUN_PATH}

Read all three. Then return a JSON object with:
  rubric_id, scenario_id, run_number, axes (map of axis_name → {score: 0-3, justification: one sentence}).

Use the 0-3 ordinal as defined in the rubric. Be honest — disagreement with the other rubrics is expected and welcome. You do not see the other rubrics' scores; do not try to predict them.
```

## Postconditions per stage

| Stage | Postcondition |
|---|---|
| Plan | `jobs.jsonl` has 60 rows (12 scenarios × 5 runs) |
| Simulation | 60 run files exist under `runs/`; each is valid JSON with the required fields |
| Plan-scoring | `scoring-jobs.jsonl` has 180 rows (60 runs × 3 rubrics) |
| Scoring | 180 score files exist under `scores/`; each is valid JSON; axis scores are integers 0-3 |
| Aggregate | three CSVs and one `disagreement-matrix.md` exist |
| Compare | `summary.md` exists, contains both versions' aggregated tables, and frames results as agreement/disagreement (not "we got better") |

## Budget-envelope rule

If a session is interrupted or a rate-limit window is hit, the runner is idempotent: re-run any step and only pending jobs will execute. If the full N=5 cannot complete, the manifest records `N_actual` and `degraded: true`; the summary report names the reduction.
