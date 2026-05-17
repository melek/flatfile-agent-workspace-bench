"""Shared utilities for reading and writing benchmark artifacts.

This module contains zero inference. It is deterministic file-shuffling and CSV
glue, designed so the runner stays auditable end-to-end.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCH_ROOT = REPO_ROOT / "bench"
SCENARIOS_ROOT = BENCH_ROOT / "scenarios"
RUBRICS_ROOT = BENCH_ROOT / "rubrics"
RESULTS_ROOT = BENCH_ROOT / "results"
TEMPLATE_ROOT = REPO_ROOT / "agent-workspace-template"


@dataclass(frozen=True)
class Scenario:
    """A scenario id + paths to its component files."""

    id: str
    dir: Path

    @property
    def brief(self) -> Path:
        return self.dir / "scenario.md"

    @property
    def user_prompt(self) -> Path:
        return self.dir / "user-prompt.md"

    @property
    def expected_signals(self) -> Path:
        return self.dir / "expected-signals.md"

    @property
    def seed(self) -> Path:
        return self.dir / "workspace-seed"


def list_scenarios() -> list[Scenario]:
    """All scenarios in id-sorted order."""
    items: list[Scenario] = []
    for child in sorted(SCENARIOS_ROOT.iterdir()):
        if child.is_dir() and child.name[0].isdigit():
            items.append(Scenario(id=child.name, dir=child))
    return items


def list_rubrics() -> list[str]:
    """Rubric ids in alphabetical order."""
    return sorted(
        p.stem for p in RUBRICS_ROOT.glob("*.md") if not p.name.startswith("README")
    )


def version_dir(version_tag: str) -> Path:
    return RESULTS_ROOT / version_tag


def run_path(version_tag: str, scenario_id: str, run_number: int) -> Path:
    return version_dir(version_tag) / "runs" / scenario_id / f"{run_number:02d}.json"


def score_path(
    version_tag: str, rubric_id: str, scenario_id: str, run_number: int
) -> Path:
    return (
        version_dir(version_tag)
        / "scores"
        / rubric_id
        / scenario_id
        / f"{run_number:02d}.json"
    )


def workspace_path(version_tag: str, scenario_id: str, run_number: int) -> Path:
    return (
        version_dir(version_tag)
        / "runs"
        / scenario_id
        / f"{run_number:02d}-workspace"
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return iter(())
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def iter_pending(jobs: Iterable[dict], complete_predicate) -> Iterator[dict]:
    """Yield only jobs whose output does not exist yet."""
    for job in jobs:
        if not complete_predicate(job):
            yield job


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
