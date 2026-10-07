import asyncio
import re
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIError, APITimeoutError
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from delivery_risk_agent.agent import generate_assessment_from_snapshot
from delivery_risk_agent.github_snapshot import fetch_github_snapshot
from delivery_risk_agent.models import (
    DeliveryRiskAssessment,
    ProjectSnapshot,
    RiskFinding,
)
from delivery_risk_agent.risk_rules import analyze_project
from delivery_risk_agent.jira_reader import fetch_jira_snapshot

app = FastAPI(title="Delivery Risk Dashboard")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_SNAPSHOT = PROJECT_ROOT / "data" / "sample_project.json"

class DashboardResponse(BaseModel):
    project_name: str
    captured_at: datetime
    findings: list[RiskFinding]


@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    snapshot = ProjectSnapshot.model_validate_json(
        SAMPLE_SNAPSHOT.read_text(encoding="utf-8")
    )

    return DashboardResponse(
        project_name=snapshot.name,
        captured_at=snapshot.captured_at,
        findings=analyze_project(snapshot),
    )


class GitHubAnalysisRequest(BaseModel):
    repository_url: str


class GitHubAnalysisResponse(BaseModel):
    project_name: str
    captured_at: datetime
    assessment: DeliveryRiskAssessment


@app.post("/api/analyze/github", response_model=GitHubAnalysisResponse)
async def analyze_github(
    request: GitHubAnalysisRequest
)-> GitHubAnalysisResponse:
    repository_url = request.repository_url.strip()

    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?",
        repository_url,
    )

    if match is None:
        raise HTTPException(
            status_code=422,
            detail="Enter a repository URL such as https://github.com/owner/repo.",
        )


    owner, repo = match.groups()

    try:
        snapshot = await run_in_threadpool(
            fetch_github_snapshot, owner, repo
        )
    except HTTPError as error:
        if error.code == 404:
            detail = "Repository not found or not publicly accessible."
        elif error.code in {403, 429}:
            detail = "GitHub denied the request or its rate limit was reached."
        else:
            detail = "GitHub could not complete the request."

        raise HTTPException(status_code=502, detail=detail) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub. Please try again.",
        ) from error

    try:
        assessment = await asyncio.wait_for(
            generate_assessment_from_snapshot(snapshot),
            timeout=600,
        )
    except (TimeoutError, APITimeoutError) as error:
        raise HTTPException(
            status_code=504,
            detail="The AI advisor took too long. Please try again.",
        ) from error
    except APIConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="The local AI advisor is unavailable. Start the model server.",
        ) from error
    except (APIError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail="The AI advisor could not produce a valid assessment.",
        ) from error

    return GitHubAnalysisResponse(
        project_name=snapshot.name,
        captured_at=snapshot.captured_at,
        assessment=assessment,
    )


class JiraAnalysisRequest(BaseModel):
    project_key: str


class JiraAnalysisResponse(BaseModel):
    project_name: str
    captured_at: datetime
    issues_inspected: int
    assessment: DeliveryRiskAssessment


@app.post("/api/analyze/jira", response_model=JiraAnalysisResponse)
async def analyze_jira(
    request: JiraAnalysisRequest,
) -> JiraAnalysisResponse:
    project_key = request.project_key.strip().upper()

    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", project_key):
        raise HTTPException(
            status_code=422,
            detail="Enter a valid Jira project key",
        )

    try:
        snapshot = await run_in_threadpool(
            fetch_jira_snapshot, project_key
        )
    except HTTPError as error:
        if error.code == 401:
            detail = "Jira authentication failed. Check the backend credentials."
        elif error.code == 403:
            detail = "The configured Jira account does not have access."
        elif error.code in {400, 404}:
            detail = "Jira could not find or access the requested project."
        elif error.code == 429:
            detail = "Jira's rate limit was reached. Please try again later."
        else:
            detail = "Jira could not complete the request."

        raise HTTPException(status_code=502, detail=detail) from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Jira. Please try again.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to load Jira issues. Check the backend configuration "
                "and priority/status mappings."
            ),
        ) from error

    if not snapshot.work_items:
        raise HTTPException(
            status_code=404,
            detail=(
                "No accessible issues were returned for this project. "
                "Check the project key, permissions, and whether it has issues."
            ),
        )

    try:
        assessment = await asyncio.wait_for(
            generate_assessment_from_snapshot(snapshot),
            timeout=600,
        )
    except (TimeoutError, APITimeoutError) as error:
        raise HTTPException(
            status_code=504,
            detail="The AI advisor took too long. Please try again.",
        ) from error
    except APIConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="The local AI advisor is unavailable. Start the model server.",
        ) from error
    except (APIError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail="The AI advisor could not produce a valid assessment.",
        ) from error

    return JiraAnalysisResponse(
        project_name=snapshot.name,
        captured_at=snapshot.captured_at,
        issues_inspected=len(snapshot.work_items),
        assessment=assessment,
    )