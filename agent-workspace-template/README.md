# Flat-File Workspace Template

A self-documenting workspace for doing real work with an AI assistant — humans and agents alike. No proprietary tools, no databases, no hidden state. Just plain files and folders, with conventions documented in plain text.

The whole workspace is designed so that a person — or an AI agent — can open any folder without prior context and figure out how to use it from the `AGENTS.md` file inside.

## Get started

You're looking at a fresh workspace. Four steps to put it to work:

1. **Open the folder in an AI coding assistant.** [Claude Code](https://claude.com/claude-code) and [OpenCode](https://opencode.ai) are terminal apps with their own quick-start guides — install one, then `cd` into this folder and launch it there. The workspace does little on its own; an agent operates it.
2. **Make it a git repo.** The workspace uses git history as its audit trail — the close-session runbook commits at the end of each day. Simplest path: ask the agent you just opened, *"initialize this folder as a git repo and make a first commit."* To do it yourself:
   ```bash
   git init && git add . && git commit -m "Initial workspace"
   ```
   No git installed? Get it from [git-scm.com/downloads](https://git-scm.com/downloads). *(Created with `create-workspace.py`? Already done — skip this step.)*
3. **Orient the agent.** Ask it: *"Read `AGENTS.md` and tell me how to start."* It reads the conventions and walks you through the rest.
4. **See it working.** The worked example at [`daybook/0000-00-00-example.md`](daybook/0000-00-00-example.md) shows the system mid-use; [`methodology.md`](methodology.md) explains why it is shaped this way. Skim both before judging the workspace — in five minutes of manual reading much of it looks like overhead; the value shows when an agent operates it across sessions. Delete the example daybook once you've written your first real entry.

On Windows, work inside [WSL](https://learn.microsoft.com/windows/wsl/install) — some runbook steps assume a bash-like shell.

## How this works

The LLM is your administrative assistant for this workspace. It reads `AGENTS.md` files on folder entry, follows the conventions documented there, and translates between what you do in plain language and what the system records. You can write entries yourself, but you usually won't — the agent drafts handoffs, logs decisions when you make them, updates project state when something moves. Your job is to do the work and review what the agent recorded.

This methodology is aspirational for a manual user — daily handoffs, append-only logs, and a session-bookend rhythm are hard to keep up by hand. The point of the workspace is that an agent operates it for you: it makes best practice *available*, and you stay in the loop by reviewing what the agent did, not by doing every step yourself.

## Layout

```
.
├── AGENTS.md        # entry point for AI agents (and curious humans)
├── methodology.md   # why this is shaped the way it is + conventions
├── decisions.md     # append-only log of commitments (ADR-style)
├── observations.md  # append-only log of findings worth saving from re-derivation
├── daybook/         # one dated file per workday (Intent / Log / Handoff)
├── projects/        # one subfolder per ongoing project
├── runbooks/        # procedural knowledge — "how to do X" (ships with start-session/ and close-session/)
├── resources/       # durable static reference material (workflow example, etc.)
└── tmp/             # gitignored scratch
```

Each folder has its own `AGENTS.md` explaining how it's meant to be used, so you can dive into any part of the workspace without re-reading the root.

## Why a template?

Most AI assistants have memory features that lock you to one vendor. This template uses git history and plain markdown files instead — your work outlives whichever tool you happen to use. Every close-session run takes a git commit — a timestamped snapshot — so `git log` becomes a searchable history: decisions you made six months ago are findable with `grep`, and yesterday's context is one command away.

See `methodology.md` for the principles, the influences (ADR, flat-file plaintext-productivity tradition, daily-handoff patterns from engineering rotations), and the conventions for keeping the workspace useful over time.

## License

MIT. Fork it, modify it, make it yours.
