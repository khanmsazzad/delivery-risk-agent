import argparse
import asyncio
from pathlib import Path

from agents import (
    Agent,
    ModelSettings,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from delivery_risk_agent.agent_tools import (
    analyze_delivery_risks,
)
from delivery_risk_agent.models import (
    DeliveryRiskAssessment,
)

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
        "Always use the analyze_delivery_risks tool before making conclusions. "
        "Use only the findings returned by the tool. "
        "Include every finding returned by the tool. "
        "Copy each finding's title, severity, and evidence exactly. "
        "Never calculate, change, downgrade, or upgrade a severity. "
        "Rank risks from most important to least important. "
        "Every recommended action must address a detected risk. "
        "Do not invent missing facts."
    ),
    tools=[analyze_delivery_risks],
    output_type=DeliveryRiskAssessment, 
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)


async def generate_assessment(
        snapshot_file: Path, 
) -> DeliveryRiskAssessment: 
    request = (
         f"Analyze the project snapshot at {snapshot_file}. "
        "Give me an executive summary, prioritized risks, "
        "and recommended next actions."
    )

    result = await Runner.run(
        delivery_risk_agent, 
        request,
    )

    assessment = result.final_output

    if not isinstance(
        assessment,
        DeliveryRiskAssessment
    ): 
        raise TypeError(
            "The agend did not return a valid " \
            "DeliveryRiskAssessment"
        )
    return assessment

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