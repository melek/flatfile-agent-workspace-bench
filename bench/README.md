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
├── scenarios/                           12 scenarios across 4 modes (3 each)
│   ├── 01-cold-pickup-guardrail/
│   ├── 02-cold-pickup-cross-day/
│   ├── 03-cold-pickup-stale-followup/
│   ├── 04-routing-novel-observation/
│   ├── 05-routing-decision-vs-observation/
│   ├── 06-routing-tldr-screening/
│   ├── 07-procedure-artifact-binding/
│   ├── 08-procedure-missing-prior-step/
│   ├── 09-procedure-synthesis-vs-verifiable/
│   ├── 10-threat-planted-error-adr/
│   ├── 11-threat-sycophantic-confirmation/
│   └── 12-threat-provenance-check/
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
| Scenarios per benchmark version | 12 |
| Total runs per version | 60 |
| Total runs across baseline + revised | 120 |
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

## Disagreement is the signal

We do not pitch v0.1 → v0.2 as improvement. The headline of any results report is **"where the three rubrics agree and where they disagree."** Disagreement matters because rubrics encode different priorities: cognitive ergonomics wants low friction, architecture wants strict routing, safety wants disclosure and resistance to ratification. A change that helps one frequently costs another. That trade-off is the result.

## Frozen-scenarios discipline

Scenarios are content, not infrastructure. Tweaking them mid-experiment kills the comparison. Once `bench-frozen-v1` is tagged in git, do not edit any file under `bench/scenarios/` until the comparison report is written. A new bench version (`bench-frozen-v2`) is a new comparison, not a continuation.
