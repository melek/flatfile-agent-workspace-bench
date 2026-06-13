# Cross-rater synthesis — v0.3-trimmed

Hand-written synthesis of the three rater-agreement studies on the same
72-job sample (12 scenarios × runs {2,4} × 3 rubrics, blinded inputs).
Machine-generated detail: `reliability.md` (same-family),
`reliability-openai-gpt-4-1.md`, `reliability-ollama-qwen2-5-14b.md`.

## The gradient

Ordinal Krippendorff's alpha, original Claude raters vs each comparison rater:

| Rubric | Claude rescore (same-family) | GPT-4.1 (cross-family, frontier) | Qwen2.5-14b (cross-family, local) |
|---|---|---|---|
| cog-erg | **0.878** | 0.742 | 0.336 |
| architecture | 0.722 | 0.570 | 0.576 |
| safety | 0.639 | 0.445 | 0.337 |

Agreement decays monotonically with judge distance (same model → other
frontier family → small local model) on cog-erg and safety. The observed
cross-family disagreement is therefore an *upper bound* on family effects:
it mixes genuine rubric-interpretation differences with judge-capability
differences, and the Qwen column shows how large the capability term can
get. Claims about self-preference bias should lean on the GPT-4.1 column
only, and even there the confound is not removed — only reduced.

## Findings that survive all three raters

1. **SA1 is intrinsically noisy.** Exact agreement: 42% (same-family),
   46% (GPT-4.1), 46% (Qwen). Three judges of very different capability
   all disagree with the originals at the same rate — the axis itself
   does not support 0–3 scoring as written. Redesign per issue #6.

2. **The originals are the outlier on AR2/SA2 applicability.** GPT-4.1's
   AR2 n/a flips land on the *identical 15 units* as the same-family
   rescore, and its SA2 flips overlap 7 of the same 8. Qwen pushes
   further (21 AR2 flips). Independent raters keep resolving the
   underspecified applicability criterion the same way — against the
   original scores. The applicability rule needs to be a deterministic
   precondition, not a rater judgment (issue #6).

3. **Safety is the least reliable rubric under every comparison**
   (0.639 / 0.445 / 0.337). The safety-column deltas in the summary
   tables remain unsupported, and the gap to the other rubrics widens
   as the judge gets farther from the original rater.

## Findings that are judge-sensitive (do not generalize)

- **CE2 (output economy) is judge-idiosyncratic.** Exact agreement
  collapses from 83% (same-family) to 33% (GPT-4.1) to 12% (Qwen) while
  within-1 stays ≥ 88% — judges share the ordering but not the anchor
  calibration. Verbosity scores should not be compared across judge
  models, and any future run must pin the judge.

- **Architecture's alpha floor (~0.57) is family-driven, not
  capability-driven** — GPT-4.1 and Qwen land in the same place despite
  the capability gap. The cross-family disagreement concentrates in AR4
  and the AR2 applicability flips rather than spreading evenly.

## Method note

A 14B local judge is not capable enough to score this bench on its own:
the Qwen column is included to *calibrate the capability confound*, not
as an independent measurement of the originals. The cost asymmetry is
also decisive — the GPT-4.1 batch took ~3 minutes against ~2.5 hours
for the local 14B model (and an aborted 32B attempt that raced the same
output directory; its 10 contaminated files were detected by the
per-file `model` field and rescored — the field exists for exactly this).
