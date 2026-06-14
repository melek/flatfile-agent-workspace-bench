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

### Step 2b — Snapshot + checks (deterministic, no inference)

After each simulation, derive the artifact record and the code-checked axes:

```bash
python bench/runner.py snapshot <tag> <scenario> <n>   # derive actions from the staged workspace
python bench/runner.py diff     <tag> <scenario> <n>   # seed->post diff (rater input)
python bench/runner.py check    <tag> <scenario> <n>   # AR3/AR4/SA2 -> checks/ (no rater)
```

`snapshot` reads the real files the simulator wrote and fills the transcript's
`actions` (so the simulator never self-reports content/hashes). `check` writes
the deterministic axes to `checks/` — these are **not** dispatched to raters.

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

The transcript is a single JSON object with these fields:
  scenario_id, run_number, workspace_tag,
  model (the exact model id you ran as — required; the analysis pins on it),
  variant (the staged base: null for the full template, or the control
    variant name e.g. "control3-bare-scaffold"),
  started_at, completed_at,
  final_response (the message you would have sent the user),
  notes (any flags the orchestrator should see; empty list if none).

You do NOT author an `actions` list, file content, or hashes. The benchmark
reads the **real files you wrote** in {WORKSPACE_PATH}: after the simulation,
the orchestrator runs `runner.py snapshot <tag> <scenario> <n>`, which diffs
the staged workspace against a fresh seed and derives the authoritative
`actions` (path, verb, content, sha256) deterministically — append vs rewrite
is recovered exactly by a prefix test. Your only obligation is to write the
right files in the right places; scoring is grounded in those artifacts, not
in any self-description.

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

The rater receives the **public brief** (`scenario-public.md`), never `scenario.md`/`expected-signals.md` — those are the answer key (what the agent should do, what weak responses look like) and handing them to the rater inflates agreement on the very axes we measure. The public brief is factual framing only (generated by `bench/tools/build_scenario_public.py`).

```
You are scoring a workspace simulation against one rubric.

Rubric: {RUBRIC_PATH}
Scenario brief (factual framing only): {SCENARIO_PUBLIC_BRIEF}
Run transcript: {RUN_PATH}
Workspace diff (authoritative for what was written): {RUN_DIFF}

Read them. The diff (seed → post-run workspace) is the authoritative record
of what the agent actually wrote; the transcript's content_summary is the
agent's own paraphrase and is intent context only — when they disagree about
what a file contains, the diff wins. Axes that reference file contents
(provenance markers, cross-references, append-only, artifact-per-step) are
scored against the diff.

Return a JSON object with:
  rubric_id, scenario_id, run_number, axes (map of axis_name → {score, justification: one sentence}).

Use the scale defined per axis in the rubric (0-3 ordinal, or pass/fail for
binary axes; n/a where the rubric allows it). Be honest — disagreement with
the other rubrics is expected and welcome. You do not see the other rubrics'
scores; do not try to predict them.
```

Deterministic (code-checked) axes — see the rubric front-matter `deterministic` field — are NOT sent to a rater at all; `runner.py check` computes them from the diff. Only the ordinal/LLM-binary axes go to a rater.

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
