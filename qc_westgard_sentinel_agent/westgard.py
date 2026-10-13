"""Deterministic Westgard multirule quality-control evaluation.

Records must be ordered chronologically, with one result per control material
and run. No patient identifiers, networking, or clinical release actions are used.
This implements the modern (non-gated) rule interpretation, with 1_2s as warning.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Sequence


RULE_DESCRIPTIONS = {
    "1_2s": "One control exceeds 2 SD (warning only).",
    "1_3s": "One control exceeds 3 SD.",
    "2_2s": "Two consecutive controls exceed 2 SD on the same side.",
    "R_4s": "In one run, controls exceed +2 SD and -2 SD.",
    "4_1s": "Four consecutive controls exceed 1 SD on the same side.",
    "10x": "Ten consecutive controls fall on the same side of the mean.",
}
REJECTION_RULES = {"1_3s", "2_2s", "R_4s", "4_1s", "10x"}


def _same_side(points: Sequence[Dict[str, Any]], threshold: float) -> bool:
    return bool(points) and (
        all(point["z"] > threshold for point in points)
        or all(point["z"] < -threshold for point in points)
    )


def evaluate_qc(measurements: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate ordered QC results against modern Westgard rules.

    Required fields per row: run, level, value, mean, sd. Results are already
    standardized to z-scores, allowing different QC materials to share a run.
    All data for a given level must use unchanged assigned mean and SD.
    The same level may occur only once in each run. R_4s is strictly within-run.
    4_1s and 10x are evaluated per level, and also across exactly two consistent
    control levels in consecutive complete runs.
    """
    if not measurements:
        raise ValueError("At least one QC measurement is required")
    if len(measurements) > 10000:
        raise ValueError("Maximum 10000 QC measurements per evaluation")

    points: List[Dict[str, Any]] = []
    by_run: Dict[str, List[Dict[str, Any]]] = {}
    level_reference: Dict[str, tuple] = {}
    last_run = None
    completed_runs = set()
    for index, row in enumerate(measurements):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index + 1}: expected an object")
        run = str(row.get("run", "")).strip()
        level = str(row.get("level", "")).strip()
        if not run or not level:
            raise ValueError(f"Row {index + 1}: run and level are required")
        if run != last_run:
            if run in completed_runs:
                raise ValueError("Runs must be contiguous and chronologically ordered")
            if last_run is not None:
                completed_runs.add(last_run)
            last_run = run
        try:
            values = [row[field] for field in ("value", "mean", "sd")]
            if any(isinstance(value, bool) for value in values):
                raise ValueError("booleans are not numeric QC values")
            value, mean, sd = (float(value) for value in values)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Row {index + 1}: value, mean and sd must be numbers") from exc
        if not all(math.isfinite(v) for v in (value, mean, sd)) or sd <= 0:
            raise ValueError(f"Row {index + 1}: finite values and positive SD required")
        ref = (mean, sd)
        if level in level_reference and level_reference[level] != ref:
            raise ValueError(f"Row {index + 1}: changed mean or SD for level {level}; separate QC lots")
        level_reference[level] = ref
        if any(p["level"] == level for p in by_run.get(run, [])):
            raise ValueError(f"Row {index + 1}: duplicate level {level} in run {run}")
        p = {"index": index, "run": run, "level": level, "value": value,
             "mean": mean, "sd": sd, "z": (value - mean) / sd, "rules": []}
        points.append(p)
        by_run.setdefault(run, []).append(p)

    violations: List[Dict[str, Any]] = []

    def flag(rule: str, segment: Sequence[Dict[str, Any]]) -> None:
        indices = [p["index"] for p in segment]
        for p in segment:
            if rule not in p["rules"]:
                p["rules"].append(rule)
        violations.append({
            "rule": rule, "indices": indices, "run": segment[-1]["run"],
            "severity": "WARNING" if rule == "1_2s" else "REJECT",
        })

    per_level: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    combined: List[Dict[str, Any]] = []
    combined_levels = None
    for run_points in by_run.values():
        for p in run_points:
            z = p["z"]
            if abs(z) > 2:
                flag("1_2s", [p])
            if abs(z) > 3:
                flag("1_3s", [p])
            history = per_level[p["level"]]
            history.append(p)
            if len(history) >= 2 and _same_side(history[-2:], 2):
                flag("2_2s", history[-2:])
            if len(history) >= 4 and _same_side(history[-4:], 1):
                flag("4_1s", history[-4:])
            if len(history) >= 10 and _same_side(history[-10:], 0):
                flag("10x", history[-10:])

        # Across different control levels, but only within the same run.
        if len(run_points) >= 2:
            if _same_side(run_points, 2):
                flag("2_2s", run_points)
            high = next((p for p in run_points if p["z"] > 2), None)
            low = next((p for p in run_points if p["z"] < -2), None)
            if high is not None and low is not None:
                flag("R_4s", [high, low])

        # Standard two-level across-run combined interpretations.
        signature = tuple(sorted(p["level"] for p in run_points))
        if len(run_points) == 2 and signature == combined_levels:
            combined.extend(run_points)
        elif len(run_points) == 2:
            combined = list(run_points)
            combined_levels = signature
        else:
            combined = []
            combined_levels = None
        if len(combined) >= 4 and _same_side(combined[-4:], 1):
            flag("4_1s", combined[-4:])
        if len(combined) >= 10 and _same_side(combined[-10:], 0):
            flag("10x", combined[-10:])

    rejected = any(item["rule"] in REJECTION_RULES for item in violations)
    status = "REJECT" if rejected else ("WARNING" if violations else "ACCEPT")
    return {
        "status": status,
        "runs": len(by_run),
        "measurements": len(points),
        "results": [{**p, "z": round(p["z"], 6)} for p in points],
        "violations": violations,
        "interpretation": (
            "QC rejection rule detected; withhold results and investigate according to local SOP."
            if rejected else
            "1_2s warning only; inspect QC before proceeding under local SOP."
            if violations else "No configured rule violation detected."
        ),
    }
