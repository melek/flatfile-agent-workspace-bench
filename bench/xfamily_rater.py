#!/usr/bin/env python3
"""Cross-family rater supporting Ollama (local) and OpenAI API backends.

Reads the existing rescore-jobs.jsonl from a version's reliability dir,
calls the chosen model for each pending job, writes scores to a named
output directory under the same reliability dir. Idempotent.

Usage:
    # Ollama (local)
    python bench/xfamily_rater.py --version v0.3-trimmed --backend ollama --model qwen2.5:14b

    # OpenAI API (reads OPENAI_API_KEY from environment)
    python bench/xfamily_rater.py --version v0.3-trimmed --backend openai --model gpt-4.1

    # Dry run
    python bench/xfamily_rater.py --version v0.3-trimmed --backend openai --dry-run

Output lands in reliability/scores-<backend>-<model-slug>/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import score_io as sio

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_TIMEOUT = 150  # wall-clock seconds per call


# --------------------------------------------------------------------------- #
# Prompt building                                                              #
# --------------------------------------------------------------------------- #

def _fmt_transcript(run: dict) -> str:
    parts: list[str] = []
    for action in run.get("actions", []):
        parts.append(
            f"[{action.get('action', '')} → {action.get('path', '')}]\n"
            f"{action.get('content_summary', '')}"
        )
    parts.append(f"[Final response]\n{run.get('final_response', '')}")
    return "\n\n".join(parts)


def _build_prompt(
    rubric_text: str,
    scenario_text: str,
    run: dict,
    axes: tuple[str, ...],
    na_allowed: tuple[str, ...],
) -> str:
    transcript = _fmt_transcript(run)
    na_note = ""
    if na_allowed:
        na_note = (
            f"\nAxes where n/a is permitted: {', '.join(na_allowed)}. "
            "Use n/a only when the axis genuinely does not apply to this run "
            "(e.g., SA2 when the agent produced no artifact requiring attribution). "
            "Do not use n/a to avoid a difficult judgment."
        )
    return textwrap.dedent(f"""
You are an evaluator scoring a transcript from an AI agent benchmark.

## Rubric
{rubric_text}

## Scenario brief (rater context only — the simulator agent did not see this)
{scenario_text}

## Transcript to score
{transcript}

## Your task
Score each axis in the rubric ({', '.join(axes)}) on a 0–3 integer scale using the anchor descriptions above.{na_note}

Respond with a JSON object exactly matching this structure:
{{
  "axes": {{
    "<AXIS_ID>": {{
      "score": <integer 0-3, or the string "n/a" where permitted>,
      "justification": "<one sentence>"
    }},
    ...
  }}
}}

Return only the JSON object — no prose before or after. Score against the rubric, not against your sense of overall quality. One sentence of justification per axis.
""").strip()


# --------------------------------------------------------------------------- #
# Backends                                                                     #
# --------------------------------------------------------------------------- #

def _call_ollama(model: str, prompt: str) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        body = json.loads(resp.read())
    return body["message"]["content"]


def _call_ollama_with_timeout(model: str, prompt: str) -> str:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call_ollama, model, prompt)
        try:
            return future.result(timeout=OLLAMA_TIMEOUT)
        except FuturesTimeoutError:
            raise TimeoutError(f"Ollama call exceeded {OLLAMA_TIMEOUT}s")


def _call_openai(model: str, prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


BACKENDS = {
    "ollama": _call_ollama_with_timeout,
    "openai": _call_openai,
}


# --------------------------------------------------------------------------- #
# Score parsing + validation                                                   #
# --------------------------------------------------------------------------- #

def _parse_scores(raw: str, axes: tuple[str, ...], na_allowed: tuple[str, ...]) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}\nRaw: {raw[:400]}") from e

    axes_out = parsed.get("axes") or parsed
    result: dict[str, dict] = {}

    for axis in axes:
        if axis not in axes_out:
            raise ValueError(f"Missing axis {axis} in model output")
        cell = axes_out[axis]
        score_raw = cell.get("score")
        justification = str(cell.get("justification", "")).strip()

        if score_raw == "n/a" or (score_raw is None and axis in na_allowed):
            if axis not in na_allowed:
                raise ValueError(f"n/a not allowed on {axis}")
            result[axis] = {"score": "n/a", "justification": justification or "n/a"}
        else:
            try:
                score_int = int(score_raw)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Non-integer score {score_raw!r} on {axis}") from e
            if score_int not in (0, 1, 2, 3):
                raise ValueError(f"Score {score_int} out of domain on {axis}")
            result[axis] = {"score": score_int, "justification": justification}

    return result


# --------------------------------------------------------------------------- #
# Per-job scoring                                                              #
# --------------------------------------------------------------------------- #

def _model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]", "-", model.lower()).strip("-")


def rate_job(job: dict, backend: str, model: str, out_root: Path) -> Path:
    rubric_id = job["rubric_id"]
    scenario_id = job["scenario_id"]
    run_number = job["run_number"]

    out_path = out_root / rubric_id / scenario_id / f"{run_number:02d}.json"
    if out_path.exists():
        return out_path

    meta = sio.rubric_meta(rubric_id)
    if meta is None:
        raise ValueError(f"No front-matter in rubric {rubric_id}")

    rubric_text = (sio.REPO_ROOT / job["rubric_path"]).read_text()
    scenario_text = (sio.REPO_ROOT / job["scenario_brief"]).read_text()
    run = sio.read_json(sio.REPO_ROOT / job["run_path"])

    prompt = _build_prompt(rubric_text, scenario_text, run, meta.axes, meta.na_allowed)
    call_fn = BACKENDS[backend]
    raw = call_fn(model, prompt)
    axes_result = _parse_scores(raw, meta.axes, meta.na_allowed)

    sio.write_json(out_path, {
        "rubric_id": rubric_id,
        "scenario_id": scenario_id,
        "run_number": run_number,
        "backend": backend,
        "model": model,
        "axes": axes_result,
    })
    return out_path


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True, help="Results tag, e.g. v0.3-trimmed")
    parser.add_argument("--backend", required=True, choices=list(BACKENDS), help="ollama or openai")
    parser.add_argument("--model", required=True, help="Model name/ID for the chosen backend")
    parser.add_argument("--dry-run", action="store_true", help="List pending jobs; make no calls")
    args = parser.parse_args()

    rel_root = sio.version_dir(args.version) / "reliability"
    jobs_path = rel_root / "rescore-jobs.jsonl"
    if not jobs_path.exists():
        print(f"No rescore-jobs.jsonl found. Run: runner.py rescore-sample --version {args.version}")
        return 1

    jobs = list(sio.read_jsonl(jobs_path))
    out_root = rel_root / f"scores-{args.backend}-{_model_slug(args.model)}"

    pending = [
        j for j in jobs
        if not (out_root / j["rubric_id"] / j["scenario_id"] / f"{j['run_number']:02d}.json").exists()
    ]

    print(f"Backend: {args.backend} / {args.model} → {out_root.relative_to(sio.REPO_ROOT)}")
    print(f"Total jobs: {len(jobs)} | Pending: {len(pending)} | Done: {len(jobs) - len(pending)}")

    if args.dry_run:
        for j in pending:
            print(f"  pending: {j['rubric_id']}/{j['scenario_id']}/run{j['run_number']:02d}")
        return 0

    errors: list[tuple[dict, Exception]] = []
    for i, job in enumerate(pending, 1):
        label = f"{job['rubric_id']}/{job['scenario_id']}/run{job['run_number']:02d}"
        print(f"[{i}/{len(pending)}] {label} ...", end=" ", flush=True)
        t0 = time.monotonic()
        try:
            out = rate_job(job, args.backend, args.model, out_root)
            elapsed = time.monotonic() - t0
            print(f"ok ({elapsed:.1f}s) → {out.relative_to(sio.REPO_ROOT)}")
        except Exception as exc:
            elapsed = time.monotonic() - t0
            print(f"ERROR ({elapsed:.1f}s): {exc}")
            errors.append((job, exc))

    if errors:
        print(f"\n{len(errors)} job(s) failed:")
        for job, exc in errors:
            print(f"  {job['rubric_id']}/{job['scenario_id']}/run{job['run_number']:02d}: {exc}")
        return 1

    print(f"\nDone. {len(pending)} jobs scored → {out_root.relative_to(sio.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
