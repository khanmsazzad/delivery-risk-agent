import base64
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from delivery_risk_agent.models import (
    Priority,
    ProjectSnapshot,
    WorkItem,
    WorkItemStatus,
)
from delivery_risk_agent.risk_rules import analyze_project


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PRIORITY_MAPPING = {
    "Highest": Priority.CRITICAL,
    "High": Priority.HIGH,
    "Medium": Priority.MEDIUM,
    "Low": Priority.LOW,
    "Lowest": Priority.LOW,
}

STATUS_CATEGORY_MAPPING = {
    "new": WorkItemStatus.TODO,
    "indeterminate": WorkItemStatus.IN_PROGRESS,
    "done": WorkItemStatus.DONE,
}


# NEW: Shared authentication and HTTP request function.
def get_jira_json(path: str, params: dict) -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    required_variables = (
        "JIRA_BASE_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
    )
    missing = [
        name for name in required_variables
        if not os.getenv(name)
    ]

    if missing:
        raise ValueError(
            f"Missing configuration: {', '.join(missing)}"
        )

    base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
    email = os.environ["JIRA_EMAIL"]
    token = os.environ["JIRA_API_TOKEN"]

    credentials = base64.b64encode(
        f"{email}:{token}".encode("utf-8")
    ).decode("ascii")

    query = urlencode(params)
    url = f"{base_url}{path}?{query}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {credentials}",
        },
    )

    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_jira_issue(issue_key: str) -> dict:
    return get_jira_json(
        f"/rest/api/3/issue/{quote(issue_key, safe='')}",
        {
            "fields": "summary,priority,status,assignee,created,duedate",
        },
    )


def issue_to_work_item(issue: dict) -> WorkItem:
    fields = issue["fields"]
    priority_name = (fields.get("priority") or {}).get("name")
    category = fields["status"]["statusCategory"]["key"]

    if priority_name not in PRIORITY_MAPPING:
        raise ValueError(
            f"Unsupported Jira priority: {priority_name}"
        )

    if category not in STATUS_CATEGORY_MAPPING:
        raise ValueError(
            f"Unsupported Jira status category: {category}"
        )

    assignee = fields.get("assignee")
    due_date = fields.get("duedate")

    return WorkItem(
        id=issue["key"],
        title=fields["summary"],
        priority=PRIORITY_MAPPING[priority_name],
        status=STATUS_CATEGORY_MAPPING[category],
        assignee=assignee["accountId"] if assignee else None,
        created_at=datetime.fromisoformat(fields["created"]),
        due_at=(
            datetime.fromisoformat(due_date).replace(tzinfo=UTC)
            if due_date
            else None
        ),
        blocked_by=[],
    )


# NEW: Fetches all accessible issues in a project, following pagination.
def fetch_jira_snapshot(project_key: str) -> ProjectSnapshot:
    project_key = project_key.strip().upper()

    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", project_key):
        raise ValueError("Enter a valid Jira project key, such as RISK.")

    issues = []
    next_page_token = None
    seen_tokens = set()

    while True:
        params = {
            "jql": f'project = "{project_key}" ORDER BY key ASC',
            "fields": "summary,priority,status,assignee,created,duedate",
            "maxResults": 100,
        }

        if next_page_token:
            params["nextPageToken"] = next_page_token

        page = get_jira_json("/rest/api/3/search/jql", params)
        issues.extend(page["issues"])

        if page.get("isLast") is True:
            break

        next_page_token = page.get("nextPageToken")

        if not next_page_token or next_page_token in seen_tokens:
            raise ValueError("Jira returned an invalid pagination response.")

        seen_tokens.add(next_page_token)

    return ProjectSnapshot(
        name=f"Jira: {project_key}",
        captured_at=datetime.now(UTC),
        work_items=[
            issue_to_work_item(issue)
            for issue in issues
        ],
    )


# UPDATED: Analyzes the configured project instead of one hardcoded issue.
def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    project_key = os.getenv("JIRA_PROJECT_KEY")
    if not project_key:
        raise ValueError("Missing configuration: JIRA_PROJECT_KEY")

    snapshot = fetch_jira_snapshot(project_key)
    findings = analyze_project(snapshot)

    print(f"Project: {snapshot.name}")
    print(f"Issues inspected: {len(snapshot.work_items)}")
    print(f"Findings: {len(findings)}")

    print(json.dumps(
        [finding.model_dump(mode="json") for finding in findings],
        indent=2,
    ))


if __name__ == "__main__":
    main()