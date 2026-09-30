import json
from pathlib import Path

from agents import function_tool

from delivery_risk_agent.models import ProjectSnapshot
from delivery_risk_agent.risk_rules import analyze_project

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = (PROJECT_ROOT / "data").resolve()


def analyze_snapshot_file(snapshot_file: str) -> str:
    file_path = (PROJECT_ROOT / snapshot_file).resolve()

    if DATA_DIRECTORY not in file_path.parents:
        raise ValueError(
            "The snapshot file must be inside the data directory."
        )

    snapshot = ProjectSnapshot.model_validate_json(
        file_path.read_text()
    )
    findings = analyze_project(snapshot)

    serialized_findings = [
        finding.model_dump(mode="json")
        for finding in findings
    ]

    return json.dumps(serialized_findings, indent=2)


@function_tool
def analyze_delivery_risks(snapshot_file: str) -> str:
    """Analyze a JSON project snapshot and return detected delivery risks."""
    return analyze_snapshot_file(snapshot_file)