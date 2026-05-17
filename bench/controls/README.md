# Controls

Three control conditions for the workspace benchmark. Designed as a ladder against `v0.1-baseline` and `v0.2-revised`.

| Control | Folder on disk | Methodology surface | Tests |
|---|---|---|---|
| **control1-blank** | Empty | None | Floor — agent must invent workspace shape from nothing |
| **control2-verbal-spec** | Empty | Pasted into user prompt as preamble | Whether the spec needs to be materialized as files or whether the verbal version is enough |
| **control3-bare-scaffold** | Folder structure + empty register files + ONE root AGENTS.md (bare orientation only) | Bare AGENTS.md only — no methodology depth, no per-folder AGENTS.md, no templates | Whether methodology depth (templates, canonical strings, review cadence) does work beyond having the files exist |
| `v0.1-baseline` | Full template | Full methodology.md + per-folder AGENTS.md + templates | Full workspace as-shipped |
| `v0.2-revised` | Full template + safety mitigations | Full + provenance markers, force-disagreement, risky-patterns disclosure | Full workspace + the v0.2 iteration |

## Smoke test scope

Initial smoke test runs against **one scenario** (chosen for the controls; see `bench/AGENTS.md` for the dispatch protocol). If the smoke test surfaces interesting deltas, the controls are run against a wider scenario subset.

The smoke test is a check on whether the control ladder is worth running at scale, not a finished result.

## Notes

- **control2** ships the verbal spec at `control2-verbal-spec/scaffold-preamble.md`. The runner prepends it to the simulator's user-prompt as if the user had pasted it into the first message.
- **control3** keeps the framing "you administer this workspace" and names the influences (flat-file, daybook, ADR, runbooks, AGENTS.md) but ships **no methodology depth** — no canonical strings, no strict bars, no per-folder AGENTS.md, no worked example, no templates in the register files.
- Raters scoring control runs need to know the variant — see the per-rubric scoring notes in the dispatch.
