# runbooks/ — AGENTS.md

This folder holds **procedural knowledge** — how to do recurring or non-obvious things in this workspace and in your work more broadly. Operations / on-call style runbooks, written for any human or agent to follow cold.

Runbooks are **living documents.** Update them as the procedure evolves; git tracks the history.

**Without `runbooks/`:** every recurring procedure gets reinvented or re-asked of the agent each time. Quality drifts because there's no stable reference. The agent does a slightly different weekly review every Friday; the new collaborator can't follow your tax-filing process because it lives in your head; the recovery-from-broken-state procedure has to be improvised under stress.

## Layout

Default to flat markdown — one file per procedure:

```
runbooks/
├── AGENTS.md
├── weekly-review/      # folder shape, has companion files
│   ├── AGENTS.md       # the procedure
│   └── template.md
├── onboard-collaborator.md
└── tax-filing-q1.md
```

Promote a single-file procedure to a folder when it grows companions — a template, a checklist, an example output, a script. Same pattern `tmp/` uses for staging.

Procedure names are short, lowercase, kebab-case, action-shaped (`weekly-review`, `onboard-collaborator`, `recover-from-abnormal-exit`).

## When to use `runbooks/`

- Procedures that recur or might be repeated by someone else (or future-you who has forgotten).
- Cross-cutting "how to do X" knowledge that isn't tied to one project.
- Rituals — weekly review, monthly retro, quarterly planning.
- Recovery procedures — what to do when something goes wrong.

## When *not* to use `runbooks/`

- **Project-specific procedures** belong inside the project. If only the blog-redesign project knows how to deploy, that's `projects/blog-redesign/deploy.md`, not a runbook.
- **Workspace conventions** belong in `methodology.md`. Runbooks are about *doing things in domains*; methodology is about *how the workspace itself works*.
- **One-off how-to-do-X** that you won't repeat. That's a daybook Log entry, not a runbook.

## Procedure template

A runbook (single file or folder `AGENTS.md`) looks like this:

```markdown
# <Procedure Name>

**When to run:** Trigger condition — schedule (weekly Friday), event (project ends), or on-demand.

**Inputs:** What you need before starting — files, access, state.

**Outputs:** What this produces — files, decisions logged, followups created.

## Steps

1. ... → produces `<artifact-path>`
2. (reads the artifact from step 1) ... → produces `<artifact-path>`
3. ...

## Notes (optional)

Gotchas, common variations, what to do if a step fails.
```

## Artifact-binding is the default, not the discipline

Every runbook step that has a verifiable output **ships with an explicit `→ produces <artifact-path>` marker**. This is the default shape, not the strict one. A step that would otherwise read "synthesize the findings" reads "synthesize the findings into `tmp/<runbook>/<step>.md`" — the file path is part of the step.

If a step legitimately has no verifiable artifact (a judgment call, a decision-as-call, a thinking-only synthesis), the step **names what makes it complete** in place of the artifact: `→ recorded under "Go/No-go decision" in <file>` or `→ counts as complete when <condition>`. This is the escape hatch, and it is rare. The default carries.

Under load, LLMs tend to skip ahead, summarize a step instead of doing it, or claim completion without producing the work. If step 3 was supposed to write `tmp/<topic>/draft.md` and the file isn't there, step 4 has nothing to read and the procedure stalls visibly rather than drifting silently. The artifact is the inspection point.

Runbooks built this way pick up gracefully into planning affordances when an agent supports them, and stand on their own as prompts that tell the LLM to follow the procedure one step at a time without skipping. See `methodology.md#runbooks-vs-agent-skills` for the full rationale.

## Performative confirmation: the Leveson-style risk

The shape of a runbook step matters as much as its content. A step that *looks like* a check but produces no friction is worse than no check at all — it consumes attention while letting the work it was supposed to catch slip through. (This is the same control-structure failure mode Nancy Leveson catalogues in safety engineering: a check is only protective if it can fail and the failure is visible.)

Two patterns mitigate this failure mode and are recommended whenever a step would otherwise be a soft confirmation:

- **Artifact-binding.** The step produces an inspectable file. The user (or a future session) can read what was actually produced and notice if it was hollow. A step that reads "consider whether to ship" is performative; a step that reads "write the Go/No-go call with reasoning into `tmp/release-readiness/<release>/checklist.md`" is not.
- **Force-disagreement.** The step requires the agent to articulate a credible counter-position grounded in the same artifacts. A ratification step where the agent owes a counter-position cannot quietly ratify — see the Force disagreement step in `runbooks/weekly-review/AGENTS.md` for the worked pattern.

If a step in a runbook reads like "check that things are OK" or "review for issues" without an artifact or a counter-position, treat it as a smell. Rewrite the step until it can fail visibly.

## Promoting a single file to a folder

If `runbooks/weekly-review.md` grows a template, rename it:

```bash
mkdir runbooks/weekly-review
mv runbooks/weekly-review.md runbooks/weekly-review/AGENTS.md
# add the template alongside
```

The procedure file becomes `AGENTS.md` so it auto-loads when an agent enters the folder.
