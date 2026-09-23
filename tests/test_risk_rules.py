from pathlib import Path

from delivery_risk_agent.models import ProjectSnapshot, RiskSeverity
from delivery_risk_agent.risk_rules import (
    analyze_project,
    detect_blocked_critical_work,
    detect_failing_ci,
    detect_unassigned_high_priority_work,
)


def load_sample_snapshot() -> ProjectSnapshot:
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "sample_project.json"

    return ProjectSnapshot.model_validate_json(data_file.read_text())


def test_blocked_critical_work_is_detected():
    snapshot = load_sample_snapshot()

    findings = detect_blocked_critical_work(snapshot)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.rule_id == "blocked-critical-work"
    assert finding.work_item_id == "PAY-101"
    assert finding.severity == RiskSeverity.CRITICAL
    assert "PAY-102" in finding.evidence[2]


def test_unassigned_high_priority_work_is_detected():
    snapshot = load_sample_snapshot()

    findings = detect_unassigned_high_priority_work(snapshot)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.rule_id == "unassigned-high-priority-work"
    assert finding.work_item_id == "PAY-102"
    assert finding.severity == RiskSeverity.HIGH


def test_failing_ci_is_detected():
    snapshot = load_sample_snapshot()

    findings = detect_failing_ci(snapshot)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.rule_id == "failing-ci"
    assert finding.pull_request_number == 42
    assert finding.work_item_id == "PAY-101"
    assert finding.severity == RiskSeverity.HIGH
    assert "not approved" in finding.evidence[1]


def test_analyze_project_runs_all_risk_rules():
    snapshot = load_sample_snapshot()

    findings = analyze_project(snapshot)

    assert len(findings) == 3

    rule_ids = {finding.rule_id for finding in findings}

    assert rule_ids == {
        "blocked-critical-work",
        "unassigned-high-priority-work",
        "failing-ci",
    }
