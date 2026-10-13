"""Regression checks for the HMAC audit chain and QC CLI."""
import csv
import json
from pathlib import Path
from agents.base import AuditTrail
from qc_westgard_sentinel_agent.cli import main


def test_hmac_tampering_detected():
    trail = AuditTrail(secret_key="unit-test-key")
    trail.log("worker", "tier", "EVENT", {"status": "OK"})
    trail.log("worker", "tier", "EVENT2", {"status": "OK"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()


def test_audit_snapshot_cannot_mutate_ledger():
    trail = AuditTrail(secret_key="unit-test-key")
    trail.log("worker", "tier", "EVENT", {"status": "OK"})
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "modified"
    assert trail.verify_integrity()
    assert trail.get_trail()[0]["actor"] == "worker"


def test_qc_cli_json_output(tmp_path):
    csv_path = tmp_path / "controls.csv"
    csv_path.write_text("run,level,value,mean,sd\n1,A,112.5,100,5\n", encoding="utf-8")
    report_path = tmp_path / "report.json"
    assert main(["qc", "-i", str(csv_path), "-o", str(report_path)]) == 0
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["status"] == "WARNING"
    assert data["violations"][0]["rule"] == "1_2s"


def test_legacy_batch_false_string_is_false(tmp_path):
    input_path = tmp_path / "legacy.csv"
    input_path.write_text(
        "case_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "T1,10,5,False,NORMAL\n", encoding="utf-8"
    )
    output_path = tmp_path / "out.csv"
    assert main(["batch", "-i", str(input_path), "-o", str(output_path)]) == 0
    with output_path.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["stat_critical_alerts"] == "0"


def test_qc_cli_rejects_invalid_stddev(tmp_path):
    source = tmp_path / "wrong.csv"
    source.write_text("run,level,value,mean,sd\n1,A,10,10,0\n", encoding="utf-8")
    assert main(["qc", "-i", str(source)]) == 1
