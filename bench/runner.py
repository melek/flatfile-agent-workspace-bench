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
    """Brief path for active or retired scenarios (frozen tags keep both)."""
    active = sio.SCENARIOS_ROOT / scenario_id / "scenario.md"
    if active.exists():
        return active
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
    """
    version = args.version
    rubrics = sio.list_rubrics()
    metas = {r: sio.rubric_meta(r) for r in rubrics}
    rel_root = sio.version_dir(version) / "reliability"

    per_rubric_pairs: dict[str, list[tuple[int, int]]] = {r: [] for r in rubrics}
    per_axis: dict[tuple[str, str], dict] = {}
    na_disagreements: list[str] = []
    n_jobs = n_scored = 0

    for job in sio.read_jsonl(rel_root / "rescore-jobs.jsonl"):
        n_jobs += 1
        rubric_id = job["rubric_id"]
        meta = metas[rubric_id]
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
            o, n_ = o_map.get(axis), n_map.get(axis)
            o_int, n_int = isinstance(o, int), isinstance(n_, int)
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

    lines = [
        f"# Judge reliability — {version}",
        "",
        f"Generated by `runner.py reliability` at {_now()}.",
        f"Sample: runs {RESCORE_RUNS} per (scenario, rubric); "
        f"{n_scored}/{n_jobs} rescore jobs completed. Original scores were "
        "produced under the isolated protocol; rescores use fresh isolated "
        "rater contexts with version-identifying transcript fields redacted.",
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
        "- The original raters' model pin was not recorded in the manifest; "
        "rescore raters may differ in model version. Agreement here is a "
        "lower bound on same-model stability.",
        "- Same model family on both sides; self-preference bias is not "
        "bounded by this study (cross-family sub-task pending).",
    ]
    out = rel_root / "reliability.md"
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
    p_rel.set_defaults(func=cmd_reliability)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
