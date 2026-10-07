from delivery_risk_agent.jira_reader import issue_to_work_item, fetch_jira_snapshot
from delivery_risk_agent.models import Priority, WorkItemStatus
from unittest.mock import patch


def test_jira_issue_maps_to_unassigned_high_priority_work():
    issue = {
        "key": "RISK-1",
        "fields": {
            "summary": "Implement payment API",
            "priority": {"name": "High"},
            "status": {
                "statusCategory": {"key": "new"},
            },
            "assignee": None,
            "created": "2026-10-07T10:49:56.520+0200",
            "duedate": None,
        },
    }

    item = issue_to_work_item(issue)

    assert item.id == "RISK-1"
    assert item.title == "Implement payment API"
    assert item.priority == Priority.HIGH
    assert item.status == WorkItemStatus.TODO
    assert item.assignee is None
    assert item.created_at.utcoffset().total_seconds() == 7200
    assert item.due_at is None


def test_jira_issue_preserves_assignee_and_done_status():
    issue = {
        "key": "RISK-2",
        "fields": {
            "summary": "Update documentation",
            "priority": {"name": "Low"},
            "status": {
                "statusCategory": {"key": "done"},
            },
            "assignee": {"accountId": "test-account"},
            "created": "2026-10-07T09:00:00+0000",
            "duedate": None,
        },
    }

    item = issue_to_work_item(issue)

    assert item.priority == Priority.LOW
    assert item.status == WorkItemStatus.DONE
    assert item.assignee == "test-account"


def test_jira_snapshot_fetches_multiple_pages():
    def make_issue(key: str) -> dict:
        return {
            "key": key,
            "fields": {
                "summary": f"Test issue {key}",
                "priority": {"name": "High"},
                "status": {
                    "statusCategory": {"key": "new"},
                },
                "assignee": None,
                "created": "2026-10-07T09:00:00+0000",
                "duedate": None,
            },
        }

    pages = [
        {
            "issues": [make_issue("RISK-1")],
            "isLast": False,
            "nextPageToken": "page-two",
        },
        {
            "issues": [make_issue("RISK-2")],
            "isLast": True,
        },
    ]

    with patch(
        "delivery_risk_agent.jira_reader.get_jira_json",
        side_effect=pages,
    ) as get_json:
        snapshot = fetch_jira_snapshot("risk")

    assert snapshot.name == "Jira: RISK"
    assert [item.id for item in snapshot.work_items] == [
        "RISK-1",
        "RISK-2",
    ]
    assert get_json.call_count == 2

    first_call, second_call = get_json.call_args_list

    assert first_call.args[0] == "/rest/api/3/search/jql"
    assert first_call.args[1]["jql"] == (
        'project = "RISK" ORDER BY key ASC'
    )
    assert "nextPageToken" not in first_call.args[1]
    assert second_call.args[1]["nextPageToken"] == "page-two"