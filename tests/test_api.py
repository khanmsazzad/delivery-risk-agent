from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from urllib.error import HTTPError

from delivery_risk_agent.api import SAMPLE_SNAPSHOT, app
from delivery_risk_agent.models import ProjectSnapshot, DeliveryRiskAssessment
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


def test_github_analysis_returns_assessment():
    snapshot = ProjectSnapshot.model_validate_json(
        SAMPLE_SNAPSHOT.read_text(encoding="utf-8")
    )
    assessment = DeliveryRiskAssessment(
        executive_summary="Test assessment",
        prioritized_risks=[],
        recommended_actions=[],
    )

    with (
        patch(
            "delivery_risk_agent.api.fetch_github_snapshot",
            return_value=snapshot,
        ) as fetch_snapshot,
        patch(
            "delivery_risk_agent.api.generate_assessment_from_snapshot",
            new_callable=AsyncMock,
            return_value=assessment,
        ) as generate_assessment,
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/analyze/github",
            json={"repository_url": "https://github.com/example/project"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "project_name": snapshot.name,
        "captured_at": snapshot.model_dump(mode="json")["captured_at"],
        "assessment": assessment.model_dump(mode="json"),
    }
    fetch_snapshot.assert_called_once_with("example", "project")
    generate_assessment.assert_awaited_once_with(snapshot)


def test_github_analysis_rejects_invalid_url():
    with (
        patch(
            "delivery_risk_agent.api.fetch_github_snapshot"
        ) as fetch_snapshot,
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/analyze/github",
            json={"repository_url": "https://example.com/owner/repo"},
        )

    assert response.status_code == 422
    fetch_snapshot.assert_not_called()


def test_github_analysis_handles_repository_not_found():
    github_error = HTTPError(
        url="https://api.github.com/repos/example/missing/pulls",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None,
    )

    with (
        patch(
            "delivery_risk_agent.api.fetch_github_snapshot",
            side_effect=github_error,
        ),
        patch(
            "delivery_risk_agent.api.generate_assessment_from_snapshot",
            new_callable=AsyncMock,
        ) as generate_assessment,
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/analyze/github",
            json={"repository_url": "https://github.com/example/missing"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Repository not found or not publicly accessible."
    )
    generate_assessment.assert_not_awaited()


def test_jira_analysis_returns_assessment():
    snapshot = ProjectSnapshot.model_validate_json(
        SAMPLE_SNAPSHOT.read_text(encoding="utf-8")
    )
    assessment = DeliveryRiskAssessment(
        executive_summary="Test Jira assessment",
        prioritized_risks=[],
        recommended_actions=[],
    )

    with (
        patch(
            "delivery_risk_agent.api.fetch_jira_snapshot",
            return_value=snapshot,
        ) as fetch_snapshot,
        patch(
            "delivery_risk_agent.api.generate_assessment_from_snapshot",
            new_callable=AsyncMock,
            return_value=assessment,
        ) as generate_assessment,
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/analyze/jira",
            json={"project_key": "risk"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "project_name": snapshot.name,
        "captured_at": snapshot.model_dump(mode="json")["captured_at"],
        "issues_inspected": len(snapshot.work_items),
        "assessment": assessment.model_dump(mode="json"),
    }
    fetch_snapshot.assert_called_once_with("RISK")
    generate_assessment.assert_awaited_once_with(snapshot)