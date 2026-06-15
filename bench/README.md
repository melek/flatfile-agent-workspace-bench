# bench/ — Workspace Benchmark

A small benchmark for comparing versions of the flatfile-agent-workspace template against itself across a fixed set of scenarios. It does *not* compare this workspace against other systems and does *not* attempt to measure absolute performance. It is a same-shape A/B intended to surface where edits to the template change agent behavior — and especially where the three scoring rubrics **disagree** about whether a change helps.

## What this benchmark is for

- Direction signals only — does an edit move the needle, and which way?
- Surfacing **disagreement between rubrics** as the load-bearing output. If cognitive-ergonomics likes a change and the safety rubric scores it as harmful, that is the result.
- Forcing the template's claimed benefits (artifact-binding, decision-supersession, provenance) into a falsifiable form.

## What this benchmark is not

- Not a head-to-head against other workspace systems.
- Not a magnitude claim. N=5 simulations per scenario will not support significance testing.
- Not a longitudinal study. Single-session simulations cannot probe Theme-3 compounding effects.
- Not a substitute for human-subjects study. Rater agents stand in for human raters. Their bias is the limitation.

## Layout

```
bench/
├── README.md                            this file
├── AGENTS.md                            how a Claude session runs the benchmark
├── scenarios/                           10 active scenarios across 4 modes
│   ├── 01-cold-pickup-guardrail/
│   ├── 02-cold-pickup-cross-day/
│   ├── 04-routing-novel-observation/
│   ├── 06-routing-tldr-screening/
│   ├── 07-procedure-artifact-binding/
│   ├── 08-procedure-missing-prior-step/
│   ├── 09-procedure-synthesis-vs-verifiable/
│   ├── 10-threat-planted-error-adr/
│   ├── 11-threat-sycophantic-confirmation/
│   └── 12-threat-provenance-check/
├── scenarios-retired/                   scenarios with broken task validity (see RETIRED.md in each)
│   ├── 03-cold-pickup-stale-followup/   tests an affordance the v0.3 trim removed
│   └── 05-routing-decision-vs-observation/  outcome not movable by template text
├── rubrics/
│   ├── cog-erg.md                       cognitive-ergonomics rubric
│   ├── architecture.md                  artifact-binding + cross-ref + routing
│   └── safety.md                        rubber-stamping / sycophancy / provenance
├── runner.py                            enumerates jobs; aggregates results
├── lib/
│   └── score_io.py                      shared JSON / CSV utilities
└── results/<workspace-tag>/             one directory per benchmark run
    ├── manifest.json                    workspace SHA, scenarios-frozen tag, model, date
    ├── runs/<scenario>/<n>.json         raw agent trace per run (1..N)
    ├── scores/<rubric>.csv              one row per (scenario, run, rubric_axis)
    ├── disagreement-matrix.md           where rubrics diverge
    └── summary.md                       human-readable comparison vs. baseline
```

## Run parameters

| Parameter | Value |
|---|---|
| N runs per scenario | 5 |
| Model | Claude (one family, pinned per run; `manifest.json` records it) |
| Scenarios per benchmark version | 10 (12 before the 2026-06 retirement of 03 and 05 — frozen tags and existing results keep all 12) |
| Total runs per version | 50 (was 60) |
| Total runs across baseline + revised | 100 (was 120) |
| Rubrics scored per run | 3 (cog-erg, architecture, safety) |

If a budget envelope is hit and N is reduced, the manifest must record `N_actual` and a `degraded: true` flag; the summary report names the reduction in its limitations section.

## How to run

See `AGENTS.md` for the full operator runbook. Short version:

```bash
python bench/runner.py plan --version v0.1-baseline    # prints jobs to run
python bench/runner.py plan-scoring --version v0.1-baseline    # prints scoring jobs
python bench/runner.py aggregate --version v0.1-baseline       # writes scores/, disagreement-matrix, summary
```

The runner enumerates work; an orchestrating agent dispatches the actual inference calls. Inference is quarantined inside the dispatched agents — `runner.py` itself makes no inference calls.

## Materializing the template

`runner.py stage` builds a run's workspace from a **base tree** plus the scenario seed. Two kinds of base tree exist:

- **Control variants** (`bench/controls/control{1,2,3}-*`) — present in-repo; stage directly.
- **The full template** (`sio.TEMPLATE_ROOT`, `agent-workspace-template/`) — a **vendored snapshot of the authoritative template** maintained in the sibling repo `flatfile-agent-workspace` (`agent-workspace-template/`). The template has a single owner there; the bench vendors a copy so it is self-contained and reproducible. The source repo + commit SHA are recorded in `template-provenance.json` at the bench repo root. Re-sync / verify with:

  ```bash
  python bench/tools/sync_template.py          # vendor from the sibling repo
  python bench/tools/sync_template.py --check  # fail if the vendored tree differs from source
  ```

  This is the v0.3-trimmed lineage of record: `followups.md` and `weekly-review` removed, `start-session`/`close-session` runbooks present, paired `AGENTS.md`/`CLAUDE.md`. The deterministic checks (`runner.py check`) encode *this* template's methodology — notably the work-product attribution footer, not the superseded per-entry `Generated-by` marker. Earlier `v0.1`–`v0.3` results predate this tooling and were staged out-of-band (legacy; see `MEASUREMENT.md`).

If the template is ever absent, `stage`/`diff` for a full-template run **fails loudly** with a pointer here rather than staging an empty or contaminated tree. Control-variant runs are unaffected.

## Measurement protocol (v0.4+) and the legacy corpus

The next real run uses the artifact-grounded, binary-checked instrument (issues
#5/#6): content-bearing transcripts, deterministic AR3/AR4/SA2 over a hash-verified
workspace diff, leakage-free rater briefs, and a per-axis binary/ordinal split.
**`MEASUREMENT.md`** specifies that run's protocol — the required two-rung pinned
control (`control1-blank` + `control3-bare-scaffold` + full template, one pinned
model), the statistics licensed at 12 scenarios (11 df; runs are replicates;
paired Wilcoxon; between-scenario CIs), and binary base-rate/ceiling reporting.

**v0.1–v0.3 are legacy and not comparable to v0.4+.** They were scored under
rubric version 1 (ordinal), with raters reading the design notes and scoring the
simulator's paraphrase rather than the artifact. The `rubric_version` bump makes
`compare` hard-fail across the boundary by design. The existing `ctrl*-haiku/opus`
control data is **quarantined**: it varies the model across arms (confounded) and
is superseded by the pinned control in `MEASUREMENT.md` — do not summarize it.

## Disagreement is the signal

We do not pitch v0.1 → v0.2 as improvement. The headline of any results report is **"where the three rubrics agree and where they disagree."** Disagreement matters because rubrics encode different priorities: cognitive ergonomics wants low friction, architecture wants strict routing, safety wants disclosure and resistance to ratification. A change that helps one frequently costs another. That trade-off is the result.

## Frozen-scenarios discipline

Scenarios are content, not infrastructure. Tweaking them mid-experiment kills the comparison. Once `bench-frozen-v1` is tagged in git, do not edit any file under `bench/scenarios/` until the comparison report is written. A new bench version (`bench-frozen-v2`) is a new comparison, not a continuation.

## Retired scenarios

A scenario is retired when it fails task validity — when its outcome no longer depends on the template under test (Agentic Benchmark Checklist, arXiv 2507.02825). Retirement moves the directory to `bench/scenarios-retired/` with a `RETIRED.md` stating what it was designed to test and why it no longer does. Retirement applies to future runs only: frozen tags and existing results keep the full original set, so past comparisons are untouched. Re-scoping a retired scenario means a new scenario ID under a new frozen tag, never an edit in place.
