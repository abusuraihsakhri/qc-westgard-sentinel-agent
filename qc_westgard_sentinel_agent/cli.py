"""
Command-Line Interface for Westgard Sentinel: Real-Time Multi-Rule Analytical Quality Control & Calibration Agent.
"""
import argparse
import csv
import json
import sys
from .models import ClinicalCasePayload
from .agents import QCCoordinator
from .westgard import evaluate_qc

coordinator = QCCoordinator()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="qc-westgard-sentinel-agent", description="Westgard Sentinel: Real-Time Multi-Rule Analytical Quality Control & Calibration Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single case clinical audit")
    p_audit.add_argument("--case-id", default="CASE-2026-001")
    p_audit.add_argument("--primary", type=float, default=26.2)
    p_audit.add_argument("--secondary", type=float, default=12.5)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Analytical Westgard QC (separate from legacy generic case audit)
    p_qc = subparsers.add_parser("qc", help="Evaluate chronological laboratory QC CSV")
    p_qc.add_argument("-i", "--input", required=True, help="CSV with run,level,value,mean,sd")
    p_qc.add_argument("-o", "--output", help="Optional JSON report path")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTH-PT-881",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        dossier = coordinator.process_case(case)
        print("=" * 80)
        print(f"  WESTGARD SENTINEL: REAL-TIME MULTI-RULE ANALYTICAL QUALITY CONTROL & CALIBRATION AGENT")
        print(f"  Domain: Laboratory Medicine | Standard: CLSI EP28-A3 & Westgard Multi-Rule QC")
        print(f"  Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['urgency']}] from {a['sub_agent']}:")
            print(f"  Title: {a['title']}")
            print(f"  Finding: {a['clinical_finding']}")
            print(f"  Action: {a['actionable_recommendation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[QCCoordinator]:\n{ans}\n")
        return 0

    if args.command in ("batch", "qc"):
        try:
            with open(args.input, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f, strict=True)
                fieldnames = list(reader.fieldnames or [])
                if not fieldnames:
                    raise ValueError("CSV header is missing")
                rows = list(reader)
            if args.command == "qc":
                required = {"run", "level", "value", "mean", "sd"}
                if not required.issubset(fieldnames):
                    raise ValueError("QC CSV requires columns: run,level,value,mean,sd")
                report = evaluate_qc(rows)
                result_json = json.dumps(report, indent=2)
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(result_json + "\n")
                else:
                    print(result_json)
                return 0

            def parse_bool(value):
                if isinstance(value, bool):
                    return value
                normalized = str(value).strip().lower()
                if normalized in ("true", "1", "yes", "y"):
                    return True
                if normalized in ("false", "0", "no", "n", ""):
                    return False
                raise ValueError(f"Invalid critical flag: {value!r}")

            out_fields = list(dict.fromkeys(fieldnames + [
                "overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"
            ]))
            out_rows = []
            for row_number, r in enumerate(rows, start=2):
                try:
                    case = ClinicalCasePayload(
                        case_id=r.get("case_id") or "CASE-01",
                        patient_synthetic_id=r.get("patient_synthetic_id") or "SYNTH-01",
                        primary_metric=float(r.get("metric_primary") or r.get("primary_metric") or 15.0),
                        secondary_metric=float(r.get("metric_secondary") or r.get("secondary_metric") or 5.0),
                        status_flag=r.get("status_flag") or r.get("status_text") or "NORMAL",
                        is_stat=parse_bool(r.get("is_stat", r.get("critical_flag", False))),
                    )
                    dossier = coordinator.process_case(case)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"CSV row {row_number}: {exc}") from exc
                row_dict = dict(r)
                row_dict.update({
                    "overall_status": dossier["overall_status"],
                    "total_alerts": dossier["total_alerts"],
                    "stat_critical_alerts": dossier["stat_critical_alerts"],
                    "consensus_summary": dossier["consensus_summary"],
                })
                out_rows.append(row_dict)

            with open(args.output, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
            print(f"Batch processed {len(out_rows)} records -> {args.output}")
            return 0
        except (OSError, UnicodeError, csv.Error, ValueError) as exc:
            print(f"Error processing CSV: {exc}", file=sys.stderr)
            return 1

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting Westgard Sentinel: Real-Time Multi-Rule Analytical Quality Control & Calibration Agent on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
