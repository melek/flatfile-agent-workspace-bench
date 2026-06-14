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

The load-bearing contrast is **full template vs `control3-bare-scaffold` on the
deterministic axes** (next section): bare-scaffold isolates the one thing the
methodology actually sells — its *content/depth* — from the mere existence of
folders. `control1-blank` answers the weaker, near-foregone "does any structure
help." For `control3` to discriminate, its bare `AGENTS.md` must encode **no**
cross-reference or authorship conventions, or AR3/SA2 will not deterministically
fail on it and the contrast is lost — verify this before the run.

**Token-mass confound (disclose it).** The full template floods the context with
far more text than the bare scaffold, so a reviewer's null is "more words/longer
instructions helped, not better methodology." Length-match `control3` as far as
practical, and **record per-arm token mass in the manifest** so the delta is on
the table. Where volume cannot be matched, scope the claim to "methodology
as-shipped vs minimal scaffold" and concede volume is partially confounded with
depth. `control2-verbal-spec` is the cleanest exploratory lever against this —
report it, keep it off the headline.

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

- **Unit of analysis is the scenario.** There are **10 active scenarios**
  (03 and 05 retired 2026-06) → **9 degrees of freedom**, regardless of how
  many runs stack inside each. Runs (N=5) are *within-scenario replicates*:
  they shrink the per-scenario standard error, they do **not** add df for any
  across-scenario claim.
- **Report each arm as 10 per-scenario means** (each with its run-level SE),
  then the **paired** delta (full-template − control) with a **between-scenario**
  confidence interval — propagate the within-scenario run variance into the
  per-scenario mean; never pool the 50 runs as if independent (per Anthropic
  "Adding Error Bars to Evals", arXiv 2411.00640).
- **Effect sizes and CIs, not significance.** At 9 df a paired test (Wilcoxon
  signed-rank) has trivial power; do **not** build or lean on it. Report the
  per-scenario means and the paired delta with a between-scenario CI; "direction
  signal" is the register. A signed-rank test pre-declared as underpowered is
  ceremony — add it only if a reviewer demands it.
- **Multiplicity:** the axis × arm grid is a multiple-comparison surface. The
  control here is "report **all** axes, every arm, no cherry-picking" — which is
  free — not FDR machinery. **Pre-register the headline-bearing axis set (the
  deterministic AR3/AR4/SA2) in a tagged commit BEFORE the run**, so "we
  predicted these three carry the claim" is distinguishable from "we found three
  that moved."
- **Binary axes:** report the **base rate** per axis; a pass-rate ≥0.90 or ≤0.10
  is at ceiling/floor and has near-zero discriminating power (a reliable axis can
  still be uninformative). `aggregate` emits these flags in `binary-rates.md`.
  The control rungs are exactly what move a ceilinged-on-template axis off the
  ceiling — a blank control should fail SA2/AR3/AR4 deterministically, which is
  where those checks earn their keep.

## 3. The headline rule (pre-registered)

**The headline is the three deterministic, code-checked, family-robust axes —
AR3, AR4, SA2 — reported as full-template-minus-control pass-rate deltas with
between-scenario CIs.** Nothing else. The 8 ordinal axes are graded by a
same-family rater (the system that authors the template's idiom also judges it),
so they are a *disclosed appendix*, never the headline. The strongest claim the
instrument licenses is: "the methodology produces measurably more
artifact-grounded behavior (provenance markers, resolved cross-references,
append-only discipline) than a no-/bare-framework workspace, across the active
scenarios, as a direction signal." Not *better*, not a magnitude/percentage, not
generalization beyond the pinned Claude-family agent, not the safety rubric's
ordinal verdict (alpha 0.639, below threshold under every judge), not SA1
(42–58% exact — known-unstable). Fence those off as limitations, not quietly.

## 4. Template of record

Stage the **v0.3-trimmed-lineage surface**, not the longitudinal one. The
`build_template.py` default derives from the longitudinal working copy, which
reintroduces `followups.md` and the `weekly-review` runbook — the exact affordance
that got scenario 03 *retired for task-invalidity*. Staging it would put a surface
on disk that no active scenario tests, and risk re-validating behavior the active
set was re-scoped around. Regenerate the template stripping those (or document
explicitly why they stay and confirm no active scenario's score depends on them),
and **pin the resulting SHA in the manifest** before any run. "Undecided template
of record" is itself a publication blocker.

## 5. Faithfulness and blinding (already enforced by the instrument)

- **Score artifacts, not self-report.** The runner derives the actions from the
  real files the simulator wrote (`snapshot`) and emits a diff; the simulator
  authors no content or hashes. Raters receive the diff; deterministic checks
  read it directly.
- **No answer-key leakage.** Raters get `scenario-public.md` (factual framing),
  never `scenario.md`/`expected-signals.md`. Deterministic checks get the diff
  only. The simulator is blinded to both.
- **Same-model bias remains on the ordinal axes.** The deterministic code-checked
  axes (AR3/AR4/SA2) are family-robust; the 8 ordinal axes are still same-family
  judged. Lean the headline on the code-checked axes; disclose the rest. A
  cross-family rater on the ordinal axes is a robustness check (a different bias,
  not bias-free — see the cross-rater synthesis).

## 6. Legacy corpus (v0.1–v0.3)

These were scored **before** artifact-grounding: ordinal axes under rubric
version 1, raters reading the answer key, scores from `content_summary` rather
than artifacts. The `rubric_version` bump to 2 makes `compare` **hard-fail** any
v0.4(binary)↔v0.3(ordinal) comparison — correct and intended. The prior corpus
is legacy and **not comparable** to v0.4+; its committed reports stand as the
record of what was measured then, with their stated caveats. Do not re-aggregate
or re-score a frozen tag.
