from fastapi.testclient import TestClient

from delivery_risk_agent.api import SAMPLE_SNAPSHOT, app
from delivery_risk_agent.models import ProjectSnapshot
from delivery_risk_agent.risk_rules import analyze_project


def test_dashboard_returns_sample_project_findings():
    snapshot = ProjectSnapshot.model_validate_json(
        SAMPLE_SNAPSHOT.read_text(encoding="utf-8")
    )
    expected_findings = analyze_project(snapshot)

    with TestClient(app) as client:
        response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json() == {
        "project_name": snapshot.name,
        "captured_at": snapshot.model_dump(mode="json")["captured_at"],
        "findings": [
            finding.model_dump(mode="json")
            for finding in expected_findings
        ],
    }