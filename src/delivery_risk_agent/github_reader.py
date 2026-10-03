import argparse
import json
from urllib.parse import quote
from urllib.request import Request, urlopen


def get_json(url: str): 
    request = Request(
        url, 
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "delivery-risk-agent",
        }
    )

    with urlopen(request, timeout=15) as response: 
        return json.load(response)

def summarize_checks(checks: list[dict]) -> str:
    if not checks: 
        return "unknown"

    failed_conclusion = {
        "failure",
        "timed_out",
        "cancelled",
        "action_required",
        "startup_failure",
    }

    if any(
        check['conclusion'] in failed_conclusion
        for check in checks
    ):
        return "failing"

    if any(
        check['status'] != "completed"
        for check in checks
    ):
        return "pending"

    if all(
        check['conclusion'] == "success"
        for check in checks
    ): 
        return "passing"

    return "unknown"

def show_pull_requests(owner: str, repo: str) -> None:
    owner = quote(owner, safe="")
    repo = quote(repo, safe="")

    pulls_url = (
        f"https://api.github.com/repos/{owner}/{repo}/pulls"
        "?state=open&per_page=5"
    )
    pull_requests = get_json(pulls_url)

    for pull_request in pull_requests:
        number = pull_request["number"]
        title = pull_request["title"]
        commit_sha = pull_request["head"]["sha"]

        print(f"\nPR #{number}: {title}")

        checks_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/commits/{commit_sha}/check-runs"
        )
        checks = get_json(checks_url)["check_runs"]
        print(f" Overall check state: {summarize_checks(checks)}")

        if not checks:
            print("  Check state: unknown (no check runs returned)")
            continue

        for check in checks:
            conclusion = check["conclusion"] or "not completed"
            print(
                f"  {check['name']}: "
                f"{check['status']} ({conclusion})"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect open GitHub pull requests and their checks."
    )
    parser.add_argument("owner", help="GitHub account or organization")
    parser.add_argument("repo", help="Repository name")
    arguments = parser.parse_args()

    show_pull_requests(arguments.owner, arguments.repo)


if __name__ == "__main__":
    main()