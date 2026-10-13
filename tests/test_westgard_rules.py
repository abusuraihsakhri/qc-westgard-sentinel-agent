"""Reference examples and edge cases for deterministic Westgard QC rules."""
import math
import pytest
from qc_westgard_sentinel_agent.westgard import evaluate_qc


def point(run, level, z):
    return {"run": str(run), "level": level, "value": 100 + z * 5,
            "mean": 100, "sd": 5}


def rules(*points):
    return [v["rule"] for v in evaluate_qc(list(points))["violations"]]


def test_accept_and_warning_not_rejection():
    assert evaluate_qc([point(1, "A", 0.5)])["status"] == "ACCEPT"
    result = evaluate_qc([point(1, "A", 2.5)])
    assert result["status"] == "WARNING"
    assert rules(point(1, "A", 2.5)) == ["1_2s"]


def test_1_3s_rejects_positive_and_negative():
    for z in (3.01, -3.01):
        assert "1_3s" in rules(point(1, "A", z))
        assert evaluate_qc([point(1, "A", z)])["status"] == "REJECT"


def test_2_2s_within_material_and_across_levels():
    assert "2_2s" in rules(point(1, "A", 2.1), point(2, "A", 2.3))
    assert "2_2s" in rules(point(1, "A", -2.1), point(1, "B", -2.4))
    assert "2_2s" not in rules(point(1, "A", 2.3), point(2, "A", -2.3))


def test_r_4s_only_within_run():
    assert "R_4s" in rules(point(1, "A", 2.5), point(1, "B", -2.5))
    assert "R_4s" not in rules(point(1, "A", 2.5), point(2, "B", -2.5))


def test_4_1s_per_level_and_two_level_windows():
    assert "4_1s" in rules(*(point(i, "A", 1.25) for i in range(1, 5)))
    two = [point(run, level, 1.25) for run in (1, 2) for level in ("A", "B")]
    assert "4_1s" in rules(*two)
    assert "4_1s" not in rules(*[point(i, "A", z) for i, z in enumerate([1.1, 1.1, -1.1, -1.1], 1)])


def test_10x_per_level_and_combined():
    assert "10x" in rules(*(point(i, "A", -0.1) for i in range(1, 11)))
    two = [point(run, level, 0.2) for run in range(1, 6) for level in ("A", "B")]
    assert "10x" in rules(*two)
    assert "10x" not in rules(*(point(i, "A", 0.0) for i in range(1, 11)))


def test_strict_sd_boundary_and_invalid_inputs():
    assert "1_2s" not in rules(point(1, "A", 2.0))
    assert "1_3s" not in rules(point(1, "A", -3.0))
    assert "R_4s" not in rules(point(1, "A", 2.0), point(1, "B", -2.5))
    with pytest.raises(ValueError, match="At least"):
        evaluate_qc([])
    for invalid in (0, -1, float("nan"), float("inf")):
        row = point(1, "A", 0)
        row["sd"] = invalid
        with pytest.raises(ValueError):
            evaluate_qc([row])


def test_invalid_sequence_and_reference_change():
    with pytest.raises(ValueError, match="contiguous"):
        evaluate_qc([point(1, "A", 0), point(2, "A", 0), point(1, "B", 0)])
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_qc([point(1, "A", 0), point(1, "A", 0)])
    row = point(2, "A", 0)
    row["mean"] = 200
    with pytest.raises(ValueError, match="changed mean"):
        evaluate_qc([point(1, "A", 0), row])
    with pytest.raises(ValueError, match="numeric"):
        evaluate_qc([{"run": 1, "level": "A", "value": True, "mean": 1, "sd": 1}])


def test_violations_reference_original_rows():
    report = evaluate_qc([point(1, "A", 2.3), point(1, "B", 2.4)])
    hits = [v for v in report["violations"] if v["rule"] == "2_2s"]
    assert len(hits) == 1 and hits[0]["indices"] == [0, 1]
    assert all("2_2s" in p["rules"] for p in report["results"])
