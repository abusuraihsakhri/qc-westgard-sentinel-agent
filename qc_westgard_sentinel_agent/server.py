"""
FastAPI REST Application & Webhooks for Westgard Sentinel: Real-Time Multi-Rule Analytical Quality Control & Calibration Agent.
"""
from typing import Dict, Any, List, Optional
from .models import ClinicalCasePayload
from .agents import QCCoordinator
from .westgard import evaluate_qc

coordinator = QCCoordinator()

def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="Westgard Sentinel: Real-Time Multi-Rule Analytical Quality Control & Calibration Agent",
            description="Legacy generic threshold evaluation plus stateless Westgard QC analysis. No batch interlock.",
            version="2.0.0-PRO",
        )

        class AuditRequest(BaseModel):
            case_id: str = "CASE-2026-001"
            patient_synthetic_id: str = "SYNTH-PT-881"
            primary_metric: float = 24.5
            secondary_metric: float = 14.0
            status_flag: str = "DISCORDANT"
            is_stat: bool = True
            clinical_notes: str = ""
            biomarkers: Dict[str, Any] = {}

        class ChatRequest(BaseModel):
            query: str

        class QCEvaluationRequest(BaseModel):
            measurements: List[Dict[str, Any]] = Field(min_length=1, max_length=10000)

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "qc-westgard-sentinel-agent", "domain": "Laboratory Medicine", "version": "2.0.0-PRO"}

        @app.post("/api/audit")
        def api_audit(req: AuditRequest):
            payload = ClinicalCasePayload(
                case_id=req.case_id,
                patient_synthetic_id=req.patient_synthetic_id,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_flag=req.status_flag,
                is_stat=req.is_stat,
                clinical_notes=req.clinical_notes,
                biomarkers=req.biomarkers,
            )
            return coordinator.process_case(payload)

        @app.post("/api/qc/evaluate")
        def api_qc_evaluate(req: QCEvaluationRequest):
            try:
                return evaluate_qc(req.measurements)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
