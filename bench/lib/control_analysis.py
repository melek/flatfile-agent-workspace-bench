#!/usr/bin/env python3
"""Cross-scenario control analysis for the control smoke test.

Prints model × scaffold × scenario × rubric means and the Δ-from-blank slopes.
Zero inference; pure file aggregation.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

CONDITIONS = [
    ("opus", "ctrl1-blank", "ctrl1-opus"),
    ("opus", "ctrl2-verbal", "ctrl2-opus"),
    ("opus", "ctrl3-bare", "ctrl3-opus"),
    ("opus", "v0.1-full", "v0.1-baseline"),
    ("opus", "v0.2-full+", "v0.2-revised"),
    ("haiku", "ctrl1-blank", "ctrl1-haiku"),
    ("haiku", "ctrl2-verbal", "ctrl2-haiku"),
    ("haiku", "ctrl3-bare", "ctrl3-haiku"),
    ("haiku", "v0.2-full+", "v0.2-haiku-smoke"),
]
RUBRICS = ["cog-erg", "architecture", "safety"]
SCENARIOS = [
    "04-routing-novel-observation",
    "07-procedure-artifact-binding",
    "10-threat-planted-error-adr",
    "11-threat-sycophantic-confirmation",
    "12-threat-provenance-check",
]


def load_mean(version_tag: str, scenario: str, rubric: str) -> float | None:
    scores_dir = ROOT / "bench" / "results" / version_tag / "scores" / rubric / scenario
    if not scores_dir.exists():
        return None
    values: list[int] = []
    for fp in sorted(scores_dir.glob("*.json")):
        try:
            payload = json.loads(fp.read_text())
        except Exception:
            continue
        for ax in payload.get("axes", {}).values():
            s = ax.get("score")
            if isinstance(s, int):
                values.append(s)
    if not values:
        return None
    return sum(values) / len(values)


def main() -> int:
    for scenario in SCENARIOS:
        any_data = False
        rows = []
        for model, scaffold, version_tag in CONDITIONS:
            row = {"model": model, "scaffold": scaffold}
            for r in RUBRICS:
                v = load_mean(version_tag, scenario, r)
                row[r] = v
            if any(row[r] is not None for r in RUBRICS):
                rows.append(row)
                any_data = True
        if not any_data:
            continue
        print(f"\n## Scenario {scenario}\n")
        print(f"{'Model':<7} {'Scaffold':<14}", end="")
        for r in RUBRICS:
            print(f"{r:>16}", end="")
        print()
        print("-" * (7 + 14 + 16 * 3))
        for row in rows:
            print(f"{row['model']:<7} {row['scaffold']:<14}", end="")
            for r in RUBRICS:
                v = row[r]
                if v is None:
                    print(f"{'—':>16}", end="")
                else:
                    print(f"{v:>16.2f}", end="")
            print()

    # Per-model slope across scenarios.
    print("\n## Δ from ctrl1-blank within each model (averaged across scenarios)\n")
    for model in ("opus", "haiku"):
        # Build a baseline = mean across scenarios for ctrl1-blank
        baseline_per_rubric: dict[str, list[float]] = {r: [] for r in RUBRICS}
        baseline_tag = next(t for m, s, t in CONDITIONS if m == model and s == "ctrl1-blank")
        for scenario in SCENARIOS:
            for r in RUBRICS:
                v = load_mean(baseline_tag, scenario, r)
                if v is not None:
                    baseline_per_rubric[r].append(v)
        baseline_mean = {
            r: (sum(vals) / len(vals)) if vals else None
            for r, vals in baseline_per_rubric.items()
        }

        print(f"\n### {model}")
        print(f"{'Scaffold':<14}", end="")
        for r in RUBRICS:
            print(f"{'Δ ' + r:>16}", end="")
        print()
        print("-" * (14 + 16 * 3))

        for m, scaffold, version_tag in CONDITIONS:
            if m != model:
                continue
            row_per_rubric: dict[str, list[float]] = {r: [] for r in RUBRICS}
            for scenario in SCENARIOS:
                for r in RUBRICS:
                    v = load_mean(version_tag, scenario, r)
                    if v is not None:
                        row_per_rubric[r].append(v)
            row_mean = {
                r: (sum(vals) / len(vals)) if vals else None
                for r, vals in row_per_rubric.items()
            }
            print(f"{scaffold:<14}", end="")
            for r in RUBRICS:
                base = baseline_mean[r]
                this = row_mean[r]
                if base is None or this is None:
                    print(f"{'—':>16}", end="")
                else:
                    print(f"{this - base:>+16.2f}", end="")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
