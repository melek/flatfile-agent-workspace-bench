# Cross-rater synthesis — v0.3-trimmed

Hand-written synthesis of four rater-agreement studies on the same
72-job sample (12 scenarios × runs {2,4} × 3 rubrics, blinded inputs).
Machine-generated detail: `reliability.md` (same-family),
`reliability-openai-gpt-5-5.md`, `reliability-openai-gpt-4-1.md`,
`reliability-ollama-qwen2-5-14b.md`.

## The four judges

Ordinal Krippendorff's alpha, original Claude raters vs each comparison
rater. Columns ordered by judge capability (frontier → local), with the
same-family rescore as the ceiling:

| Rubric | Claude rescore (same-family) | GPT-5.5 (frontier) | GPT-4.1 (prior gen) | Qwen2.5-14b (local) |
|---|---|---|---|---|
| cog-erg | **0.878** | 0.722 | 0.742 | 0.336 |
| architecture | 0.722 | 0.412 | 0.570 | 0.576 |
| safety | 0.639 | 0.565 | 0.445 | 0.337 |

## The hypothesis that failed

Going in, the expectation was a clean capability gradient: a stronger
cross-family judge should converge toward the Claude raters, so
agreement would rise Qwen → GPT-4.1 → GPT-5.5 → same-family. **It does
not.** The two frontier OpenAI models bracket each other on cog-erg
(0.72/0.74) and safety (0.57/0.45), and on architecture the *newest and
strongest* judge agrees least of the four (0.412, below the 14B). More
cross-family capability did not buy more agreement with Claude. On the
evidence here, **family difference dominates capability difference** —
a frontier non-Claude judge does not behave like a Claude judge, and
making it more capable does not change that.

This is the load-bearing correction. Had the study stopped at GPT-4.1
(the first cross-family run), the gradient story would have looked
plausible and been wrong.

## What the capability axis actually reveals

Reading down the four columns axis by axis separates two different
defects that a single cross-family judge would have conflated:

- **CE2 (output economy) was mis-diagnosed as family-idiosyncratic; it
  is capability-sensitive.** Exact agreement: same-family 83%, GPT-5.5
  83%, GPT-4.1 33%, Qwen 12%. The earlier (GPT-4.1-only) read — "verbosity
  anchors don't transfer across families" — was an artifact of judge
  weakness. A frontier judge of *either* family scores output economy
  the same; weak judges cannot. This conclusion only became visible by
  adding a stronger cross-family judge, and it reverses the prior write-up.

- **Architecture disagreement is genuinely cross-family.** GPT-5.5
  (0.412) and GPT-4.1 (0.570) both sit well below same-family (0.722)
  and capability does not close the gap — if anything the stronger model
  applies a different architectural reading more confidently. (See the
  temperature caveat below before over-reading the 0.412.)

- **Safety improves with capability but never enough.** 0.337 → 0.445 →
  0.565 across Qwen → GPT-4.1 → GPT-5.5, yet the best cross-family safety
  agreement (0.565) still falls short of same-family (0.639) and of the
  0.67 support threshold. The safety rubric is not rescued by a better
  judge; it needs redesign.

## Findings that survive all four judges

These reproduce regardless of judge capability or family, which makes
them properties of the *instrument*, not of any rater:

1. **The AR2/SA2 applicability rule is underspecified.** AR2 n/a flips
   land on the same ~15 units under same-family, GPT-5.5, and GPT-4.1
   (Qwen pushes to 21). Independent raters keep resolving "does this
   axis apply?" against the original scores. This must become a
   deterministic precondition, not a rater judgment (#6).

2. **SA1 (rubber-stamping resistance) is intrinsically unstable** —
   exact agreement 42–58% across every judge. No judge supports 0–3
   scoring of it as written.

3. **Safety is the weakest or tied-weakest rubric under every
   comparison.** The safety-column deltas in the summary tables remain
   unsupported.

## The temperature confound (read before ranking GPT-5.5)

GPT-5.5 rejects `temperature: 0` and runs only at its default
temperature 1; GPT-4.1, Qwen, and the original raters were scored at
temperature 0. GPT-5.5's column therefore carries sampling
nondeterminism the others do not, which depresses its agreement by an
unknown amount. Consequences:

- Where GPT-5.5 *beats* a temperature-0 judge despite this handicap —
  safety (0.565 > GPT-4.1's 0.445), CE2 (83% > 33%) — the signal is
  strong, having overcome a headwind.
- Where GPT-5.5 *trails* — architecture 0.412 — the result is confounded
  with sampling noise and should not be read as a clean family/capability
  effect. The "frontier judge agrees least on architecture" headline is
  directionally real (both OpenAI models trail same-family) but its
  magnitude for GPT-5.5 specifically is inflated by temperature.

## Method note

The four-judge design exists to separate family difference from
capability difference, which a single cross-family judge cannot do. It
worked: it caught one mis-diagnosis (CE2) and falsified the capability-
gradient hypothesis. The local 14B judge is calibration scaffolding for
the capability axis, not an independent measurement of the originals.
Cost/latency spanned ~3 min (GPT-4.1) to ~18 min (GPT-5.5, reasoning
tier) to ~2.5 h (local 14B); an aborted 32B local attempt raced the
14B output directory and contaminated 10 files, caught by the per-file
`model` field and rescored — the field exists for exactly this.

The honest takeaway for the bench: cross-family agreement is
substantially below same-family on every rubric and does not improve to
acceptable levels with judge capability. Any future run must pin the
judge model; cross-model score comparison is not supported. The
instrument fixes that would actually raise these numbers are #5
(score artifacts, not self-report) and #6 (binary applicability
preconditions and behavioral checks), both still unbuilt.
