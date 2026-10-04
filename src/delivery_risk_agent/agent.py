import argparse
import asyncio
import json
from pathlib import Path

from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from delivery_risk_agent.models import (
    AgentAdvice,
    DeliveryRiskAssessment,
    PrioritizedRisk,
    ProjectSnapshot,
    RecommendedAction,
)
from delivery_risk_agent.risk_rules import analyze_project

local_client = AsyncOpenAI(
    base_url="http://localhost:8080/v1",
    api_key="local-no-key",
)

set_default_openai_client(
    local_client,
    use_for_tracing=False,
)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)


delivery_risk_agent = Agent(
    name="Engineering Delivery Risk Advisor",
    model="qwen-local",
    instructions=(
        "You are an engineering delivery risk advisor. "
        "You will receive numbered, authoritative risk findings. "
        "Return exactly one risk_advice item for each finding_id. "
        "Explain its likely delivery impact and recommend a concrete action. "
        "Order risk_advice by your recommended priority. "
        "Use only the supplied evidence; do not invent project facts. "
        "Do not assign severity, rewrite evidence, or create new findings."
    ),
    output_type=AgentAdvice, 
    
)


async def generate_assessment(
        snapshot_file: Path, 
) -> DeliveryRiskAssessment: 

    # 1. Python loads the snapshot and detects risks.
    snapshot = ProjectSnapshot.model_validate_json(
        snapshot_file.read_text(encoding="utf-8")
    )

    return await generate_assessment_from_snapshot(snapshot)


async def generate_assessment_from_snapshot(
        snapshot: ProjectSnapshot,
) -> DeliveryRiskAssessment: 

    findings = analyze_project(snapshot)

    # 2. Give each finding a unique number for this assessment.
    numbered_findings = [
        {
            "finding_id": number,
            **finding.model_dump(mode="json"),
        }
        for number, finding in enumerate(findings, start=1)
    ]

    request = (
         "Assess these authoritative delivery-risk findings. "
        "Return one risk_advice item for every finding_id. "
        "Order the items by your recommended priority.\n\n"
        + json.dumps(numbered_findings, indent=2)
    )

    # 3. The agent supplies impact analysis and recommendations.
    result = await Runner.run(delivery_risk_agent, request)
    advice = result.final_output

    if not isinstance(advice, AgentAdvice):
        raise TypeError("The agent did not return AgentAdvice.")

    # 4. Verify that the agent addressed every detected finding once.
    expected_ids = set(range(1, len(findings) + 1))
    returned_ids = [
        item.finding_id
        for item in advice.risk_advice
    ]

    if (
        len(returned_ids) != len(findings)
        or set(returned_ids) != expected_ids
    ):
        raise ValueError(
            "Agent advice is missing, duplicating, "
            "or inventing a finding."
        )

    findings_by_id = {
        number: finding
        for number, finding in enumerate(findings, start=1)
    }


    # 5. Python enforces severity order. Within a severity,
    # the agent's preferred order is preserved.
    severity_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    ordered_advice = sorted(
        advice.risk_advice,
        key=lambda item: severity_order[
            findings_by_id[item.finding_id].severity.value
        ],
    )

    prioritized_risks = []
    recommended_actions = []

    # 6. Python combines authoritative facts with agent advice.
    for rank, item in enumerate(ordered_advice, start=1):
        finding = findings_by_id[item.finding_id]

        prioritized_risks.append(
            PrioritizedRisk(
                rank=rank,
                title=finding.title,
                severity=finding.severity,
                impact=item.impact,
                evidence=finding.evidence,
            )
        )

        recommended_actions.append(
            RecommendedAction(
                priority=rank,
                action=item.recommended_action,
                rationale=item.rationale,
            )
        )

    return DeliveryRiskAssessment(
        executive_summary=advice.executive_summary,
        prioritized_risks=prioritized_risks,
        recommended_actions=recommended_actions,
    )

async def run_agent(snapshot_file: Path) -> None:
    assessment = await generate_assessment(
        snapshot_file
    )
    print(
        assessment.model_dump_json(indent=2)
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the AI delivery-risk advisor."
    )
    parser.add_argument(
        "snapshot_file",
        type=Path,
        help="Path to a snapshot inside the data directory.",
    )
    arguments = parser.parse_args()

    asyncio.run(
        run_agent(arguments.snapshot_file)
    )


if __name__ == "__main__":
    main()