import asyncio
import os
from collections import Counter
from pathlib import Path

import pytest

from delivery_risk_agent.agent import generate_assessment
from delivery_risk_agent.models import (
    DeliveryRiskAssessment,
    ProjectSnapshot,
    RiskSeverity,
)
from delivery_risk_agent.risk_rules import analyze_project


def _risk_counts(items):
    """Count risks by their authoritative title, severity, and evidence."""
    return Counter(
        (
            item.title,
            item.severity,
            tuple(item.evidence),
        )
        for item in items
    )


def _assert_risks_preserved(assessment, findings):
    """Check that the final report contains every detected risk exactly once."""
    assert _risk_counts(assessment.prioritized_risks) == _risk_counts(
        findings
    )


def _assert_advice_complete(assessment):
    """Check that each risk has an explanation and a matching action."""
    risks = assessment.prioritized_risks
    actions = assessment.recommended_actions

    assert len(actions) == len(risks)

    for risk, action in zip(risks, actions):
        assert risk.impact.strip()
        assert action.action.strip()
        assert action.rationale.strip()
        assert risk.rank == action.priority


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_AGENT_TESTS") != "1",
    reason="Local agent integration tests are disabled.",
)
def test_agent_produces_structured_assessment():
    snapshot_file = (
        Path(__file__).parent.parent
        / "data"
        / "sample_project.json"
    )

    # Run the complete workflow, including the local model.
    assessment = asyncio.run(generate_assessment(snapshot_file))

    # Run the rules separately to get the authoritative findings.
    snapshot = ProjectSnapshot.model_validate_json(
        snapshot_file.read_text(encoding="utf-8")
    )
    findings = analyze_project(snapshot)

    assert isinstance(assessment, DeliveryRiskAssessment)
    assert assessment.executive_summary.strip()
    assert findings
    assert any(
        finding.severity == RiskSeverity.CRITICAL
        for finding in findings
    )

    _assert_risks_preserved(assessment, findings)
    _assert_advice_complete(assessment)