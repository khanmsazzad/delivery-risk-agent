from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from delivery_risk_agent.models import ProjectSnapshot, RiskFinding
from delivery_risk_agent.risk_rules import analyze_project 

app = FastAPI(title="Delivery Risk Dashboard")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_SNAPSHOT = PROJECT_ROOT / "data" / "sample_project.json"

class DashboardResponse(BaseModel):
    project_name: str
    captured_at: datetime
    findings: list[RiskFinding]


@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    snapshot = ProjectSnapshot.model_validate_json(
        SAMPLE_SNAPSHOT.read_text(encoding="utf-8")
    )

    return DashboardResponse(
        project_name=snapshot.name,
        captured_at=snapshot.captured_at,
        findings=analyze_project(snapshot),
    )