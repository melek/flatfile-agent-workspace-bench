# Methodology

*The "why" behind this workspace. Templates and formats live inside the files they govern — this document only explains the reasoning.*

## Goal

A minimalist, tool-agnostic AI workspace suitable for real work. Most users will operate it through an AI agent that enforces the methodology; the same shape also stands up to a disciplined human or stock tools like `vim` and `grep`.

## Operating principles

The intention is a system that would be tedious for most people to keep up with manually, but gives rich instructions for an LLM to operate it for you. The agent's job is enforcing the methodology, not leaving you with a mess.

- **Flat files + git.** Every artifact is plain markdown. Daily commits are the revision history; `git log` is the audit trail. No proprietary formats, no database, no hidden indexes.
- **Tool-agnostic.** Everything lives locally in plain files. You can switch AI tools, drop the agent entirely, or pick up your work on a machine with stock applications. Nothing depends on any vendor's memory system.
- **Incremental and drop-in.** Discipline must survive a busy week. Workflows you can drop in and out of (open daybook, add a line, leave) survive; workflows that require clean starts and clean ends don't.
- **Scratch is allowed but never trusted.** `tmp/` is gitignored. If you'd miss it, move it to a project or a top-level log. The gitignore is structural pressure to commit what matters.

Each file's own rules (append-only — new entries go at the bottom, old entries never get edited — and the strict bar for `decisions.md`, the catch-all role of the daybook Log) live with that file. See "What each file is for" below.

A note on the word **artifact**: throughout this workspace it means "a concrete file the work produces" — a daybook entry, an ADR, a draft, a scan output. In the runbook discussion below it has a sharper sense: each step in a runbook should produce a *named artifact on disk* so the next step has something specific to read.

## Where the formats live

Templates and field-level conventions live inside the files they govern. This document only explains the *why*; for the *how*, open the file:

- ADR template + supersession rule → `decisions.md` header
- Observation entry shape → `observations.md` header
- Followup entry shape and lifecycle → `followups.md` header
- Daybook sections + naming → `daybook/AGENTS.md`
- Per-project `AGENTS.md` skeleton → `projects/AGENTS.md`
- Procedure template + when to use runbooks → `runbooks/AGENTS.md`

## What each file is for

- **`decisions.md`** records commitments that constrain future action. A future reader asking "wait, are we allowed to do X?" should find the answer here, not by reading every daybook.
- **`observations.md`** records descriptive patterns — how things tend to go, framings worth re-recognizing. Lower bar than decisions; not prescriptive.
- **`followups.md`** holds forward commitments (asks, expected replies, things to chase). Distinct from the reflective files because it's not append-only — items close when the loop closes — and because forward-commitment management is its own discipline.
- **`daybook/`** is the chronological working surface. One file per workday, three sections (Intent / Log / Handoff). The Log absorbs everything that doesn't yet have a home in one of the other files; the Handoff is the cold-pickup artifact for the next session.
- **`projects/<name>/`** holds anything spanning multiple sessions. Each project's `AGENTS.md` is the single-pane current state — the rest of the project folder is the working material. The file's role depends on its folder: at the workspace root, `AGENTS.md` carries conventions; in a project, it carries project state.
- **`runbooks/`** holds procedural knowledge — "how to do X" — for recurring or non-obvious procedures across your work, not just inside one project. Living documents (not append-only); git tracks revisions. Project-specific procedures stay inside the project, not here.
- **`resources/`** holds static reference material — research, source documents, templates, worked examples, fact-check material. Durable and non-executable. Distinct from `runbooks/` (procedures) and `tmp/` (scratch).

## The workspace-as-project pattern

The workspace shape and the project shape are the same shape, in miniature. A project folder can carry its own copy of any of the top-level files when it grows enough to need them:

- `projects/<name>/AGENTS.md` — required (current state).
- `projects/<name>/decisions.md` — optional, for project-local ADRs that don't affect the broader workspace.
- `projects/<name>/observations.md` — optional, for patterns scoped to one project.
- `projects/<name>/resources/` — optional, for project-specific static reference.
- `projects/<name>/runbooks/` — optional, for procedures scoped to one project.

Add these lazily, not preemptively. A short-lived project usually needs only an `AGENTS.md`; a long-running one picks up the other files as the need arises. The recursion is permission, not a checklist.

## Runbook discipline: artifact-binding

**Plain runbooks and skills are hope-and-see.** Nothing physically prevents the LLM from skipping a step, summarizing instead of doing, or claiming completion without producing the work. Under load, that's what happens. The ideal fix is deterministic scripts that gate each step; this template skips scripts to keep complexity low. The middle ground that costs nothing: **design runbooks so every step produces a concrete artifact, and the next step reads it.** If step 3 was supposed to write `tmp/foo/draft.md` and the file isn't there, step 4 stalls visibly instead of drifting silently — the same chunking Claude Code's planner uses.

If you have critical workflows where skipping steps has serious consequences, **don't use inference to run them.** A well-validated deterministic script is better than either an LLM or a human performing critical procedures.

## Provenance markers

Entries in this workspace's registers (`decisions.md`, `observations.md`, daybook entries, project status sections) carry a `**Generated-by:** inference | user | mixed` marker. The marker records who actually produced the entry. The agent that drafts on the user's behalf marks `inference`; the user typing themselves marks `user`; collaborative entries where the agent drafted and the user materially revised mark `mixed`.

The marker uses the word **inference**, not "drafted." Inference is calculation with intentional and unintentional randomness; it is not a creative act. Calling agent-produced content "drafted" mistakes token production for authorship. Future-you (or a new collaborator) reading the file should know whether they are reading the user's thinking, the agent's calculation, or some combination — that judgment is part of the file's value.

This marker is small, structural, and easy to skim. It does not gate workflow; the workspace functions whether or not the marker is present. But absent it, agent-produced records become indistinguishable from user-produced ones on quick re-read, which is the exact condition the SLR flagged as the rubber-stamping risk surface ([@tabalba2024], [@pilli2026]).

## Threats to the workspace pattern

This workspace makes some uses of an AI agent easier and lower-friction. That same lowered friction is a documented risk surface. Two well-supported findings from the EA literature shape what to watch for:

- **Proactive assistance reduces user confidence in own judgment.** When an assistant surfaces context, drafts decisions, or pre-empts the user's reasoning, the user's confidence in their own framing decays over time ([@tabalba2024]). The mitigation is not to remove proactive assistance — that defeats the workspace's value — but to keep agent-produced content **provenance-marked and falsifiable**: the user must be able to tell what came from the agent, and the agent must produce work the user can verify cheaply.
- **AI assistants reinforce confirmation bias when they mirror users.** Assistants tuned to be agreeable converge on the user's framing, even when the framing is wrong, especially on judgment calls ([@pilli2026]). The mitigation is the **Force disagreement** step in the weekly review and the **performative-confirmation** rule in `runbooks/AGENTS.md`: review rituals that require articulating a credible counter-position, not just ratifying agent output.

Both risks compound over time. The workspace's accumulation properties (decisions.md, observations.md building up over months) make these risks larger, not smaller — the further back agent-produced content extends, the harder it is for the user to re-litigate whether the framing was theirs or the assistant's. Treat the provenance marker as the low-cost mitigation that scales.

See the EA practices review at `~/research/ea-practices-for-ai-assistants/review.md §3.2.7` for the broader catalog of concerns the workspace cannot fully mitigate (provenance-of-thought, decision-fluency conflated with quality, longitudinal de-skilling). These are not solved here; they are named.

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

To keep the logs from becoming graveyards:

- **Weekly:** skim `decisions.md` for ADRs whose status is now stale or superseded. Update statuses. Skim `followups.md` and chase anything quiet.
- **Monthly:** skim `daybook/`. Roll up significant ones into a milestone note (e.g. `decisions.md` entry: "what shipped in May"). Older daybooks stay as-is — they're append-only history.
- **Quarterly:** skim `projects/`. Anything finished or abandoned should be noted in `decisions.md` and either left in place (cold storage) or moved to a `projects/archive/` subfolder if the active list gets unwieldy.
