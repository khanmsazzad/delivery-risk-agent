from delivery_risk_agent.models import (
    Priority,
    ProjectSnapshot,
    RiskFinding,
    RiskSeverity,
    WorkItemStatus,
)


def detect_blocked_critical_work(
    snapshot: ProjectSnapshot):

    findings: list[RiskFinding] = []

    for item in snapshot.work_items:
        if (
            item.priority == Priority.CRITICAL
            and item.status == WorkItemStatus.BLOCKED
        ):
            findings.append(
                RiskFinding(
                    rule_id="blocked-critical-work",
                    title=f"Critical work item {item.id} is blocked",
                    severity=RiskSeverity.CRITICAL,
                    work_item_id=item.id,
                    evidence=[
                        f"{item.id} has critical priority",
                        f"{item.id} has blocked status",
                        f"Blocking dependencies: {', '.join(item.blocked_by)}",
                    ],
                    recommendation=(
                        "Assign an owner to resolve the blocking dependency "
                        "and confirm whether the delivery date is still achievable."
                    ),
                )
            )

    return findings



def detect_failing_ci(snapshot:ProjectSnapshot):

    findings: list[RiskFinding] = []
    
    for pull_request in snapshot.pull_requests:
        if not pull_request.ci_passed:
            evidence = [
                f"PR# {pull_request.number} has falling CI"
            ]
            if not pull_request.approved:
                evidence.append(
                    f"PR #{pull_request.number} is not approved"
                )
        
            findings.append(
                RiskFinding(
                    rule_id="failing-ci",
                    title=f"Pull request #{pull_request.number} has failing CI",
                    severity=RiskSeverity.HIGH,
                    work_item_id=pull_request.linked_work_item,
                    pull_request_number=pull_request.number,
                    evidence=evidence,
                    recommendation=(
                        "Investigate the failing checks before merging "
                        "or approving the release."
                    ),
                )
            )
    return findings 


def detect_unassigned_high_priority_work(snapshot: ProjectSnapshot,):
    findings: list[RiskFinding] = []

    for item in snapshot.work_items:
        is_high_priority = item.priority in {
            Priority.HIGH,
            Priority.CRITICAL,
        }
        is_active = item.status != WorkItemStatus.DONE
        has_no_assignee = item.assignee is None

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