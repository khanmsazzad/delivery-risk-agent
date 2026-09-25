import argparse
from pathlib import Path

from delivery_risk_agent.models import ProjectSnapshot, RiskFinding
from delivery_risk_agent.risk_rules import analyze_project


def format_report(
    snapshot: ProjectSnapshot,
    findings: list[RiskFinding],
) -> str:
    lines = [
        f"Delivery Risk Report: {snapshot.name}",
        f"Captured at: {snapshot.captured_at}",
        f"Total findings: {len(findings)}",
    ]

    for finding in findings:
        lines.append("")
        lines.append(
            f"[{finding.severity.value.upper()}] {finding.title}"
        )

        if finding.work_item_id is not None:
            lines.append(
                f"Work item: {finding.work_item_id}"
            )

        if finding.pull_request_number is not None:
            lines.append(
                f"Pull request: #{finding.pull_request_number}"
            )

        lines.append("Evidence:")

        for evidence_item in finding.evidence:
            lines.append(f"  - {evidence_item}")

        lines.append(
            f"Recommendation: {finding.recommendation}"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a project snapshot for delivery risks."
    )
    parser.add_argument(
        "snapshot_file",
        type=Path,
        help="Path to the project snapshot JSON file.",
    )

    arguments = parser.parse_args()

    snapshot = ProjectSnapshot.model_validate_json(
        arguments.snapshot_file.read_text()
    )

    findings = analyze_project(snapshot)
    report = format_report(snapshot, findings)

    print(report)


if __name__ == "__main__":
    main()