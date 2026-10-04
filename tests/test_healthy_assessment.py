import asyncio
import os
from pathlib import Path

import pytest

from delivery_risk_agent.agent import generate_assessment


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_AGENT_TESTS") != "1",
    reason="Local agent integration tests are disabled.",
)

def test_healthy_project_returns_no_risks():
    snapshot_file = (
        Path(__file__).parent.parent
        / "data"
        / "healthy_project.json"
    )

    assessment = asyncio.run(
        generate_assessment(snapshot_file)
    )

    assert assessment.executive_summary
    assert assessment.prioritized_risks == []
    assert assessment.recommended_actions == []

