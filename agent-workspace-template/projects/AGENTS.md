# projects/ — AGENTS.md

This folder holds **one subfolder per ongoing project**. Every project folder has its own `AGENTS.md` carrying the current state of the project — so any human or agent entering the folder cold can pick it up.

## Why `AGENTS.md` and not `README.md`

Two reasons. First, AI tools auto-load `AGENTS.md` on folder entry — putting project state there means an agent working in a project gets oriented automatically. Second, in this workspace the file *is* agent orientation: it tells whoever enters what the project is and where it stands. That matches `AGENTS.md`'s purpose better than `README.md`'s (which traditionally documents how to install or use software).

The file's role depends on its folder. At the workspace root, `AGENTS.md` carries conventions. In a project folder, it carries the project's current state. Same name, different work — by design.

## Layout

```
projects/
├── <project-name>/
│   ├── AGENTS.md          # required — project context, scope, status
│   ├── ...                # whatever the project needs (notes, drafts, data, code)
│   └── decisions.md       # optional — project-local ADRs that don't deserve a top-level entry
└── <another-project>/
    └── AGENTS.md
```

Project names are short, lowercase, kebab-case (`blog-redesign`, `tax-2025`, `home-renovation`).

## The project `AGENTS.md`

Every project folder has one. Minimum sections:

```markdown
# <Project Name>

**Status:** active | blocked | paused | done | abandoned

**Started:** YYYY-MM-DD
**Goal:** One sentence — what does "done" look like?

## Context
Why this project exists. What problem it solves. Anything a fresh reader (or new agent) needs to know to be useful.

## Scope
What's in. What's explicitly out. Boundaries.

## Status / where we are now
What's done, what's in progress, what's blocked. Update this whenever the state changes meaningfully.

## Next steps
The next concrete action(s). When this is empty, the project is either done or paused. Where possible, write these as a small decision tree (if X happens, do Y; if Y, do Z) — that survives weeks of absence better than a single-shot "do this next."
```

This file is **not** append-only — it's meant to be the current state of the project, in one place. Update it as the project evolves.

## When to create a project

When work has:

- A goal you could state in a sentence
- More than one session's worth of material
- Files or decisions that would clutter the root if left there

If something doesn't meet those, it's not a project yet. Capture it in `observations.md`, today's daybook, or `tmp/<topic>/` and see if it grows.

## When a project ends

- **Done:** mark `Status: done` in the project's `AGENTS.md`, summarize outcomes, write an ADR in the top-level `decisions.md` if the outcome matters beyond the project. Leave the folder in place — it's history.
- **Abandoned:** mark `Status: abandoned`, note why. Also leave in place. Future-you will want to know it was tried.

If the active project list gets unwieldy (more than ~10 entries), create `projects/archive/` and move completed/abandoned projects in. Each archived project's `AGENTS.md` still tells the story.

## Project-local copies of workspace files

A project can carry its own copy of any top-level file when it grows enough to need it. Add them lazily, not preemptively:

- `projects/<name>/decisions.md` — project-internal ADRs that don't affect the broader workspace. Same template as the top-level `decisions.md`.
- `projects/<name>/observations.md` — patterns scoped to this project.
- `projects/<name>/resources/` — project-specific reference material (research, source docs, fact-check material).
- `projects/<name>/runbooks/` — procedures scoped to this project (e.g. `runbooks/deploy.md` for a blog project).

Cross-reference between project-local and top-level files when relevant. The workspace shape and the project shape are the same shape, in miniature — see `methodology.md#the-workspace-as-project-pattern`.

## What goes in here vs. in `tmp/`

- **In a project:** anything you'd want to find again, anything the project needs to make sense.
- **In `tmp/`:** scratch, intermediate artifacts, drafts you might throw away. `tmp/` is gitignored — files there don't survive. If a `tmp/<topic>/` subfolder turns out to be durable, `mv tmp/<topic> projects/<topic>` and add an `AGENTS.md`.
