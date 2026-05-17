# Workspace Orientation

This is a flat-file workspace designed to make digital work clear, well organized, and stateful across work sessions. It is designed to be useful for both people and LLM agents.

This workspace is best used in a bash-like environment. If on Windows, it is recommended to use WSL and set up this workspace through bash.

## Working alongside inference

This workspace lowers the cost of working with an AI agent. It also lowers the cost of three documented failure modes — **system safety** (agent acting on stale or out-of-scope state), **privacy** (agent records that leak when shared), and **sycophancy** (agent ratifying weak rationales). Mitigations are built in: provenance markers on register entries, artifact-bound runbooks, and a force-disagreement step in the weekly review. For background, see the [Future of Life Institute](https://futureoflife.org/) introductions to AI safety and AI risk.

## Layout

| Path | What it is | When to write to it |
|---|---|---|
| `methodology.md` | Reference of the frameworks, rationale, and conventions behind this folder's structure and purpose. Consult to orient on correct process. | Only adjust to reflect changes in the workspace's operating methodology. Should not be edited unless there are corresponding alterations to workspace's structure. |
| `decisions.md` | Append-only log of **commitments that constrain future action**. Tool-agnostic, durable. Strict bar — not every choice is a decision. | When a commitment changes what is or isn't allowed going forward. If it's not a commitment, it's probably an observation. |
| `observations.md` | Append-only descriptive notes. Norms, patterns, framings, half-formed thoughts that aren't commitments. | When you notice something worth keeping but it's not a "we decided X" — closer to "this is how it tends to go". |
| `followups.md` | Tickler / waiting-on log. Outstanding asks, expected replies, things to chase. The most-used forward-commitment surface. | When you've sent a request, made a delegation, or set an expectation that needs to come back. Include who, when sent, and expected-by. |
| `daybook/YYYY-MM-DD.md` | One file per workday with three sections: **Intent** (top, written when the day's purpose becomes clear), **Log** (middle, accreted through the day), **Handoff** (bottom, written before end-of-day commit). | Open or create at start of day; add to it throughout; close with the handoff section. |
| `projects/<name>/` | Projects are tasks or areas of interest likely spanning more than one session or that need durable artifact storage. One folder per ongoing project. Each has its own `AGENTS.md` carrying the project's current state — status, goal, context, scope, next steps. Can have their own decision and observation files when appropriate. | When work is project-scoped. See `projects/AGENTS.md` for the per-project convention. |
| `runbooks/` | Procedural knowledge — "how to do X" — for recurring or non-obvious procedures across your work, not just inside one project. Living documents. Flat files for simple procedures; folder + companions when a procedure has templates or scripts. | When you find yourself doing the same procedure more than once, or when a procedure is non-obvious and you'd want a teammate (or future you) to be able to follow it cold. See `runbooks/AGENTS.md`. |
| `resources/` | Static reference material — research, source documents, templates, worked examples, fact-check material. Durable and non-executable. Distinct from `runbooks/` (procedures) and `tmp/` (scratch). | When you have durable reference material that doesn't fit a single project. See `resources/AGENTS.md`. |
| `tmp/` | Gitignored scratch. Intermediate artifacts, search results, downloaded items to be triaged, drafts for non-project work. | When the file is throwaway. **Never** put anything you'd miss in here — it's not committed. If it is in here and you'd miss it, move it into a project. |

Changes to this basic structure should have a corresponding justification in `methodology.md`.

## Core workflow discipline

### As you work

1. **Open today's daybook entry.** Create `daybook/YYYY-MM-DD.md` if it's not there, or open the existing one. Drop a line under **Intent** when the day's purpose becomes clear. Add to the **Log** section throughout the day as things happen — interim notes, partial findings, anything worth a second look. The log is incremental and bidirectional; you can drop in and out at any point.
2. **Scan `followups.md`.** Quick pass for anything overdue or due today. Don't wait for a ritual moment — do it when you're between threads.
3. **Read the previous daybook entry _when something feels unfamiliar_.** Not as a morning ceremony. The handoff section of yesterday's daybook is there for when you (or the agent) think "wait, where did we leave off with X?" — not as required reading.
4. **Store work artifacts in project folders.** Each project folder can contain a briefing in its own `AGENTS.md` plus project-level artifacts and organization.
5. **Use `tmp/` as ad-hoc storage and a staging ground for potential projects.** If a topic or task grows into project scale, name it a project and move the files into a new project folder.

### At end of each working session

1. **Write the handoff section** at the bottom of today's `daybook/YYYY-MM-DD.md`: what got done, what's left, blockers, where to pick up next time. See `daybook/AGENTS.md` for the template.
2. **Log commitments.** If anything that constrains future action was decided today, append an entry to `decisions.md`. The bar is strict — not every choice is a decision.
3. **Capture observations.** Anything descriptive worth keeping beyond the daybook → `observations.md`. Good place for "maybe later" ideas to reckon with in a future session.
4. **Update `followups.md`.** New asks you've made, items that came back, items that should now move to a project.
5. **Commit.** `git add . && git commit -m "<short summary / headline for the day's work>"`. The commit history is the local recovery and history layer.

If you are an LLM agent running at end-of-day, **proactively offer** to write the handoff section. Don't wait for the user to remember.

## Canonical strings

To keep `grep` reliable and avoid silent miscategorization, use these exact strings — don't paraphrase.

**Status enums:**

- `decisions.md` entries: `proposed` | `accepted` | `superseded by YYYY-MM-DD — <title>` | `reversed`
- `projects/<name>/AGENTS.md`: `active` | `blocked` | `paused` | `done` | `abandoned`
- `followups.md` status (optional, free-text but prefer): `chased once` | `escalated` | `blocked on <X>`

Do not invent variants (`in-progress`, `shipped`, `stalled`, `complete` — none of these exist).

**Filename patterns:**

- Daybook: `daybook/YYYY-MM-DD.md` (ISO date)
- Weekly review output: `projects/weekly-review/YYYY-WW.md` (ISO week, e.g. `2026-W20.md`)
- Project / runbook / `tmp/` subfolder names: lowercase kebab-case (`blog-redesign`, `weekly-review`, `acme-robotics-deal`)

**Heading slugs for cross-reference anchors:**

For decisions and observations entries, the heading should start with the ISO date so the GitHub-rendered anchor is stable and greppable: `## 2026-05-15 — Short title`. Avoid em-dashes inside the title where possible — they slugify unpredictably across renderers. The cross-reference convention in `methodology.md` assumes anchors of the form `decisions.md#YYYY-MM-DD-short-title`.

## Cross-tool note

This workspace is tool-agnostic. It works the same whether the agent is Claude Code, OpenCode, Codex CLI, Aider, or anything else that reads `AGENTS.md`. The conventions live in the files; the tool just executes them. Nothing here depends on any specific assistant's memory, plugins, or proprietary state, and strong LLM agents should prioritize the methodology when working.

## When in doubt

Read `methodology.md`. It explains the *why* behind every convention here. If the user asks "why are we doing it this way?" — that's where the answer lives.

If you haven't already, also read `resources/workspace-workflow-example.md`. It walks through one situation routing across all four top-level files (`decisions.md`, `observations.md`, `followups.md`, daybook) so you can see how the files interlock. The example is in B2B SaaS framing but explicitly translates to other domains — don't let the example's flavor dictate yours.
