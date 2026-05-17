# Flat-File Workspace Template

A self-documenting workspace for doing real work with an AI assistant — humans and agents alike. No proprietary tools, no databases, no hidden state. Just plain files and folders, with conventions documented in plain text.

The whole workspace is designed so that a person — or an AI agent — can open any folder cold and figure out how to use it from the `AGENTS.md` file inside.

## Get started

### If you already have an AI tool

If you have [Claude Code](https://claude.com/claude-code), [OpenCode](https://opencode.ai), or another AI coding assistant installed, the fastest path is:

1. Open your AI tool.
2. Tell it: *"Download `<owner>/<repo>` from GitHub into a new folder and set it up as a workspace."*
3. Reopen the tool inside the new folder.
4. Ask it: *"Read `AGENTS.md` and tell me how to start."*

That's it. The agent handles the rest — downloading, removing the template's git history, initializing a fresh git repo in the folder, and walking you through any missing tools.

### Without an AI tool

1. Click the green **Code** button at the top of this repo, then **Download ZIP**.
2. Extract the ZIP wherever you keep work.
3. Install an AI coding assistant. [Claude Code](https://claude.com/claude-code) and [OpenCode](https://opencode.ai) both run from your terminal and can edit files in any folder.
4. Open the assistant inside the extracted folder.
5. Tell it: *"Read `AGENTS.md` and walk me through setting this up."*

## How this works

The LLM is your administrative assistant for this workspace. It reads `AGENTS.md` files on folder entry, follows the conventions documented there, and translates between what you do in plain language and what the system records. You can write entries yourself, but you usually won't — the agent drafts handoffs, logs decisions when you make them, files followups when you delegate. Your job is to do the work and review what the agent recorded.

Be upfront about the tradeoff: this methodology is **aspirational for a manual user**. Daily handoffs, append-only logs, weekly reviews — most people can't keep this up on their own. An LLM, given the right structure, can do best practice more reliably than discipline alone. That's the design center: the workspace makes the methodology *available*, and the agent operates it. You stay in the loop by reviewing what the agent did, not by doing every step yourself.

The simple-enough-for-cold-pickup and rich-enough-for-real-work goals are in genuine tension, and this workspace leans toward the second. The structure earns its keep when an LLM is running it; if you're evaluating it manually in five minutes, much of it will look like overhead.

### A day in this workspace

For a worked tour showing how one situation routes across `decisions.md`, `observations.md`, `followups.md`, and the daybook, see [`resources/workspace-workflow-example.md`](resources/workspace-workflow-example.md). The full filled daybook for that same day is at [`daybook/0000-00-00-example.md`](daybook/0000-00-00-example.md).

## Layout

```
.
├── AGENTS.md        # entry point for AI agents (and curious humans)
├── methodology.md   # why this is shaped the way it is + conventions
├── decisions.md     # append-only log of decisions (ADR-style)
├── observations.md  # append-only notes that aren't decisions
├── followups.md     # tickler / waiting-on log
├── daybook/         # one dated file per workday (Intent / Log / Handoff)
├── projects/        # one subfolder per ongoing project
├── runbooks/        # procedural knowledge — "how to do X"
├── resources/       # durable static reference material (workflow example, etc.)
└── tmp/             # gitignored scratch
```

Each folder has its own `AGENTS.md` explaining how it's meant to be used, so you can dive into any part of the workspace without re-reading the root.

## Why a template?

Most AI assistants have memory features that lock you to one vendor. This template uses git history and plain markdown files instead — your work outlives whichever tool you happen to use. Decisions you made six months ago are findable with `grep`. Yesterday's context is a `git log` away.

See `methodology.md` for the principles, the influences (ADR, flat-file plaintext-productivity tradition, daily-handoff patterns from engineering rotations), and the conventions for keeping the workspace useful over time.

## License

MIT. Fork it, modify it, make it yours.
