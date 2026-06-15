# v0.4 pre-registration

Registered **before** any v0.4 measurement run, so the headline-bearing analysis
is a prediction, not a post-hoc selection. Tagged `v0.4-prereg`.

- **Date:** 2026-06-14
- **Template of record:** vendored `agent-workspace-template/`, source
  `flatfile-agent-workspace` @ `00ffbfe` (see `template-provenance.json`).
- **Instrument:** artifact-grounded (snapshot → diff → check), deterministic
  AR3/AR4/SA2, leakage-free `scenario-public.md` rater briefs, partitioned
  aggregation (binary pass-rates vs ordinal means). Rubrics at version 2.

## Headline (the only claim the run will stake)

Full-template **minus control** pass-rate deltas on the three deterministic,
code-checked, family-robust axes — **AR3** (cross-references resolve), **AR4**
(append-only respected), **SA2** (work-product attribution footer) — reported as
per-scenario deltas with between-scenario CIs across the 10 active scenarios
(9 df). Direction signal only; no significance, no magnitude claim.

**SA2 caveat, registered up front:** under the canonical methodology, attribution
is a footer on *work products* (`projects/`/`resources/`/`tmp/`), not a per-entry
marker on internal records. SA2 is therefore **n/a on register-routing scenarios**
(most of the active set) and only discriminates where a scenario produces a work
product. AR3/AR4 are expected to carry most of the deterministic headline; SA2's
applicable-n will be reported and SA2 will not be headlined where n is tiny.

## Disclosed appendix (not headline)

The 8 ordinal axes (AR1, AR2, CE1–CE4, SA1, SA3, SA4) are graded by a same-family
rater and carry shared-model bias. Reported with that bias named; never the
headline. AR2 is exploratory (LLM-binary, off headline). The safety rubric's
ordinal verdict (alpha 0.639) and SA1 (42–58% exact) are reported as
known-unreliable, not as results.

## Run configuration

| Parameter | Value |
|---|---|
| Simulator model | `claude-sonnet-4-6` (pinned, recorded per run) |
| Rater model | `claude-opus-4-8` (pinned, same family) |
| N runs / scenario | 5 |
| Arms | full-template, control1-blank, control2-verbal-spec, control3-bare-scaffold |
| Scoring protocol | isolated (one rater per scenario × run × ordinal-rubric); deterministic axes in code |
| Scenarios | 10 active (03, 05 retired) |

Per-arm token mass will be recorded in the manifest (token-mass confound
disclosure). control2 is included as the skeptical baseline ("did the curated
methodology beat the agent's self-authored one"); its deterministic-axis fails
may reflect an invented-different-scheme rather than worse behavior — read with
the ordinal/qualitative axes.
