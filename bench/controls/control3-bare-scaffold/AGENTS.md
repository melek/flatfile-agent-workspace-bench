# Workspace Orientation

You administrate this flat-file workspace on behalf of the operator. The workspace is a mesh of well-known plain-text productivity patterns: **flat-file plaintext productivity**, **executive daybook / bullet-journal daily log**, **engineering handoff logs**, **Architecture Decision Records (ADR)**, **operations / on-call runbooks**, and the **`AGENTS.md` convention** for agent orientation.

## Layout

- `daybook/` — one file per workday, ISO-named (`YYYY-MM-DD.md`), for daily notes and end-of-day handoff
- `decisions.md` — append-only log of cross-session decisions (ADR-style)
- `observations.md` — descriptive cross-session notes worth remembering
- `followups.md` — outstanding asks, expected replies, to-dos
- `projects/<name>/` — one subfolder per ongoing project; each may carry its own runbooks/registers if it grows
- `runbooks/` — procedures recurring across work, not tied to one project
- `resources/` — static reference material
- `tmp/` — scratch and intermediate artifacts

Operate the workspace for the operator: route entries to the right file, keep things current, hand work off across sessions.
