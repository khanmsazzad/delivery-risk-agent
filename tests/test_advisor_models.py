from delivery_risk_agent.models import (
    DeliveryRiskAssessment,
    PrioritizedRisk,
    RecommendedAction,
    RiskSeverity,
)


def test_delivery_risk_assessment_structure():
    assessment = DeliveryRiskAssessment(
        executive_summary=(
            "The project has significant delivery risk."
        ),
        prioritized_risks=[
            PrioritizedRisk(
                rank=1,
                title="Critical work is blocked",
                severity=RiskSeverity.CRITICAL,
                impact="The planned release may be delayed.",
                evidence=[
                    "PAY-101 is critical",
                    "PAY-101 is blocked by PAY-102",
                ],
            )
        ],
        recommended_actions=[
            RecommendedAction(
                priority=1,
                action="Assign an owner to PAY-102",
                rationale=(
                    "PAY-102 blocks critical delivery work."
                ),
            )
        ],
    )

    assert assessment.executive_summary
    assert len(assessment.prioritized_risks) == 1
    assert assessment.prioritized_risks[0].rank == 1
    assert (
        assessment.prioritized_risks[0].severity
        == RiskSeverity.CRITICAL
    )
    assert len(assessment.recommended_actions) == 1