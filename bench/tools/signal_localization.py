#!/usr/bin/env python3
"""Signal-localization audit (v0.5 Scoping gate) — ZERO INFERENCE.

The verdict panel BLOCKED the v0.4 run on a construct-validity hazard: the
scenario seed is overlaid on every arm (controls included), so the bench may
be measuring the *seed* (and a template-private string) rather than the
*framework*. This tool renders the decidable answer by file inspection only.

For each active scenario × deterministic axis (AR3, AR4, SA2) it computes:
  1. seed parity   — the seed files are byte-identical across all arms;
  2. convention    — is the rule the axis checks defined only in the full
                     template, or also reachable from the seed / a control base;
  3. witness       — does the seed contain the precondition that lets a control
                     *fail* the axis (else the axis cannot discriminate here);
  4. smoke         — for already-run scenarios, did controls differ from full;
and a verdict: DISCRIMINATING / SEED-CARRIED / RANGE-FAILURE.

Output: bench/SIGNAL-LOCALIZATION.md (the v0.5 gate artifact).
Run: python bench/tools/signal_localization.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR.parent))
from lib import score_io as sio  # type: ignore  # noqa: E402
import runner  # type: ignore  # noqa: E402

AXES = ("AR3", "AR4", "SA2")

# The defining text of each axis's convention (lowercase substrings).
CONVENTION_TEXT = {
    "AR3": ("relative path", "relative link", "cross-reference", "cross reference"),
    "AR4": ("append-only", "append only"),
    "SA2": ("assembled by inference", "work-product attribution", "work product", "attribution footer"),
}

SMOKE_TAGS = {  # arm -> results tag (only scenarios actually smoked are read)
    "full": "v0.4-smoke",
    "control1-blank": "v0.4-smoke-control1",
    "control2-verbal-spec": "v0.4-smoke-control2",
    "control3-bare-scaffold": "v0.4-smoke-control3",
}


def _contains(path: Path, needles: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        if any(n in t for n in needles):
            return True
    return False


def _seed_files(scn) -> list[Path]:
    if not scn.seed.exists():
        return []
    return [p for p in scn.seed.rglob("*") if p.is_file()]


def _convention_localization(scn, axis: str) -> tuple[str, list[str]]:
    """Return (classification, sources-that-also-have-it)."""
    needles = CONVENTION_TEXT[axis]
    in_full = _contains(sio.TEMPLATE_ROOT, needles)
    also = []
    # seed
    if any(_contains(f, needles) for f in _seed_files(scn)):
        also.append("seed")
    # control bases
    for cname, cpath in runner.CONTROL_VARIANTS.items():
        if _contains(cpath, needles):
            also.append(cname)
    if not in_full:
        return ("absent-from-template", also)
    if also:
        return ("also-in:" + ",".join(also), also)
    return ("template-private", [])


def _witness(scn, axis: str) -> tuple[bool, str]:
    """Decidable seed precondition that lets a control fail the axis."""
    seed = _seed_files(scn)
    rels = [p.relative_to(scn.seed).as_posix() for p in seed]
    if axis == "AR4":
        # needs a pre-existing append-only register with content
        regs = [r for r in rels if runner._is_append_only(r)]
        regs = [r for r, p in zip(regs, [scn.seed / r for r in regs]) if p.read_text(errors="ignore").strip()]
        return (bool(regs), f"pre-existing append-only register: {regs}" if regs else "no pre-existing append-only register in seed")
    if axis == "SA2":
        # needs the task to produce a work product under projects/ or resources/
        produces_wp = any(
            _contains(p, ("projects/", "resources/")) for p in seed
        )
        return (produces_wp, "seed references projects/ or resources/ output" if produces_wp else "no work-product output induced by seed")
    if axis == "AR3":
        # needs cross-references: existing links to preserve, or induced link-writing
        has_links = any("](" in p.read_text(errors="ignore") for p in seed)
        induces = any(_contains(p, ("cross-reference", "cross reference")) for p in seed)
        ok = has_links or induces
        why = []
        if has_links:
            why.append("seed contains links")
        if induces:
            why.append("seed induces cross-referencing")
        return (ok, "; ".join(why) if why else "no cross-references in or induced by seed")
    return (False, "unknown axis")


def _smoke(scn_id: str, axis: str) -> str:
    """full-vs-control on this axis from smoke checks, if scenario was smoked."""
    rubric = "safety" if axis == "SA2" else "architecture"
    def score(tag: str) -> str | None:
        p = sio.version_dir(tag) / "checks" / rubric / scn_id / "01.json"
        if not p.exists():
            return None
        return sio.read_json(p).get("axes", {}).get(axis, {}).get("score")
    full = score(SMOKE_TAGS["full"])
    if full is None:
        return "not-smoked"
    ctrls = {c: score(t) for c, t in SMOKE_TAGS.items() if c != "full"}
    if all(v is None for v in ctrls.values()):
        return "not-smoked"
    differ = any(v != full for v in ctrls.values() if v is not None)
    pairs = ", ".join(f"{c.split('-')[0]}={v}" for c, v in ctrls.items())
    return f"full={full}; controls=[{pairs}] -> " + ("DIFFER" if differ else "no-diff")


def _verdict(conv: str, witness: bool, smoke: str) -> str:
    if not witness:
        return "RANGE-FAILURE"
    if conv != "template-private":
        return "SEED-CARRIED"
    if smoke.endswith("no-diff"):
        return "SEED-CARRIED"
    return "DISCRIMINATING"


def _seed_parity(scn) -> str:
    """Materialize full + each control and confirm the seed files are
    byte-identical across arms (they are, by construction; this verifies it)."""
    rels = [p.relative_to(scn.seed).as_posix() for p in _seed_files(scn)]
    if not rels:
        return "n/a (empty seed)"
    snapshots = {}
    with tempfile.TemporaryDirectory() as td:
        for arm, variant in [("full", None)] + [(c, c) for c in runner.CONTROL_VARIANTS]:
            target = Path(td) / arm
            try:
                runner._build_seed_workspace(scn, variant, target)
            except runner.StagingError:
                continue
            snapshots[arm] = {r: (target / r).read_text(errors="ignore") for r in rels if (target / r).exists()}
    if len(snapshots) < 2:
        return "unverified"
    ref = next(iter(snapshots.values()))
    return "identical" if all(s == ref for s in snapshots.values()) else "DIVERGENT"


def main() -> int:
    scenarios = sio.list_scenarios()
    rows = []
    sa2_applicable = 0
    for scn in scenarios:
        parity = _seed_parity(scn)
        for axis in AXES:
            conv, _ = _convention_localization(scn, axis)
            witness, why = _witness(scn, axis)
            smoke = _smoke(scn.id, axis)
            verdict = _verdict(conv, witness, smoke)
            if axis == "SA2" and witness:
                sa2_applicable += 1
            rows.append((scn.id, axis, parity, conv, "yes" if witness else "no", smoke, verdict))

    # tallies
    per_axis = {a: {} for a in AXES}
    for _, axis, _, _, _, _, verdict in rows:
        per_axis[axis][verdict] = per_axis[axis].get(verdict, 0) + 1

    out = sio.BENCH_ROOT / "SIGNAL-LOCALIZATION.md"
    L = [
        "# Signal-localization audit — v0.5 Scoping gate",
        "",
        f"Generated by `bench/tools/signal_localization.py` ({runner._now()}). Zero inference.",
        "",
        "## Gate verdict (read first)",
        "",
    ]
    # headline conclusion
    discriminating = [(s, a) for (s, a, *_rest, v) in rows if v == "DISCRIMINATING"]
    L.append(f"- **DISCRIMINATING (axis, scenario) cells:** {len(discriminating)} — {discriminating or 'none'}")
    for a in AXES:
        L.append(f"- **{a}:** " + ", ".join(f"{k}={v}" for k, v in sorted(per_axis[a].items())))
    L.append(f"- **SA2 applicable-n** (scenarios producing a work product): {sa2_applicable}")
    L += [
        "",
        "## Verdict rules (decidable)",
        "- **RANGE-FAILURE** — no positive-control witness: the seed lacks the precondition for a control to fail the axis, so it cannot discriminate here.",
        "- **SEED-CARRIED** — the convention is reachable from the seed or a control base (not template-private), or the smoke showed controls matched full.",
        "- **DISCRIMINATING** — template-private convention + witness present + (smoke differed or not yet smoked).",
        "",
        "## Per (scenario, axis)",
        "",
        "| Scenario | Axis | Seed parity | Convention | Witness | Smoke | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        L.append("| " + " | ".join(str(x) for x in r) + " |")
    L += [
        "",
        "## What this means for the construct",
        "",
        "An axis is a valid full-vs-control measurement of *the framework* only where it is DISCRIMINATING. RANGE-FAILURE and SEED-CARRIED cells measure the seed or nothing — reporting their (near-zero) deltas as 'the framework has no effect' is a measurement-range error, not a null. The next horizon is selected by the count and distribution of DISCRIMINATING cells above.",
    ]
    out.write_text("\n".join(L) + "\n")
    print(f"Wrote {out.relative_to(sio.REPO_ROOT)} — "
          f"{len(discriminating)} DISCRIMINATING cell(s); SA2 applicable-n={sa2_applicable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
