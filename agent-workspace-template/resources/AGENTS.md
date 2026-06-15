# resources/ — AGENTS.md

This folder holds **static reference material** — research, source documents, templates, worked examples, fact-check material, anything durable and non-executable that supports the work but isn't itself the work.

Distinct from `runbooks/` (procedures — *how to do X*). Distinct from `tmp/` (gitignored scratch). Resources are committed, version-controlled, and meant to stay useful over time.

**Without `resources/`:** durable reference material gets dumped into `tmp/` (gitignored and lost), buried inside one project (where it can't be shared across projects), or kept in the user's head (where it's not durable at all).

## What goes here

- External references you keep coming back to (a style guide, a checklist you didn't write but rely on, a research paper that frames your domain).
- Long-form items pointed to from `observations.md` (policy docs, vendor specs, multi-paragraph rules whose pointer + short rule live in `observations.md`).
- Reusable templates that aren't tied to a single project.
- Worked examples of procedures or formats that benefit from being seen in full.

## What doesn't go here

- **Procedures.** "How to do X" lives in `runbooks/`.
- **Project-specific reference material.** That lives inside the project — see "Recursive pattern" below.
- **Throwaway downloads.** That's `tmp/`.

## Layout

Flat files for single artifacts; subfolders when a topic has multiple companions. Same shape as `tmp/` and `runbooks/`.

```
resources/
├── AGENTS.md
└── style-guide/
    ├── AGENTS.md
    └── tone-examples.md
```

## Recursive pattern

A project folder can have its own `resources/` for project-specific reference material:

```
projects/blog-redesign/
├── AGENTS.md
└── resources/
    ├── competitor-screenshots/
    └── style-references.md
```

This is part of a broader pattern: the workspace shape and the project shape are the same shape, in miniature. A project can carry its own copy of any top-level file (`decisions.md`, `observations.md`, `resources/`, even `runbooks/` for project-specific procedures) when it grows enough to need them. Add them lazily, not preemptively. See `methodology.md` for the full discussion.
