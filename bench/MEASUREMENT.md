# Measurement protocol for the next real run (v0.4+)

This document specifies how the **first artifact-grounded run** (under the #5/#6
instrument: content-bearing transcripts, deterministic AR3/AR4/SA2, leakage-free
rater briefs) must be designed and analyzed so the result holds up to outside
review. It is written *before* that run so the run executes a fixed protocol
rather than re-deriving one. Nothing here re-scores frozen data; v0.1–v0.3 are
untouched legacy (see "Legacy corpus" below).

## 1. The control condition (required, not optional)

The bench's published claims have so far been **within-template version deltas**
("where the rubrics agree/disagree about v0.2→v0.3"), which need no control. The
moment the artifact makes any claim that *the workspace methodology helps an
agent*, a no-framework control becomes mandatory — without a floor, every number
is relative to another version of the same template, and an external reviewer
names this first.

**Design — two pinned rungs plus the template, one model:**

| Arm | Base tree | Question it answers |
|---|---|---|
| `control1-blank` | empty workspace | floor: does *any* structure help? |
| `control3-bare-scaffold` | folders + empty registers + one bare AGENTS.md, no methodology depth | does methodology *depth* help beyond the files existing? |
| full template | `agent-workspace-template/` (materialize first — see README) | the framework as shipped |

`control2-verbal-spec` stays **exploratory** (a files-vs-prose mechanism probe),
off the headline.

**Break the model confound by pinning, not pairing.** Every arm runs at *one*
pinned simulator model, recorded in each transcript's required `model` field;
`validate` hard-fails if `model` is missing or varies within the comparison set.
Do **not** run a model×arm factorial (no budget at this scale, and model
generalization is not the question). Score every arm in the **same scoring pass,
same session window, same pinned rater model, same isolated 180-call protocol** —
arms must differ in exactly one factor (presence/depth of methodology) and
nothing else. Running arms weeks apart under drifted conditions recreates the
cross-protocol drift the v0.2/v0.3 summaries already carry.

**Quarantine the existing control data.** `ctrl{1,2,3}-{haiku,opus}` vary the
*model* across arms (and the template runs never recorded a model pin), so
control-vs-framework there is confounded with haiku-vs-opus. It is smoke-scale,
ragged, and unsummarized. Treat it as quarantined: do not write a summary over
it, do not cite it as a control result. Supersede it with a pinned run.

## 2. Statistics licensed at this scale

- **Unit of analysis is the scenario.** There are 12 fixed scenarios → **11
  degrees of freedom**, regardless of how many runs stack inside each. Runs
  (N=5) are *within-scenario replicates*: they shrink the per-scenario standard
  error, they do **not** add df for any across-scenario claim.
- **Report each arm as 12 per-scenario means** (each with its run-level SE),
  then the **paired** delta (full-template − control) with a **between-scenario**
  confidence interval — propagate the within-scenario run variance into the
  per-scenario mean; never pool the 60 runs as if independent (per Anthropic
  "Adding Error Bars to Evals", arXiv 2411.00640).
- **If testing at all, use a paired test across the 12 scenarios** (Wilcoxon
  signed-rank — honest for bounded/ordinal data; n=12 gives minimal but nonzero
  power). No significance language otherwise; "direction signal" is the register.
- **Multiplicity:** 12 axes × arms is a multiple-comparison surface. Pre-register
  the axis dispositions (the #6 front-matter does this) and report **all** axes,
  every arm — no cherry-picking "6 of 12 scenarios show X." If ever testing,
  control FDR across the axis family.
- **Binary axes:** report the **base rate** per axis; a pass-rate ≥0.90 or ≤0.10
  is at ceiling/floor and has near-zero discriminating power (a reliable axis can
  still be uninformative). `aggregate` emits these flags in `binary-rates.md`.
  The control rungs are exactly what move a ceilinged-on-template axis off the
  ceiling — a blank control should fail SA2/AR3/AR4 deterministically, which is
  where those checks earn their keep.

## 3. Faithfulness and blinding (already enforced by the instrument)

- **Score artifacts, not self-report.** Raters receive the runner-emitted diff;
  `content_summary` is non-authoritative. The diff is reconstructed from the
  transcript and **hash-verified** against the recorded `sha256` — a self-report
  inconsistent with its own hash is flagged, not scored.
- **No answer-key leakage.** Raters get `scenario-public.md` (factual framing),
  never `scenario.md`/`expected-signals.md`. Deterministic checks get the diff
  only. The simulator is blinded to both.
- **Same-model bias remains on the ordinal axes.** The deterministic code-checked
  axes (AR3/AR4/SA2) are family-robust; the 8 ordinal axes are still same-family
  judged. Lean the headline on the code-checked axes; disclose the rest. A
  cross-family rater on the ordinal axes is a robustness check (a different bias,
  not bias-free — see the cross-rater synthesis).

## 4. Legacy corpus (v0.1–v0.3)

These were scored **before** artifact-grounding: ordinal axes under rubric
version 1, raters reading the answer key, scores from `content_summary` rather
than artifacts. The `rubric_version` bump to 2 makes `compare` **hard-fail** any
v0.4(binary)↔v0.3(ordinal) comparison — correct and intended. The prior corpus
is legacy and **not comparable** to v0.4+; its committed reports stand as the
record of what was measured then, with their stated caveats. Do not re-aggregate
or re-score a frozen tag.
