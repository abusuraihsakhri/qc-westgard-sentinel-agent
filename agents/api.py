"""
FastAPI REST API Server for Qc Westgard Sentinel Agent.
"""
from fastapi import FastAPI, HTTPException
from typing import Any, Dict, List
from pydantic import BaseModel
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor
from qc_westgard_sentinel_agent.westgard import evaluate_qc

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Qc Westgard Sentinel Agent API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class QCEvaluationRequest(BaseModel):
    measurements: List[Dict[str, Any]]


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "qc-westgard-sentinel-agent", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/qc/evaluate")
def api_qc_evaluate(req: QCEvaluationRequest):
    """Stateless, deterministic Westgard evaluation (no patient data)."""
    try:
        return evaluate_qc(req.measurements)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
