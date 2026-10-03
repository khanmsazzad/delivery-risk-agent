import asyncio
from pathlib import Path

from delivery_risk_agent.agent import generate_assessment


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