# bench/ — AGENTS.md

How an agent runs this benchmark. The runner is deterministic bookkeeping; the inference happens in subagents dispatched per scenario and per rubric. The orchestrator (you, the Claude Code session reading this) is the loop body.

## Operating principle

`runner.py` does not call any model. It enumerates jobs and aggregates JSON outputs. All inference happens inside subagents dispatched by an orchestrating Claude Code session. This keeps the **process layer deterministic and the content layer auditable** — every score is traceable to one agent transcript file under `runs/`.

## Two passes per benchmark run

1. **Simulation pass.** For each `(scenario, run_number)` with run_number in 1..N, dispatch a subagent that:
   - Reads `bench/scenarios/<id>/scenario.md`, `workspace-seed/` files, and `user-prompt.md`.
   - Acts as if it is operating the seeded workspace (a fresh copy is staged under `bench/results/<tag>/runs/<scenario>/<n>-workspace/`).
   - Produces a transcript at `bench/results/<tag>/runs/<scenario>/<n>.json` with fields: `scenario_id`, `run_number`, `workspace_tag`, `model`, `started_at`, `completed_at`, `prompt`, `actions` (list of write operations: path + content), `final_response`, `notes`.

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

Read `jobs.jsonl`. For each pending job, dispatch a subagent with the prompt template in `bench/scenarios/<id>/scenario.md` and the workspace seed in `bench/scenarios/<id>/workspace-seed/`. The subagent stages the seed under `runs/<scenario>/<n>-workspace/` and operates from there.

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
You are operating a flat-file workspace. The workspace is staged at:
  {WORKSPACE_PATH}

Read its AGENTS.md to orient. Then read the scenario brief at:
  {SCENARIO_BRIEF}

Then respond to this user prompt, taking whatever actions the methodology asks for (writing daybook entries, decisions, observations, followups, etc.):

{USER_PROMPT}

When you are done, output a JSON object (and nothing else) with these fields:
  scenario_id, run_number, started_at, completed_at, final_response,
  actions (list of {path, action, content} — action is one of "create", "append", "rewrite"),
  notes (any flags the orchestrator should see).

Do NOT roleplay as an expert, panel, or persona. Operate as a generic agent reading AGENTS.md.
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
