import json

import pytest

from delivery_risk_agent.agent_tools import analyze_snapshot_file


def test_analyze_snapshot_file_returns_findings():
    result = analyze_snapshot_file(
        "data/sample_project.json"
    )
    findings = json.loads(result)

    assert len(findings) == 3

    rule_ids = {
        finding["rule_id"]
        for finding in findings
    }

    assert rule_ids == {
        "blocked-critical-work",
        "unassigned-high-priority-work",
        "failing-ci",
    }


def test_tool_rejects_files_outside_data_directory():
    with pytest.raises(ValueError):
        analyze_snapshot_file("pyproject.toml")