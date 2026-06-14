#!/usr/bin/env python3
"""Materialize the clean full template `agent-workspace-template/`.

`runner.py stage` builds a full-template run from `sio.TEMPLATE_ROOT`
(`agent-workspace-template/`). That tree is the *pristine* template: full
methodology depth (methodology.md, every AGENTS.md, register templates, the
worked examples) with **empty registers** — no accumulated entries.

The only full-template-shaped tree in the repo is the longitudinal working
copy at `bench/longitudinal/state/workspace/`, which is *accumulated state*
(dated daybook entries, real decisions/observations/followups, specific
projects). This tool derives the pristine template from it deterministically,
so the template is an auditable derivation, not a hand-fabricated artifact.

Derivation rules (a file is *scaffolding* unless a rule strips it):
  - register files (decisions.md, observations.md): drop any `## 20XX-..`
    dated-entry section (from that heading to the next non-dated `## ` / EOF).
    The literal `## YYYY-MM-DD — Short title` template block is kept.
  - followups.md: drop `- **20XX-..` dated list items; keep headers + the
    `- **YYYY-MM-DD ...` how-to template line.
  - daybook/: keep AGENTS.md and the `0000-00-00-example.md` template; drop
    real dated entries (`20XX-..md`).
  - projects/: keep projects/AGENTS.md; drop concrete project subdirectories.
  - everything else (methodology.md, README.md, every AGENTS.md, resources/,
    runbooks/, tmp/, .gitignore) is copied verbatim.

This reflects the longitudinal-workspace methodology surface. If a given
benchmark version (e.g. a v0.4 trim) differs from it, adjust the derived tree
or the source and regenerate; the result is the template of record for runs
staged from it.

Run: python bench/tools/build_template.py [--check]
  --check : exit non-zero if the on-disk template differs from a fresh build.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent))
from lib import score_io as sio  # type: ignore  # noqa: E402

SOURCE = sio.BENCH_ROOT / "longitudinal" / "state" / "workspace"
DEST = sio.TEMPLATE_ROOT

# v0.3-trimmed lineage: the trim removed forward-task tracking (followups.md)
# and the scheduled weekly-review runbook. The longitudinal source still
# carries them; drop them so the staged template matches the active-scenario
# surface (scenario 03, which exercised followups, was retired for
# task-invalidity — staging the affordance it tested would put a surface on
# disk that no active scenario probes). Scenarios that need followups overlay
# their own via the seed. NOTE: methodology.md / AGENTS.md prose still mentions
# these; finalizing the v0.4 methodology text (and whether to add the v0.3
# start-session/close-session runbooks, which are not in this source) is a
# run-owner decision to settle before pinning the template SHA.
_TRIMMED_DROP_FILES = {"followups.md"}
_TRIMMED_DROP_PREFIXES = ("runbooks/weekly-review/",)

_DATED_HEADING = re.compile(r"^##\s+20\d\d-")
_DATED_ITEM = re.compile(r"^[-*]\s+\*\*20\d\d-")
_DATED_DAYBOOK = re.compile(r"^20\d\d-\d\d-\d\d.*\.md$")


def _strip_dated_sections(text: str) -> str:
    """Drop `## 20XX-..` sections; keep all other scaffolding."""
    out: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith("## "):
            skipping = bool(_DATED_HEADING.match(line))
        if not skipping:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _strip_dated_items(text: str) -> str:
    """Drop `- **20XX-..` dated list items (followups)."""
    out = [ln for ln in text.splitlines() if not _DATED_ITEM.match(ln)]
    return "\n".join(out).rstrip() + "\n"


def _derive(src_root: Path) -> dict[str, str | None]:
    """Return relpath -> content (None means a directory marker). Drives both
    the build and the --check, so they cannot diverge."""
    tree: dict[str, str | None] = {}
    for p in sorted(src_root.rglob("*")):
        rel = p.relative_to(src_root).as_posix()
        if p.is_dir():
            continue
        name = p.name
        # v0.3-trimmed lineage: drop retired-affordance files.
        if rel in _TRIMMED_DROP_FILES or rel.startswith(_TRIMMED_DROP_PREFIXES):
            continue
        # daybook: keep AGENTS.md + the example; drop real dated entries.
        if rel.startswith("daybook/") and _DATED_DAYBOOK.match(name):
            continue
        # projects: keep only the folder AGENTS.md (drop concrete projects).
        if rel.startswith("projects/") and rel != "projects/AGENTS.md":
            continue
        text = p.read_text(encoding="utf-8")
        if rel in ("decisions.md", "observations.md"):
            text = _strip_dated_sections(text)
        elif rel == "followups.md":
            text = _strip_dated_items(text)
        tree[rel] = text
    return tree


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if on-disk template is stale")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"ERROR: source workspace not found: {SOURCE}", file=sys.stderr)
        return 2
    tree = _derive(SOURCE)

    if args.check:
        if not DEST.exists():
            print(f"STALE: {DEST.relative_to(sio.REPO_ROOT)} does not exist", file=sys.stderr)
            return 1
        on_disk = {
            p.relative_to(DEST).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(DEST.rglob("*")) if p.is_file()
        }
        if on_disk != tree:
            extra = set(on_disk) - set(tree)
            missing = set(tree) - set(on_disk)
            changed = {k for k in set(tree) & set(on_disk) if on_disk[k] != tree[k]}
            print(
                f"STALE template: +{sorted(extra)} -{sorted(missing)} ~{sorted(changed)}",
                file=sys.stderr,
            )
            return 1
        print("template is current")
        return 0

    if DEST.exists():
        shutil.rmtree(DEST)
    for rel, text in tree.items():
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        assert text is not None
        dst.write_text(text, encoding="utf-8")
    print(f"Materialized {len(tree)} files -> {DEST.relative_to(sio.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
