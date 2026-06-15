# Methodology

*The "why" behind this workspace. Templates and formats live inside the files they govern — this document only explains the reasoning.*

## Goal

A minimalist, tool-agnostic AI workspace suitable for real work. The template is a **seed** — minimal and opinionated. It carries the load-bearing pieces; extension is expected, either organically (the user adds files and runbooks as patterns settle) or through plugins (scripts, scoring hooks, automation that enforce the discipline the methodology only declares).

Most users will operate the workspace through an AI agent; the same shape stands up to a disciplined human or stock tools like `vim` and `grep`. The methodology declares intent; if drift becomes a problem, tooling at the plugin or hook layer is where enforcement lives.

## Operating principles

The intention is a system that would be tedious for most people to keep up with manually, but gives rich instructions for an LLM to operate it for you.

- **Flat files + git.** Every artifact is plain markdown. Daily commits are the revision history; `git log` is the audit trail. No proprietary formats, no database, no hidden indexes.
- **Tool-agnostic.** Everything lives locally in plain files. You can switch AI tools, drop the agent entirely, or pick up your work on a machine with stock applications. Nothing depends on any vendor's memory system.
- **Incremental and drop-in.** Discipline must survive a busy week. Workflows you can drop in and out of (open daybook, add a line, leave) survive; workflows that require clean starts and clean ends don't.
- **Scratch is allowed but never trusted.** `tmp/` is gitignored. If you'd miss it, move it to a project or a top-level log. The gitignore is structural pressure to commit what matters.
- **Intent, not enforcement.** The workspace declares the shape of good practice; it doesn't enforce it. Where enforcement matters (followup hygiene, close-session discipline, drift detection), use scripts or tool affordances at the plugin layer.

Each file's own rules (append-only — new entries go at the bottom, old entries never get edited — and what belongs in `decisions.md`, the catch-all role of the daybook Log) live with that file. See "What each file is for" below.

A note on the word **artifact**: throughout this workspace it means "a concrete file the work produces" — a daybook entry, an ADR, a draft, a scan output. In the runbook discussion below it has a sharper sense: each step in a runbook should produce a *named artifact on disk* so the next step has something specific to read.

## Where the formats live

Templates and field-level conventions live inside the files they govern. This document only explains the *why*; for the *how*, open the file:

- ADR template + supersession rule → `decisions.md` header
- Observation entry shape → `observations.md` header
- Daybook sections + naming → `daybook/AGENTS.md`
- Per-project `AGENTS.md` skeleton → `projects/AGENTS.md`
- Procedure template + when to use runbooks → `runbooks/AGENTS.md`

## What each file is for

- **`decisions.md`** is the primary durable memory system. It records commitments that constrain future action. A future reader asking "wait, are we allowed to do X?" should find the answer here, not by reading every daybook. Pairing this log with the tool's built-in memory (if any) keeps workspace knowledge visible outside the tool.
- **`observations.md`** is the optional second log. It records findings that **cost significant inference to arrive at** — things that would force the next session to re-derive a hard-won rule, a domain gotcha, a non-obvious framing. The bar is utility-shaped: would future-you (or the agent) waste time deriving this again? If yes, save it. Long reference items (policies, vendor docs, multi-paragraph specs) live in `resources/`; `observations.md` carries the pointer + the rule. Expect sparse use; quality over quantity.
- **`daybook/`** is the chronological working surface. One file per workday, three sections (Intent / Log / Handoff). The Log absorbs everything that doesn't yet have a home in one of the other files; the Handoff is the cold-pickup artifact for the next session.
- **`projects/<name>/`** holds anything spanning multiple sessions. Each project's `AGENTS.md` is the single-pane current state — the rest of the project folder is the working material. The file's role depends on its folder: at the workspace root, `AGENTS.md` carries conventions; in a project, it carries project state.
- **`runbooks/`** holds procedural knowledge — "how to do X" — for recurring or non-obvious procedures. Two defaults ship with the workspace: `start-session/` (user-invoked orientation, one load-bearing step: read the most recent daybook handoff) and `close-session/` (user-invoked end-of-session sweep: write the daybook Handoff, append decisions, commit). Both are minimal seeds; the user is expected to extend them as the workspace's patterns settle. Per-repo conventions and project-specific procedures are also common runbook content.
- **`resources/`** holds static reference material — research, source documents, templates, worked examples, fact-check material, and the long-form items pointed to from `observations.md`. Durable and non-executable.

**Forward-task tracking is deliberately not a default file.** Some users want a structured backlog; some prefer querying the daybook handoffs + external trackers; some install a planner plugin. The seed leaves this layer open rather than pre-committing to a format — add it the way that fits your workflow.

## Work-product attribution

Distinguish *internal records* from *work products*:

- **Internal records** — `decisions.md`, `observations.md`, daybook entries, project `AGENTS.md` Status sections. These are the agent's bookkeeping as it operates the workspace. Attribution would say "inference" on virtually every line and add no information, so the seed does not carry per-entry attribution on these files.
- **Work products** — reports, deliverables, analyses, drafts that a human will act on at real stakes. These benefit from attribution because the reader needs to know what they're consuming.

For inference-produced work products, end the file with one of these two footers (one line, at the bottom of the file):

- `Report assembled by inference` — autonomous agent output, single-pass, no interactive revision.
- `Report assembled by inference with interactive revision` — used when revision has materially changed findings, recommendations, or framing (not typo fixes).

Where this applies: under `projects/<name>/` (project work products), under `resources/` (reference reports and summaries), and under `tmp/` (intermediate artifacts in artifact-bound runbook chains; the attribution carries forward when content is promoted to `projects/`).

The two-grade pattern is the seed default. Users can extend it (a richer four-degree taxonomy keyed on source canonicity is one option) but the seed prescribes only the two grades.

## Undocumented files in the workspace

Agents may encounter files in the workspace that are not described in any `AGENTS.md` — legacy from older workspace versions, user-added, generated by other tools, dropped in by another agent or skill. Treat them as **user-curated state**: read them, consult `git log` if available to understand intent, respect their content as part of the workspace's lived state. Do not delete or ignore them. If a file's purpose is unclear from contents alone, surface the question to the user rather than guessing.

## The workspace-as-project pattern

The workspace shape and the project shape are the same shape, in miniature. A project folder can carry its own copy of any of the top-level files when it grows enough to need them:

- `projects/<name>/AGENTS.md` — required (current state).
- `projects/<name>/decisions.md` — optional, for project-local ADRs that don't affect the broader workspace.
- `projects/<name>/observations.md` — optional, for project-scoped findings worth saving from re-derivation.
- `projects/<name>/resources/` — optional, for project-specific static reference.
- `projects/<name>/runbooks/` — optional, for procedures scoped to one project (e.g., per-repo contribution norms).

Add these lazily, not preemptively. A short-lived project usually needs only an `AGENTS.md`; a long-running one picks up the other files as the need arises. The recursion is permission, not a checklist.

## Runbook discipline: artifact-binding

**Plain runbooks and skills are hope-and-see.** Nothing physically prevents the LLM from skipping a step, summarizing instead of doing, or claiming completion without producing the work. Under load, that's what happens. The ideal fix is deterministic scripts that gate each step; this template skips scripts to keep complexity low. The middle ground that costs nothing: **design runbooks so every step produces a concrete artifact, and the next step reads it.** If step 3 was supposed to write `tmp/foo/draft.md` and the file isn't there, step 4 stalls visibly instead of drifting silently — the same chunking Claude Code's planner uses.

If you have critical workflows where skipping steps has serious consequences, **don't use inference to run them.** A well-validated deterministic script is better than either an LLM or a human performing critical procedures.

## Threats to the workspace pattern

This workspace makes some uses of an AI agent easier and lower-friction. That same lowered friction is a documented risk surface. Two well-supported findings from the EA literature shape what to watch for:

- **Proactive assistance reduces user confidence in own judgment.** When an assistant surfaces context, drafts decisions, or pre-empts the user's reasoning, the user's confidence in their own framing decays over time ([@tabalba2024]). The mitigation is not to remove proactive assistance — that defeats the workspace's value — but to keep work products **attribution-marked and falsifiable** (see *Work-product attribution* above): when the agent produces a deliverable a human will act on, the attribution footer names the human's involvement, and the work itself should be cheap to verify.
- **AI assistants reinforce confirmation bias when they mirror users.** Assistants tuned to be agreeable converge on the user's framing, even when the framing is wrong, especially on judgment calls ([@pilli2026]). The mitigation surface lives at the tooling layer — scoring hooks that flag ratification-shaped output, scripts that periodically inject a "what's the strongest counter-argument" prompt, or review rituals the user can layer on. The workspace itself doesn't enforce this; it ships work-product attribution so plugins or careful review *can* trace patterns across artifacts.

Both risks compound over time. The workspace's accumulation properties (decisions.md, observations.md building up over months) make these risks larger, not smaller — the further back agent-produced content extends, the harder it is for the user to re-litigate whether the framing was theirs or the assistant's. The seed's low-cost mitigation is work-product attribution; richer enforcement (failure-mode flagging, ratification scoring, separate-doing-from-reporting patterns for high-stakes work) lives at the plugin layer.

The workspace cannot fully mitigate the broader concerns this risk surface implies — provenance-of-thought, decision-fluency conflated with quality, longitudinal de-skilling. These are named here, not solved.

## Single-agent vs. multi-agent

The workspace shape, as written, is single-agent by default: one agent operates one workspace at a time. The recursive pattern (a project folder carrying its own `AGENTS.md`, `decisions.md`, `runbooks/`) is the natural extension point if multi-agent operation becomes useful — each project folder can be operated by a separate sub-agent reading that folder's `AGENTS.md`, without coordination at the root.

This is design space, not a recommendation. Multi-agent setups that have been catalogued in the literature ([@loffredo2026] EKA, [@jyothi2026] MCP multi-agent) generally trade lower per-step complexity for higher coordination cost; whether that trade pays depends on how project-scoped the user's work actually is. For one user juggling 3–5 small projects, the single-agent shape is probably right. For larger teams or larger projects with truly orthogonal sub-work, the per-project sub-agent shape is worth considering. The workspace's root structure does not prevent either choice.

## Cross-reference convention

Use relative paths with optional section anchors:

- File: `decisions.md`
- Section: `decisions.md#2026-05-15-short-title`
- Cross-folder: `projects/foo/AGENTS.md#status`

Avoid absolute paths and wiki-style `[[links]]` — relative paths render cleanly in any editor, and in `grep` output.

## Review cadence

To keep the logs from becoming graveyards (all optional; run when it pays off, not on a calendar):

- Skim `decisions.md` for ADRs whose status is now stale or superseded.
- Skim `daybook/`. Roll up significant entries into a milestone note in `decisions.md` if a meaningful chunk of work shipped. Older daybooks stay as-is — they're append-only history.
- Skim `projects/`. Anything finished or abandoned should be noted in `decisions.md` and either left in place (cold storage) or moved to a `projects/archive/` subfolder if the active list gets unwieldy.

If this kind of review needs to happen on a schedule rather than ad-hoc, that's a candidate for a custom runbook (and possibly tooling that pings you when the cadence slips).
