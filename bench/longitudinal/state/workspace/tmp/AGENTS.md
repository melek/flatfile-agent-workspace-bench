# tmp/ — AGENTS.md

Gitignored scratch. Intermediate artifacts, search results, downloaded items to be triaged, drafts for non-project work. Nothing here is committed.

**Rule:** if you'd miss it, it doesn't belong here. Move it into a project folder, a daybook entry, or a top-level log.

This file (`AGENTS.md`) is the one exception — it's allowed past the gitignore via `!tmp/AGENTS.md` so the folder always exists and the rule is visible in place.

## Layout

Use one subfolder per topic, mirroring `projects/`:

```
tmp/
├── AGENTS.md
├── <topic-1>/
│   └── ...scratch files...
└── <topic-2>/
    └── ...scratch files...
```

Topic names are short, lowercase, kebab-case — same shape as project names. Loose files at `tmp/` root are fine for one-off scratch (a single search result, a single download) but anything that grows past two files should get a subfolder.

## Promoting a scratch topic to a project

If a `tmp/<topic>/` subfolder turns out to be durable work, promote it:

```bash
mv tmp/<topic> projects/<topic>
```

Then add an `AGENTS.md` per `projects/AGENTS.md`. Because the layout already matches, promotion is a rename — no reorganization needed. The daybook entry for that day should note the promotion.

## When to use `tmp/`

- Throwaway scratch you don't want polluting working folders.
- Staging ground for a topic that *might* become a project. If it does, `mv` it.
- Search results, downloads, exports to be triaged.

## When not to use `tmp/`

- Anything you'd be upset to lose. Use a project or a log.
- Anything someone else (or a future agent) might need to find. `tmp/` is private to this session.
- Anything you've already decided is worth keeping. Move it now, not later.
