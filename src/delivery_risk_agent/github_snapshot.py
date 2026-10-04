
import argparse
import asyncio
from datetime import UTC, datetime
from urllib.parse import quote

from delivery_risk_agent.agent import generate_assessment_from_snapshot
from delivery_risk_agent.github_reader import (
    get_json,
    summarize_checks,
)
from delivery_risk_agent.models import (
    ProjectSnapshot,
    PullRequest,
)


def fetch_github_snapshot(
        owner:str, 
        repo:str,
) -> ProjectSnapshot:
    encoded_owner = quote(owner,safe="")
    encoded_repo = quote(repo, safe="")

    pulls_url = (
        f"https://api.github.com/repos/"
        f"{encoded_owner}/{encoded_repo}/pulls"
        "?state=open&per_page=5"
    )
    github_pulls = get_json(pulls_url)

    pull_requests = []

    for github_pr in github_pulls:
        commit_sha = github_pr["head"]["sha"]
        checks_url = (
            f"https://api.github.com/repos/"
            f"{encoded_owner}/{encoded_repo}"
            f"/commits/{commit_sha}/check-runs"
        )

        checks = get_json(checks_url)["check_runs"]

        failed_checks = [
            f"{check['name']} ({check['conclusion']})"
            for check in checks
                if check["conclusion"] in {
                    "failure",
                    "timed_out",
                    "cancelled",
                    "action_required",
                    "startup_failure",
                }
        ]

        check_state = summarize_checks(checks)

        # Pending and unknown remain None, so they cannot
        # trigger the failing-CI rule.
        ci_passed = {
            "passing": True,
            "failing": False,
        }.get(check_state)

        pull_requests.append(
            PullRequest(
                number=github_pr["number"],
                title=github_pr["title"],
                author=(
                    (github_pr.get("user") or {}).get("login")
                    or "unknown"
                ),
                created_at=datetime.fromisoformat(
                    github_pr["created_at"]
                ),
                linked_work_item=None,
                approved=None,
                ci_passed=ci_passed,
                failed_checks=failed_checks,
            )
        )

    return ProjectSnapshot(
        name=f"GitHub: {owner}/{repo} (first 5 open PRs)",
        captured_at=datetime.now(UTC),
        work_items=[],
        pull_requests=pull_requests,
    )



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze open PRs from a public GitHub repo."
    )
    parser.add_argument("owner")
    parser.add_argument("repo")
    arguments = parser.parse_args()

    snapshot = fetch_github_snapshot(
        arguments.owner,
        arguments.repo,
    )
    
    assessment = asyncio.run(
        generate_assessment_from_snapshot(snapshot)
    )

    print(assessment.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
