from pathlib import Path

from delivery_risk_agent.models import ProjectSnapshot, RiskSeverity
from delivery_risk_agent.risk_rules import (
    detect_blocked_critical_work, 
    detect_unassigned_high_priority_work,
    detect_failing_ci,
)

def load_sample_snapshot() -> ProjectSnapshot:
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "sample_project.json"

    return ProjectSnapshot.model_validate_json(
        data_file.read_text()
    )


def test_blocked_critical_work_is_detected():
    snapshot = load_sample_snapshot()

    findings = detect_blocked_critical_work(snapshot)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.rule_id == "blocked-critical-work"
    assert finding.work_item_id == "PAY-101"
    assert finding.severity == RiskSeverity.CRITICAL
    assert "PAY-102" in finding.evidence[2]

def detect_unassignned_high_priority_work(
    snapshot:ProjectSnapshot):

    findings: list[RiskFinding] = []

    for item in snapshot.work_items:
        is_high_priority = item.priority in {
            Priority.HIGH,
            Priority.CRITICAL,
        }
        is_active = item.status != WorkItemStatus.DONE
        has_no_assignee = item.assinee in None

        if is_high_priority and is_active and has_no_assignee:
            findings.append(
                RiskFinding(
                    rule_id="unassigned-high-priority-work",
                    title=f"High-priority work item {item.id} has no assignee",
                    severity=RiskSeverity.HIGH,
                    work_item_id=item.id,
                    evidence=[
                        f"{item.id} has {item.priority.value} priority",
                        f"{item.id} has {item.status.value} status",
                        f"{item.id} has no assigned owner",
                    ],
                    recommendation=(
                        "Assign an owner and confirm that the work can be "
                        "completed before its due date."
                    ),
                )
            )

    return findings


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
