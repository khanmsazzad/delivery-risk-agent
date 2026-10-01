import asyncio
import os
from pathlib import Path

import pytest

from delivery_risk_agent.agent import (
    generate_assessment,
)
from delivery_risk_agent.models import (
    DeliveryRiskAssessment,
    RiskSeverity,
)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_AGENT_TESTS") != "1",
    reason="Local agent integration tests are disabled.",
)
def test_agent_produces_structured_assessment():
    project_root = Path(__file__).parent.parent
    snapshot_file = (
        project_root / "data" / "sample_project.json"
    )

    assessment = asyncio.run(
        generate_assessment(snapshot_file)
    )

    assert isinstance(
        assessment,
        DeliveryRiskAssessment,
    )
    assert assessment.executive_summary
    assert assessment.prioritized_risks
    assert assessment.recommended_actions

    severities = {
        risk.severity
        for risk in assessment.prioritized_risks
    }

    print(assessment.model_dump_json(indent=2))
    assert RiskSeverity.CRITICAL in severities

    for risk in assessment.prioritized_risks:
        assert risk.title
        assert risk.impact
        assert risk.evidence

    for action in assessment.recommended_actions:
        assert action.action
        assert action.rationale