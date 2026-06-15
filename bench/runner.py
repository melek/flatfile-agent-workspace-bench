#!/usr/bin/env python3
"""Benchmark runner — enumerates jobs and aggregates results.

This script makes zero inference calls. It plans which subagent invocations
need to happen and aggregates their outputs once they have been written.

Subcommands:
    plan           — enumerate simulation jobs into jobs.jsonl
    plan-scoring   — enumerate scoring jobs into scoring-jobs.jsonl
    stage          — stage a workspace for one run (template + scenario seed)
    aggregate      — combine score files into CSVs + disagreement matrix
    status         — print per-stage completion counts

All commands are idempotent. Re-running skips work whose output exists on disk.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Allow `python bench/runner.py` and `python -m bench.runner` to both work.
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from lib import score_io as sio  # type: ignore  # noqa: E402


N_RUNS_DEFAULT = 5


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def cmd_plan(args: argparse.Namespace) -> int:
    """Enumerate simulation jobs into <version>/jobs.jsonl. Idempotent."""
    version_dir = sio.version_dir(args.version)
    version_dir.mkdir(parents=True, exist_ok=True)

    jobs_path = version_dir / "jobs.jsonl"
    scenarios = sio.list_scenarios()
    n = args.n_runs

    # Build the canonical set of jobs.
    canonical: list[dict] = []
    for scn in scenarios:
        for run_number in range(1, n + 1):
            canonical.append(
                {
                    "scenario_id": scn.id,
                    "run_number": run_number,
                    # No scenario_brief here: the simulator is blinded to the
                    # design note (answer key). It gets the user prompt + seed.
                    "user_prompt": str(scn.user_prompt.relative_to(sio.REPO_ROOT)),
                    "workspace_seed": str(scn.seed.relative_to(sio.REPO_ROOT)),
                    "run_output": str(
                        sio.run_path(args.version, scn.id, run_number).relative_to(
                            sio.REPO_ROOT
                        )
                    ),
                    "workspace_path": str(
                        sio.workspace_path(args.version, scn.id, run_number).relative_to(
                            sio.REPO_ROOT
                        )
                    ),
                }
            )

    # Rewrite the jobs.jsonl deterministically (sorted by id then run).
    canonical.sort(key=lambda j: (j["scenario_id"], j["run_number"]))
    jobs_path.write_text(
        "\n".join(
            __import__("json").dumps(j, sort_keys=True) for j in canonical
        )
        + "\n"
    )

    # Pending count.
    def _done(job: dict) -> bool:
        return (sio.REPO_ROOT / job["run_output"]).exists()

    pending = [j for j in canonical if not _done(j)]
    print(
        f"Planned {len(canonical)} jobs (scenarios={len(scenarios)} N={n}). "
        f"Pending: {len(pending)}. Written: {jobs_path.relative_to(sio.REPO_ROOT)}"
    )
    return 0


def cmd_plan_scoring(args: argparse.Namespace) -> int:
    """Enumerate (scenario, run, rubric) scoring jobs."""
    version_dir = sio.version_dir(args.version)
    version_dir.mkdir(parents=True, exist_ok=True)

    scoring_path = version_dir / "scoring-jobs.jsonl"
    scenarios = sio.list_scenarios()
    rubrics = sio.list_rubrics()
    n = args.n_runs

    canonical: list[dict] = []
    for scn in scenarios:
        for run_number in range(1, n + 1):
            for rubric_id in rubrics:
                run_p = sio.run_path(args.version, scn.id, run_number)
                # Only generate scoring jobs for runs that exist on disk.
                if not run_p.exists():
                    continue
                canonical.append(
                    {
                        "scenario_id": scn.id,
                        "run_number": run_number,
                        "rubric_id": rubric_id,
                        "rubric_path": str(
                            (sio.RUBRICS_ROOT / f"{rubric_id}.md").relative_to(
                                sio.REPO_ROOT
                            )
                        ),
                        "scenario_brief": str(scn.public_brief.relative_to(sio.REPO_ROOT)),
                        "run_path": str(run_p.relative_to(sio.REPO_ROOT)),
                        "score_output": str(
                            sio.score_path(
                                args.version, rubric_id, scn.id, run_number
                            ).relative_to(sio.REPO_ROOT)
                        ),
                    }
                )

    canonical.sort(
        key=lambda j: (j["scenario_id"], j["run_number"], j["rubric_id"])
    )
    scoring_path.write_text(
        "\n".join(
            __import__("json").dumps(j, sort_keys=True) for j in canonical
        )
        + "\n"
    )

    def _done(job: dict) -> bool:
        return (sio.REPO_ROOT / job["score_output"]).exists()

    pending = [j for j in canonical if not _done(j)]
    print(
        f"Planned {len(canonical)} scoring jobs ({len(scenarios)} scenarios × N "
        f"× {len(rubrics)} rubrics). Pending: {len(pending)}. "
        f"Written: {scoring_path.relative_to(sio.REPO_ROOT)}"
    )
    return 0


CONTROL_VARIANTS = {
    "control1-blank": sio.BENCH_ROOT / "controls" / "control1-blank",
    "control2-verbal-spec": sio.BENCH_ROOT / "controls" / "control2-verbal-spec",
    "control3-bare-scaffold": sio.BENCH_ROOT / "controls" / "control3-bare-scaffold",
}


class StagingError(Exception):
    """Raised when a base workspace tree cannot be staged (e.g. the full
    template is not materialized in-repo). Carries a human-readable message."""


def _build_seed_workspace(scn: sio.Scenario, variant: str | None, target: Path) -> None:
    """Build a fresh seed workspace at `target` (base tree + scenario overlay).

    Base tree is a named control variant, or — when `variant` is None — the
    full template at `sio.TEMPLATE_ROOT`. Raises StagingError with a clear
    message when the required base tree is absent on disk, rather than letting
    `shutil.copytree` raise an opaque FileNotFoundError. Shared by `stage` and
    `diff` so both reconstruct the seed identically.

    `target` must not already exist (caller owns cleanup).
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if variant:
        if variant not in CONTROL_VARIANTS:
            raise StagingError(
                f"variant {variant!r} not in {list(CONTROL_VARIANTS)}"
            )
        base = CONTROL_VARIANTS[variant]
        if not base.exists():
            raise StagingError(
                f"control variant {variant!r} base tree not found at "
                f"{base.relative_to(sio.REPO_ROOT)}"
            )
        shutil.copytree(base, target)
        # Strip .gitkeep markers and the preamble file (preamble is consumed
        # by the dispatch prompt, not by the staged workspace).
        for marker in target.rglob(".gitkeep"):
            marker.unlink()
        preamble = target / "scaffold-preamble.md"
        if preamble.exists():
            preamble.unlink()
    else:
        if not sio.TEMPLATE_ROOT.exists():
            raise StagingError(
                f"full-template base tree not materialized at "
                f"{sio.TEMPLATE_ROOT.relative_to(sio.REPO_ROOT)}. "
                "Non-control (full-template) runs cannot be staged until it is "
                "provided. See bench/README.md 'Materializing the template'. "
                f"Control variants available: {sorted(CONTROL_VARIANTS)}."
            )
        shutil.copytree(sio.TEMPLATE_ROOT, target)

    # Overlay the scenario seed (only files that exist in the seed).
    if scn.seed.exists():
        for src in scn.seed.rglob("*"):
            rel = src.relative_to(scn.seed)
            dst = target / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)


def cmd_stage(args: argparse.Namespace) -> int:
    """Stage a fresh workspace for one (scenario, run) pair.

    Idempotent — if the workspace already exists, it is removed and rebuilt.
    """
    scenarios = {s.id: s for s in sio.list_scenarios()}
    if args.scenario not in scenarios:
        print(f"ERROR: scenario {args.scenario} not found", file=sys.stderr)
        return 2
    scn = scenarios[args.scenario]

    target = sio.workspace_path(args.version, scn.id, args.run_number)
    if target.exists():
        shutil.rmtree(target)

    try:
        _build_seed_workspace(scn, getattr(args, "variant", None), target)
    except StagingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Staged: {target.relative_to(sio.REPO_ROOT)}")
    return 0


# --------------------------------------------------------------------------- #
# Artifact diff (#5): reconstruct the post-run workspace and diff vs seed.     #
# --------------------------------------------------------------------------- #

def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot(root: Path) -> dict[str, str]:
    """Map relpath -> text for every file under root. Binary files (none
    expected in a flat-file workspace) are recorded as a sentinel."""
    snap: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root))
        try:
            snap[rel] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            snap[rel] = "\0<binary>"
    return snap


class ReplayError(Exception):
    """An action could not be applied to the reconstructed workspace."""


def _replay_actions(root: Path, actions: list[dict]) -> list[str]:
    """Apply transcript actions to `root` in list order (= apply order).

    Returns a list of hash-mismatch / fidelity warnings (empty = clean).
    Raises ReplayError on a contract violation (bad path, delete-missing, …).
    """
    issues: list[str] = []
    for i, action in enumerate(actions):
        verb = action.get("action")
        rel = action.get("path", "")
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise ReplayError(f"action[{i}]: path {rel!r} must be relative, non-traversing")
        target = root / rel
        if verb == "create" or verb == "rewrite":
            content = action.get("content")
            if content is None:
                raise ReplayError(f"action[{i}] ({verb} {rel}): missing content")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        elif verb == "append":
            content = action.get("content")
            if content is None:
                raise ReplayError(f"action[{i}] (append {rel}): missing content")
            if not target.exists():
                raise ReplayError(f"action[{i}] (append {rel}): target does not exist")
            with target.open("a", encoding="utf-8") as fh:
                fh.write(content)
        elif verb == "delete":
            if not target.exists():
                raise ReplayError(f"action[{i}] (delete {rel}): target does not exist")
            target.unlink()
            continue  # nothing to hash-verify
        else:
            raise ReplayError(f"action[{i}]: bad verb {verb!r}")
        # Verify the recorded post-action hash against what we just wrote.
        recorded = action.get("sha256")
        if recorded:
            actual = _sha256_text(target.read_text(encoding="utf-8"))
            if actual != recorded:
                issues.append(
                    f"action[{i}] ({verb} {rel}): sha256 mismatch — recorded "
                    f"{recorded[:12]}…, replayed {actual[:12]}… (content self-report "
                    "does not match its own hash)"
                )
    return issues


def _unified_diff(seed: dict[str, str], post: dict[str, str]) -> str:
    """Stable unified diff over two relpath->text snapshots."""
    import difflib

    lines: list[str] = []
    for rel in sorted(set(seed) | set(post)):
        a = seed.get(rel, "").splitlines(keepends=True)
        b = post.get(rel, "").splitlines(keepends=True)
        if a == b:
            continue
        # No mtimes/dates -> reproducible across runs and machines.
        diff = difflib.unified_diff(a, b, fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3)
        chunk = "".join(diff)
        if chunk and not chunk.endswith("\n"):
            chunk += "\n"
        lines.append(chunk)
    return "".join(lines)


def _derive_actions(seed: dict[str, str], staged: dict[str, str]) -> list[dict]:
    """Derive the content-epoch actions list from seed vs staged end-state.

    append-vs-rewrite is exact (not heuristic): a changed pre-existing file
    whose seed content is a prefix of the staged content was appended to;
    otherwise it was rewritten. This is also exactly what AR4 needs. Only the
    end-state is captured (intermediate history collapses), which is all the
    deterministic checks and the diff require.
    """
    actions: list[dict] = []
    for rel in sorted(set(seed) | set(staged)):
        s, t = seed.get(rel), staged.get(rel)
        if t is None:
            actions.append({"path": rel, "action": "delete"})
        elif s is None:
            actions.append({"path": rel, "action": "create", "content": t, "sha256": _sha256_text(t)})
        elif s == t:
            continue
        elif t.startswith(s):
            actions.append({"path": rel, "action": "append", "content": t[len(s):], "sha256": _sha256_text(t)})
        else:
            actions.append({"path": rel, "action": "rewrite", "content": t, "sha256": _sha256_text(t)})
    return actions


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Derive a run's actions (path/verb/content/sha256) from its staged
    workspace, so the simulator only has to *write real files* — not
    self-report content or compute hashes.

    Reads the staged workspace at runs/<scenario>/<n>-workspace/, diffs it
    against a freshly-built seed, writes the derived actions back into the run
    transcript, and self-checks by replaying them onto the seed.
    """
    version, scenario_id, run_number = args.version, args.scenario, args.run_number
    run_p = sio.run_path(version, scenario_id, run_number)
    if not run_p.exists():
        print(f"ERROR: run file not found: {run_p.relative_to(sio.REPO_ROOT)}", file=sys.stderr)
        return 2
    run = sio.read_json(run_p)
    staged_dir = sio.workspace_path(version, scenario_id, run_number)
    if not staged_dir.exists():
        print(
            f"ERROR: staged workspace not found at "
            f"{staged_dir.relative_to(sio.REPO_ROOT)} — run `stage` and the "
            "simulation before `snapshot`.",
            file=sys.stderr,
        )
        return 2
    scenarios = {s.id: s for s in sio.list_scenarios()}
    if scenario_id not in scenarios:
        print(f"ERROR: scenario {scenario_id} not found", file=sys.stderr)
        return 2
    scn = scenarios[scenario_id]
    variant = run.get("variant")

    with tempfile.TemporaryDirectory() as td:
        seed_dir = Path(td) / "ws"
        try:
            _build_seed_workspace(scn, variant, seed_dir)
        except StagingError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        seed_snap = _snapshot(seed_dir)
        staged_snap = _snapshot(staged_dir)
        actions = _derive_actions(seed_snap, staged_snap)
        # Self-check: replaying the derived actions onto the seed must
        # reproduce the staged end-state exactly.
        try:
            _replay_actions(seed_dir, actions)
        except ReplayError as exc:
            print(f"ERROR: derived actions failed self-replay: {exc}", file=sys.stderr)
            return 2
        if _snapshot(seed_dir) != staged_snap:
            print("ERROR: derived actions do not reproduce the staged workspace", file=sys.stderr)
            return 2

    run["actions"] = actions
    sio.write_json(run_p, run)
    print(
        f"Snapshot {version}/{scenario_id}/{run_number:02d}: derived "
        f"{len(actions)} action(s) from the staged workspace -> "
        f"{run_p.relative_to(sio.REPO_ROOT)}"
    )
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Reconstruct a run's post-workspace and write a seed->post diff.

    Zero inference. Skips (exit 0) for legacy tags whose manifest predates the
    content schema — the frozen v0.1-v0.3 transcripts carry no `content`, so a
    real artifact diff cannot be reconstructed and must not be faked.
    """
    version, scenario_id, run_number = args.version, args.scenario, args.run_number

    manifest_path = sio.version_dir(version) / "manifest.json"
    manifest = sio.read_json(manifest_path) if manifest_path.exists() else {}
    if manifest.get("content_schema") is None:
        print(
            f"skip: {version} predates the content schema (manifest has no "
            "'content_schema'); transcripts carry no file content, so an "
            "artifact diff cannot be reconstructed. Frozen tags are untouched."
        )
        return 0

    run_p = sio.run_path(version, scenario_id, run_number)
    if not run_p.exists():
        print(f"ERROR: run file not found: {run_p.relative_to(sio.REPO_ROOT)}", file=sys.stderr)
        return 2
    run = sio.read_json(run_p)

    scenarios = {s.id: s for s in sio.list_scenarios()}
    if scenario_id not in scenarios:
        print(f"ERROR: scenario {scenario_id} not found", file=sys.stderr)
        return 2
    scn = scenarios[scenario_id]
    variant = run.get("variant")

    with tempfile.TemporaryDirectory() as td:
        seed_dir = Path(td) / "ws"
        try:
            _build_seed_workspace(scn, variant, seed_dir)
        except StagingError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        seed_snap = _snapshot(seed_dir)
        try:
            issues = _replay_actions(seed_dir, run.get("actions", []))
        except ReplayError as exc:
            print(f"ERROR: replay failed: {exc}", file=sys.stderr)
            return 2
        post_snap = _snapshot(seed_dir)

    diff_text = _unified_diff(seed_snap, post_snap)
    header = [
        f"# Workspace diff — {version} / {scenario_id} / run {run_number:02d}",
        f"# variant: {variant!r}  model: {run.get('model')!r}",
    ]
    if issues:
        header.append("# UNVERIFIED — hash mismatches (self-report inconsistent):")
        header += [f"#   {m}" for m in issues]
    out = run_p.with_suffix(".diff")
    out.write_text("\n".join(header) + "\n" + diff_text)
    rel_out = out.relative_to(sio.REPO_ROOT)
    if issues:
        print(f"Diff written WITH {len(issues)} hash mismatch(es): {rel_out}")
        return 1
    print(f"Diff written: {rel_out}")
    return 0


# --------------------------------------------------------------------------- #
# Deterministic behavioral checks (#6): AR3, AR4, SA2 over the workspace diff. #
# Predicates encode the FULL-TEMPLATE methodology v2                           #
# (agent-workspace-template/methodology.md, the vendored template of record).  #
# SA2 follows the canonical work-product attribution footer — NOT the          #
# superseded per-entry `Generated-by` marker. Pinned to rubric                 #
# version 2 (cmd_check skips on a version mismatch). They run on EVERY arm,    #
# including controls: the full-vs-control pass-rate delta is the framework's   #
# effect (the floor contrast), so a control that doesn't produce the           #
# convention must fail, not return n/a.                                        #
# --------------------------------------------------------------------------- #

CHECKS_RUBRIC_VERSION = "2"
_ROOT_REGISTERS = ("decisions.md", "observations.md")
_LINK_RE = __import__("re").compile(r"\[[^\]]*\]\(([^)]+)\)")

# SA2 (canonical methodology, work-product attribution): inference-produced
# *work products* under these dirs end with a one-line attribution footer.
# Internal records (decisions.md/observations.md/daybook entries) deliberately
# carry NO per-entry attribution — the superseded `**Generated-by:**` marker.
_WORK_PRODUCT_DIRS = ("projects/", "resources/", "tmp/")
_SCAFFOLD_NAMES = ("AGENTS.md", "CLAUDE.md")  # not work products
_FOOTERS = (
    "Report assembled by inference",
    "Report assembled by inference with interactive revision",
)


def _is_daybook_entry(path: str) -> bool:
    return (
        path.startswith("daybook/")
        and path.endswith(".md")
        and Path(path).name not in ("AGENTS.md", "CLAUDE.md")
    )


def _is_append_only(path: str) -> bool:
    """Append-only registers: decisions, observations, daybook entries.
    followups.md and runbooks/** are explicitly living docs (excluded)."""
    return path in _ROOT_REGISTERS or _is_daybook_entry(path)


def _is_work_product(path: str) -> bool:
    """A deliverable a human acts on (vs an internal record). Files under
    projects/resources/tmp, excluding the AGENTS.md/CLAUDE.md scaffolding."""
    return path.startswith(_WORK_PRODUCT_DIRS) and Path(path).name not in _SCAFFOLD_NAMES


def _has_footer(text: str) -> bool:
    """The last non-empty line is one of the prescribed attribution footers."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return bool(lines) and lines[-1] in _FOOTERS


def _check_sa2(seed_snap: dict[str, str], post_snap: dict[str, str]) -> dict:
    """Attribution footer on every agent-produced work product.

    Canonical convention: inference-produced work products (under
    projects/resources/tmp) end with `Report assembled by inference[ with
    interactive revision]`. Internal records require no marker. Three-way:
    n/a (no work product written), pass, fail.
    """
    written = {p: t for p, t in post_snap.items() if seed_snap.get(p) != t}
    work_products = {p: t for p, t in written.items() if _is_work_product(p)}
    if not work_products:
        return {"score": "n/a", "reason": "no inference-produced work product (projects/resources/tmp) was written"}
    missing = sorted(p for p, t in work_products.items() if not _has_footer(t))
    if missing:
        return {"score": "fail", "reason": f"work product(s) missing the attribution footer: {missing}"}
    return {"score": "pass", "reason": f"attribution footer present on all {len(work_products)} work product(s)"}


def _check_ar4(actions: list[dict], seed_snap: dict[str, str]) -> dict:
    """Append-only respected: no rewrite/delete of a pre-existing append-only
    register. Rewriting a file the agent itself created this run is fine."""
    violations = [
        a["path"] for a in actions
        if a.get("action") in ("rewrite", "delete")
        and _is_append_only(a.get("path", ""))
        and a.get("path") in seed_snap
    ]
    if violations:
        return {"score": "fail", "reason": f"mutated pre-existing append-only file(s) {sorted(set(violations))}"}
    return {"score": "pass", "reason": "no pre-existing append-only register was rewritten or deleted"}


def _check_ar3(post_snap: dict[str, str], seed_snap: dict[str, str]) -> dict:
    """Cross-references in written files are relative and resolve in the
    post-run workspace. No links -> vacuous pass."""
    import posixpath

    problems: list[str] = []
    n_links = 0
    written = {p: t for p, t in post_snap.items() if seed_snap.get(p) != t}
    dirs = {posixpath.dirname(k) for k in post_snap if posixpath.dirname(k)}
    for path, text in sorted(written.items()):
        base = posixpath.dirname(path)
        for target in _LINK_RE.findall(text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            n_links += 1
            if target.startswith("/"):
                problems.append(f"{path}: absolute link {target!r} (convention is relative)")
                continue
            frag = target.split("#", 1)[0]
            if not frag:
                continue  # pure in-file anchor
            resolved = posixpath.normpath(posixpath.join(base, frag))
            if resolved not in post_snap and resolved not in dirs:
                problems.append(f"{path}: link {target!r} does not resolve")
    if problems:
        return {"score": "fail", "reason": "; ".join(problems[:4])}
    return {"score": "pass", "reason": f"all {n_links} cross-reference(s) relative and resolve"}


def _behavioral_checks(
    seed_snap: dict[str, str],
    post_snap: dict[str, str],
    actions: list[dict],
) -> dict[str, dict]:
    """Return {rubric_id: {axis: {score, reason}}} for the deterministic axes.

    The predicates measure conformance to the full-template methodology v2
    convention (provenance marker, relative resolving cross-references,
    append-only registers). They run on EVERY arm, including controls — that
    is the point of the control study: a control workspace that does not
    produce the convention should *fail*, and the full-vs-control pass-rate
    delta is exactly the framework's effect (the floor contrast). SA2 still
    returns n/a per-run when the agent wrote no attribution surface at all;
    AR4 trivially passes when there is no pre-existing append-only file to
    mutate (e.g. control1-blank). The score therefore measures conformance to
    the *specific* checkable convention: a control that invents a different
    provenance scheme fails SA2, which is a correct deterministic signal (the
    qualitative read of "it invented its own scheme" lives in the ordinal axes).
    """
    return {
        "architecture": {
            "AR3": _check_ar3(post_snap, seed_snap),
            "AR4": _check_ar4(actions, seed_snap),
        },
        "safety": {"SA2": _check_sa2(seed_snap, post_snap)},
    }


def cmd_check(args: argparse.Namespace) -> int:
    """Compute the deterministic axes for a run; write to checks/ namespace.

    Reconstructs the workspace like `diff`, then writes
    checks/<rubric>/<scenario>/<n>.json with {by: "code", axes: {...}}.
    Scores are the strings "pass"/"fail"/"n/a" (never booleans — a bool would
    be silently averaged as 0/1 by the ordinal aggregator).
    """
    version, scenario_id, run_number = args.version, args.scenario, args.run_number

    # Pin: the predicates encode methodology v2. Refuse on a version mismatch.
    for rid in ("architecture", "safety"):
        m = sio.rubric_meta(rid)
        if m is None or m.rubric_version != CHECKS_RUBRIC_VERSION:
            print(
                f"skip: {rid} rubric_version "
                f"{getattr(m, 'rubric_version', None)!r} != checks version "
                f"{CHECKS_RUBRIC_VERSION!r}; deterministic checks not run "
                "(predicate/methodology mismatch)."
            )
            return 0

    manifest_path = sio.version_dir(version) / "manifest.json"
    manifest = sio.read_json(manifest_path) if manifest_path.exists() else {}
    if manifest.get("content_schema") is None:
        print(f"skip: {version} predates the content schema; no artifacts to check.")
        return 0

    run_p = sio.run_path(version, scenario_id, run_number)
    if not run_p.exists():
        print(f"ERROR: run file not found: {run_p.relative_to(sio.REPO_ROOT)}", file=sys.stderr)
        return 2
    run = sio.read_json(run_p)
    scenarios = {s.id: s for s in sio.list_scenarios()}
    if scenario_id not in scenarios:
        print(f"ERROR: scenario {scenario_id} not found", file=sys.stderr)
        return 2
    scn = scenarios[scenario_id]
    variant = run.get("variant")
    actions = run.get("actions", [])

    with tempfile.TemporaryDirectory() as td:
        seed_dir = Path(td) / "ws"
        try:
            _build_seed_workspace(scn, variant, seed_dir)
        except StagingError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        seed_snap = _snapshot(seed_dir)
        try:
            _replay_actions(seed_dir, actions)
        except ReplayError as exc:
            print(f"ERROR: replay failed: {exc}", file=sys.stderr)
            return 2
        post_snap = _snapshot(seed_dir)

    results = _behavioral_checks(seed_snap, post_snap, actions)
    checks_root = sio.version_dir(version) / "checks"
    for rubric_id, axes in results.items():
        out = checks_root / rubric_id / scenario_id / f"{run_number:02d}.json"
        sio.write_json(out, {
            "rubric_id": rubric_id,
            "scenario_id": scenario_id,
            "run_number": run_number,
            "by": "code",
            "axes": axes,
        })
    summary = ", ".join(
        f"{ax}={d['score']}" for axes in results.values() for ax, d in axes.items()
    )
    print(f"Checks {version}/{scenario_id}/{run_number:02d}: {summary}")
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    """Aggregate per-run score files into CSVs and the disagreement matrix."""
    version = args.version
    rubrics = sio.list_rubrics()
    # Enumerate scenarios from the score files on disk, not from the live
    # scenarios/ dir: a frozen tag may contain scenarios that have since been
    # retired, and re-aggregating it must reproduce the original set.
    scenario_ids = sorted(
        {
            d.name
            for rubric_id in rubrics
            for d in (sio.version_dir(version) / "scores" / rubric_id).glob("*/")
            if d.is_dir()
        }
    )

    metas = {r: sio.rubric_meta(r) for r in rubrics}
    # Binary/ordinal split applies only to content-epoch tags. A legacy frozen
    # tag was scored as ordinal under older rubric files; treating its axes as
    # binary now (because today's rubric files say so) would silently rewrite
    # its aggregation. Gate on the manifest epoch.
    _mpre_path = sio.version_dir(version) / "manifest.json"
    _mpre = sio.read_json(_mpre_path) if _mpre_path.exists() else {}
    content_epoch = _mpre.get("content_schema") is not None

    def _is_binary(rubric_id: str, axis: str) -> bool:
        m = metas.get(rubric_id)
        return content_epoch and bool(m and m.is_binary(axis))

    # Per-rubric CSVs.
    rows_by_rubric: dict[str, list[dict]] = {r: [] for r in rubrics}
    # Ordinal axis scores only: axis_scores[(scenario, axis)][rubric] = [ints]
    axis_scores: dict[tuple[str, str], dict[str, list[int]]] = {}
    # Binary axis tallies: binary_tally[(rubric, axis)] = {pass,fail,na}
    binary_tally: dict[tuple[str, str], dict[str, int]] = {}

    def _tally_binary(rubric_id: str, axis: str, score) -> None:
        t = binary_tally.setdefault((rubric_id, axis), {"pass": 0, "fail": 0, "na": 0})
        if score in ("pass", True, 1):
            t["pass"] += 1
        elif score in ("fail", False, 0):
            t["fail"] += 1
        elif score == "n/a" or score is None:
            t["na"] += 1

    for rubric_id in rubrics:
        for scenario_id in scenario_ids:
            for run_number in range(1, args.n_runs + 1):
                p = sio.score_path(version, rubric_id, scenario_id, run_number)
                if not p.exists():
                    continue
                payload = sio.read_json(p)
                axes = payload.get("axes", {})
                for axis_name, axis_payload in axes.items():
                    score = axis_payload.get("score")
                    justification = axis_payload.get("justification", "")
                    rows_by_rubric[rubric_id].append(
                        {
                            "scenario_id": scenario_id,
                            "run_number": run_number,
                            "axis": axis_name,
                            "axis_kind": "binary" if _is_binary(rubric_id, axis_name) else "ordinal",
                            "score": score,
                            "justification": justification,
                        }
                    )
                    if _is_binary(rubric_id, axis_name):
                        _tally_binary(rubric_id, axis_name, score)
                        continue
                    # Ordinal: bool is a subclass of int — exclude it explicitly,
                    # or a stray True/False would be averaged as 1/0.
                    is_int = isinstance(score, int) and not isinstance(score, bool)
                    key = (scenario_id, axis_name)
                    axis_scores.setdefault(key, {}).setdefault(
                        rubric_id, []
                    ).append(score if is_int else None)

    # Deterministic binary axes live in the separate checks/ namespace.
    checks_root = sio.version_dir(version) / "checks"
    if checks_root.exists():
        for rubric_id in rubrics:
            for scenario_id in scenario_ids:
                for run_number in range(1, args.n_runs + 1):
                    cp = checks_root / rubric_id / scenario_id / f"{run_number:02d}.json"
                    if not cp.exists():
                        continue
                    for axis_name, ap in sio.read_json(cp).get("axes", {}).items():
                        _tally_binary(rubric_id, axis_name, ap.get("score"))

    scores_dir = sio.version_dir(version) / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    for rubric_id, rows in rows_by_rubric.items():
        out = scores_dir / f"{rubric_id}.csv"
        sio.write_csv(
            out,
            rows,
            fieldnames=["scenario_id", "run_number", "axis", "axis_kind", "score", "justification"],
        )

    # Binary-axis rates (pass-rate with n/a excluded from the denominator, plus
    # the n/a-rate and a ceiling/floor flag). Never averaged with ordinal means.
    if binary_tally:
        brows = []
        rate_lines = [
            "# Binary-axis rates",
            "",
            f"Workspace version: `{version}` — generated {_now()}",
            "",
            "Pass-rate = pass / (pass + fail); n/a is excluded from the "
            "denominator and reported separately (n/a is missing-not-at-random). "
            "Ceiling/floor: a rate ≥0.90 or ≤0.10 has low discriminating power — "
            "read with the base rate, do not headline a ceilinged axis.",
            "",
            "| Rubric | Axis | pass | fail | n/a | pass-rate | n/a-rate | flag |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for (rubric_id, axis) in sorted(binary_tally):
            t = binary_tally[(rubric_id, axis)]
            denom = t["pass"] + t["fail"]
            total = denom + t["na"]
            rate = (t["pass"] / denom) if denom else None
            na_rate = (t["na"] / total) if total else 0.0
            flag = ""
            if rate is not None and (rate >= 0.90 or rate <= 0.10):
                flag = "ceiling/floor"
            rate_s = f"{rate:.2f}" if rate is not None else "—"
            rate_lines.append(
                f"| {rubric_id} | {axis} | {t['pass']} | {t['fail']} | {t['na']} | "
                f"{rate_s} | {na_rate:.2f} | {flag} |"
            )
            brows.append({
                "rubric_id": rubric_id, "axis": axis,
                "pass": t["pass"], "fail": t["fail"], "na": t["na"],
                "pass_rate": rate_s, "na_rate": f"{na_rate:.2f}", "flag": flag,
            })
        (sio.version_dir(version) / "binary-rates.md").write_text("\n".join(rate_lines) + "\n")
        sio.write_csv(
            sio.version_dir(version) / "binary-rates.csv", brows,
            fieldnames=["rubric_id", "axis", "pass", "fail", "na", "pass_rate", "na_rate", "flag"],
        )

    # Per-scenario per-rubric mean (averaged across that rubric's axes for the
    # scenario). Each rubric uses different axis names, so disagreement is
    # measured at the scenario level — does the rubric, taken as a whole, say
    # the runs of this scenario were strong or weak?
    scenario_rubric_means: dict[tuple[str, str], float] = {}
    for (scenario_id, axis_name), rubric_map in axis_scores.items():
        for r, scores in rubric_map.items():
            non_null = [s for s in scores if s is not None]
            if not non_null:
                continue
            scenario_rubric_means.setdefault((scenario_id, r), []).append(
                sum(non_null) / len(non_null)
            )

    # Flatten the per-axis means within (scenario, rubric) into one overall mean.
    flattened: dict[tuple[str, str], float] = {
        k: sum(v) / len(v) for k, v in scenario_rubric_means.items()
    }

    matrix_lines = [
        "# Disagreement matrix",
        "",
        f"Workspace version: `{version}`",
        f"Generated at: {_now()}",
        "",
        "Each rubric uses its own axes; comparison is at the **scenario level**. "
        "The cell shows the per-rubric mean (averaged across that rubric's "
        "axes, then across the N=5 runs of that scenario). The spread column "
        "is the difference between the highest- and lowest-scoring rubric for "
        "the scenario; spread ≥ 1.0 is flagged as rubric tension worth a closer "
        "look. The size of the spread tells you how much the rubrics disagree "
        "about whether the workspace handled that scenario well — disagreement "
        "is the load-bearing output of this benchmark, not raw scores.",
        "",
        "| Scenario | "
        + " | ".join(f"{r} mean" for r in rubrics)
        + " | Spread | Tension? |",
        "|---|"
        + "|".join("---" for _ in rubrics)
        + "|---|---|",
    ]
    scenarios_sorted = sorted({k[0] for k in flattened.keys()})
    flagged = 0
    for scenario_id in scenarios_sorted:
        cells: list[str] = []
        means_here: list[float] = []
        for r in rubrics:
            value = flattened.get((scenario_id, r))
            if value is None:
                cells.append("—")
                continue
            cells.append(f"{value:.2f}")
            means_here.append(value)
        if len(means_here) >= 2:
            spread = max(means_here) - min(means_here)
            tension = "yes" if spread >= 1.0 else ""
            if tension:
                flagged += 1
        else:
            spread = 0.0
            tension = ""
        matrix_lines.append(
            f"| {scenario_id} | "
            + " | ".join(cells)
            + f" | {spread:.2f} | {tension} |"
        )

    matrix_lines.append("")
    matrix_lines.append(
        f"**Flagged scenarios (rubric spread ≥ 1.0):** {flagged}"
    )

    # Per-axis detail table for the curious — useful for digging into why a
    # scenario was flagged. Not aggregated across rubrics (axes are disjoint),
    # just laid out side by side.
    matrix_lines.extend(
        [
            "",
            "## Per-axis means (within each rubric, across runs)",
            "",
            "Each rubric uses its own axis names; rows where the same scenario "
            "appears under different rubrics are NOT directly comparable. The "
            "table is provided as a drill-down from the scenario-level "
            "disagreement above.",
            "",
            "| Scenario | Rubric | Axis | Mean | N |",
            "|---|---|---|---|---|",
        ]
    )
    for (scenario_id, axis_name), rubric_map in sorted(axis_scores.items()):
        for r in rubrics:
            scores = [s for s in rubric_map.get(r, []) if s is not None]
            if not scores:
                continue
            matrix_lines.append(
                f"| {scenario_id} | {r} | {axis_name} | "
                f"{sum(scores)/len(scores):.2f} | {len(scores)} |"
            )

    (sio.version_dir(version) / "disagreement-matrix.md").write_text(
        "\n".join(matrix_lines) + "\n"
    )

    # Manifest writeback.
    manifest_path = sio.version_dir(version) / "manifest.json"
    if manifest_path.exists():
        manifest = sio.read_json(manifest_path)
    else:
        manifest = {}
    manifest.setdefault("workspace_tag", version)
    manifest.setdefault("workspace_sha", _git_sha(sio.REPO_ROOT))
    manifest["aggregated_at"] = _now()
    manifest["n_runs_planned"] = args.n_runs
    manifest["scenarios_count"] = len(scenario_ids)
    manifest["rubrics"] = rubrics
    # Stamp rubric versions as a postcondition of aggregate (not an opt-in
    # validate flag), so the compare version-gate cannot be bypassed by
    # skipping a step. Only for content-epoch tags: a legacy frozen tag was
    # scored under older rubric files, so re-aggregating it must NOT stamp
    # today's versions onto it.
    if manifest.get("content_schema") is not None and "rubric_versions" not in manifest:
        manifest["rubric_versions"] = {
            r: (metas[r].rubric_version if metas[r] else "unversioned") for r in rubrics
        }
    sio.write_json(manifest_path, manifest)

    print(
        f"Aggregated {sum(len(v) for v in rows_by_rubric.values())} score rows "
        f"into {scores_dir.relative_to(sio.REPO_ROOT)}. "
        f"Flagged cells: {flagged}. "
        f"Manifest: {manifest_path.relative_to(sio.REPO_ROOT)}"
    )
    return 0


def _canonical_axis(axis_name: str, canonical: tuple[str, ...]) -> str | None:
    """Map a possibly-drifted axis name onto its canonical id.

    Score files exist with both `CE1` and `CE1_orientation_cost` for the same
    axis; the canonical id is the prefix before the first underscore when that
    prefix is a declared axis. Returns None for names that match nothing.
    """
    if axis_name in canonical:
        return axis_name
    prefix = axis_name.split("_", 1)[0]
    return prefix if prefix in canonical else None


def _scenario_ids_on_disk(version: str, rubrics: list[str]) -> list[str]:
    return sorted(
        {
            d.name
            for rubric_id in rubrics
            for d in (sio.version_dir(version) / "scores" / rubric_id).glob("*/")
            if d.is_dir()
        }
    )


def _validate_content_run(
    rel: Path,
    payload: dict,
    errors: list[str],
    warnings: list[str],
    models_seen: set[str],
) -> None:
    """Enforce the content-epoch transcript contract on one run file.

    Catches a half-migrated run (missing model, content, or a malformed
    action) instead of letting the diff reconstruct against it silently.
    """
    model = payload.get("model")
    if not model:
        errors.append(f"{rel}: content-epoch run missing required 'model'")
    else:
        models_seen.add(model)
    if "variant" not in payload:
        errors.append(
            f"{rel}: content-epoch run missing 'variant' "
            "(null for full template, else the control-variant name)"
        )

    actions = payload.get("actions")
    if not isinstance(actions, list):
        return  # the base-field check already flagged a missing/bad actions
    for i, action in enumerate(actions):
        where = f"{rel}: action[{i}]"
        verb = action.get("action")
        path = action.get("path", "")
        if verb not in ("create", "append", "rewrite", "delete"):
            errors.append(f"{where}: bad action verb {verb!r}")
        if not path or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"{where}: path {path!r} must be relative, non-traversing")
        if verb in ("create", "rewrite", "append"):
            if "content" not in action:
                errors.append(f"{where} ({verb} {path}): missing 'content'")
            if "sha256" not in action:
                warnings.append(f"{where} ({verb} {path}): missing 'sha256' (unverifiable)")
        elif verb == "delete" and "content" in action:
            warnings.append(f"{where} (delete {path}): 'content' ignored on delete")


def cmd_validate(args: argparse.Namespace) -> int:
    """Check a results tag against the AGENTS.md postconditions.

    Errors (exit 1): invalid JSON, axis names matching no declared axis,
    scores outside 0-3/n/a, rubrics without front-matter.
    Warnings (exit 0): drifted axis names, n/a on axes not declared
    na_allowed, n/a encoded as something other than the string "n/a",
    missing runs/scores relative to n_runs, missing manifest fields.
    """
    version = args.version
    rubrics = sio.list_rubrics()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = sio.version_dir(version) / "manifest.json"
    manifest = sio.read_json(manifest_path) if manifest_path.exists() else {}
    # The content-schema epoch gates the new artifact-grounding requirements.
    # Legacy tags (v0.1-v0.3) carry no marker -> the new checks do not apply,
    # so they remain valid unchanged.
    content_epoch = manifest.get("content_schema") is not None
    models_seen: set[str] = set()

    metas: dict[str, sio.RubricMeta] = {}
    for rubric_id in rubrics:
        meta = sio.rubric_meta(rubric_id)
        if meta is None:
            errors.append(f"rubric {rubric_id}: no front-matter (axes undeclared)")
            continue
        metas[rubric_id] = meta
        # axis_types integrity: declared kinds must cover exactly the axes, and
        # deterministic axes must all be binary (a code check on an ordinal axis
        # is a category error).
        if meta.axis_types:
            extra = set(meta.axis_types) - set(meta.axes)
            missing = set(meta.axes) - set(meta.axis_types)
            if extra:
                errors.append(f"rubric {rubric_id}: axis_types names non-axes {sorted(extra)}")
            if missing:
                errors.append(f"rubric {rubric_id}: axis_types omits axes {sorted(missing)}")
            bad_kind = {a: k for a, k in meta.axis_types.items() if k not in ("ordinal", "binary")}
            if bad_kind:
                errors.append(f"rubric {rubric_id}: bad axis kinds {bad_kind}")
        non_binary_det = [a for a in meta.deterministic if not meta.is_binary(a)]
        if non_binary_det:
            errors.append(
                f"rubric {rubric_id}: deterministic axes {non_binary_det} are not binary"
            )

    scenario_ids = _scenario_ids_on_disk(version, rubrics)
    if not scenario_ids:
        errors.append(f"{version}: no score files found")

    n = args.n_runs
    score_files = 0
    for rubric_id, meta in metas.items():
        for scenario_id in scenario_ids:
            present = 0
            for run_number in range(1, n + 1):
                p = sio.score_path(version, rubric_id, scenario_id, run_number)
                if not p.exists():
                    continue
                present += 1
                score_files += 1
                rel = p.relative_to(sio.REPO_ROOT)
                try:
                    payload = sio.read_json(p)
                except Exception as exc:
                    errors.append(f"{rel}: invalid JSON ({exc})")
                    continue
                axes = payload.get("axes", {})
                seen: set[str] = set()
                for axis_name, axis_payload in axes.items():
                    canon = _canonical_axis(axis_name, meta.axes)
                    if canon is None:
                        errors.append(
                            f"{rel}: axis {axis_name!r} matches no declared "
                            f"axis of {rubric_id} {meta.axes}"
                        )
                        continue
                    if axis_name != canon:
                        warnings.append(
                            f"{rel}: drifted axis name {axis_name!r} (canonical {canon})"
                        )
                    seen.add(canon)
                    score = axis_payload.get("score")
                    if isinstance(score, int):
                        if not 0 <= score <= 3:
                            errors.append(f"{rel}: {canon} score {score} outside 0-3")
                    elif score == "n/a" or score is None:
                        if canon not in meta.na_allowed:
                            warnings.append(
                                f"{rel}: n/a on {canon}, not declared na_allowed"
                            )
                        if score is None:
                            warnings.append(
                                f"{rel}: {canon} uses null for n/a (expected \"n/a\")"
                            )
                    else:
                        errors.append(
                            f"{rel}: {canon} score {score!r} is neither int nor n/a"
                        )
                    if not str(axis_payload.get("justification", "")).strip():
                        warnings.append(f"{rel}: {canon} has empty justification")
                missing = set(meta.axes) - seen
                if missing:
                    errors.append(f"{rel}: missing axes {sorted(missing)}")
            if 0 < present < n:
                warnings.append(
                    f"{version}/{rubric_id}/{scenario_id}: {present}/{n} score files"
                )

    run_files = 0
    runs_root = sio.version_dir(version) / "runs"
    for scenario_id in scenario_ids:
        for run_number in range(1, n + 1):
            p = sio.run_path(version, scenario_id, run_number)
            if not p.exists():
                warnings.append(
                    f"{version}/runs/{scenario_id}/{run_number:02d}: missing run file"
                )
                continue
            run_files += 1
            rel = p.relative_to(sio.REPO_ROOT)
            try:
                payload = sio.read_json(p)
            except Exception as exc:
                errors.append(f"{rel}: invalid JSON ({exc})")
                continue
            for field in ("scenario_id", "run_number", "final_response", "actions"):
                if field not in payload:
                    errors.append(f"{rel}: missing field {field!r}")
            if content_epoch:
                _validate_content_run(rel, payload, errors, warnings, models_seen)

    if content_epoch and len(models_seen) > 1:
        errors.append(
            f"{version}: runs use multiple models {sorted(models_seen)}; a "
            "version must be a single pinned model for comparison validity"
        )

    if not manifest:
        warnings.append(f"{version}: no manifest.json")
    if "scoring_granularity" not in manifest:
        warnings.append(
            f"{version}: manifest does not record scoring_granularity "
            "(isolated vs batched rater dispatch)"
        )

    if args.update_manifest and manifest_path.exists():
        manifest["validated_at"] = _now()
        manifest["validation"] = {
            "errors": len(errors),
            "warnings": len(warnings),
            "run_files": run_files,
            "score_files": score_files,
        }
        manifest["rubric_versions"] = {
            r: m.rubric_version for r, m in metas.items()
        }
        sio.write_json(manifest_path, manifest)

    for msg in errors:
        print(f"ERROR   {msg}")
    for msg in warnings:
        print(f"warning {msg}")
    print(
        f"Validate {version}: {len(scenario_ids)} scenarios, {run_files} run "
        f"files, {score_files} score files, {len(errors)} errors, "
        f"{len(warnings)} warnings"
    )
    return 1 if errors else 0


# Two-sided 97.5th percentile of Student's t, for 95% CIs on paired
# scenario-level deltas. Indexed by degrees of freedom.
T_975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
    14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
    20: 2.086, 25: 2.060, 30: 2.042,
}


def _t975(df: int) -> float:
    if df in T_975:
        return T_975[df]
    keys = sorted(T_975)
    for k in reversed(keys):
        if df >= k:
            return T_975[k]
    return T_975[keys[0]]


def _version_cell_stats(
    version: str, rubrics: list[str], metas: dict[str, "sio.RubricMeta"], n_runs: int
) -> dict[tuple[str, str], dict]:
    """Per (scenario, rubric): rubric mean, n/a rate, and observation counts.

    Replicates the aggregate-step estimator: mean over runs within each axis
    (int scores only), then mean over axes. Axis names are normalized onto
    the canonical schema. n/a rate counts non-int scores over all axis
    observations.
    """
    cells: dict[tuple[str, str], dict] = {}
    scenario_ids = _scenario_ids_on_disk(version, rubrics)
    for rubric_id in rubrics:
        meta = metas[rubric_id]
        for scenario_id in scenario_ids:
            axis_vals: dict[str, list[int]] = {}
            total_obs = 0
            na_obs = 0
            min_axis_n: int | None = None
            for run_number in range(1, n_runs + 1):
                p = sio.score_path(version, rubric_id, scenario_id, run_number)
                if not p.exists():
                    continue
                for axis_name, axis_payload in sio.read_json(p).get(
                    "axes", {}
                ).items():
                    canon = _canonical_axis(axis_name, meta.axes)
                    if canon is None:
                        continue
                    total_obs += 1
                    score = axis_payload.get("score")
                    if isinstance(score, int):
                        axis_vals.setdefault(canon, []).append(score)
                    else:
                        na_obs += 1
            if not total_obs:
                continue
            axis_means = [sum(v) / len(v) for v in axis_vals.values()]
            if axis_vals:
                min_axis_n = min(len(v) for v in axis_vals.values())
            cells[(scenario_id, rubric_id)] = {
                "mean": sum(axis_means) / len(axis_means) if axis_means else None,
                "na_rate": na_obs / total_obs,
                "n_obs": total_obs - na_obs,
                "min_axis_n": min_axis_n,
            }
    return cells


def cmd_compare(args: argparse.Namespace) -> int:
    """Compute the baseline→revised delta tables deterministically.

    Refuses to compare across different rubric versions: when scoring
    semantics change, the baseline's affected axes must be re-scored under
    the new policy first (common measurement frame). Manifests that predate
    rubric versioning require --assume-same-rubrics to proceed.
    """
    baseline, revised = args.baseline, args.revised
    rubrics = sio.list_rubrics()
    metas: dict[str, sio.RubricMeta] = {}
    for rubric_id in rubrics:
        meta = sio.rubric_meta(rubric_id)
        if meta is None:
            print(f"ERROR: rubric {rubric_id} has no front-matter", file=sys.stderr)
            return 1
        metas[rubric_id] = meta

    # Rubric-version gate.
    manifests = {}
    for tag in (baseline, revised):
        mp = sio.version_dir(tag) / "manifest.json"
        if not mp.exists():
            print(f"ERROR: {tag} has no manifest.json", file=sys.stderr)
            return 1
        manifests[tag] = sio.read_json(mp)
    recorded = [manifests[t].get("rubric_versions") for t in (baseline, revised)]
    if recorded[0] is None or recorded[1] is None:
        if not args.assume_same_rubrics:
            print(
                "ERROR: one or both tags predate rubric versioning (no "
                "rubric_versions in manifest). If both were scored under "
                "identical rubric semantics, re-run with "
                "--assume-same-rubrics. If semantics changed between them "
                "(e.g. the v0.1→v0.2 SA2 n/a policy), the baseline's "
                "affected axes must be re-scored under the newer policy "
                "before comparison.",
                file=sys.stderr,
            )
            return 1
    elif recorded[0] != recorded[1]:
        print(
            f"ERROR: rubric versions differ between {baseline} {recorded[0]} "
            f"and {revised} {recorded[1]}. Re-score the baseline's affected "
            "axes under the newer rubric before comparing (common "
            "measurement frame); a version-pin mismatch is not a footnote.",
            file=sys.stderr,
        )
        return 1

    n = args.n_runs
    base_cells = _version_cell_stats(baseline, rubrics, metas, n)
    rev_cells = _version_cell_stats(revised, rubrics, metas, n)

    base_scn = {k[0] for k in base_cells}
    rev_scn = {k[0] for k in rev_cells}
    common = sorted(base_scn & rev_scn)
    asym = sorted(base_scn ^ rev_scn)

    batched = any(
        "batched" in str(manifests[t].get("scoring_granularity", "unrecorded"))
        or "scoring_granularity" not in manifests[t]
        for t in (baseline, revised)
    )

    lines = [
        f"# {baseline} → {revised} — deterministic comparison",
        "",
        f"Generated by `runner.py compare` at {_now()}.",
        f"Common scenarios: {len(common)}"
        + (f" (asymmetric, excluded: {', '.join(asym)})" if asym else ""),
        "",
    ]
    if batched:
        lines += [
            "> **Dependence caveat.** At least one side of this comparison "
            "was batch-scored (or has unrecorded scoring granularity): "
            "scores within a (scenario, rubric) batch are not independent, "
            "so the intervals below understate uncertainty by an unknown "
            "amount. See the scoring-protocol disclosure in the tags' "
            "summary.md files.",
            "",
        ]

    # Per-scenario delta table.
    lines += [
        "## Per-scenario per-rubric delta (revised − baseline)",
        "",
        "Cells show Δ mean, with Δ n/a-rate in parentheses when either side "
        "has any n/a observations (n/a is missing-not-at-random here: axis "
        "applicability depends on agent behavior, so a mean delta can be a "
        "composition shift). `†` marks cells where any contributing axis "
        "mean rests on fewer than 3 runs on either side.",
        "",
        "| Scenario | " + " | ".join(f"{r} Δ" for r in rubrics) + " |",
        "|---|" + "|".join("---" for _ in rubrics) + "|",
    ]
    csv_rows: list[dict] = []
    for scenario_id in common:
        cells_out = []
        for r in rubrics:
            b = base_cells.get((scenario_id, r))
            v = rev_cells.get((scenario_id, r))
            if not b or not v or b["mean"] is None or v["mean"] is None:
                cells_out.append("—")
                continue
            delta = v["mean"] - b["mean"]
            na_delta = v["na_rate"] - b["na_rate"]
            thin = (
                (b["min_axis_n"] is not None and b["min_axis_n"] < 3)
                or (v["min_axis_n"] is not None and v["min_axis_n"] < 3)
            )
            cell = f"{delta:+.2f}"
            if b["na_rate"] or v["na_rate"]:
                cell += f" (n/a {na_delta:+.2f})"
            if thin:
                cell += " †"
            cells_out.append(cell)
            csv_rows.append(
                {
                    "scenario_id": scenario_id,
                    "rubric": r,
                    "baseline_mean": f"{b['mean']:.4f}",
                    "revised_mean": f"{v['mean']:.4f}",
                    "delta": f"{delta:.4f}",
                    "baseline_na_rate": f"{b['na_rate']:.4f}",
                    "revised_na_rate": f"{v['na_rate']:.4f}",
                    "baseline_n_obs": b["n_obs"],
                    "revised_n_obs": v["n_obs"],
                }
            )
        lines.append(f"| {scenario_id} | " + " | ".join(cells_out) + " |")

    # Per-rubric paired summary across scenarios.
    lines += [
        "",
        "## Per-rubric paired summary (across common scenarios)",
        "",
        "Mean of the per-scenario deltas with a t-interval over scenarios "
        "(the inference target is this fixed scenario set, not a scenario "
        "population). A CI excluding 0 is a direction signal under the "
        "dependence caveat above; it is not a magnitude claim.",
        "",
        "| Rubric | n scenarios | mean Δ | sd | 95% CI |",
        "|---|---|---|---|---|",
    ]
    for r in rubrics:
        deltas = [
            rev_cells[(s, r)]["mean"] - base_cells[(s, r)]["mean"]
            for s in common
            if (s, r) in base_cells
            and (s, r) in rev_cells
            and base_cells[(s, r)]["mean"] is not None
            and rev_cells[(s, r)]["mean"] is not None
        ]
        k = len(deltas)
        if k < 2:
            lines.append(f"| {r} | {k} | — | — | — |")
            continue
        mean = sum(deltas) / k
        var = sum((d - mean) ** 2 for d in deltas) / (k - 1)
        sd = var ** 0.5
        half = _t975(k - 1) * sd / k ** 0.5
        lines.append(
            f"| {r} | {k} | {mean:+.3f} | {sd:.3f} | "
            f"[{mean - half:+.3f}, {mean + half:+.3f}] |"
        )

    out_md = sio.version_dir(revised) / f"compare-vs-{baseline}.md"
    out_md.write_text("\n".join(lines) + "\n")
    out_csv = sio.version_dir(revised) / f"compare-vs-{baseline}.csv"
    sio.write_csv(
        out_csv,
        csv_rows,
        fieldnames=[
            "scenario_id", "rubric", "baseline_mean", "revised_mean", "delta",
            "baseline_na_rate", "revised_na_rate", "baseline_n_obs",
            "revised_n_obs",
        ],
    )
    print(
        f"Compared {len(common)} scenarios × {len(rubrics)} rubrics. "
        f"Wrote {out_md.relative_to(sio.REPO_ROOT)} and "
        f"{out_csv.relative_to(sio.REPO_ROOT)}"
    )
    return 0


RESCORE_RUNS = (2, 4)  # fixed stratified picks: 2 runs per (scenario, rubric)
REDACTED_FIELDS = ("workspace_tag",)  # version-identifying transcript fields


def _scenario_brief_path(scenario_id: str) -> Path:
    """Leakage-free rater brief for active or retired scenarios.

    Returns the public brief (answer key removed); falls back to the full
    scenario.md only for retired scenarios that predate public-brief
    generation, so an old reliability rescore still resolves.
    """
    active_public = sio.SCENARIOS_ROOT / scenario_id / "scenario-public.md"
    if active_public.exists():
        return active_public
    retired_public = sio.BENCH_ROOT / "scenarios-retired" / scenario_id / "scenario-public.md"
    if retired_public.exists():
        return retired_public
    return sio.BENCH_ROOT / "scenarios-retired" / scenario_id / "scenario.md"


def cmd_rescore_sample(args: argparse.Namespace) -> int:
    """Enumerate the reliability rescore sample and stage redacted inputs.

    For each (scenario, rubric) cell of the tag, runs RESCORE_RUNS are
    rescored in fresh isolated rater contexts. Transcript copies are staged
    with version-identifying fields stripped so raters are blind to which
    tag they are scoring. Idempotent: existing outputs are skipped.
    """
    version = args.version
    rubrics = sio.list_rubrics()
    rel_root = sio.version_dir(version) / "reliability"
    inputs_root = rel_root / "inputs"
    scenario_ids = _scenario_ids_on_disk(version, rubrics)

    jobs: list[dict] = []
    staged = 0
    for scenario_id in scenario_ids:
        for run_number in RESCORE_RUNS:
            src = sio.run_path(version, scenario_id, run_number)
            if not src.exists():
                continue
            redacted_p = inputs_root / scenario_id / f"{run_number:02d}.json"
            if not redacted_p.exists():
                payload = sio.read_json(src)
                for field in REDACTED_FIELDS:
                    payload.pop(field, None)
                sio.write_json(redacted_p, payload)
                staged += 1
            for rubric_id in rubrics:
                out = (
                    rel_root / "scores" / rubric_id / scenario_id
                    / f"{run_number:02d}.json"
                )
                jobs.append(
                    {
                        "scenario_id": scenario_id,
                        "run_number": run_number,
                        "rubric_id": rubric_id,
                        "rubric_path": str(
                            (sio.RUBRICS_ROOT / f"{rubric_id}.md").relative_to(
                                sio.REPO_ROOT
                            )
                        ),
                        "scenario_brief": str(
                            _scenario_brief_path(scenario_id).relative_to(
                                sio.REPO_ROOT
                            )
                        ),
                        "run_path": str(redacted_p.relative_to(sio.REPO_ROOT)),
                        "score_output": str(out.relative_to(sio.REPO_ROOT)),
                    }
                )

    jobs.sort(key=lambda j: (j["scenario_id"], j["run_number"], j["rubric_id"]))
    jobs_path = rel_root / "rescore-jobs.jsonl"
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        "\n".join(__import__("json").dumps(j, sort_keys=True) for j in jobs) + "\n"
    )
    pending = [
        j for j in jobs if not (sio.REPO_ROOT / j["score_output"]).exists()
    ]
    print(
        f"Rescore sample for {version}: {len(jobs)} jobs "
        f"({len(scenario_ids)} scenarios × runs {RESCORE_RUNS} × "
        f"{len(rubrics)} rubrics). Staged {staged} redacted inputs. "
        f"Pending: {len(pending)}. Written: "
        f"{jobs_path.relative_to(sio.REPO_ROOT)}"
    )
    return 0


def _ordinal_alpha(pairs: list[tuple[int, int]]) -> float | None:
    """Krippendorff's alpha for two raters on an ordinal scale.

    `pairs` holds (original, rescore) integer scores per unit; units with a
    missing side are excluded by the caller (alpha's missing-data handling
    reduces to listwise deletion in the two-rater case). Ordinal distance
    uses the standard marginal-rank metric over the coincidence matrix.
    """
    if not pairs:
        return None
    values = sorted({v for p in pairs for v in p})
    if len(values) == 1:
        return None  # no variation: alpha undefined
    # Coincidence matrix: each pair contributes both orderings.
    n_ck: dict[tuple[int, int], float] = {}
    for a, b in pairs:
        n_ck[(a, b)] = n_ck.get((a, b), 0) + 1
        n_ck[(b, a)] = n_ck.get((b, a), 0) + 1
    n_c = {c: sum(v for (a, _), v in n_ck.items() if a == c) for c in values}
    n_total = sum(n_c.values())

    def delta_sq(c: int, k: int) -> float:
        lo, hi = min(c, k), max(c, k)
        between = sum(n_c[g] for g in values if lo <= g <= hi)
        return (between - (n_c[c] + n_c[k]) / 2) ** 2

    d_o = sum(
        n_ck.get((c, k), 0) * delta_sq(c, k)
        for c in values
        for k in values
        if c != k
    )
    d_e = sum(
        n_c[c] * n_c[k] * delta_sq(c, k)
        for c in values
        for k in values
        if c != k
    ) / (n_total - 1)
    if d_e == 0:
        return None
    return 1 - d_o / d_e


def cmd_reliability(args: argparse.Namespace) -> int:
    """Pair original and rescored scores; write reliability.md.

    Per rubric (axes pooled): ordinal Krippendorff's alpha, exact and
    within-1 agreement. Per axis: raw agreement counts (alpha at axis level
    is underpowered at this sample size and degenerates on near-constant
    axes — raw agreement is reported instead).

    By default the comparison rater is the same-family rescore set written
    by `rescore-sample` (job["score_output"]). Pass --rater-dir to compare
    the originals against an alternative rater's scores (e.g. a cross-family
    model's output from xfamily_rater.py); the directory must mirror the
    scores layout (<rubric>/<scenario>/<run>.json). --label names the
    output report reliability-<label>.md.
    """
    version = args.version
    rubrics = sio.list_rubrics()
    metas = {r: sio.rubric_meta(r) for r in rubrics}
    rel_root = sio.version_dir(version) / "reliability"
    rater_dir = (sio.REPO_ROOT / args.rater_dir) if args.rater_dir else None
    label = args.label
    if rater_dir is not None and not label:
        print("--rater-dir requires --label (names the report)")
        return 1
    if rater_dir is not None and not rater_dir.is_dir():
        print(f"rater dir not found: {rater_dir}")
        return 1

    # Binary axes are excluded from ordinal alpha only for content-epoch tags;
    # a legacy tag scored everything ordinal and its committed report must
    # reproduce.
    _mpath = sio.version_dir(version) / "manifest.json"
    _m = sio.read_json(_mpath) if _mpath.exists() else {}
    rel_content_epoch = _m.get("content_schema") is not None

    per_rubric_pairs: dict[str, list[tuple[int, int]]] = {r: [] for r in rubrics}
    per_axis: dict[tuple[str, str], dict] = {}
    na_disagreements: list[str] = []
    n_jobs = n_scored = 0

    for job in sio.read_jsonl(rel_root / "rescore-jobs.jsonl"):
        n_jobs += 1
        rubric_id = job["rubric_id"]
        meta = metas[rubric_id]
        if rater_dir is not None:
            rescore_p = (
                rater_dir / rubric_id / job["scenario_id"]
                / f"{job['run_number']:02d}.json"
            )
        else:
            rescore_p = sio.REPO_ROOT / job["score_output"]
        orig_p = sio.score_path(
            version, rubric_id, job["scenario_id"], job["run_number"]
        )
        if not rescore_p.exists() or not orig_p.exists():
            continue
        n_scored += 1
        orig_axes = sio.read_json(orig_p).get("axes", {})
        new_axes = sio.read_json(rescore_p).get("axes", {})

        def canon_map(axes: dict) -> dict:
            out = {}
            for name, payload in axes.items():
                c = _canonical_axis(name, meta.axes)
                if c:
                    out[c] = payload.get("score")
            return out

        o_map, n_map = canon_map(orig_axes), canon_map(new_axes)
        for axis in meta.axes:
            # Ordinal Krippendorff's alpha is meaningless over binary pass/fail
            # axes; exclude them (their agreement is reported as raw percent in
            # the binary-rates path, not pooled into alpha). Content-epoch only,
            # so legacy reports reproduce.
            if rel_content_epoch and meta.is_binary(axis):
                continue
            o, n_ = o_map.get(axis), n_map.get(axis)
            o_int, n_int = (
                isinstance(o, int) and not isinstance(o, bool),
                isinstance(n_, int) and not isinstance(n_, bool),
            )
            stats = per_axis.setdefault(
                (rubric_id, axis),
                {"n": 0, "exact": 0, "within1": 0, "na_mismatch": 0},
            )
            if o_int and n_int:
                stats["n"] += 1
                stats["exact"] += o == n_
                stats["within1"] += abs(o - n_) <= 1
                per_rubric_pairs[rubric_id].append((o, n_))
            elif o_int != n_int:
                stats["na_mismatch"] += 1
                na_disagreements.append(
                    f"{job['scenario_id']}/{job['run_number']:02d} "
                    f"{rubric_id}.{axis}: original={o!r} rescore={n_!r}"
                )

    title = f"# Judge reliability — {version}"
    if label:
        title += f" — cross-rater: {label}"
    lines = [
        title,
        "",
        f"Generated by `runner.py reliability` at {_now()}.",
        f"Sample: runs {RESCORE_RUNS} per (scenario, rubric); "
        f"{n_scored}/{n_jobs} rescore jobs completed. Original scores were "
        "produced under the isolated protocol; rescores use fresh isolated "
        "rater contexts with version-identifying transcript fields redacted."
        + (
            f" Comparison rater: {label} (scores from "
            f"`{rater_dir.relative_to(sio.REPO_ROOT)}`), against the "
            "original Claude-family raters."
            if label
            else ""
        ),
        "",
        "## Per-rubric reliability (axes pooled)",
        "",
        "Krippendorff's alpha, ordinal metric, two raters (original vs "
        "rescore), units with n/a on either side excluded (counted "
        "separately below). Interpretation convention: alpha ≥ 0.80 "
        "reliable; 0.67–0.80 tentative; < 0.67 insufficient to support "
        "the delta tables.",
        "",
        "| Rubric | paired units | alpha (ordinal) | exact | within-1 |",
        "|---|---|---|---|---|",
    ]
    for r in rubrics:
        pairs = per_rubric_pairs[r]
        axes_stats = [v for (rr, _), v in per_axis.items() if rr == r]
        n_units = len(pairs)
        exact = sum(1 for a, b in pairs if a == b)
        within1 = sum(1 for a, b in pairs if abs(a - b) <= 1)
        alpha = _ordinal_alpha(pairs)
        alpha_s = f"{alpha:.3f}" if alpha is not None else "undefined"
        if n_units:
            lines.append(
                f"| {r} | {n_units} | {alpha_s} | "
                f"{exact / n_units:.0%} | {within1 / n_units:.0%} |"
            )
        else:
            lines.append(f"| {r} | 0 | — | — | — |")

    lines += [
        "",
        "## Per-axis raw agreement",
        "",
        "Axis-level alpha is underpowered at this n and degenerates on "
        "near-constant axes; raw agreement is reported instead.",
        "",
        "| Rubric | Axis | n | exact | within-1 | n/a mismatches |",
        "|---|---|---|---|---|---|",
    ]
    for (r, axis), s in sorted(per_axis.items()):
        if s["n"]:
            lines.append(
                f"| {r} | {axis} | {s['n']} | {s['exact'] / s['n']:.0%} | "
                f"{s['within1'] / s['n']:.0%} | {s['na_mismatch']} |"
            )
        else:
            lines.append(
                f"| {r} | {axis} | 0 | — | — | {s['na_mismatch']} |"
            )

    if na_disagreements:
        lines += [
            "",
            "## n/a applicability disagreements",
            "",
            "One rater scored, the other said n/a — applicability judgment "
            "drift, the same class of defect as the v0.1→v0.2 SA2 policy "
            "shift:",
            "",
        ]
        lines += [f"- {d}" for d in na_disagreements]

    lines += [
        "",
        "## Limitations",
        "",
        "- Two ratings per unit; test-retest stability, not a validity claim.",
    ]
    if label:
        lines += [
            "- Disagreement here confounds family difference with capability "
            "difference: a weaker cross-family judge missing a subtlety is "
            "indistinguishable from a genuine rubric-interpretation split. "
            "Read alongside the same-family report (`reliability.md`).",
            "- The original raters' model pin was not recorded in the "
            "manifest; the Claude side of each pair is approximate.",
        ]
    else:
        lines += [
            "- The original raters' model pin was not recorded in the manifest; "
            "rescore raters may differ in model version. Agreement here is a "
            "lower bound on same-model stability.",
            "- Same model family on both sides; self-preference bias is not "
            "bounded by this study (see the `reliability-*.md` cross-rater "
            "reports where present).",
        ]
    out = rel_root / (f"reliability-{label}.md" if label else "reliability.md")
    out.write_text("\n".join(lines) + "\n")
    print(
        f"Reliability report: {out.relative_to(sio.REPO_ROOT)} "
        f"({n_scored}/{n_jobs} jobs scored)"
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Print completion counts per stage."""
    version = args.version
    scenarios = sio.list_scenarios()
    rubrics = sio.list_rubrics()
    n = args.n_runs

    sim_total = len(scenarios) * n
    sim_done = sum(
        1
        for s in scenarios
        for r in range(1, n + 1)
        if sio.run_path(version, s.id, r).exists()
    )
    score_total = sim_total * len(rubrics)
    score_done = sum(
        1
        for s in scenarios
        for r in range(1, n + 1)
        for rb in rubrics
        if sio.score_path(version, rb, s.id, r).exists()
    )
    print(f"Version: {version}")
    print(f"Simulation runs: {sim_done} / {sim_total}")
    print(f"Scoring calls:   {score_done} / {score_total}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="flatfile-agent-workspace bench runner")
    parser.add_argument(
        "--n-runs", type=int, default=N_RUNS_DEFAULT,
        help="Number of runs per scenario (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="enumerate simulation jobs")
    p_plan.add_argument("--version", required=True)
    p_plan.set_defaults(func=cmd_plan)

    p_scoring = sub.add_parser("plan-scoring", help="enumerate scoring jobs")
    p_scoring.add_argument("--version", required=True)
    p_scoring.set_defaults(func=cmd_plan_scoring)

    p_stage = sub.add_parser("stage", help="stage a workspace for one run")
    p_stage.add_argument("--version", required=True)
    p_stage.add_argument("--scenario", required=True)
    p_stage.add_argument("--run-number", type=int, required=True)
    p_stage.add_argument(
        "--variant",
        choices=sorted(CONTROL_VARIANTS),
        default=None,
        help="Use a control variant instead of the full template",
    )
    p_stage.set_defaults(func=cmd_stage)

    p_snap = sub.add_parser(
        "snapshot", help="derive a run's actions from its staged workspace"
    )
    p_snap.add_argument("version")
    p_snap.add_argument("scenario")
    p_snap.add_argument("run_number", type=int)
    p_snap.set_defaults(func=cmd_snapshot)

    p_diff = sub.add_parser(
        "diff", help="reconstruct a run's post-workspace; write seed->post diff"
    )
    p_diff.add_argument("version")
    p_diff.add_argument("scenario")
    p_diff.add_argument("run_number", type=int)
    p_diff.set_defaults(func=cmd_diff)

    p_check = sub.add_parser(
        "check", help="compute deterministic axes (AR3/AR4/SA2) into checks/"
    )
    p_check.add_argument("version")
    p_check.add_argument("scenario")
    p_check.add_argument("run_number", type=int)
    p_check.set_defaults(func=cmd_check)

    p_agg = sub.add_parser("aggregate", help="aggregate scores into CSVs and matrix")
    p_agg.add_argument("--version", required=True)
    p_agg.set_defaults(func=cmd_aggregate)

    p_status = sub.add_parser("status", help="print completion counts")
    p_status.add_argument("--version", required=True)
    p_status.set_defaults(func=cmd_status)

    p_val = sub.add_parser(
        "validate", help="check a results tag against AGENTS.md postconditions"
    )
    p_val.add_argument("--version", required=True)
    p_val.add_argument(
        "--update-manifest",
        action="store_true",
        help="record validation result and rubric versions in the manifest",
    )
    p_val.set_defaults(func=cmd_validate)

    p_cmp = sub.add_parser(
        "compare", help="deterministic delta tables between two tags"
    )
    p_cmp.add_argument("--baseline", required=True)
    p_cmp.add_argument("--revised", required=True)
    p_cmp.add_argument(
        "--assume-same-rubrics",
        action="store_true",
        help=(
            "proceed when manifests predate rubric versioning, asserting "
            "both tags were scored under identical rubric semantics"
        ),
    )
    p_cmp.set_defaults(func=cmd_compare)

    p_rs = sub.add_parser(
        "rescore-sample",
        help="enumerate reliability rescore jobs with redacted inputs",
    )
    p_rs.add_argument("--version", required=True)
    p_rs.set_defaults(func=cmd_rescore_sample)

    p_rel = sub.add_parser(
        "reliability", help="pair original vs rescored scores; write report"
    )
    p_rel.add_argument("--version", required=True)
    p_rel.add_argument(
        "--rater-dir",
        default=None,
        help="repo-relative dir of an alternative rater's scores "
        "(mirrors <rubric>/<scenario>/<run>.json layout)",
    )
    p_rel.add_argument(
        "--label",
        default=None,
        help="short rater label; writes reliability-<label>.md "
        "(required with --rater-dir)",
    )
    p_rel.set_defaults(func=cmd_reliability)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
