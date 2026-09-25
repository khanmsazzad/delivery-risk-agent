from pathlib import Path

from delivery_risk_agent.models import ProjectSnapshot
from delivery_risk_agent.report import format_report
from delivery_risk_agent.risk_rules import analyze_project


def test_report_contains_project_and_findings():
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "sample_project.json"

    snapshot = ProjectSnapshot.model_validate_json(
        data_file.read_text()
    )
    findings = analyze_project(snapshot)

    report = format_report(snapshot, findings)

    assert "Delivery Risk Report: Payments Platform" in report
    assert "Total findings: 3" in report
    assert "PAY-101" in report
    assert "PAY-102" in report
    assert "Pull request: #42" in report