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
import shutil
import subprocess
import sys
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
                    "scenario_brief": str(scn.brief.relative_to(sio.REPO_ROOT)),
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
                        "scenario_brief": str(scn.brief.relative_to(sio.REPO_ROOT)),
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


def cmd_stage(args: argparse.Namespace) -> int:
    """Stage a fresh workspace for one (scenario, run) pair.

    1. Copy the base tree (template OR control variant) to the workspace path.
    2. Overlay the scenario seed (only files that exist in the seed).

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
    target.parent.mkdir(parents=True, exist_ok=True)

    # 1. Pick the base tree.
    variant = getattr(args, "variant", None)
    if variant:
        if variant not in CONTROL_VARIANTS:
            print(
                f"ERROR: variant {variant} not in {list(CONTROL_VARIANTS)}",
                file=sys.stderr,
            )
            return 2
        base = CONTROL_VARIANTS[variant]
        if not base.exists():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copytree(base, target)
            # Strip .gitkeep markers and the preamble file (preamble is consumed
            # by the dispatch prompt, not by the staged workspace).
            for marker in target.rglob(".gitkeep"):
                marker.unlink()
            preamble = target / "scaffold-preamble.md"
            if preamble.exists():
                preamble.unlink()
    else:
        shutil.copytree(sio.TEMPLATE_ROOT, target)

    # 2. Overlay the seed.
    if scn.seed.exists():
        for src in scn.seed.rglob("*"):
            rel = src.relative_to(scn.seed)
            dst = target / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    print(f"Staged: {target.relative_to(sio.REPO_ROOT)}")
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

    # Per-rubric CSVs.
    rows_by_rubric: dict[str, list[dict]] = {r: [] for r in rubrics}
    # axis_means[(scenario, axis)][rubric] = list of scores
    axis_scores: dict[tuple[str, str], dict[str, list[int]]] = {}

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
                            "score": score,
                            "justification": justification,
                        }
                    )
                    key = (scenario_id, axis_name)
                    axis_scores.setdefault(key, {}).setdefault(
                        rubric_id, []
                    ).append(score if isinstance(score, int) else None)

    scores_dir = sio.version_dir(version) / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    for rubric_id, rows in rows_by_rubric.items():
        out = scores_dir / f"{rubric_id}.csv"
        sio.write_csv(
            out,
            rows,
            fieldnames=["scenario_id", "run_number", "axis", "score", "justification"],
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

    metas: dict[str, sio.RubricMeta] = {}
    for rubric_id in rubrics:
        meta = sio.rubric_meta(rubric_id)
        if meta is None:
            errors.append(f"rubric {rubric_id}: no front-matter (axes undeclared)")
            continue
        metas[rubric_id] = meta

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

    manifest_path = sio.version_dir(version) / "manifest.json"
    manifest = sio.read_json(manifest_path) if manifest_path.exists() else {}
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
