# Vision Envelope — flatfile-agent-workspace-bench, v0.5 (construct-validity scoping)

**Diátaxis mode.** Reference (with how-to in §"How to use").

**Project.** flatfile-agent-workspace-bench
**Vision horizon.** Scoping: a decidable verdict on whether — and under what design — the bench can measure the workspace methodology's construct, reached before any further measurement spend.
**Ratified by.** Project Lead (human)
**Ratification date.** 2026-06-16
**Governing Charter.** ieops Project-Lead Charter (`~/repos/ieops/workspace-template/methodology/project-lead-charter.md`) — default; no substitution.

---

## 0. Well-formedness checklist

- [x] **M. Metadata** populated above.
- [x] **§1** declares a horizon end-condition.
- [x] **§2** quality goals in priority order; ties declared.
- [x] **§3** In/Out/Deferred explicit; In ∩ Out = ∅.
- [x] **§4** decision latitude is enumerated permissions.
- [x] **§5** ≥1 project-specific escalation trigger beyond Charter defaults.
- [x] **§6** drift cadence + criteria named.
- [x] **§7** substitution record explicit.
- [x] **§8** inference regime declared.
- [x] **§9** context budget declared.

## 1. Vision statement

A verdict panel (Flyvbjerg / Leveson-STPA / INCOSE, ieops BLOCK criterion) **BLOCKED** running the pre-registered v0.4 200-run matrix. The code-verified reason: the scenario seed is overlaid on every arm including controls, so the *procedural signal lives in the seed, not the framework* — and the only thing the full template adds that controls lack is a template-private attribution string. The bench, as the smoke revealed, risks measuring the seed and a string rather than "does the methodology change behavior."

This horizon produces the **decidable answer**: for each deterministic axis (AR3, AR4, SA2) × scenario, is it *discriminating*, *seed-carried*, or *range-failure*? **The envelope closes when that per-axis verdict exists**, alongside the Flyvbjerg reference-class record and the STPA hazard record. Producing the verdict — not running a study — is the entire horizon. The verdict selects the next horizon; this envelope does not pre-commit it.

## 2. Stakeholders and quality goals

**Stakeholders.** Project Lead (decides the next horizon from the verdict); any future external reader of a published result (the party the STPA loss protects).

**Quality goals (priority order, ties declared):**
1. **Construct validity** — the instrument measures "the methodology changes agent behavior," not the seed and not a template-private string.
2. **Honesty / defensibility** — no claim outruns what the instrument can resolve.
3. **Cost.**

Speed is explicitly **not** a quality goal. (1) strictly dominates (3): a cheaper run that measures the wrong construct has negative value.

## 3. Scope

**In-scope.** This Vision Envelope; the signal-localization audit tool and its generated verdict; the positive-control-witness inventory; honest re-registration discipline; annotating v0.4 docs as superseded-pending-verdict.

**Out-of-scope.** Running the 200-run matrix or any measurement matrix; building the longitudinal arm; editing or re-scoring frozen v0.1–v0.3; retracting the v0.4-smoke record.

**Deferred (surfaceable, not unilaterally resolvable).** The longitudinal/multi-session arm; relocating signals out of scenario seeds; a narrowed work-product-weighted run; the narrow-claim writeup — each gated on the verdict and re-ratified in a later envelope.

In ∩ Out = ∅.

## 4. Decision latitude

The operator may, without escalation: choose the file-inspection method and output format of the audit; classify an (axis, scenario) per the stated decidable rules; reuse runner.py predicate constants and helpers; annotate (not retract) superseded docs.

## 5. Escalation triggers (beyond Charter §6 defaults)

Return to the PL before action on: any move to run a measurement matrix before the verdict gate passes; any scenario or seed edit that would alter a frozen tag; any new claim of "the methodology works" not licensed by an axis the audit marks DISCRIMINATING; adopting a verdict rule the audit cannot decide by file inspection.

## 6. Drift checkpoints

**Cadence.** Per-artifact (envelope, audit tool, verdict).
**Method.** Hollnagel work-as-done vs work-as-imagined: re-read §§1–3 against what was built.
**Drift criteria.** Audit drifting toward an inference call (it must stay zero-inference); scope creep into running a study; the verdict becoming a judgment rather than a file-decidable classification.

## 7. Substitution record

None — ieops default Charter applies.

## 8. Inference regime

**Posture.** `zero-inference` for this horizon's deliverable. The signal-localization audit is deterministic file analysis; it makes no model calls. (The simulator/rater pins — Sonnet sim / Opus rater — apply only to *future* corroboration runs in a later horizon, not to this audit.)

**Required oracle capabilities.** None for the audit.

**Provenance-audit location.** N/A (zero-inference horizon).

## 9. Context budget

**Primary consumer.** Claude Code (operator). Budget per Context Engineering A1: ≤50% effective window.
**Critical-artifact size ceiling.** Any single doc the operator reads end-to-end ≤ ~400 lines; the audit output (`SIGNAL-LOCALIZATION.md`) must fit a single read.
**Edge-placement convention.** Per A2 default (the verdict table and gate conclusion at the top of the generated report).

---

## How to use

1. PL ratifies this envelope (done: 2026-06-16).
2. Operator builds the audit, runs it, produces `SIGNAL-LOCALIZATION.md`.
3. The verdict gate is checked (X.S.core in the plan). The operator returns the verdict to the PL, who selects the next horizon. The operator does not run a measurement matrix under this envelope.
