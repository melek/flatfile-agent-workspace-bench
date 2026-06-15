#!/usr/bin/env python3
"""Vendor the canonical agent-workspace-template into the bench.

`runner.py stage` builds full-template runs from `sio.TEMPLATE_ROOT`
(`agent-workspace-template/`). The template of record is NOT reconstructed
here — it is the authoritative copy maintained in the sibling repo
`flatfile-agent-workspace` (`agent-workspace-template/`). This tool vendors a
snapshot of it into the bench and records the source commit SHA, so the bench
is self-contained and reproducible while the template has a single owner.

Run:
  python bench/tools/sync_template.py                 # vendor from the sibling repo
  python bench/tools/sync_template.py --source PATH    # vendor from an explicit path
  python bench/tools/sync_template.py --check          # fail if vendored != source

Provenance (source repo + SHA) is written to `template-provenance.json` at the
bench repo root — outside the template tree, so it never gets staged into a run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent))
from lib import score_io as sio  # type: ignore  # noqa: E402

DEFAULT_SOURCE = sio.REPO_ROOT.parent / "flatfile-agent-workspace" / "agent-workspace-template"
DEST = sio.TEMPLATE_ROOT
PROVENANCE = sio.REPO_ROOT / "template-provenance.json"


def _git_sha(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return None


def _tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(DEFAULT_SOURCE), help="canonical template dir")
    ap.add_argument("--check", action="store_true", help="fail if vendored tree differs from source")
    args = ap.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"ERROR: canonical template not found at {source}", file=sys.stderr)
        return 2
    src_tree = _tree(source)

    if args.check:
        if not DEST.exists():
            print(f"STALE: {DEST.relative_to(sio.REPO_ROOT)} does not exist", file=sys.stderr)
            return 1
        if _tree(DEST) != src_tree:
            print("STALE: vendored template differs from source — re-run sync_template.py", file=sys.stderr)
            return 1
        print("vendored template matches source")
        return 0

    if DEST.exists():
        shutil.rmtree(DEST)
    for rel, text in src_tree.items():
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")

    sha = _git_sha(source)
    PROVENANCE.write_text(json.dumps({
        "source_repo": "flatfile-agent-workspace",
        "source_path": str(source),
        "source_sha": sha,
        "files": len(src_tree),
    }, indent=2) + "\n")
    print(f"Vendored {len(src_tree)} files from {source} (sha {sha[:12] if sha else '?'}) -> {DEST.relative_to(sio.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
