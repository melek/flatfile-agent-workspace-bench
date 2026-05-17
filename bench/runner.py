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


def cmd_stage(args: argparse.Namespace) -> int:
    """Stage a fresh workspace for one (scenario, run) pair.

    1. Copy the template tree to the workspace path.
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

    # 1. Copy template tree.
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
    scenarios = sio.list_scenarios()

    # Per-rubric CSVs.
    rows_by_rubric: dict[str, list[dict]] = {r: [] for r in rubrics}
    # axis_means[(scenario, axis)][rubric] = list of scores
    axis_scores: dict[tuple[str, str], dict[str, list[int]]] = {}

    for rubric_id in rubrics:
        for scn in scenarios:
            for run_number in range(1, args.n_runs + 1):
                p = sio.score_path(version, rubric_id, scn.id, run_number)
                if not p.exists():
                    continue
                payload = sio.read_json(p)
                axes = payload.get("axes", {})
                for axis_name, axis_payload in axes.items():
                    score = axis_payload.get("score")
                    justification = axis_payload.get("justification", "")
                    rows_by_rubric[rubric_id].append(
                        {
                            "scenario_id": scn.id,
                            "run_number": run_number,
                            "axis": axis_name,
                            "score": score,
                            "justification": justification,
                        }
                    )
                    key = (scn.id, axis_name)
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

    # Disagreement matrix: per (scenario, axis), compute the spread of rubric
    # means. Flag spread >= 2 as a disagreement.
    matrix_lines = [
        "# Disagreement matrix",
        "",
        f"Workspace version: `{version}`",
        f"Generated at: {_now()}",
        "",
        "Cell shows the mean score per rubric for a (scenario, axis) pair, "
        "followed by the spread between the highest- and lowest-scoring "
        "rubrics. Spread ≥ 2 is flagged as rubric tension.",
        "",
        "| Scenario | Axis | "
        + " | ".join(f"{r} mean" for r in rubrics)
        + " | Spread | Tension? |",
        "|---|---|"
        + "|".join("---" for _ in rubrics)
        + "|---|---|",
    ]
    flagged = 0
    for (scenario_id, axis_name), rubric_map in sorted(axis_scores.items()):
        cells = []
        means: dict[str, float] = {}
        for r in rubrics:
            scores = [s for s in rubric_map.get(r, []) if s is not None]
            if not scores:
                cells.append("—")
                continue
            mean = sum(scores) / len(scores)
            means[r] = mean
            cells.append(f"{mean:.2f}")
        if len(means) >= 2:
            spread = max(means.values()) - min(means.values())
            tension = "yes" if spread >= 2.0 else ""
            if tension:
                flagged += 1
        else:
            spread = 0.0
            tension = ""
        matrix_lines.append(
            f"| {scenario_id} | {axis_name} | "
            + " | ".join(cells)
            + f" | {spread:.2f} | {tension} |"
        )

    matrix_lines.append("")
    matrix_lines.append(f"**Flagged cells (spread ≥ 2):** {flagged}")
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
    manifest["scenarios_count"] = len(scenarios)
    manifest["rubrics"] = rubrics
    sio.write_json(manifest_path, manifest)

    print(
        f"Aggregated {sum(len(v) for v in rows_by_rubric.values())} score rows "
        f"into {scores_dir.relative_to(sio.REPO_ROOT)}. "
        f"Flagged cells: {flagged}. "
        f"Manifest: {manifest_path.relative_to(sio.REPO_ROOT)}"
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
    p_stage.set_defaults(func=cmd_stage)

    p_agg = sub.add_parser("aggregate", help="aggregate scores into CSVs and matrix")
    p_agg.add_argument("--version", required=True)
    p_agg.set_defaults(func=cmd_aggregate)

    p_status = sub.add_parser("status", help="print completion counts")
    p_status.add_argument("--version", required=True)
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
