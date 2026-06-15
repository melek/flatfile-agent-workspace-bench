# Workspace Orientation

This is a flat-file workspace designed to make digital work clear, well organized, and stateful across work sessions. It is designed to be useful for both people and LLM agents.

This workspace is best used in a bash-like environment. If on Windows, it is recommended to use WSL and set up this workspace through bash.

## Working alongside inference

Working with an AI agent against a flat-file workspace lowers some costs (orientation, recall, routing) and also exposes some failure modes worth naming in passing: **workplace safety** (errors, bad outputs, wasted time), **system safety** (data loss, risky apps or configs), **privacy** (unintentional data sharing), and **mental health** (sycophancy, misplaced trust, premature cognitive off-loading). The conventions in this workspace — work-product attribution, artifact-bound runbooks, the daybook handoff — are intent, not enforcement. For background, see the [Future of Life Institute](https://futureoflife.org/our-mission/) introductions to AI safety and AI risk.

The workspace declares intent, but it is tool-agnostic — and because workspace text cannot bind a model, enforcement belongs at the tool/plugin layer. As the workspace grows, a need will arise to resolve drift from the methodology — skipped session starts or closures, incorrectly logged items, skipped steps, and invented details all accumulate. Scripts and tool affordances like in-session hooks can be used to enforce the methodology.

## Work-product attribution

Inference-generated work products carry an attribution footer per `methodology.md#work-product-attribution`. Where this applies: under `projects/<name>/` (project work products), under `resources/` (reference reports and summaries), and under `tmp/` (intermediate artifacts in artifact-bound runbook chains; attribution carries forward on promotion to `projects/`). Where this does NOT apply: the logs (`decisions.md`, `observations.md`), daybook entries, project `AGENTS.md` Status sections — those are the agent's internal bookkeeping, and attribution would be uniform and information-free.

## Layout

| Path | What it is | When to write to it |
|---|---|---|
| `methodology.md` | Reference of the frameworks, rationale, and conventions behind this folder's structure and purpose. Consult to orient on correct process. | Only adjust to reflect changes in the workspace's operating methodology. Should not be edited unless there are corresponding alterations to workspace's core files or structure. |
| `decisions.md` | Append-only log of **commitments that constrain future action**. The primary durable memory system. | When a commitment changes what is or isn't allowed going forward. Better than a tool's "memory" so workspace knowledge stays visible outside the tool. |
| `observations.md` | Append-only log of findings that **cost significant inference to arrive at** and would help future-you (or the agent) avoid re-deriving them. | When you notice something the next session would re-derive without this entry. Long reference items live in `resources/`; `observations.md` carries the pointer + the rule. |
| `daybook/YYYY-MM-DD.md` | One file per workday with three sections: **Intent** (top, written when the day's purpose becomes clear), **Log** (middle, accreted through the day), **Handoff** (bottom, written at session close). | Open or create at start of day; add to it throughout; close with the handoff section. |
| `projects/<name>/` | Projects are tasks or areas of interest likely spanning more than one session or that need durable artifact storage. One folder per ongoing project. Each has its own `AGENTS.md` carrying the project's current state — status, goal, context, scope, next steps. Can have their own decision and observation files when appropriate. | When work is project-scoped. See `projects/AGENTS.md` for the per-project convention. |
| `runbooks/` | Procedural knowledge — "how to do X" — for recurring or non-obvious procedures across your work, not just inside one project. Living documents. Flat files for simple procedures; folder + companions when a procedure has templates or scripts. | When you find yourself doing the same procedure more than once, or when a procedure is non-obvious and you'd want a teammate (or future you) to be able to follow it cold. See `runbooks/AGENTS.md`. |
| `resources/` | Static reference material — research, source documents, templates, worked examples, fact-check material. Durable and non-executable. Distinct from `runbooks/` (procedures) and `tmp/` (scratch). | When you have durable reference material that doesn't fit a single project. See `resources/AGENTS.md`. |
| `tmp/` | Gitignored scratch. Intermediate artifacts, search results, downloaded items to be triaged, drafts for non-project work. | When the file is throwaway. **Never** put anything you'd miss in here — it's not committed. If it is in here and you'd miss it, move it into a project. |

Changes to this basic structure should have a corresponding justification in `methodology.md`.

## Daily workflow

Two default runbooks at `runbooks/start-session/` and `runbooks/close-session/` carry the load-bearing rhythm: orient at the start, sweep at the close. Both are **user-invoked** — the agent doesn't detect session boundaries.

### At session start

Run `runbooks/start-session/`. The runbook reads the most recent daybook Handoff (cold-pickup artifact for the next session) and opens today's `daybook/YYYY-MM-DD.md` with an **Intent** line if the user stated one.

Soft invocation: when the user opens with intent-shaped language ("I want to work on...", "today I'm trying to...", "let's start with..."), treat that as the trigger to run `start-session/`. Also invoke explicitly on request.

### As you work

- **Add to today's daybook `Log` as things happen** — interim notes, partial findings, anything worth a second look. The Log is incremental and bidirectional; you can drop in and out throughout the day.
- **Read the previous daybook entry _when something feels unfamiliar_** — the Handoff section is the cold-pickup artifact. If you ran `start-session/`, you've already done this.
- **Search `decisions.md` and `observations.md` during planning.** Actively use the workspace features to enrich context.
- **Store work artifacts in project folders.** Each project folder can carry a briefing in its own `AGENTS.md` plus project-level artifacts reflecting the root (project-scoped decisions, observations, resources, and runbooks) as appropriate to the scale of the project.
- **Use `tmp/` as ad-hoc storage and a staging ground.** If a topic grows into project scale, `mv` it into `projects/<name>/` and add an `AGENTS.md`.

### At session close

Run `runbooks/close-session/`. The runbook writes today's daybook Handoff, appends any decisions and observations that earned their place to the durable logs, and commits.

Soft invocation: when the user signals the session is ending ("end of day", "done for now", "close the session"), treat that as the trigger to run `close-session/`. **Proactively offer** to run it rather than waiting to be asked.

## Canonical strings

To keep `grep` reliable and avoid silent miscategorization, use these exact strings — don't paraphrase.

**Status enums:**

- `decisions.md` entries: `proposed` | `accepted` | `superseded by YYYY-MM-DD — <title>` | `reversed`
- `projects/<name>/AGENTS.md`: `active` | `blocked` | `paused` | `done` | `abandoned`

Do not invent variants (`in-progress`, `shipped`, `stalled`, `complete` — none of these exist).

**Filename patterns:**

- Daybook: `daybook/YYYY-MM-DD.md` (ISO date)
- Project / runbook / `tmp/` subfolder names: lowercase kebab-case

**Heading slugs for cross-reference anchors:**

For decisions and observations entries, the heading should start with the ISO date so the GitHub-rendered anchor is stable and greppable: `## 2026-05-15 — Short title`. Avoid em-dashes inside the title where possible — they slugify unpredictably across renderers. The cross-reference convention in `methodology.md` assumes anchors of the form `decisions.md#YYYY-MM-DD-short-title`.

## Cross-tool note

This workspace is tool-agnostic. The conventions live in the files; the tool just executes them. Nothing here depends on any specific assistant's memory, plugins, or proprietary state, and strong LLM agents should prioritize the methodology when working.

Most agents auto-read `AGENTS.md` on entering a folder. Claude Code reads `CLAUDE.md` instead — so every folder here ships a one-line `CLAUDE.md` that imports its `AGENTS.md` (`@AGENTS.md`). Both kinds of agent get the same layered context; the `CLAUDE.md` files carry no content of their own. If you add a folder with an `AGENTS.md`, add the passthrough `CLAUDE.md` beside it.

## When in doubt

Read `methodology.md`. It explains the *why* behind every convention here. If the user asks "why are we doing it this way?" — that's where the answer lives.
